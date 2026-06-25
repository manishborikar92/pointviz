"""Unit tests for core.clipping module.

Tests Working Set Clipping: mask computation, apply_mask,
bounds calculation, ClippingState, and edge cases.
"""
import numpy as np
import pytest
import time

from core.clipping import (
    ClippingMode,
    ClippingState,
    compute_obb_mask,
    apply_mask,
    get_cloud_bounds,
)


def compute_box_mask(points, bounds, invert=False):
    """Helper to route legacy AABB tests to compute_obb_mask with identity transform."""
    return compute_obb_mask(points, np.identity(4), bounds, invert=invert)


# --- Fixtures ---

@pytest.fixture
def sample_points():
    """10 points in a known grid pattern for deterministic testing."""
    return np.array([
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


@pytest.fixture
def sample_colors():
    """Color array matching sample_points."""
    return np.tile([128, 64, 32], (10, 1)).astype(np.uint8)


# --- ClippingState Tests ---

class TestClippingState:
    def test_default_state_is_disabled(self):
        state = ClippingState()
        assert state.mode == ClippingMode.DISABLED
        assert not state.is_active
        assert state.summary == ""

    def test_active_state_summary(self):
        state = ClippingState(
            mode=ClippingMode.BOX,
            bounds=(0, 1, 0, 1, 0, 1),
            clipped_count=500,
            original_count=1000,
        )
        assert state.is_active
        assert state.summary == "Showing 500 of 1,000 points"

    def test_zero_clipped_count_summary(self):
        state = ClippingState(
            mode=ClippingMode.BOX,
            clipped_count=0,
            original_count=1000,
        )
        assert state.summary == "Showing 0 of 1,000 points"

    def test_large_counts_formatting(self):
        state = ClippingState(
            mode=ClippingMode.BOX,
            clipped_count=142305,
            original_count=500000,
        )
        assert "142,305" in state.summary
        assert "500,000" in state.summary


# --- compute_box_mask Tests ---

class TestComputeBoxMask:
    def test_full_bounds_selects_all(self, sample_points):
        bounds = (0.0, 2.0, 0.0, 1.0, 0.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        assert mask.all()
        assert mask.dtype == bool

    def test_partial_bounds_selects_subset(self, sample_points):
        # Select only points where x <= 1.0
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        selected = sample_points[mask]
        assert all(p[0] <= 1.0 for p in selected)
        # Points at x=0, x=1 are selected; x=2 excluded
        assert mask.sum() == 7  # 7 points have x <= 1.0

    def test_empty_bounds_selects_none(self, sample_points):
        # Bounds that contain no points
        bounds = (10.0, 20.0, 10.0, 20.0, 10.0, 20.0)
        mask = compute_box_mask(sample_points, bounds)
        assert mask.sum() == 0

    def test_single_point_bounds(self, sample_points):
        # Bounds exactly at a single point (degenerate case, should select all points)
        bounds = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        assert mask.all()

    def test_invert_flag(self, sample_points):
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        mask_normal = compute_box_mask(sample_points, bounds, invert=False)
        mask_inverted = compute_box_mask(sample_points, bounds, invert=True)
        # Inverted mask should be complement
        assert np.all(mask_normal == ~mask_inverted)
        assert mask_normal.sum() + mask_inverted.sum() == len(sample_points)

    def test_boundary_inclusive(self, sample_points):
        # Points exactly on the boundary should be included (>= and <=)
        bounds = (1.0, 2.0, 0.0, 1.0, 0.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        # All points with x in [1,2], y in [0,1], z in [0,1] are included
        for i, p in enumerate(sample_points):
            if 1.0 <= p[0] <= 2.0 and 0.0 <= p[1] <= 1.0 and 0.0 <= p[2] <= 1.0:
                assert mask[i], f"Point {p} should be inside bounds"

    def test_returns_correct_shape(self, sample_points):
        bounds = (0.0, 2.0, 0.0, 1.0, 0.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        assert mask.shape == (len(sample_points),)


# --- apply_mask Tests ---

class TestApplyMask:
    def test_filters_points_correctly(self, sample_points):
        mask = np.array([True, False, True, False, True, False, True, False, True, False])
        result = apply_mask(sample_points, mask)
        assert len(result['points']) == 5
        np.testing.assert_array_equal(result['points'][0], sample_points[0])

    def test_filters_colors_in_parallel(self, sample_points, sample_colors):
        mask = np.array([True, True, False, False, True, False, True, False, False, True])
        result = apply_mask(sample_points, mask, colors=sample_colors)
        assert result['colors'] is not None
        assert len(result['colors']) == mask.sum()

    def test_none_colors_returns_none(self, sample_points):
        mask = np.ones(len(sample_points), dtype=bool)
        result = apply_mask(sample_points, mask, colors=None)
        assert result['colors'] is None

    def test_none_scalars_returns_none(self, sample_points):
        mask = np.ones(len(sample_points), dtype=bool)
        result = apply_mask(sample_points, mask, scalars=None)
        assert result['scalars'] is None

    def test_filters_scalars(self, sample_points):
        scalars = np.arange(10, dtype=np.float64)
        mask = np.array([True, False, True, False, True, False, True, False, True, False])
        result = apply_mask(sample_points, mask, scalars=scalars)
        assert result['scalars'] is not None
        np.testing.assert_array_equal(result['scalars'], [0, 2, 4, 6, 8])

    def test_all_false_mask(self, sample_points, sample_colors):
        mask = np.zeros(len(sample_points), dtype=bool)
        result = apply_mask(sample_points, mask, colors=sample_colors)
        assert len(result['points']) == 0
        assert len(result['colors']) == 0

    def test_all_true_mask(self, sample_points, sample_colors):
        mask = np.ones(len(sample_points), dtype=bool)
        result = apply_mask(sample_points, mask, colors=sample_colors)
        assert len(result['points']) == len(sample_points)
        np.testing.assert_array_equal(result['points'], sample_points)


# --- get_cloud_bounds Tests ---

class TestGetCloudBounds:
    def test_correct_bounds(self, sample_points):
        bounds = get_cloud_bounds(sample_points)
        assert bounds == (0.0, 2.0, 0.0, 1.0, 0.0, 1.0)

    def test_single_point(self):
        points = np.array([[5.0, 3.0, 7.0]])
        bounds = get_cloud_bounds(points)
        assert bounds == (5.0, 5.0, 3.0, 3.0, 7.0, 7.0)

    def test_negative_coordinates(self):
        points = np.array([[-1.0, -2.0, -3.0], [1.0, 2.0, 3.0]])
        bounds = get_cloud_bounds(points)
        assert bounds == (-1.0, 1.0, -2.0, 2.0, -3.0, 3.0)

    def test_returns_floats(self, sample_points):
        bounds = get_cloud_bounds(sample_points)
        assert all(isinstance(b, float) for b in bounds)


# --- Integration: compute_box_mask + apply_mask pipeline ---

class TestClippingPipeline:
    def test_full_pipeline(self, sample_points, sample_colors):
        """Test the complete clip pipeline: bounds -> mask -> filter."""
        # Clip to lower-left octant
        bounds = (0.0, 1.0, 0.0, 0.5, 0.0, 0.5)
        mask = compute_box_mask(sample_points, bounds)
        result = apply_mask(sample_points, mask, colors=sample_colors)

        # Verify all filtered points are within bounds
        for p in result['points']:
            assert 0.0 <= p[0] <= 1.0
            assert 0.0 <= p[1] <= 0.5
            assert 0.0 <= p[2] <= 0.5

    def test_clip_preserves_original(self, sample_points):
        """Verify that clipping does NOT modify the original array."""
        original_copy = sample_points.copy()
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        mask = compute_box_mask(sample_points, bounds)
        _ = apply_mask(sample_points, mask)
        np.testing.assert_array_equal(sample_points, original_copy)

    def test_roundtrip_full_bounds(self, sample_points):
        """Clipping with full bounds should return all points."""
        bounds = get_cloud_bounds(sample_points)
        mask = compute_box_mask(sample_points, bounds)
        result = apply_mask(sample_points, mask)
        assert len(result['points']) == len(sample_points)


# --- Performance sanity check ---

class TestClippingPerformance:
    @pytest.mark.parametrize("n_points", [100_000, 500_000])
    def test_mask_computation_time(self, n_points):
        """Verify mask computation completes in reasonable time."""
        points = np.random.rand(n_points, 3).astype(np.float64) * 100
        bounds = (10.0, 90.0, 10.0, 90.0, 10.0, 90.0)

        start = time.perf_counter()
        mask = compute_box_mask(points, bounds)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert mask.shape == (n_points,)
        # Should complete well under 100ms even for 500K
        assert elapsed_ms < 500, f"Mask computation took {elapsed_ms:.1f}ms for {n_points} points"


# --- compute_obb_mask Tests ---

class TestComputeObbMask:
    def test_identity_rotation_equals_aabb(self, sample_points):
        """Verify compute_obb_mask with identity transform yields identical results to compute_box_mask."""
        from core.clipping import compute_obb_mask
        bounds = (0.0, 1.5, 0.0, 1.0, 0.0, 1.0)
        identity_transform = np.identity(4)

        mask_aabb = compute_box_mask(sample_points, bounds)
        mask_obb = compute_obb_mask(sample_points, identity_transform, bounds)

        np.testing.assert_array_equal(mask_aabb, mask_obb)

    def test_translation_masking(self, sample_points):
        """Verify translation of oriented bounding box works correctly."""
        from core.clipping import compute_obb_mask
        # Box centered initially around [0.5, 0.5, 0.5] with bounds [0, 1, 0, 1, 0, 1]
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        
        # Translate the box by [1.0, 0.0, 0.0]
        # Transform matrix represents local-to-world mapping, so a translation by [1, 0, 0]
        transform = np.identity(4)
        transform[0, 3] = 1.0

        # Now the box in world coordinates is at [1, 2, 0, 1, 0, 1]
        mask_obb = compute_obb_mask(sample_points, transform, bounds)
        
        # Check which points should be inside (X coordinates in [1.0, 2.0] inclusive)
        # sample_points at:
        # [1,0,0] (idx 1), [2,0,0] (idx 2), [1,1,0] (idx 4), [2,1,0] (idx 5), 
        # [1,0,1] (idx 7), [2,0,1] (idx 8), [1,1,1] (idx 9)
        expected_indices = [1, 2, 4, 5, 7, 8, 9]
        actual_indices = np.where(mask_obb)[0].tolist()
        assert set(actual_indices) == set(expected_indices)

    def test_rotation_masking(self):
        """Verify rotation of oriented bounding box works correctly."""
        from core.clipping import compute_obb_mask
        # Let's test a simple rotated box.
        # Initial box bounds: [-1, 1, -1, 1, -1, 1]
        bounds = (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
        
        # Rotate by 45 degrees around Z axis
        angle = np.radians(45.0)
        c, s = np.cos(angle), np.sin(angle)
        transform = np.identity(4)
        transform[:2, :2] = [[c, -s], [s, c]]

        # Points to test
        points = np.array([
            [0.0, 0.0, 0.0],    # Center: inside
            [1.0, 0.0, 0.0],    # Corner in unrotated local: [cos(45), -sin(45)] in local which is inside
            [1.5, 0.0, 0.0],    # Far along world X: outside (local is [1.5*cos(45), -1.5*sin(45)] = [1.06, -1.06] which is outside [-1, 1])
            [1.41, 1.41, 0.0],  # Way outside
        ])
        
        mask = compute_obb_mask(points, transform, bounds)
        np.testing.assert_array_equal(mask, [True, True, False, False])

    def test_degenerate_bounds_handling(self, sample_points):
        """Verify degenerate box dimensions do not crash and fall back to all-True mask."""
        from core.clipping import compute_obb_mask
        transform = np.identity(4)
        
        # Zero width
        bounds_zero_width = (1.0, 1.0, 0.0, 2.0, 0.0, 2.0)
        mask = compute_obb_mask(sample_points, transform, bounds_zero_width)
        assert mask.all()

        # Zero height
        bounds_zero_height = (0.0, 2.0, 1.0, 1.0, 0.0, 2.0)
        mask = compute_obb_mask(sample_points, transform, bounds_zero_height)
        assert mask.all()

    def test_singular_matrix_handling(self, sample_points):
        """Verify singular transform matrix falls back to all-True mask without crash."""
        from core.clipping import compute_obb_mask
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        
        # Singular matrix (all zeros except one row/column)
        singular_transform = np.zeros((4, 4))
        mask = compute_obb_mask(sample_points, singular_transform, bounds)
        assert mask.all()

    def test_near_singular_matrix_fallback(self, sample_points):
        """Verify near-singular/ill-conditioned or non-finite transform matrix falls back to all-True mask."""
        from core.clipping import compute_obb_mask
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        
        # Scale one dimension to near-zero (ill-conditioned)
        ill_conditioned_transform = np.identity(4)
        ill_conditioned_transform[0, 0] = 1e-15
        
        mask = compute_obb_mask(sample_points, ill_conditioned_transform, bounds)
        assert mask.all()

        # Matrix with NaN
        nan_transform = np.identity(4)
        nan_transform[0, 0] = np.nan
        mask = compute_obb_mask(sample_points, nan_transform, bounds)
        assert mask.all()

    def test_empty_points(self):
        """Verify empty points input returns empty boolean mask."""
        from core.clipping import compute_obb_mask
        points = np.empty((0, 3))
        transform = np.identity(4)
        bounds = (-1, 1, -1, 1, -1, 1)
        mask = compute_obb_mask(points, transform, bounds)
        assert len(mask) == 0
        assert mask.dtype == bool

    def test_invert_flag(self, sample_points):
        """Verify invert flag returns the complement mask."""
        from core.clipping import compute_obb_mask
        bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        transform = np.identity(4)
        
        mask_normal = compute_obb_mask(sample_points, transform, bounds, invert=False)
        mask_inverted = compute_obb_mask(sample_points, transform, bounds, invert=True)
        
        np.testing.assert_array_equal(mask_normal, ~mask_inverted)

