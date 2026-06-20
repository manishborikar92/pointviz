import numpy as np

def calculate_volume(points: np.ndarray) -> float:
    """Calculate bounding box volume."""
    if len(points) == 0:
        return 0.0
    ranges = points.max(axis=0) - points.min(axis=0)
    return float(np.prod(ranges))

def calculate_density(points: np.ndarray, volume: float) -> float:
    """Calculate point density."""
    if volume == 0:
        return 0.0
    return len(points) / volume

def compute_centroid(points: np.ndarray) -> np.ndarray:
    """Calculate centroid of points."""
    if len(points) == 0:
        return np.zeros(3)
    return points.mean(axis=0)

def compute_ranges(points: np.ndarray) -> dict:
    """Calculate min/max for coordinate dimensions."""
    if len(points) == 0:
        return {
            "x": (0.0, 0.0),
            "y": (0.0, 0.0),
            "z": (0.0, 0.0)
        }
    return {
        "x": (float(points[:, 0].min()), float(points[:, 0].max())),
        "y": (float(points[:, 1].min()), float(points[:, 1].max())),
        "z": (float(points[:, 2].min()), float(points[:, 2].max()))
    }

def compute_distance_stats(points: np.ndarray, centroid: np.ndarray) -> dict:
    """Calculate distance statistics from centroid."""
    if len(points) == 0:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
    distances = np.linalg.norm(points - centroid, axis=1)
    return {
        "min": float(distances.min()),
        "max": float(distances.max()),
        "mean": float(distances.mean()),
        "std": float(distances.std())
    }

def compute_color_stats(colors: np.ndarray) -> dict:
    """Calculate RGB channel mean and standard deviation."""
    if len(colors) == 0:
        return {
            "r": {"mean": 0.0, "std": 0.0},
            "g": {"mean": 0.0, "std": 0.0},
            "b": {"mean": 0.0, "std": 0.0}
        }
    return {
        "r": {"mean": float(colors[:, 0].mean()), "std": float(colors[:, 0].std())},
        "g": {"mean": float(colors[:, 1].mean()), "std": float(colors[:, 1].std())},
        "b": {"mean": float(colors[:, 2].mean()), "std": float(colors[:, 2].std())}
    }

def compute_coordinate_stats(points: np.ndarray) -> dict:
    """Calculate coordinate-wise mean and standard deviation."""
    if len(points) == 0:
        return {
            "x": {"mean": 0.0, "std": 0.0},
            "y": {"mean": 0.0, "std": 0.0},
            "z": {"mean": 0.0, "std": 0.0}
        }
    return {
        "x": {"mean": float(points[:, 0].mean()), "std": float(points[:, 0].std())},
        "y": {"mean": float(points[:, 1].mean()), "std": float(points[:, 1].std())},
        "z": {"mean": float(points[:, 2].mean()), "std": float(points[:, 2].std())}
    }
