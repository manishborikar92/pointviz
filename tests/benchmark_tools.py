"""Tools Benchmark: Clipping and Measurement Performance Validation.

Validates performance against the approved design expectations:
- 100K: <5ms mask, <10ms total pipeline
- 500K: <5ms mask, <25ms total pipeline  
- 1M:   <10ms mask, <50ms total pipeline
"""
import time
import numpy as np
import open3d as o3d

from core.clipping import compute_box_mask, apply_mask, get_cloud_bounds
from core.measurement import MeasurementManager


def benchmark_clipping(n_points: int, n_iterations: int = 10):
    """Benchmark the full clipping pipeline for a given point count."""
    points = np.random.rand(n_points, 3).astype(np.float64) * 100.0
    colors = np.random.randint(0, 256, (n_points, 3), dtype=np.uint8)
    
    # Use 80% volume selection (~51% selectivity for 3D)
    bounds = (10.0, 90.0, 10.0, 90.0, 10.0, 90.0)
    
    mask_times = []
    apply_times = []
    total_times = []
    
    for _ in range(n_iterations):
        t0 = time.perf_counter()
        mask = compute_box_mask(points, bounds)
        t1 = time.perf_counter()
        result = apply_mask(points, mask, colors=colors)
        t2 = time.perf_counter()
        
        mask_times.append((t1 - t0) * 1000)
        apply_times.append((t2 - t1) * 1000)
        total_times.append((t2 - t0) * 1000)
    
    selected = mask.sum()
    selectivity = selected / n_points * 100
    
    return {
        'n_points': n_points,
        'selected': selected,
        'selectivity': f"{selectivity:.1f}%",
        'mask_ms': f"{np.median(mask_times):.2f}",
        'apply_ms': f"{np.median(apply_times):.2f}",
        'total_ms': f"{np.median(total_times):.2f}",
        'mask_p95': f"{np.percentile(mask_times, 95):.2f}",
        'total_p95': f"{np.percentile(total_times, 95):.2f}",
    }
 

def benchmark_kdtree(n_points: int, n_queries: int = 100):
    """Benchmark KD-tree build and snap-to-point for measurement."""
    points = np.random.rand(n_points, 3).astype(np.float64) * 100.0
    
    mgr = MeasurementManager()
    
    # Build time
    t0 = time.perf_counter()
    mgr.build_index_from_points(points)
    build_ms = (time.perf_counter() - t0) * 1000
    
    # Snap query times
    query_times = []
    for _ in range(n_queries):
        approx = np.random.rand(3) * 100.0
        t0 = time.perf_counter()
        mgr.snap_to_point(approx)
        query_times.append((time.perf_counter() - t0) * 1000)
    
    return {
        'n_points': n_points,
        'build_ms': f"{build_ms:.2f}",
        'snap_median_ms': f"{np.median(query_times):.4f}",
        'snap_p95_ms': f"{np.percentile(query_times, 95):.4f}",
    }


def benchmark_measurement_cleanup(n_points: int, n_measurements: int = 50):
    """Benchmark measurement endpoint visibility check."""
    points = np.random.rand(n_points, 3).astype(np.float64) * 100.0
    
    mgr = MeasurementManager()
    
    # Create measurements with endpoints from the point set
    for i in range(n_measurements):
        idx_a = np.random.randint(0, n_points)
        idx_b = np.random.randint(0, n_points)
        mgr.create_measurement(points[idx_a], points[idx_b])
    
    # Clip to 50% of points
    visible = points[:n_points // 2]
    
    t0 = time.perf_counter()
    removed = mgr.remove_measurements_by_points(visible)
    cleanup_ms = (time.perf_counter() - t0) * 1000
    
    return {
        'n_points': n_points,
        'n_measurements': n_measurements,
        'removed': len(removed),
        'kept': len(mgr.results),
        'cleanup_ms': f"{cleanup_ms:.2f}",
    }


if __name__ == '__main__':
    print("=" * 70)
    print("Tools Benchmark: Clipping Pipeline Performance")
    print("=" * 70)
    
    print(f"\n{'Points':>10} | {'Selected':>10} | {'Selected':>11} | {'Mask (ms)':>9} | {'Apply (ms)':>10} | {'Total (ms)':>10} | {'P95 Total':>10}")
    print("-" * 85)
    
    for n in [100_000, 500_000, 1_000_000]:
        r = benchmark_clipping(n)
        print(f"{r['n_points']:>10,} | {r['selected']:>10,} | {r['selectivity']:>11} | {r['mask_ms']:>9} | {r['apply_ms']:>10} | {r['total_ms']:>10} | {r['total_p95']:>10}")
    
    print("\n" + "=" * 70)
    print("Tools Benchmark: KD-Tree Build + Snap-to-Point")
    print("=" * 70)
    
    print(f"\n{'Points':>10} | {'Build (ms)':>10} | {'Snap Median':>12} | {'Snap P95':>10}")
    print("-" * 55)
    
    for n in [100_000, 500_000, 1_000_000]:
        r = benchmark_kdtree(n)
        print(f"{r['n_points']:>10,} | {r['build_ms']:>10} | {r['snap_median_ms']:>12} | {r['snap_p95_ms']:>10}")
    
    print("\n" + "=" * 70)
    print("Tools Benchmark: Measurement Cleanup on Clip Change")
    print("=" * 70)
    
    print(f"\n{'Points':>10} | {'Measurements':>12} | {'Removed':>8} | {'Kept':>6} | {'Cleanup (ms)':>12}")
    print("-" * 60)
    
    for n in [100_000, 500_000, 1_000_000]:
        r = benchmark_measurement_cleanup(n)
        print(f"{r['n_points']:>10,} | {r['n_measurements']:>12} | {r['removed']:>8} | {r['kept']:>6} | {r['cleanup_ms']:>12}")
    
    print("\n" + "=" * 70)
    print("Benchmark complete.")
