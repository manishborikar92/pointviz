"""Unit tests for core.measurement module.

Tests MeasurementManager lifecycle, KD-tree snapping, distance/delta
computation, cleanup operations, and edge cases.
"""
import numpy as np
import open3d as o3d
import pytest

from core.measurement import (
    MeasurementMode,
    Measurement,
    MeasurementManager,
)


# --- Fixtures ---

@pytest.fixture
def manager():
    """Fresh MeasurementManager instance."""
    return MeasurementManager()


@pytest.fixture
def sample_pcd():
    """Open3D point cloud with 10 known points."""
    pcd = o3d.geometry.PointCloud()
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0],
        [2.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 1.0],
        [2.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
    ], dtype=np.float64)
    pcd.points = o3d.utility.Vector3dVector(points)
    return pcd


@pytest.fixture
def sample_points(sample_pcd):
    """NumPy array of sample points."""
    return np.asarray(sample_pcd.points)


@pytest.fixture
def indexed_manager(manager, sample_pcd):
    """Manager with KD-tree already built."""
    manager.build_index(sample_pcd)
    return manager


# --- MeasurementManager Initialization ---

class TestManagerInit:
    def test_initial_state(self, manager):
        assert manager.mode == MeasurementMode.INACTIVE
        assert not manager.is_active
        assert not manager.has_measurements
        assert manager.results == []
        assert manager.pending_point is None

    def test_properties_defensive_copy(self, manager):
        results1 = manager.results
        results2 = manager.results
        assert results1 is not results2  # Different list objects


# --- KD-tree Index ---

class TestSpatialIndex:
    def test_build_index_from_pcd(self, manager, sample_pcd):
        manager.build_index(sample_pcd)
        assert manager._kd_tree is not None
        assert manager._points_array is not None
        assert len(manager._points_array) == 10

    def test_build_index_from_points(self, manager, sample_points):
        manager.build_index_from_points(sample_points)
        assert manager._kd_tree is not None
        assert len(manager._points_array) == 10

    def test_snap_to_exact_point(self, indexed_manager):
        result = indexed_manager.snap_to_point(np.array([1.0, 0.0, 0.0]))
        assert result is not None
        idx, coord = result
        np.testing.assert_array_almost_equal(coord, [1.0, 0.0, 0.0])

    def test_snap_to_nearby_point(self, indexed_manager):
        # Slightly off from [1,1,1] — should snap to it
        result = indexed_manager.snap_to_point(np.array([1.05, 0.95, 1.02]))
        assert result is not None
        _, coord = result
        np.testing.assert_array_almost_equal(coord, [1.0, 1.0, 1.0])

    def test_snap_returns_copy(self, indexed_manager):
        result = indexed_manager.snap_to_point(np.array([0.0, 0.0, 0.0]))
        assert result is not None
        _, coord = result
        # Modifying returned coord should not affect internal state
        coord[0] = 999.0
        result2 = indexed_manager.snap_to_point(np.array([0.0, 0.0, 0.0]))
        assert result2 is not None
        _, coord2 = result2
        assert coord2[0] != 999.0

    def test_snap_without_index_returns_none(self, manager):
        result = manager.snap_to_point(np.array([0.0, 0.0, 0.0]))
        assert result is None

    def test_snap_empty_cloud(self, manager):
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.empty((0, 3)))
        manager.build_index_from_points(np.empty((0, 3)))
        result = manager.snap_to_point(np.array([0.0, 0.0, 0.0]))
        assert result is None


# --- Mode Transitions ---

