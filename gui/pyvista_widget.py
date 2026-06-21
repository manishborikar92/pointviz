import numpy as np
import open3d as o3d
import pyvista as pv
from pyvistaqt import QtInteractor
import matplotlib.pyplot as plt
from typing import Optional

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

from config import (
    COLOR_MODES,
    BACKGROUND_STYLES,
    DEFAULT_POINT_SIZE,
    MAX_NORMALS_DISPLAY,
    NORMAL_ESTIMATION_RADIUS,
    NORMAL_ESTIMATION_MAX_NN
)
from logger import logger

class PyVistaWidget(QWidget):
    """PyVista visualization widget with improved update mechanisms"""
    
    def __init__(self):
        super().__init__()
        self.plotter = None
        self.point_cloud_actor = None
        self.normals_actor = None
        self.axes_actor = None
        self.current_point_cloud = None
        self.color_cache = {}
        
        # Track current visualization settings
        self.current_point_size = DEFAULT_POINT_SIZE
        self.current_color_mode = 'Original'
        self.current_background = 'Gradient'
        self.show_normals = False
        
        self.setup_visualization()
        
    def setup_visualization(self):
        """Setup the PyVista plotter with OpenGL compatibility fixes"""
        layout = QVBoxLayout()
        
        try:
            # Create PyVista plotter with safe settings
            self.plotter = QtInteractor(
                self, 
                multi_samples=0,
                line_smoothing=False,
                point_smoothing=False,
                polygon_smoothing=False
            )
            
            # Set initial gradient background
            self.set_background_style('Gradient')
            
            # Add basic lighting with error handling
            try:
                light = pv.Light(position=(10, 10, 10), focal_point=(0, 0, 0))
                self.plotter.add_light(light)
            except Exception as e:
                logger.warning(f"Could not add lighting: {e}")
            
            # Add coordinate axes in lower right corner
            try:
                self.axes_actor = self.plotter.add_axes(viewport=(0.8, 0, 1.0, 0.2))
            except Exception as e:
                logger.warning(f"Could not add coordinate axes: {e}")
            
            layout.addWidget(self.plotter.interactor)
            layout.setContentsMargins(0, 0, 0, 0)
            
        except Exception as e:
            logger.error(f"Error setting up PyVista plotter: {e}", exc_info=True)
            # Fallback: create a simple label if PyVista fails
            fallback_label = QLabel("3D Visualization unavailable\nOpenGL compatibility issue")
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_label.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
            layout.addWidget(fallback_label)
            self.plotter = None
            
        self.setLayout(layout)
        
    def set_background_style(self, style: str):
        """Set background style with gradient options"""
        if self.plotter is None:
            return
            
        try:
            bg_config = BACKGROUND_STYLES.get(style)
            if bg_config:
                if isinstance(bg_config, tuple):
                    self.plotter.set_background(bg_config[0], top=bg_config[1])
                else:
                    self.plotter.set_background(bg_config)
            
            self.current_background = style
        except Exception as e:
            logger.warning(f"Could not set background: {e}")
            
    def update_point_cloud(self, point_cloud, force_refresh: bool = False):
        """Update the point cloud visualization"""
        if point_cloud is None:
            return
            
        # Only do full re-render if point cloud changed or forced
        if self.current_point_cloud is not point_cloud or force_refresh:
            self.current_point_cloud = point_cloud
            self.color_cache.clear()
            self.render_point_cloud()
        
    def render_point_cloud(self):
        """Render the current point cloud efficiently"""
        if self.current_point_cloud is None or self.plotter is None:
            return
            
        try:
            # Clear existing actors
            self._clear_actors()
        except Exception as e:
            logger.warning(f"Could not remove actors: {e}")
            
        # Convert Open3D point cloud to PyVista
        points = np.asarray(self.current_point_cloud.points)
        
        if len(points) == 0:
            return
            
        # Create PyVista point cloud
        self.pv_cloud = pv.PolyData(points)
        
        # Apply current color mode
        colored_points = self._apply_color_mode(points)
        if colored_points is not None:
            self.pv_cloud['colors'] = colored_points
            
        # Add point cloud to plotter
        render_args = {
            'point_size': self.current_point_size,
            'render_points_as_spheres': len(points) <= 50000
        }
        
        if 'colors' in self.pv_cloud.array_names:
            render_args.update({'scalars': 'colors', 'rgb': True})
            
        self.point_cloud_actor = self.plotter.add_mesh(self.pv_cloud, **render_args)
        
        # Add normals if enabled
        if self.show_normals:
            self._add_normals_visualization(points)
            
        # Update the display
        self.plotter.update()
        
    def _clear_actors(self):
        """Clear existing point cloud and normal actors"""
        if self.point_cloud_actor is not None:
            self.plotter.remove_actor(self.point_cloud_actor)
            self.point_cloud_actor = None
        if self.normals_actor is not None:
            self.plotter.remove_actor(self.normals_actor)
            self.normals_actor = None
        self.pv_cloud = None
        
    def _add_normals_visualization(self, points: np.ndarray):
        """Add normal vectors visualization with on-demand estimation"""
        if not self.current_point_cloud.has_normals():
            try:
                logger.info("Estimating normals on-demand for visualization")
                self.current_point_cloud.estimate_normals(
                    search_param=o3d.geometry.KDTreeSearchParamHybrid(
                        radius=NORMAL_ESTIMATION_RADIUS, max_nn=NORMAL_ESTIMATION_MAX_NN))
            except Exception as e:
                logger.warning(f"Could not estimate normals: {e}")
                return
            
        try:
            normals = np.asarray(self.current_point_cloud.normals)
            
            # Subsample for performance (max MAX_NORMALS_DISPLAY normals)
            step = max(1, len(points) // MAX_NORMALS_DISPLAY)
            sampled_points = points[::step]
            sampled_normals = normals[::step]
            
            # Create arrow glyphs
            arrows = pv.PolyData(sampled_points)
            arrows['normals'] = sampled_normals
            
            # Generate arrow glyphs
            arrow_glyph = arrows.glyph(orient='normals', scale=False, factor=0.05)
            
            self.normals_actor = self.plotter.add_mesh(
                arrow_glyph, color='red', opacity=0.7
            )
        except Exception as e:
            logger.warning(f"Could not add normals visualization: {e}")
        
    def _apply_color_mode(self, points: np.ndarray) -> Optional[np.ndarray]:
        """Apply different color modes to the point cloud with caching"""
        if self.current_color_mode in self.color_cache:
            return self.color_cache[self.current_color_mode]
            
        original_colors = None
        if self.current_point_cloud.has_colors():
            original_colors = np.asarray(self.current_point_cloud.colors)
        
        colors = None
        if self.current_color_mode == "Original" and original_colors is not None:
            if original_colors.max() <= 1.0:
                colors = (original_colors * 255).astype(np.uint8)
            else:
                colors = original_colors.astype(np.uint8)
            
        elif self.current_color_mode == "Height":
            colors = self._color_by_height(points)
            
        elif self.current_color_mode == "Elevation":
            colors = self._color_by_elevation(points)
            
        elif self.current_color_mode == "Distance":
            colors = self._color_by_distance(points)
            
        elif self.current_color_mode == "Normal":
            colors = self._color_by_normal()
            
        elif self.current_color_mode == "Curvature":
            colors = self._color_by_curvature(points)
            
        if colors is None:
            # Default uniform color
            colors = np.full((len(points), 3), [128, 128, 128], dtype=np.uint8)
            
        self.color_cache[self.current_color_mode] = colors
        return colors
    
    def _color_by_height(self, points: np.ndarray) -> np.ndarray:
        """Color points by Z coordinate (height)"""
        z_coords = points[:, 2]
        if z_coords.max() == z_coords.min():
            return np.full((len(points), 3), [128, 128, 255], dtype=np.uint8)
        z_norm = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
        colormap = plt.colormaps.get_cmap('viridis')
        colors = colormap(z_norm)[:, :3]
        return (colors * 255).astype(np.uint8)
    
    def _color_by_elevation(self, points: np.ndarray) -> np.ndarray:
        """Color by elevation with terrain-like colors"""
        z_coords = points[:, 2]
        if z_coords.max() == z_coords.min():
            return np.full((len(points), 3), [128, 128, 128], dtype=np.uint8)
        z_norm = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
        colormap = plt.colormaps.get_cmap('terrain')
        colors = colormap(z_norm)[:, :3]
        return (colors * 255).astype(np.uint8)
    
    def _color_by_distance(self, points: np.ndarray) -> np.ndarray:
        """Color by distance from center"""
        center = points.mean(axis=0)
        distances = np.linalg.norm(points - center, axis=1)
        if distances.max() == distances.min():
            return np.full((len(points), 3), [255, 128, 128], dtype=np.uint8)
        dist_norm = (distances - distances.min()) / (distances.max() - distances.min())
        colormap = plt.colormaps.get_cmap('plasma')
        colors = colormap(dist_norm)[:, :3]
        return (colors * 255).astype(np.uint8)
    
    def _color_by_normal(self) -> Optional[np.ndarray]:
        """Color by normal direction with on-demand estimation"""
        if not self.current_point_cloud.has_normals():
            try:
                logger.info("Estimating normals on-demand for Normal color mode")
                self.current_point_cloud.estimate_normals(
                    search_param=o3d.geometry.KDTreeSearchParamHybrid(
                        radius=NORMAL_ESTIMATION_RADIUS, max_nn=NORMAL_ESTIMATION_MAX_NN))
            except Exception as e:
                logger.warning(f"Could not estimate normals: {e}")
                return None
        normals = np.asarray(self.current_point_cloud.normals)
        colors = np.abs(normals)
        return (colors * 255).astype(np.uint8)
    
    def _color_by_curvature(self, points: np.ndarray) -> np.ndarray:
        """Color by proper curvature estimation using local neighborhood covariance"""
        try:
            # Estimate covariances if they are not already calculated
            if not self.current_point_cloud.has_covariances():
                logger.info("Estimating covariances on-demand for Curvature color mode")
                self.current_point_cloud.estimate_covariances(
                    search_param=o3d.geometry.KDTreeSearchParamKNN(knn=30)
                )
            
            covs = np.asarray(self.current_point_cloud.covariances)
            if len(covs) == 0:
                return np.full((len(points), 3), [128, 128, 255], dtype=np.uint8)
            
            # Compute eigenvalues for each covariance matrix (sorted in ascending order)
            evs = np.linalg.eigvalsh(covs)
            sum_evs = np.sum(evs, axis=1)
            
            curv = np.zeros_like(sum_evs)
            valid_mask = sum_evs > 1e-8
            curv[valid_mask] = evs[valid_mask, 0] / sum_evs[valid_mask]
            
            # Normalize curvature to [0, 1] range for colormap mapping
            c_min, c_max = curv.min(), curv.max()
            if c_max > c_min:
                curv_norm = (curv - c_min) / (c_max - c_min)
            else:
                curv_norm = np.zeros_like(curv)
                
            colormap = plt.colormaps.get_cmap('coolwarm')
            colors = colormap(curv_norm)[:, :3]
            return (colors * 255).astype(np.uint8)
        except Exception as e:
            logger.warning(f"Could not compute curvature: {e}")
            return np.full((len(points), 3), [128, 128, 255], dtype=np.uint8)
            
    def set_view(self, view_type: str):
        """Set specific camera view"""
        if self.plotter is None:
            return
            
        try:
            view_map = {
                "top": self.plotter.view_xy,
                "front": self.plotter.view_xz,
                "side": self.plotter.view_yz,
                "iso": self.plotter.view_isometric,
                "default": lambda: (self.plotter.view_isometric(), self.plotter.reset_camera())
            }
            
            if view_type in view_map:
                view_func = view_map[view_type]
                if callable(view_func):
                    view_func()
                        
        except Exception as e:
            logger.warning(f"Could not set view: {e}")
        
        if self.plotter:
            self.plotter.update()
        
    def update_point_size(self, size: int):
        """Update point size without full refresh"""
        if size == self.current_point_size:
            return
            
        self.current_point_size = size
        
        if self.point_cloud_actor and self.plotter:
            try:
                self.point_cloud_actor.GetProperty().SetPointSize(size)
                self.plotter.update()
            except Exception as e:
                logger.warning(f"Could not update point size: {e}")
                # Fallback: full re-render if direct update fails
                self.render_point_cloud()
                
    def update_color_mode(self, mode: str):
        """Update color mode and re-render only if changed"""
        if mode == self.current_color_mode:
            return
            
        self.current_color_mode = mode
        
        # Optimize by updating scalars in-place if possible
        if (self.point_cloud_actor is not None and 
            hasattr(self, 'pv_cloud') and 
            self.pv_cloud is not None and 
            self.current_point_cloud is not None):
            try:
                points = np.asarray(self.current_point_cloud.points)
                colored_points = self._apply_color_mode(points)
                if colored_points is not None:
                    self.pv_cloud.point_data['colors'] = colored_points
                    
                    # If normals are visible, they might need to be redrawn
                    if self.show_normals:
                        self.toggle_normals_display(False)
                        self.toggle_normals_display(True)
                        
                    if self.plotter:
                        self.plotter.render()
                    return
            except Exception as e:
                logger.warning(f"Could not update colors in-place: {e}")
                
        self.render_point_cloud()
        
    def update_background(self, bg_type: str):
        """Update background without full refresh"""
        if bg_type == self.current_background:
            return
            
        self.set_background_style(bg_type)
        if self.plotter:
            self.plotter.update()
        
    def toggle_normals_display(self, show: bool):
        """Toggle normal vectors display"""
        if show == self.show_normals:
            return
            
        self.show_normals = show
        
        if show and self.current_point_cloud:
            points = np.asarray(self.current_point_cloud.points)
            self._add_normals_visualization(points)
        elif self.normals_actor and self.plotter:
            try:
                self.plotter.remove_actor(self.normals_actor)
                self.normals_actor = None
            except Exception as e:
                logger.warning(f"Could not remove normals: {e}")
                
        if self.plotter:
            self.plotter.update()
        
    def reset_camera(self):
        """Reset camera to fit all data"""
        if self.plotter is None:
            return
            
        try:
            self.plotter.reset_camera()
            self.plotter.update()
        except Exception as e:
            logger.warning(f"Could not reset camera: {e}")
        
    def take_screenshot(self, filename: Optional[str] = None) -> Optional[str]:
        """Take a screenshot of the current view"""
        if self.plotter is None:
            return None
            
        try:
            if filename is None:
                filename = "screenshot.png"
            self.plotter.screenshot(filename)
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
            
    def cleanup(self):
        """Clean up PyVista resources properly"""
        try:
            if self.plotter is not None:
                self._clear_actors()
                
                # Clear axes actor
                try:
                    if self.axes_actor is not None:
                        self.plotter.remove_actor(self.axes_actor)
                        self.axes_actor = None
                except Exception:
                    pass
                
                # Close plotter
                try:
                    self.plotter.close()
                except Exception:
                    pass
                    
                self.plotter = None
        except Exception as e:
            logger.warning(f"Warning during PyVista cleanup: {e}")
