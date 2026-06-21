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
    bounds: Optional[Tuple[float, ...]] = None  # (xmin,xmax,ymin,ymax,zmin,zmax)
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


def compute_box_mask(
    points: np.ndarray,
    bounds: Tuple[float, float, float, float, float, float],
    invert: bool = False,
) -> np.ndarray:
    """Compute a boolean mask for axis-aligned bounding box clipping.

    Parameters
    ----------
    points : np.ndarray
        (N, 3) array of point coordinates.
    bounds : tuple of 6 floats
        (xmin, xmax, ymin, ymax, zmin, zmax) defining the clip region.
    invert : bool
        If True, select points OUTSIDE the box instead of inside.

    Returns
    -------
    np.ndarray
        (N,) boolean mask. True = point is in the selected region.
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    mask = (
        (points[:, 0] >= xmin) & (points[:, 0] <= xmax) &
        (points[:, 1] >= ymin) & (points[:, 1] <= ymax) &
        (points[:, 2] >= zmin) & (points[:, 2] <= zmax)
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
