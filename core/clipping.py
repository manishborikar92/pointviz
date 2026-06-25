"""Working Set Clipping — state and computation.

Implements Working Set Clipping semantics: non-destructive filtering
where the original dataset is preserved and a boolean mask defines
the visible (active) subset.

Architecture: Pure Python/NumPy. No Qt, VTK, or GUI dependencies.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
import numpy as np


class ClippingMode(Enum):
    """Supported clipping region types."""
    DISABLED = "disabled"
    BOX = "box"
    # Future: PLANE = "plane", POLYGON = "polygon"


@dataclass
class ClippingState:
    """Immutable snapshot of clipping configuration."""
    mode: ClippingMode = ClippingMode.DISABLED
    bounds: Optional[Tuple[float, ...]] = None  # (xmin,xmax,ymin,ymax,zmin,zmax) - keep for backward compatibility
    transform_matrix: Optional[np.ndarray] = None  # 4x4 forward transform matrix
    inverse_transform_matrix: Optional[np.ndarray] = None  # 4x4 inverse transform matrix
    ref_bounds: Optional[Tuple[float, ...]] = None  # (xmin,xmax,ymin,ymax,zmin,zmax) in local coords
    active_mask: Optional[np.ndarray] = None  # (N,) boolean mask of active points
    invert: bool = False
    clipped_count: int = 0
    original_count: int = 0

    @property
    def is_active(self) -> bool:
        """Return True if clipping is currently applied."""
        return self.mode != ClippingMode.DISABLED

    @property
    def summary(self) -> str:
        """Human-readable summary for status bar / UI labels."""
        if not self.is_active:
            return ""
        return f"Showing {self.clipped_count:,} of {self.original_count:,} points"


def compute_obb_mask(
    points: np.ndarray,
    transform_matrix: np.ndarray,
    ref_bounds: Tuple[float, float, float, float, float, float],
    invert: bool = False,
) -> np.ndarray:
    """Compute a boolean mask for oriented bounding box clipping.

    Parameters
    ----------
    points : np.ndarray
        (N, 3) array of point coordinates.
    transform_matrix : np.ndarray
        (4, 4) forward transformation matrix from local to world coordinates.
    ref_bounds : tuple of 6 floats
        (xmin, xmax, ymin, ymax, zmin, zmax) defining the box in local coordinates.
    invert : bool
        If True, select points OUTSIDE the box instead of inside.

    Returns
    -------
    np.ndarray
        (N,) boolean mask. True = point is in the selected region.
    """
    if len(points) == 0:
        return np.array([], dtype=bool)

    # 1. Check for singular/ill-conditioned transform matrix
    try:
        cond = np.linalg.cond(transform_matrix)
        if not np.isfinite(cond) or cond > 1e12:
            return np.ones(len(points), dtype=bool)
        m_inv = np.linalg.inv(transform_matrix)
    except (np.linalg.LinAlgError, ValueError, TypeError):
        # Fall back to selecting all points (True) if matrix is singular/non-invertible/invalid
        return np.ones(len(points), dtype=bool)

    # 3. Transform points using inverse matrix (Optimized: points @ R_inv.T + t_inv)
    R_inv = m_inv[:3, :3]
    t_inv = m_inv[:3, 3]
    local_points = points @ R_inv.T + t_inv

    # 4. Perform bounds check in local coordinate space
    xmin, xmax, ymin, ymax, zmin, zmax = ref_bounds
    if (xmax - xmin <= 1e-7) or (ymax - ymin <= 1e-7) or (zmax - zmin <= 1e-7):
        return np.ones(len(points), dtype=bool)

    mask = (
        (local_points[:, 0] >= xmin) & (local_points[:, 0] <= xmax) &
        (local_points[:, 1] >= ymin) & (local_points[:, 1] <= ymax) &
        (local_points[:, 2] >= zmin) & (local_points[:, 2] <= zmax)
    )
    if invert:
        mask = ~mask
    return mask

def apply_mask(
    points: np.ndarray,
    mask: np.ndarray,
    colors: Optional[np.ndarray] = None,
    scalars: Optional[np.ndarray] = None,
) -> Dict[str, Optional[np.ndarray]]:
    """Apply a boolean mask to filter points and associated arrays.

    Parameters
    ----------
    points : np.ndarray
        (N, 3) point coordinates.
    mask : np.ndarray
        (N,) boolean mask.
    colors : np.ndarray or None
        (N, 3) color array to filter in parallel.
    scalars : np.ndarray or None
        (N,) or (N, K) scalar array to filter in parallel.

    Returns
    -------
    dict
        {'points': filtered_points, 'colors': filtered_colors, 'scalars': filtered_scalars}
    """
    result: Dict[str, Optional[np.ndarray]] = {
        'points': points[mask],
        'colors': colors[mask] if colors is not None else None,
        'scalars': scalars[mask] if scalars is not None else None,
    }
    return result


def get_cloud_bounds(points: np.ndarray) -> Tuple[float, float, float, float, float, float]:
    """Compute axis-aligned bounding box from a point array.

    Parameters
    ----------
    points : np.ndarray
        (N, 3) point coordinates.

    Returns
    -------
    tuple
        (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    return (float(mins[0]), float(maxs[0]),
            float(mins[1]), float(maxs[1]),
            float(mins[2]), float(maxs[2]))