class TestModeTransitions:
    def test_activate(self, manager):
        manager.activate()
        assert manager.mode == MeasurementMode.PICKING_FIRST
        assert manager.is_active

    def test_deactivate(self, manager):
        manager.activate()
        manager.deactivate()
        assert manager.mode == MeasurementMode.INACTIVE
        assert not manager.is_active

    def test_set_first_point(self, manager):
        manager.activate()
        point = np.array([1.0, 2.0, 3.0])
        manager.set_first_point(point)
        assert manager.mode == MeasurementMode.PICKING_SECOND
        np.testing.assert_array_equal(manager.pending_point, point)

    def test_set_first_point_is_copy(self, manager):
        manager.activate()
        point = np.array([1.0, 2.0, 3.0])
        manager.set_first_point(point)
        point[0] = 999.0  # Modify original
        assert manager.pending_point[0] == 1.0  # Should not change

    def test_cancel_pending(self, manager):
        manager.activate()
        manager.set_first_point(np.array([1.0, 2.0, 3.0]))
        manager.cancel_pending()
        assert manager.mode == MeasurementMode.PICKING_FIRST
        assert manager.pending_point is None

    def test_deactivate_clears_pending(self, manager):
        manager.activate()
        manager.set_first_point(np.array([1.0, 2.0, 3.0]))
        manager.deactivate()
        assert manager.pending_point is None


# --- Measurement Creation ---

class TestMeasurementCreation:
    def test_create_measurement_basic(self, manager):
        point_a = np.array([0.0, 0.0, 0.0])
        point_b = np.array([3.0, 4.0, 0.0])
        m = manager.create_measurement(point_a, point_b)

        assert m.id == 0
        assert m.distance == pytest.approx(5.0)
        np.testing.assert_array_almost_equal(m.delta, [3.0, 4.0, 0.0])
        assert m.visible is True
        assert len(m.actor_names) == 4

    def test_delta_components(self, manager):
        point_a = np.array([1.0, 2.0, 3.0])
        point_b = np.array([4.0, 6.0, 3.0])
        m = manager.create_measurement(point_a, point_b)

        np.testing.assert_array_almost_equal(m.delta, [3.0, 4.0, 0.0])
        assert m.distance == pytest.approx(5.0)

    def test_zero_distance(self, manager):
        point = np.array([1.0, 1.0, 1.0])
        m = manager.create_measurement(point, point)
        assert m.distance == pytest.approx(0.0)
        np.testing.assert_array_almost_equal(m.delta, [0.0, 0.0, 0.0])

    def test_monotonic_ids(self, manager):
        for i in range(5):
            m = manager.create_measurement(
                np.array([0.0, 0.0, 0.0]),
                np.array([float(i), 0.0, 0.0])
            )
            assert m.id == i

    def test_auto_transition_after_create(self, manager):
        manager.activate()
        manager.set_first_point(np.array([0.0, 0.0, 0.0]))
        m = manager.create_measurement(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0])
        )
        # Should auto-transition back to PICKING_FIRST
        assert manager.mode == MeasurementMode.PICKING_FIRST
        assert manager.pending_point is None

    def test_results_accumulate(self, manager):
        for i in range(3):
            manager.create_measurement(
                np.array([0.0, 0.0, 0.0]),
                np.array([float(i + 1), 0.0, 0.0])
            )
        assert manager.has_measurements
        assert len(manager.results) == 3

    def test_create_copies_inputs(self, manager):
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([4.0, 5.0, 6.0])
        m = manager.create_measurement(a, b)
        a[0] = 999.0
        b[0] = 999.0
        assert m.point_a[0] == 1.0
        assert m.point_b[0] == 4.0


# --- Actor Name Generation ---

class TestActorNames:
    def test_generate_unique_names(self, manager):
        names0 = manager.generate_actor_names(0)
        names1 = manager.generate_actor_names(1)

        # All 4 keys present
        assert set(names0.keys()) == {'line', 'marker_a', 'marker_b', 'label'}

        # Names are unique across measurements
        all_names = list(names0.values()) + list(names1.values())
        assert len(set(all_names)) == 8  # All unique

    def test_names_contain_id(self, manager):
        names = manager.generate_actor_names(42)
        for name in names.values():
            assert "meas_42" in name


# --- Cleanup ---

