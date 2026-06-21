import numpy as np
import open3d as o3d
import pyvista as pv
from pyvistaqt import QtInteractor
import matplotlib.pyplot as plt
from typing import Optional, List

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

from config import (
    COLOR_MODES,
    BACKGROUND_STYLES,
    DEFAULT_POINT_SIZE,
    MAX_NORMALS_DISPLAY,
    NORMAL_ESTIMATION_RADIUS,
    NORMAL_ESTIMATION_MAX_NN
)
from logger import logger
from core.clipping import ClippingMode, ClippingState, compute_box_mask, apply_mask, get_cloud_bounds
from core.measurement import MeasurementMode, MeasurementManager

class PyVistaWidget(QWidget):
    """PyVista visualization widget with clipping and measurement support."""

    # Signals for cross-component communication
    clipping_state_changed = pyqtSignal(object)   # Emits ClippingState
    measurement_completed = pyqtSignal(object)     # Emits Measurement
    measurement_mode_changed = pyqtSignal(str)     # Emits mode string for status bar
    measurement_failed = pyqtSignal()              # Emits on pick failures for rollback
    
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

        # Day 5: Working Set Clipping state
        self.clipping_state = ClippingState()
        self._original_points = None
        self._original_colors = None
        self._original_normals = None
        self._original_bounds = None
        self._clip_mask = None               # Current boolean mask

        # Day 5: Measurement state
        self.measurement_manager = MeasurementManager()
        self._pending_marker_actor = None    # Actor for Point A marker during picking
        
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
            
    def update_point_cloud(self, point_cloud, force_refresh: bool = False, reset_camera: bool = True):
        """Update the point cloud visualization"""
        if point_cloud is None:
            return
            
        # Only do full re-render if point cloud changed or forced
        if self.current_point_cloud is not point_cloud or force_refresh:
            # Clean up all widgets and overlays transactionally
            self.disable_clipping()
            self.disable_measurement()
            self.clear_measurements()

            self.current_point_cloud = point_cloud
            self.color_cache.clear()
            
            # Store single stable source of truth
            self._original_points = np.asarray(point_cloud.points).copy()
            self._original_colors = np.asarray(point_cloud.colors).copy() if point_cloud.has_colors() else None
            self._original_normals = np.asarray(point_cloud.normals).copy() if point_cloud.has_normals() else None
            self._original_bounds = get_cloud_bounds(self._original_points)
            self._clip_mask = None

            self.render_point_cloud()
            
            # Explicitly reset the camera and view only on load or if requested
            if reset_camera:
                self.reset_camera()
                self.set_view("default")

            # Day 5: Build KD-tree for measurement snapping
            self.measurement_manager.build_index(point_cloud)
        
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
        if self.clipping_state.is_active and self._clip_mask is not None:
            points = self._original_points[self._clip_mask]
        else:
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
            'render_points_as_spheres': len(points) <= 50000,
            'name': 'point_cloud_main',
            'reset_camera': False,
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
            if self._clip_mask is not None and len(normals) == len(self._clip_mask) and len(points) == self._clip_mask.sum():
                normals = normals[self._clip_mask]
            
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
                arrow_glyph, color='red', opacity=0.7,
                reset_camera=False
            )
        except Exception as e:
            logger.warning(f"Could not add normals visualization: {e}")
        
    def _apply_color_mode(self, points: np.ndarray) -> Optional[np.ndarray]:
        """Apply different color modes to the point cloud with caching"""
        if len(points) == 0:
            return np.empty((0, 3), dtype=np.uint8)
            
        if self.current_color_mode in self.color_cache:
            return self.color_cache[self.current_color_mode]
            
        original_colors = None
        if self.current_point_cloud.has_colors():
            original_colors = np.asarray(self.current_point_cloud.colors)
            if self._clip_mask is not None and len(original_colors) == len(self._clip_mask) and len(points) == self._clip_mask.sum():
                original_colors = original_colors[self._clip_mask]
        
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
            colors = self._color_by_normal(points)
            
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
    
    def _color_by_normal(self, points: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
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
        if points is not None and self._clip_mask is not None and len(normals) == len(self._clip_mask) and len(points) == self._clip_mask.sum():
            normals = normals[self._clip_mask]
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
            if self._clip_mask is not None and len(covs) == len(self._clip_mask) and len(points) == self._clip_mask.sum():
                covs = covs[self._clip_mask]
                
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
                if self.clipping_state.is_active and self._clip_mask is not None:
                    points = self._original_points[self._clip_mask]
                else:
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
            if self.clipping_state.is_active and self._clip_mask is not None:
                points = self._original_points[self._clip_mask]
            else:
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

    # ================================================================
    # Day 5: Working Set Clipping
    # ================================================================

    def enable_clipping(self) -> bool:
        """Activate the box clipping widget on the current point cloud."""
        if self.plotter is None or not hasattr(self, 'pv_cloud') or self.pv_cloud is None:
            return False

        # Use single stable source of truth
        bounds = self._original_bounds

        try:
            widget = self.plotter.add_box_widget(
                callback=self._on_box_clip,
                bounds=bounds,
                rotation_enabled=False,  # AABB only for Day 5
            )
            widget.SetHandleSize(0.005)
            self._box_widget = widget

            # Update clipping state
            self.clipping_state = ClippingState(
                mode=ClippingMode.BOX,
                bounds=bounds,
                original_count=len(self._original_points),
                clipped_count=len(self._original_points),
            )
            self.clipping_state_changed.emit(self.clipping_state)
            logger.info("Clipping box widget enabled")
            return True
        except Exception as e:
            logger.error(f"Could not enable clipping: {e}")
            return False

    def disable_clipping(self):
        """Remove the clipping widget and restore the full point cloud."""
        if self.plotter is None:
            return

        try:
            self.plotter.clear_box_widgets()
            self._box_widget = None
        except Exception as e:
            logger.warning(f"Could not clear box widgets: {e}")

        had_clip = self._clip_mask is not None

        # Reset clipping state first so render functions know it is disabled
        self._reset_clipping_state()

        # Restore full cloud if we had clipped
        if had_clip:
            self._restore_full_cloud()

        self.clipping_state_changed.emit(self.clipping_state)
        logger.info("Clipping disabled, full cloud restored")

    def reset_clipping(self):
        """Reset clipping box to encompass the full point cloud (keep widget active)."""
        if not self.clipping_state.is_active:
            return
        # Disable then re-enable to reset box bounds
        self.disable_clipping()
        self.enable_clipping()

    def _on_box_clip(self, box_polydata):
        """Callback invoked by PyVista box widget on release (interaction_event='end').

        Computes the boolean mask, filters points, updates rendering,
        rebuilds the KD-tree, and removes stale measurements.
        """
        if self._original_points is None:
            return

        try:
            # Extract bounds from the box PolyData
            box_bounds = box_polydata.bounds  # (xmin,xmax,ymin,ymax,zmin,zmax)

            # 1. Compute mask
            mask = compute_box_mask(self._original_points, box_bounds)
            self._clip_mask = mask

            # 2. Filter points
            filtered = apply_mask(self._original_points, mask)
            filtered_points = filtered['points']

            if len(filtered_points) == 0:
                # Edge case: all points clipped out
                self.pv_cloud = pv.PolyData()
                self.clipping_state = ClippingState(
                    mode=ClippingMode.BOX,
                    bounds=box_bounds,
                    original_count=len(self._original_points),
                    clipped_count=0,
                )
                self.clipping_state_changed.emit(self.clipping_state)
                
                # Rebuild KD-tree as empty
                self.measurement_manager.build_index_from_points(filtered_points)
                
                # Remove all measurements since no points are visible
                if self.measurement_manager.has_measurements:
                    removed = self.measurement_manager.remove_measurements_by_points(filtered_points)
                    for m in removed:
                        self._remove_actors_by_name(m.actor_names)

                # Clear the rendered cloud
                if self.point_cloud_actor is not None:
                    try:
                        self.plotter.remove_actor(self.point_cloud_actor)
                    except Exception:
                        pass
                    self.point_cloud_actor = None
                self.plotter.render()
                return

            # 3. Create new PolyData from filtered points
            clipped_pv = pv.PolyData(filtered_points)

            # 4. Apply color mode to filtered subset
            self.color_cache.clear()  # Invalidate cache — point set changed
            colored = self._apply_color_mode(filtered_points)
            if colored is not None:
                clipped_pv['colors'] = colored

            # 5. Update actor using named mesh for efficient replacement
            render_args = {
                'point_size': self.current_point_size,
                'render_points_as_spheres': len(filtered_points) <= 50000,
                'name': 'point_cloud_main',
                'reset_camera': False,
            }
            if 'colors' in clipped_pv.array_names:
                render_args.update({'scalars': 'colors', 'rgb': True})

            self.point_cloud_actor = self.plotter.add_mesh(clipped_pv, **render_args)
            self.pv_cloud = clipped_pv

            # 6. Update clipping state
            self.clipping_state = ClippingState(
                mode=ClippingMode.BOX,
                bounds=box_bounds,
                original_count=len(self._original_points),
                clipped_count=len(filtered_points),
            )
            self.clipping_state_changed.emit(self.clipping_state)

            # 7. Rebuild KD-tree on clipped subset for measurement snapping
            self.measurement_manager.build_index_from_points(filtered_points)

            # 8. Remove measurements whose endpoints are no longer visible
            if self.measurement_manager.has_measurements:
                removed = self.measurement_manager.remove_measurements_by_points(filtered_points)
                for m in removed:
                    self._remove_actors_by_name(m.actor_names)

            self.plotter.render()

        except Exception as e:
            logger.error(f"Error in box clip callback: {e}", exc_info=True)

    def _restore_full_cloud(self):
        """Restore the full (unclipped) point cloud rendering."""
        if self._original_points is None or self.current_point_cloud is None:
            return

        self.color_cache.clear()
        self.render_point_cloud()

        # Rebuild KD-tree on full cloud
        if self.current_point_cloud is not None:
            self.measurement_manager.build_index(self.current_point_cloud)

    def _reset_clipping_state(self):
        """Reset all clipping-related internal state."""
        self.clipping_state = ClippingState()
        self._clip_mask = None

        if self.plotter is not None:
            try:
                self.plotter.clear_box_widgets()
            except Exception:
                pass

    # ================================================================
    # Day 5: Measurement
    # ================================================================

    def enable_measurement(self) -> bool:
        """Activate point picking for distance measurement."""
        if self.plotter is None:
            return False

        self.measurement_manager.activate()
        self.measurement_mode_changed.emit("Click first measurement point (ESC to cancel)")

        try:
            self.plotter.enable_point_picking(
                callback=self._on_point_picked,
                show_message=False,
                show_point=False,
                use_picker=True,
                picker='point',
                left_clicking=True,
                pickable_window=True,
                tolerance=0.03,
            )
            return True
        except Exception as e:
            logger.error(f"Could not enable point picking: {e}")
            return False

    def disable_measurement(self):
        """Deactivate measurement mode and picking."""
        if self.plotter is None:
            return

        self.measurement_manager.deactivate()
        self._remove_pending_marker()

        try:
            self.plotter.disable_picking()
        except Exception:
            pass

        self.measurement_mode_changed.emit("")

    def clear_measurements(self) -> None:
        """Remove all measurement overlays and results."""
        actor_names = self.measurement_manager.clear_all()
        self._remove_actors_by_name(actor_names)
        self._remove_pending_marker()

    def _on_point_picked(self, point, picker=None):
        """Callback for PyVista point picking during measurement."""
        if point is None or picker is None:
            self.measurement_mode_changed.emit("Click miss - click directly on the point cloud (ESC to cancel)")
            self.measurement_failed.emit()
            return

        actor = picker.GetActor()
        dataset = picker.GetDataSet()
        point_id = picker.GetPointId()
        
        if actor is None or dataset is None or point_id < 0:
            self.measurement_mode_changed.emit("Click miss - click directly on the point cloud (ESC to cancel)")
            self.measurement_failed.emit()
            return

        approx = np.array(point, dtype=np.float64)

        # Snap to nearest actual point via KD-tree
        snap_result = self.measurement_manager.snap_to_point(approx)
        if snap_result is None:
            self.measurement_mode_changed.emit("No point found - click closer to the point cloud")
            self.measurement_failed.emit()
            return

        _, exact_coord = snap_result

        if self.measurement_manager.mode == MeasurementMode.PICKING_FIRST:
            # Store first point and render marker
            self.measurement_manager.set_first_point(exact_coord)
            self._render_pending_marker(exact_coord)
            self.measurement_mode_changed.emit("Click second measurement point (ESC to cancel)")

        elif self.measurement_manager.mode == MeasurementMode.PICKING_SECOND:
            # Complete the measurement
            point_a = self.measurement_manager.pending_point
            point_b = exact_coord

            measurement = self.measurement_manager.create_measurement(point_a, point_b)

            # Render measurement overlays
            self._render_measurement(measurement)
            self._remove_pending_marker()

            # Emit completion signal
            self.measurement_completed.emit(measurement)

            # Status: show result, ready for next
            self.measurement_mode_changed.emit(
                f"Distance: {measurement.distance:.3f}  |  "
                f"dX: {measurement.delta[0]:.3f}  "
                f"dY: {measurement.delta[1]:.3f}  "
                f"dZ: {measurement.delta[2]:.3f}"
            )

    def _render_measurement(self, measurement):
        """Render a completed measurement's visual overlays (line + markers + label)."""
        if self.plotter is None:
            return

        names = self.measurement_manager.generate_actor_names(measurement.id)

        try:
            # Line between the two points
            line = pv.Line(measurement.point_a, measurement.point_b)
            self.plotter.add_mesh(
                line, color='#60a5fa', line_width=2,
                name=names['line'],
                reset_camera=False,
            )

            # Marker spheres at endpoints
            bbox_diag = 1.0
            if hasattr(self, 'pv_cloud') and self.pv_cloud is not None:
                b = self.pv_cloud.bounds
                bbox_diag = np.sqrt((b[1]-b[0])**2 + (b[3]-b[2])**2 + (b[5]-b[4])**2)
            marker_radius = max(bbox_diag * 0.003, 0.005)

            sphere_a = pv.Sphere(radius=marker_radius, center=measurement.point_a)
            self.plotter.add_mesh(sphere_a, color='#2563eb', name=names['marker_a'], reset_camera=False)

            sphere_b = pv.Sphere(radius=marker_radius, center=measurement.point_b)
            self.plotter.add_mesh(sphere_b, color='#2563eb', name=names['marker_b'], reset_camera=False)

            # Text label at midpoint
            midpoint = (measurement.point_a + measurement.point_b) / 2.0
            label_text = f"{measurement.distance:.3f}"
            self.plotter.add_point_labels(
                pv.PolyData(midpoint.reshape(1, 3)),
                [label_text],
                font_size=10,
                text_color='#f8fafc',
                shape_color='#1e293b',
                shape_opacity=0.8,
                shape='rounded_rect',
                fill_shape=True,
                always_visible=True,
                show_points=False,
                name=names['label'],
            )

            self.plotter.render()
        except Exception as e:
            logger.warning(f"Could not render measurement overlay: {e}")

    def _render_pending_marker(self, point: np.ndarray):
        """Render a temporary marker for Point A while waiting for Point B."""
        if self.plotter is None:
            return

        self._remove_pending_marker()

        try:
            bbox_diag = 1.0
            if hasattr(self, 'pv_cloud') and self.pv_cloud is not None:
                b = self.pv_cloud.bounds
                bbox_diag = np.sqrt((b[1]-b[0])**2 + (b[3]-b[2])**2 + (b[5]-b[4])**2)
            marker_radius = max(bbox_diag * 0.0035, 0.006)

            sphere = pv.Sphere(radius=marker_radius, center=point)
            self._pending_marker_actor = self.plotter.add_mesh(
                sphere, color='#10b981', name='pending_marker_a', reset_camera=False
            )
            self.plotter.render()
        except Exception as e:
            logger.warning(f"Could not render pending marker: {e}")

    def _remove_pending_marker(self):
        """Remove the temporary Point A marker."""
        if self.plotter is None:
            return
        try:
            self.plotter.remove_actor('pending_marker_a')
        except Exception:
            pass
        self._pending_marker_actor = None

    def _remove_actors_by_name(self, actor_names: List[str]):
        """Remove a list of named actors from the plotter."""
        if self.plotter is None:
            return
        for name in actor_names:
            try:
                self.plotter.remove_actor(name)
            except Exception:
                pass
