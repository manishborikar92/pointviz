"""
PyVista 3D Visualization Widget
Handles all 3D rendering and visualization operations.
"""

import numpy as np
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False


class PyVistaWidget(QWidget):
    """PyVista visualization widget with optimized update mechanisms."""
    
    def __init__(self):
        super().__init__()
        self.plotter = None
        self.point_cloud_actor = None
        self.normals_actor = None
        self.axes_actor = None
        self.current_point_cloud = None
        
        # Track visualization state
        self.current_point_size = 5
        self.current_color_mode = 'Original'
        self.current_background = 'Gradient'
        self.show_normals = False
        
        self.setup_visualization()
        
    def setup_visualization(self):
        """Setup PyVista plotter with compatibility settings."""
        layout = QVBoxLayout()
        
        if not PYVISTA_AVAILABLE:
            self.create_fallback_widget(layout)
            return
        
        try:
            # Create PyVista plotter with safe settings
            self.plotter = QtInteractor(self, 
                                      multi_samples=0,
                                      line_smoothing=False,
                                      point_smoothing=False,
                                      polygon_smoothing=False)
            
            # Set initial gradient background
            self.set_background_style('Gradient')
            
            # Add lighting
            try:
                self.plotter.add_light(pv.Light(position=(10, 10, 10), focal_point=(0, 0, 0)))
            except Exception as e:
                print(f"Warning: Could not add lighting: {e}")
            
            # Add coordinate axes in lower right corner
            try:
                self.axes_actor = self.plotter.add_axes(viewport=(0.8, 0, 1.0, 0.2))
            except Exception as e:
                print(f"Warning: Could not add coordinate axes: {e}")
            
            layout.addWidget(self.plotter.interactor)
            
        except Exception as e:
            print(f"Error setting up PyVista plotter: {e}")
            self.create_fallback_widget(layout)
            
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def create_fallback_widget(self, layout):
        """Create fallback widget when PyVista is unavailable."""
        fallback_label = QLabel("3D Visualization unavailable\nPyVista/OpenGL compatibility issue")
        fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_label.setStyleSheet("background-color: lightgray; border: 1px solid gray;")
        layout.addWidget(fallback_label)
        self.plotter = None
        
    def set_background_style(self, style):
        """Set background style with gradient options."""
        if self.plotter is None:
            return
            
        try:
            if style == "White":
                self.plotter.set_background('white')
            elif style == "Black":
                self.plotter.set_background('black')
            elif style == "Gray":
                self.plotter.set_background('#f0f0f0')
            elif style == "Gradient":
                self.plotter.set_background('#ffffff', top='lightblue')
            elif style == "Dark Gradient":
                self.plotter.set_background("#1A1A26", top="#212136")
            elif style == "Sunset Gradient":
                self.plotter.set_background('#ffeaa7', top='#fd79a8')
            
            self.current_background = style
        except Exception as e:
            print(f"Warning: Could not set background: {e}")
            
    def update_point_cloud(self, point_cloud, force_refresh=False):
        """Update point cloud visualization."""
        if point_cloud is None:
            return
            
        if self.current_point_cloud is not point_cloud or force_refresh:
            self.current_point_cloud = point_cloud
            self.render_point_cloud()
        
    def render_point_cloud(self):
        """Render the current point cloud efficiently."""
        if self.current_point_cloud is None or self.plotter is None:
            return
            
        try:
            # Clear existing actors
            if self.point_cloud_actor is not None:
                self.plotter.remove_actor(self.point_cloud_actor)
                self.point_cloud_actor = None
            if self.normals_actor is not None:
                self.plotter.remove_actor(self.normals_actor)
                self.normals_actor = None
        except Exception as e:
            print(f"Warning: Could not remove actors: {e}")
            
        # Convert to PyVista format
        points = np.asarray(self.current_point_cloud.points)
        if len(points) == 0:
            return
            
        pv_cloud = pv.PolyData(points)
        
        # Apply colors
        original_colors = None
        if self.current_point_cloud.has_colors():
            original_colors = np.asarray(self.current_point_cloud.colors)
            
        colored_points = self.apply_color_mode(points, original_colors)
        if colored_points is not None:
            pv_cloud['colors'] = colored_points
            
        # Render point cloud
        render_args = {
            'point_size': self.current_point_size,
            'render_points_as_spheres': True
        }
        
        if 'colors' in pv_cloud.array_names:
            render_args['scalars'] = 'colors'
            render_args['rgb'] = True
            
        self.point_cloud_actor = self.plotter.add_mesh(pv_cloud, **render_args)
        
        # Add normals if enabled
        if self.show_normals:
            self.add_normals_visualization(points)
            
        self.plotter.update()
        
    def apply_color_mode(self, points, original_colors):
        """Apply different color modes to the point cloud."""
        if self.current_color_mode == "Original" and original_colors is not None:
            if original_colors.max() <= 1.0:
                return (original_colors * 255).astype(np.uint8)
            return original_colors.astype(np.uint8)
            
        elif self.current_color_mode == "Height":
            z_coords = points[:, 2]
            if z_coords.max() == z_coords.min():
                return np.full((len(points), 3), [128, 128, 255], dtype=np.uint8)
            z_norm = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
            colormap = plt.colormaps.get_cmap('viridis')
            colors = colormap(z_norm)[:, :3]
            return (colors * 255).astype(np.uint8)
            
        elif self.current_color_mode == "Elevation":
            z_coords = points[:, 2]
            if z_coords.max() == z_coords.min():
                return np.full((len(points), 3), [128, 128, 128], dtype=np.uint8)
            z_norm = (z_coords - z_coords.min()) / (z_coords.max() - z_coords.min())
            colormap = plt.colormaps.get_cmap('terrain')
            colors = colormap(z_norm)[:, :3]
            return (colors * 255).astype(np.uint8)
            
        elif self.current_color_mode == "Distance":
            center = points.mean(axis=0)
            distances = np.linalg.norm(points - center, axis=1)
            if distances.max() == distances.min():
                return np.full((len(points), 3), [255, 128, 128], dtype=np.uint8)
            dist_norm = (distances - distances.min()) / (distances.max() - distances.min())
            colormap = plt.colormaps.get_cmap('plasma')
            colors = colormap(dist_norm)[:, :3]
            return (colors * 255).astype(np.uint8)
            
        elif self.current_color_mode == "Normal" and self.current_point_cloud.has_normals():
            normals = np.asarray(self.current_point_cloud.normals)
            colors = np.abs(normals)
            return (colors * 255).astype(np.uint8)
            
        elif self.current_color_mode == "Curvature":
            z_coords = points[:, 2]
            curvature = np.gradient(np.gradient(z_coords))
            curv_norm = np.abs(curvature)
            if curv_norm.max() > 0:
                curv_norm = (curv_norm - curv_norm.min()) / (curv_norm.max() - curv_norm.min())
            colormap = plt.colormaps.get_cmap('coolwarm')
            colors = colormap(curv_norm)[:, :3]
            return (colors * 255).astype(np.uint8)
            
        else:
            return np.full((len(points), 3), [128, 128, 128], dtype=np.uint8)
            
    def add_normals_visualization(self, points):
        """Add normal vectors visualization."""
        if not self.current_point_cloud.has_normals():
            return
            
        try:
            normals = np.asarray(self.current_point_cloud.normals)
            
            # Subsample for performance
            step = max(1, len(points) // 1000)
            sampled_points = points[::step]
            sampled_normals = normals[::step]
            
            # Create arrow glyphs
            arrows = pv.PolyData(sampled_points)
            arrows['normals'] = sampled_normals
            
            arrow_glyph = arrows.glyph(orient='normals', scale=False, factor=0.05)
            
            self.normals_actor = self.plotter.add_mesh(
                arrow_glyph, color='red', opacity=0.7
            )
        except Exception as e:
            print(f"Warning: Could not add normals visualization: {e}")
        
    def set_view(self, view_type):
        """Set specific camera view."""
        if self.plotter is None:
            return
            
        try:
            if view_type == "top":
                self.plotter.view_xy()
            elif view_type == "front":
                self.plotter.view_xz()
            elif view_type == "side":
                self.plotter.view_yz()
            elif view_type == "iso":
                self.plotter.view_isometric()
            elif view_type == "default":
                self.plotter.view_isometric()
                self.plotter.reset_camera()
        except Exception as e:
            print(f"Warning: Could not set view: {e}")
        
        self.plotter.update()
        
    def update_point_size(self, size):
        """Update point size efficiently."""
        if size == self.current_point_size:
            return
            
        self.current_point_size = size
        
        if self.point_cloud_actor and self.plotter:
            try:
                self.point_cloud_actor.GetProperty().SetPointSize(size)
                self.plotter.update()
            except Exception as e:
                print(f"Warning: Could not update point size: {e}")
                self.render_point_cloud()
                
    def update_color_mode(self, mode):
        """Update color mode and re-render if changed."""
        if mode == self.current_color_mode:
            return
            
        self.current_color_mode = mode
        self.render_point_cloud()
        
    def update_background(self, bg_type):
        """Update background efficiently."""
        if bg_type == self.current_background:
            return
            
        self.set_background_style(bg_type)
        if self.plotter:
            self.plotter.update()
        
    def toggle_normals_display(self, show):
        """Toggle normal vectors display."""
        if show == self.show_normals:
            return
            
        self.show_normals = show
        
        if show and self.current_point_cloud:
            points = np.asarray(self.current_point_cloud.points)
            self.add_normals_visualization(points)
        elif self.normals_actor and self.plotter:
            try:
                self.plotter.remove_actor(self.normals_actor)
                self.normals_actor = None
            except Exception as e:
                print(f"Warning: Could not remove normals: {e}")
                
        if self.plotter:
            self.plotter.update()
        
    def reset_camera(self):
        """Reset camera to fit all data."""
        if self.plotter is None:
            return
            
        try:
            self.plotter.reset_camera()
            self.plotter.update()
        except Exception as e:
            print(f"Warning: Could not reset camera: {e}")
        
    def take_screenshot(self, filename=None):
        """Take a screenshot of the current view."""
        if self.plotter is None:
            return None
            
        try:
            if filename is None:
                filename = "screenshot.png"
            self.plotter.screenshot(filename)
            return filename
        except Exception as e:
            print(f"Error taking screenshot: {e}")
            return None
            
    def cleanup(self):
        """Clean up PyVista resources properly."""
        try:
            if self.plotter is not None:
                # Clear actors
                try:
                    if self.point_cloud_actor is not None:
                        self.plotter.remove_actor(self.point_cloud_actor)
                        self.point_cloud_actor = None
                    if self.normals_actor is not None:
                        self.plotter.remove_actor(self.normals_actor)
                        self.normals_actor = None
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
            print(f"Warning during PyVista cleanup: {e}")