class TestCleanup:
    def test_clear_all_returns_actor_names(self, manager):
        manager.create_measurement(np.array([0, 0, 0.0]), np.array([1, 0, 0.0]))
        manager.create_measurement(np.array([0, 0, 0.0]), np.array([0, 1, 0.0]))

        actor_names = manager.clear_all()
        assert len(actor_names) == 8  # 4 actors per measurement × 2
        assert not manager.has_measurements

    def test_clear_all_preserves_next_id(self, manager):
        manager.create_measurement(np.array([0, 0, 0.0]), np.array([1, 0, 0.0]))
        manager.clear_all()
        m = manager.create_measurement(np.array([0, 0, 0.0]), np.array([0, 1, 0.0]))
        assert m.id == 1  # Not reset to 0

    def test_reset_clears_everything(self, indexed_manager):
        indexed_manager.create_measurement(np.array([0, 0, 0.0]), np.array([1, 0, 0.0]))
        indexed_manager.activate()

        actor_names = indexed_manager.reset()
        assert len(actor_names) == 4
        assert indexed_manager.mode == MeasurementMode.INACTIVE
        assert indexed_manager._kd_tree is None
        assert indexed_manager._next_id == 0

    def test_remove_measurements_by_points(self, manager):
        # Create two measurements
        manager.create_measurement(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0])
        )
        manager.create_measurement(
            np.array([5.0, 5.0, 5.0]),
            np.array([6.0, 5.0, 5.0])
        )

        # Visible points include [0,0,0] and [1,0,0] but NOT [5,5,5] or [6,5,5]
        visible = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
        ])

        removed = manager.remove_measurements_by_points(visible)
        assert len(removed) == 1  # Second measurement removed
        assert removed[0].id == 1
        assert len(manager.results) == 1  # First measurement kept
        assert manager.results[0].id == 0

    def test_remove_measurements_empty_visible(self, manager):
        manager.create_measurement(np.array([0, 0, 0.0]), np.array([1, 0, 0.0]))
        removed = manager.remove_measurements_by_points(np.empty((0, 3)))
        assert len(removed) == 1
        assert not manager.has_measurements

    def test_remove_measurements_all_visible(self, manager):
        manager.create_measurement(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0])
        )
        visible = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
        ])
        removed = manager.remove_measurements_by_points(visible)
        assert len(removed) == 0
        assert manager.has_measurements


# --- Full Workflow Integration ---

class TestFullWorkflow:
    def test_complete_measurement_workflow(self, indexed_manager):
        mgr = indexed_manager

        # 1. Activate
        mgr.activate()
        assert mgr.mode == MeasurementMode.PICKING_FIRST

        # 2. Snap and set first point
        result = mgr.snap_to_point(np.array([0.05, 0.05, 0.05]))
        assert result is not None
        _, point_a = result
        mgr.set_first_point(point_a)
        assert mgr.mode == MeasurementMode.PICKING_SECOND

        # 3. Snap and complete measurement
        result = mgr.snap_to_point(np.array([0.95, 0.95, 0.95]))
        assert result is not None
        _, point_b = result
        m = mgr.create_measurement(point_a, point_b)

        # 4. Verify result
        assert m.distance > 0
        assert len(m.actor_names) == 4
        assert mgr.mode == MeasurementMode.PICKING_FIRST  # Ready for next

        # 5. Deactivate
        mgr.deactivate()
        assert mgr.mode == MeasurementMode.INACTIVE
        assert mgr.has_measurements

    def test_esc_cancel_workflow(self, indexed_manager):
        mgr = indexed_manager

        # Activate and pick first point
        mgr.activate()
        mgr.set_first_point(np.array([0.0, 0.0, 0.0]))
        assert mgr.mode == MeasurementMode.PICKING_SECOND

        # ESC — should cancel and go back to INACTIVE
        mgr.deactivate()
        assert mgr.mode == MeasurementMode.INACTIVE
        assert mgr.pending_point is None
        assert not mgr.has_measurements  # No measurement was completed
