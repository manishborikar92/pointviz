import os
import sys
import time
import numpy as np
import open3d as o3d
import pyvista as pv

# Headless execution settings for off-screen rendering
os.environ['PYVISTA_OFF_SCREEN'] = 'true'
pv.OFF_SCREEN = True

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication
from pcd_visualizer import PyVistaWidget

def generate_dummy_pcd(filename, num_points=500000):
    print(f"Generating temporary point cloud with {num_points:,} points...")
    points = np.random.rand(num_points, 3).astype(np.float32)
    # Generate some mock colors
    colors = np.random.rand(num_points, 3).astype(np.float32)
    
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    
    o3d.io.write_point_cloud(filename, pcd)
    print(f"Temporary point cloud saved to {filename}")

def run_benchmark():
    # Initialize QApplication for widget testing
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        
    temp_file = "temp_benchmark_cloud.pcd"
    num_points = 500000
    
    try:
        generate_dummy_pcd(temp_file, num_points)
        
        # 1. Benchmark Loading
        t0 = time.time()
        pcd = o3d.io.read_point_cloud(temp_file)
        load_time = time.time() - t0
        print(f"Loading time: {load_time:.4f} seconds")
        
        # 2. Benchmark Rendering Widget Init
        t0 = time.time()
        widget = PyVistaWidget()
        init_time = time.time() - t0
        print(f"Widget initialization time: {init_time:.4f} seconds")
        
        # 3. Benchmark Initial Render
        t0 = time.time()
        widget.update_point_cloud(pcd, force_refresh=True)
        initial_render_time = time.time() - t0
        print(f"Initial render time: {initial_render_time:.4f} seconds")
        
        # 4. Benchmark Color Modes (Uncached vs. Cached)
        color_modes = ["Original", "Height", "Elevation", "Distance", "Normal", "Curvature"]
        
        print("\nBenchmarking Color Switch Times (seconds):")
        print(f"{'Color Mode':<15} | {'Uncached (First Run)':<22} | {'Cached (Second Run)':<22} | {'Speedup':<10}")
        print("-" * 78)
        
        for mode in color_modes:
            # Measure Uncached
            # (Clear cache first to ensure it's uncached)
            widget.color_cache.clear()
            t0 = time.time()
            widget.update_color_mode(mode)
            uncached_time = time.time() - t0
            
            # Measure Cached
            t0 = time.time()
            widget.update_color_mode(mode)
            cached_time = time.time() - t0
            
            speedup = uncached_time / cached_time if cached_time > 0 else float('inf')
            print(f"{mode:<15} | {uncached_time:<22.4f} | {cached_time:<22.4f} | {speedup:.1f}x")
            
        print("\nBenchmark completed successfully.")
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"Cleaned up temporary file: {temp_file}")

if __name__ == "__main__":
    run_benchmark()
