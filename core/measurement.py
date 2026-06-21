"""Distance measurement — state, spatial indexing, and computation.

Manages multi-measurement state, Open3D KD-tree for point snapping,
and distance/delta calculations.

Architecture: Pure Python/NumPy/Open3D. No Qt, VTK, or GUI dependencies.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple, Dict
import numpy as np
import open3d as o3d


class MeasurementMode(Enum):
    """State machine modes for the measurement workflow."""
    INACTIVE = "inactive"
    PICKING_FIRST = "picking_first"
    PICKING_SECOND = "picking_second"


@dataclass
class Measurement:
    """A single distance measurement between two picked points (Option A+)."""
    id: int                      # Monotonic counter
    point_a: np.ndarray          # (3,) first picked point
    point_b: np.ndarray          # (3,) second picked point
    distance: float              # Euclidean distance
    delta: np.ndarray            # (3,) dX, dY, dZ
    actor_names: List[str] = field(default_factory=list)
    visible: bool = True


class MeasurementManager:
    """Manages measurement state, KD-tree index, and results.

    This class owns the measurement lifecycle:
    - Mode transitions (INACTIVE -> PICKING_FIRST -> PICKING_SECOND -> ...)
    - Spatial index for point snapping (Open3D KDTreeFlann)
    - Measurement creation and storage
    - Actor name generation for GUI cleanup
    """

    def __init__(self):
        self.mode: MeasurementMode = MeasurementMode.INACTIVE
        self._kd_tree: Optional[o3d.geometry.KDTreeFlann] = None
        self._points_array: Optional[np.ndarray] = None
        self._pending_point: Optional[np.ndarray] = None
        self._results: List[Measurement] = []
        self._next_id: int = 0

    # --- Properties ---

    @property
    def results(self) -> List[Measurement]:
        """Return a copy of the results list (defensive copy)."""
        return list(self._results)

    @property
    def has_measurements(self) -> bool:
        """Return True if at least one completed measurement exists."""
        return len(self._results) > 0

    @property
    def pending_point(self) -> Optional[np.ndarray]:
        """Return the pending Point A (if in PICKING_SECOND state)."""
        return self._pending_point

    @property
    def is_active(self) -> bool:
        """Return True if measurement mode is active (not INACTIVE)."""
        return self.mode != MeasurementMode.INACTIVE

    # --- Spatial Index ---

    def build_index(self, point_cloud: o3d.geometry.PointCloud) -> None:
        """Build KD-tree spatial index for snap-to-point queries.

        Parameters
        ----------
        point_cloud : o3d.geometry.PointCloud
            The point cloud to index. Can be the full cloud or a clipped subset.
        """
        self._kd_tree = o3d.geometry.KDTreeFlann(point_cloud)
        self._points_array = np.asarray(point_cloud.points)

    def build_index_from_points(self, points: np.ndarray) -> None:
        """Build KD-tree from a raw NumPy array.

        Parameters
        ----------
        points : np.ndarray
            (N, 3) point coordinates.
        """
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        self._kd_tree = o3d.geometry.KDTreeFlann(pcd)
        self._points_array = np.array(points)

    def snap_to_point(self, approx_coord: np.ndarray) -> Optional[Tuple[int, np.ndarray]]:
        """Snap an approximate coordinate to the nearest indexed point.

        Parameters
        ----------
        approx_coord : np.ndarray
            (3,) approximate coordinate from hardware picker.

        Returns
        -------
        tuple(int, np.ndarray) or None
            (point_index, exact_coordinate) or None if no index built.
        """
        if self._kd_tree is None or self._points_array is None:
            return None
        if len(self._points_array) == 0:
            return None

        k, idx, dist = self._kd_tree.search_knn_vector_3d(approx_coord.astype(np.float64), 1)
        if k == 0:
            return None

        point_idx = idx[0]
        exact_coord = self._points_array[point_idx].copy()
        return (point_idx, exact_coord)

    # --- Mode Transitions ---

    def activate(self) -> None:
        """Enter measurement mode (PICKING_FIRST)."""
        self.mode = MeasurementMode.PICKING_FIRST
        self._pending_point = None

    def deactivate(self) -> None:
        """Exit measurement mode, discarding any pending pick."""
        self.mode = MeasurementMode.INACTIVE
        self._pending_point = None

    def set_first_point(self, point: np.ndarray) -> None:
        """Store the first picked point and transition to PICKING_SECOND."""
        self._pending_point = point.copy()
        self.mode = MeasurementMode.PICKING_SECOND

    def cancel_pending(self) -> None:
        """Cancel a pending first-point pick, return to PICKING_FIRST."""
        self._pending_point = None
        self.mode = MeasurementMode.PICKING_FIRST

    # --- Measurement Creation ---

    def create_measurement(self, point_a: np.ndarray, point_b: np.ndarray) -> Measurement:
        """Compute distance and deltas, create and store a Measurement.

        Parameters
        ----------
        point_a, point_b : np.ndarray
            (3,) coordinates of the two endpoints.

        Returns
        -------
        Measurement
            The newly created measurement.
        """
        delta = point_b - point_a
        distance = float(np.linalg.norm(delta))
        actor_names_dict = self.generate_actor_names(self._next_id)

        measurement = Measurement(
            id=self._next_id,
            point_a=point_a.copy(),
            point_b=point_b.copy(),
            distance=distance,
            delta=delta.copy(),
            actor_names=list(actor_names_dict.values()),
            visible=True,
        )

        self._results.append(measurement)
        self._next_id += 1

        # Auto-transition back to PICKING_FIRST for next measurement
        self.mode = MeasurementMode.PICKING_FIRST
        self._pending_point = None

        return measurement

    def generate_actor_names(self, measurement_id: int) -> Dict[str, str]:
        """Generate unique actor names for a measurement's visual overlays.

        Returns
        -------
        dict
            Keys: 'line', 'marker_a', 'marker_b', 'label'
            Values: unique string names for PyVista actors.
        """
        prefix = f"meas_{measurement_id}"
        return {
            'line': f"{prefix}_line",
            'marker_a': f"{prefix}_marker_a",
            'marker_b': f"{prefix}_marker_b",
            'label': f"{prefix}_label",
        }

    def remove_measurement_by_id(self, m_id: int) -> Optional[Measurement]:
        """Remove a measurement by its unique ID.

        Parameters
        ----------
        m_id : int
            The ID of the measurement to remove.

        Returns
        -------
        Measurement or None
            The removed measurement if found, else None.
        """
        for i, m in enumerate(self._results):
            if m.id == m_id:
                return self._results.pop(i)
        return None

    # --- Cleanup ---

    def remove_measurements_by_points(
        self, visible_points: np.ndarray, tolerance: float = 1e-6
    ) -> List[Measurement]:
        """Remove measurements whose endpoints are not in the visible point set.

        Parameters
        ----------
        visible_points : np.ndarray
            (K, 3) currently visible points after clipping.
        tolerance : float
            Distance threshold for considering a point as 'present'.

        Returns
        -------
        list of Measurement
            Measurements that were removed (caller should clean up their actors).
        """
        if len(visible_points) == 0:
            removed = list(self._results)
            self._results.clear()
            return removed

        # Build a temporary KD-tree on visible points for fast lookup
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(visible_points)
        tree = o3d.geometry.KDTreeFlann(pcd)

        keep = []
        removed = []
        for m in self._results:
            # Check if both endpoints exist in visible set
            _, _, dist_a = tree.search_knn_vector_3d(m.point_a.astype(np.float64), 1)
            _, _, dist_b = tree.search_knn_vector_3d(m.point_b.astype(np.float64), 1)

            a_visible = dist_a[0] < (tolerance ** 2)
            b_visible = dist_b[0] < (tolerance ** 2)

            if a_visible and b_visible:
                keep.append(m)
            else:
                removed.append(m)

        self._results = keep
        return removed

    def clear_all(self) -> List[str]:
        """Clear all measurements and return actor names for GUI cleanup.

        Returns
        -------
        list of str
            All actor names that should be removed from the plotter.
        """
        actor_names = []
        for m in self._results:
            actor_names.extend(m.actor_names)
        self._results.clear()
        self._pending_point = None
        # Do not reset _next_id — IDs are monotonic across the session
        return actor_names

    def reset(self) -> List[str]:
        """Full reset: clear results, KD-tree, and mode.

        Returns
        -------
        list of str
            All actor names that should be removed from the plotter.
        """
        actor_names = self.clear_all()
        self.mode = MeasurementMode.INACTIVE
        self._kd_tree = None
        self._points_array = None
        self._next_id = 0
        return actor_names
