import sys
import os
import numpy as np
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                            QSlider, QComboBox, QFileDialog, QMessageBox, 
                            QGroupBox, QCheckBox, QSplitter, QProgressBar,
                            QTabWidget, QStatusBar, QScrollArea, QDialog,
                            QLineEdit, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot, QSettings
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPalette, QColor, QAction, QSurfaceFormat

import open3d as o3d
import pyvista as pv
from pyvistaqt import QtInteractor
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).parent

class PointCloudProcessor(QThread):
    """Thread for processing point cloud operations"""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    loaded = pyqtSignal(object)
    
    def __init__(self, file_path: str, operation: str = "load"):
        super().__init__()
        self.file_path = file_path
        self.operation = operation
        self.point_cloud = None
        
    def run(self):
        try:
            self.progress.emit(10)
            
            if self.operation == "load":
                # Load point cloud
                file_ext = Path(self.file_path).suffix.lower()
                
                if file_ext in ['.pcd', '.ply']:
                    self.point_cloud = o3d.io.read_point_cloud(self.file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: .pcd, .ply")
                
                if len(self.point_cloud.points) == 0:
                    raise ValueError("No points found in the file")
                
                self.progress.emit(30)
                
                # Estimate normals if not present
                if not self.point_cloud.has_normals():
                    self.point_cloud.estimate_normals(
                        search_param=o3d.geometry.KDTreeSearchParamHybrid(
                            radius=0.1, max_nn=30))
                
                self.progress.emit(60)
                
                # Center the point cloud
                center = self.point_cloud.get_center()
                self.point_cloud.translate(-center)
                
                self.progress.emit(90)
                
                # Emit the loaded point cloud
                self.loaded.emit(self.point_cloud)
                
                self.progress.emit(100)
                
        except Exception as e:
            self.error.emit(f"Error loading point cloud: {str(e)}")
        
        finally:
            self.finished.emit()


class PyVistaWidget(QWidget):
    """PyVista visualization widget with improved update mechanisms"""
    
    # Color mode mapping
    COLOR_MODES = {
        'Original': 'original',
        'Height': 'height',
        'Elevation': 'elevation',
        'Distance': 'distance',
        'Normal': 'normal',
        'Curvature': 'curvature'
    }
    
    BACKGROUND_STYLES = {
        'White': 'white',
        'Black': 'black',
        'Gray': '#f0f0f0',
        'Gradient': ('white', 'lightblue'),
        'Dark Gradient': ('#1A1A26', '#212136'),
        'Sunset Gradient': ('#ffeaa7', '#fd79a8')
    }
    
    def __init__(self):
        super().__init__()
        self.plotter = None
        self.point_cloud_actor = None
        self.normals_actor = None
        self.axes_actor = None
        self.current_point_cloud = None
        
        # Track current visualization settings
        self.current_point_size = 5
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
                print(f"Warning: Could not add lighting: {e}")
            
            # Add coordinate axes in lower right corner
            try:
                self.axes_actor = self.plotter.add_axes(viewport=(0.8, 0, 1.0, 0.2))
            except Exception as e:
                print(f"Warning: Could not add coordinate axes: {e}")
            
            layout.addWidget(self.plotter.interactor)
            layout.setContentsMargins(0, 0, 0, 0)
            
        except Exception as e:
            print(f"Error setting up PyVista plotter: {e}")
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
            bg_config = self.BACKGROUND_STYLES.get(style)
            if bg_config:
                if isinstance(bg_config, tuple):
                    self.plotter.set_background(bg_config[0], top=bg_config[1])
                else:
                    self.plotter.set_background(bg_config)
            
            self.current_background = style
        except Exception as e:
            print(f"Warning: Could not set background: {e}")
            
    def update_point_cloud(self, point_cloud, force_refresh: bool = False):
        """Update the point cloud visualization"""
        if point_cloud is None:
            return
            
        # Only do full re-render if point cloud changed or forced
        if self.current_point_cloud is not point_cloud or force_refresh:
            self.current_point_cloud = point_cloud
            self.render_point_cloud()
        
    def render_point_cloud(self):
        """Render the current point cloud efficiently"""
        if self.current_point_cloud is None or self.plotter is None:
            return
            
        try:
            # Clear existing actors
            self._clear_actors()
        except Exception as e:
            print(f"Warning: Could not remove actors: {e}")
            
        # Convert Open3D point cloud to PyVista
        points = np.asarray(self.current_point_cloud.points)
        
        if len(points) == 0:
            return
            
        # Create PyVista point cloud
        pv_cloud = pv.PolyData(points)
        
        # Apply current color mode
        colored_points = self._apply_color_mode(points)
        if colored_points is not None:
            pv_cloud['colors'] = colored_points
            
        # Add point cloud to plotter
        render_args = {
            'point_size': self.current_point_size,
            'render_points_as_spheres': True
        }
        
        if 'colors' in pv_cloud.array_names:
            render_args.update({'scalars': 'colors', 'rgb': True})
            
        self.point_cloud_actor = self.plotter.add_mesh(pv_cloud, **render_args)
        
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
        
    def _add_normals_visualization(self, points: np.ndarray):
        """Add normal vectors visualization"""
        if not self.current_point_cloud.has_normals():
            return
            
        try:
            normals = np.asarray(self.current_point_cloud.normals)
            
            # Subsample for performance (max 1000 normals)
            step = max(1, len(points) // 1000)
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
            print(f"Warning: Could not add normals visualization: {e}")
        
    def _apply_color_mode(self, points: np.ndarray) -> Optional[np.ndarray]:
        """Apply different color modes to the point cloud"""
        original_colors = None
        if self.current_point_cloud.has_colors():
            original_colors = np.asarray(self.current_point_cloud.colors)
        
        if self.current_color_mode == "Original" and original_colors is not None:
            if original_colors.max() <= 1.0:
                return (original_colors * 255).astype(np.uint8)
            return original_colors.astype(np.uint8)
            
        elif self.current_color_mode == "Height":
            return self._color_by_height(points)
            
        elif self.current_color_mode == "Elevation":
            return self._color_by_elevation(points)
            
        elif self.current_color_mode == "Distance":
            return self._color_by_distance(points)
            
        elif self.current_color_mode == "Normal":
            return self._color_by_normal()
            
        elif self.current_color_mode == "Curvature":
            return self._color_by_curvature(points)
            
        # Default uniform color
        return np.full((len(points), 3), [128, 128, 128], dtype=np.uint8)
    
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
        """Color by normal direction"""
        if not self.current_point_cloud.has_normals():
            return None
        normals = np.asarray(self.current_point_cloud.normals)
        colors = np.abs(normals)
        return (colors * 255).astype(np.uint8)
    
    def _color_by_curvature(self, points: np.ndarray) -> np.ndarray:
        """Color by simple curvature estimation"""
        z_coords = points[:, 2]
        curvature = np.gradient(np.gradient(z_coords))
        curv_norm = np.abs(curvature)
        if curv_norm.max() > 0:
            curv_norm = (curv_norm - curv_norm.min()) / (curv_norm.max() - curv_norm.min())
        colormap = plt.colormaps.get_cmap('coolwarm')
        colors = colormap(curv_norm)[:, :3]
        return (colors * 255).astype(np.uint8)
            
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
                    if view_type == "default":
                        view_func()
                    else:
                        view_func()
                        
        except Exception as e:
            print(f"Warning: Could not set view: {e}")
        
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
                print(f"Warning: Could not update point size: {e}")
                # Fallback: full re-render if direct update fails
                self.render_point_cloud()
                
    def update_color_mode(self, mode: str):
        """Update color mode and re-render only if changed"""
        if mode == self.current_color_mode:
            return
            
        self.current_color_mode = mode
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
                print(f"Warning: Could not remove normals: {e}")
                
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
            print(f"Warning: Could not reset camera: {e}")
        
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
            print(f"Error taking screenshot: {e}")
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
            print(f"Warning during PyVista cleanup: {e}")


class PCDVisualizer(QMainWindow):
    """Main application window for PCD visualization"""
    
    def __init__(self, initial_file_path: Optional[str] = None):
        super().__init__()
        self.point_cloud = None
        self.original_point_cloud = None
        self.processor_thread = None
        self.settings = QSettings('PCDVisualizer', 'Settings')
        self.initial_file_path = initial_file_path
        
        # Initialize theme
        self.is_dark_mode = self._get_system_theme_preference()
        
        self.init_ui()
        self.apply_theme(self.is_dark_mode)
        
        # Load initial file if provided
        if self.initial_file_path:
            # Use QTimer to load file after UI is fully initialized
            QTimer.singleShot(100, self._load_initial_file)
        
    def _get_system_theme_preference(self) -> bool:
        """Detect system theme preference"""
        try:
            palette = QApplication.instance().palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            return bg_color.lightness() < 128
        except:
            return False
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PCD Point Cloud Visualizer")
        icon_path = SCRIPT_DIR / 'assets' / 'visualizer_icon.ico'
        self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1000, 700)
        self._center_window()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Setup panels
        control_panel = self._setup_control_panel()
        visualization_panel = self._setup_visualization_panel()
        
        # Add panels to splitter
        main_splitter.addWidget(control_panel)
        main_splitter.addWidget(visualization_panel)
        main_splitter.setSizes([250, 750])
        
        # Set main layout
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        central_widget.setLayout(layout)
        
        # Setup menus and status bar
        self._setup_menus()
        self._setup_statusbar()
        
    def _center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
        
    def _setup_control_panel(self) -> QScrollArea:
        """Setup the control panel with all settings"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        panel = QWidget()
        layout = QVBoxLayout()
        
        # File info section
        layout.addWidget(self._create_file_info_group())
        
        # Visualization settings
        layout.addWidget(self._create_visualization_group())
        
        # Camera controls
        layout.addWidget(self._create_camera_group())
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        panel.setLayout(layout)
        scroll_area.setWidget(panel)
        return scroll_area
    
    def _create_file_info_group(self) -> QGroupBox:
        """Create file information group"""
        file_group = QGroupBox("File Information")
        file_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        file_layout.addWidget(self.progress_bar)
        
        # Load button
        load_btn = QPushButton("Load Point Cloud File")
        load_btn.clicked.connect(self.load_file)
        load_btn.setMinimumHeight(35)
        file_layout.addWidget(load_btn)
        
        file_group.setLayout(file_layout)
        return file_group
    
    def _create_visualization_group(self) -> QGroupBox:
        """Create visualization settings group"""
        viz_group = QGroupBox("Visualization Settings")
        viz_layout = QGridLayout()
        
        # Point size with slider
        viz_layout.addWidget(QLabel("Point Size:"), 0, 0)
        self.point_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_size_slider.setRange(1, 20)
        self.point_size_slider.setValue(5)
        self.point_size_slider.valueChanged.connect(self._on_point_size_changed)
        viz_layout.addWidget(self.point_size_slider, 0, 1)
        
        self.point_size_label = QLabel("5")
        self.point_size_label.setMinimumWidth(25)
        viz_layout.addWidget(self.point_size_label, 0, 2)
        
        # Color mode
        viz_layout.addWidget(QLabel("Color Mode:"), 1, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(list(PyVistaWidget.COLOR_MODES.keys()))
        self.color_mode_combo.currentTextChanged.connect(self._on_color_mode_changed)
        viz_layout.addWidget(self.color_mode_combo, 1, 1, 1, 2)
        
        # Background
        viz_layout.addWidget(QLabel("Background:"), 2, 0)
        self.background_combo = QComboBox()
        self.background_combo.addItems(list(PyVistaWidget.BACKGROUND_STYLES.keys()))
        self.background_combo.currentTextChanged.connect(self._on_background_changed)
        viz_layout.addWidget(self.background_combo, 2, 1, 1, 2)
        
        # Show normals checkbox
        self.normals_checkbox = QCheckBox("Show Normal Vectors")
        self.normals_checkbox.toggled.connect(self._on_normals_toggled)
        viz_layout.addWidget(self.normals_checkbox, 3, 0, 1, 3)
        
        viz_group.setLayout(viz_layout)
        return viz_group
    
    def _create_camera_group(self) -> QGroupBox:
        """Create camera controls group"""
        camera_group = QGroupBox("Camera Controls")
        camera_layout = QGridLayout()
        
        # Create view buttons
        buttons = [
            ("Reset View", self.reset_view, 0, 0, 1, 2),
            ("Top View", self._set_top_view, 1, 0),
            ("Front View", self._set_front_view, 1, 1),
            ("Side View", self._set_side_view, 2, 0),
            ("Isometric", self._set_iso_view, 2, 1)
        ]
        
        for button_data in buttons:
            btn = QPushButton(button_data[0])
            btn.clicked.connect(button_data[1])
            if len(button_data) == 6:  # Spans multiple columns
                btn.setMinimumHeight(30)
                camera_layout.addWidget(btn, button_data[2], button_data[3], button_data[4], button_data[5])
            else:
                camera_layout.addWidget(btn, button_data[2], button_data[3])
        
        camera_group.setLayout(camera_layout)
        return camera_group
        
    def _setup_visualization_panel(self) -> QWidget:
        """Setup the visualization panel with tabs"""
        panel = QWidget()
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 3D Visualization tab
        self.pyvista_widget = PyVistaWidget()
        self.tab_widget.addTab(self.pyvista_widget, "3D View")
        
        # Statistics tab
        self.stats_widget = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_widget, "Statistics")
        
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        panel.setLayout(layout)
        return panel
        
    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create scroll area for statistics content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Statistics content widget
        stats_content = QWidget()
        stats_layout = QVBoxLayout()
        
        # Create statistics groups
        stats_groups = [
            ("Basic Information", "basic_stats_label"),
            ("Geometric Properties", "geo_stats_label"),
            ("Features", "features_stats_label"),
            ("Additional Statistics", "additional_stats_label")
        ]
        
        for group_name, label_attr in stats_groups:
            group = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            
            label = QLabel("No data available")
            label.setFont(QFont("Courier", 9))
            setattr(self, label_attr, label)
            
            group_layout.addWidget(label)
            group.setLayout(group_layout)
            stats_layout.addWidget(group)
        
        stats_layout.addStretch()
        stats_content.setLayout(stats_layout)
        scroll_area.setWidget(stats_content)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
        
    def _setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        self._add_file_menu_actions(file_menu)
        
        # View menu
        view_menu = menubar.addMenu('View')
        self._add_view_menu_actions(view_menu)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        self._add_help_menu_actions(help_menu)
    
    def _add_file_menu_actions(self, file_menu):
        """Add actions to file menu"""
        actions = [
            ("Open Point Cloud File", "Ctrl+O", self.load_file),
            None,  # Separator
            ("Export Point Cloud...", "Ctrl+E", self.export_file),
            None,  # Separator
            ("Take Screenshot...", "Ctrl+S", self.take_screenshot),
            None,  # Separator
            ("Exit", "Ctrl+Q", self.close)
        ]
        
        self._add_menu_actions(file_menu, actions)
    
    def _add_view_menu_actions(self, view_menu):
        """Add actions to view menu"""
        actions = [
            ("Reset Camera", "0", self.reset_view),
            None,  # Separator
            ("Top View", "1", self._set_top_view),
            ("Front View", "2", self._set_front_view),
            ("Side View", "3", self._set_side_view),
            ("Isometric View", "4", self._set_iso_view),
            None,  # Separator
            ("Fullscreen", "F11", self.toggle_fullscreen),
            ("Toggle Theme", "Ctrl+T", self.toggle_theme)
        ]
        
        self._add_menu_actions(view_menu, actions)
    
    def _add_help_menu_actions(self, help_menu):
        """Add actions to help menu"""
        actions = [
            ("About", None, self.show_about)
        ]
        
        self._add_menu_actions(help_menu, actions)
    
    def _add_menu_actions(self, menu, actions):
        """Helper to add actions to a menu"""
        for action_data in actions:
            if action_data is None:
                menu.addSeparator()
            else:
                action = QAction(action_data[0], self)
                if action_data[1]:  # Has shortcut
                    action.setShortcut(action_data[1])
                action.triggered.connect(action_data[2])
                menu.addAction(action)
        
    def _setup_statusbar(self):
        """Setup status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a point cloud file to begin")
        
    # Event handlers
    def _on_point_size_changed(self):
        """Handle point size slider changes"""
        size = self.point_size_slider.value()
        self.point_size_label.setText(str(size))
        
        if self.point_cloud:
            self.pyvista_widget.update_point_size(size)
        
    def _on_color_mode_changed(self):
        """Handle color mode changes"""
        if self.point_cloud:
            color_mode = self.color_mode_combo.currentText()
            self.pyvista_widget.update_color_mode(color_mode)
        
    def _on_background_changed(self):
        """Handle background changes"""
        bg_type = self.background_combo.currentText()
        self.pyvista_widget.update_background(bg_type)
        
    def _on_normals_toggled(self):
        """Handle normals toggle"""
        show = self.normals_checkbox.isChecked()
        self.pyvista_widget.toggle_normals_display(show)
    
    # Camera view methods
    def reset_view(self):
        """Reset camera view"""
        if self.point_cloud:
            self.pyvista_widget.reset_camera()
        
    def _set_top_view(self):
        """Set top view"""
        self.pyvista_widget.set_view("top")
        
    def _set_front_view(self):
        """Set front view"""
        self.pyvista_widget.set_view("front")
        
    def _set_side_view(self):
        """Set side view"""
        self.pyvista_widget.set_view("side")
        
    def _set_iso_view(self):
        """Set isometric view"""
        self.pyvista_widget.set_view("iso")
    
    # File operations
    def load_file(self):
        """Load point cloud file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Point Cloud File", "", 
            "Point Cloud Data (*.pcd *.ply);;PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
        )
        
        if file_path:
            self._load_specific_file(file_path)
            
    def _load_initial_file(self):
        """Load the initial file provided via command line"""
        if self.initial_file_path:
            self._load_specific_file(self.initial_file_path)
    
    def _load_specific_file(self, file_path: str):
        """Load a specific file path"""
        if not Path(file_path).exists():
            QMessageBox.warning(self, "File Not Found", f"File does not exist: {file_path}")
            return
            
        self.file_label.setText(f"Loading: {Path(file_path).name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Loading point cloud...")
        
        # Disable UI during loading
        self.setEnabled(False)
        
        # Start processing thread
        self.processor_thread = PointCloudProcessor(file_path)
        self.processor_thread.progress.connect(self.progress_bar.setValue)
        self.processor_thread.error.connect(self._show_error)
        self.processor_thread.loaded.connect(self._on_point_cloud_loaded)
        self.processor_thread.finished.connect(self._on_processing_finished)
        self.processor_thread.start()
    
    def export_file(self):
        """Export point cloud to file"""
        if not self.point_cloud:
            QMessageBox.warning(self, "Warning", "No point cloud loaded")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Point Cloud", "exported_cloud.pcd",
            "PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
        )
        
        if file_path:
            try:
                o3d.io.write_point_cloud(file_path, self.point_cloud)
                QMessageBox.information(self, "Success", f"Point cloud exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def take_screenshot(self):
        """Take a screenshot"""
        if not self.point_cloud:
            QMessageBox.warning(self, "Warning", "No point cloud loaded")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "screenshot.png",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        
        if file_path:
            filename = self.pyvista_widget.take_screenshot(file_path)
            if filename:
                QMessageBox.information(self, "Success", f"Screenshot saved as {filename}")
            else:
                QMessageBox.warning(self, "Warning", "Failed to save screenshot")
    
    # Processing callbacks
    def _on_point_cloud_loaded(self, point_cloud):
        """Handle successful point cloud loading"""
        self.point_cloud = point_cloud
        self.original_point_cloud = o3d.geometry.PointCloud(point_cloud)
        
        # Update UI
        point_count = len(point_cloud.points)
        self.file_label.setText(f"Loaded: {point_count:,} points")
        
        # Update statistics and visualization
        self._update_statistics()
        self.pyvista_widget.update_point_cloud(point_cloud, force_refresh=True)
        
        # Update status and enable controls
        self.status_bar.showMessage(f"Loaded {point_count:,} points successfully")
        self._enable_point_cloud_controls(True)
        
    def _on_processing_finished(self):
        """Handle processing completion"""
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        
    def _show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("Error occurred - Ready")
        
    def _enable_point_cloud_controls(self, enabled: bool):
        """Enable/disable controls that require a loaded point cloud"""
        controls = [
            self.point_size_slider,
            self.color_mode_combo,
            self.normals_checkbox
        ]
        for control in controls:
            control.setEnabled(enabled)
    
    # Statistics and calculations
    def _update_statistics(self):
        """Update the statistics display"""
        if not self.point_cloud:
            self._clear_statistics()
            return
            
        points = np.asarray(self.point_cloud.points)
        point_count = len(points)
        
        # Update each statistics section
        self._update_basic_stats(points, point_count)
        self._update_geometric_stats(points)
        self._update_features_stats()
        self._update_additional_stats(points)
    
    def _clear_statistics(self):
        """Clear all statistics displays"""
        labels = [
            self.basic_stats_label,
            self.geo_stats_label, 
            self.features_stats_label,
            self.additional_stats_label
        ]
        for label in labels:
            label.setText("No point cloud loaded" if label == self.basic_stats_label else "No data available")
    
    def _update_basic_stats(self, points: np.ndarray, point_count: int):
        """Update basic statistics"""
        basic_info = f"""Points: {point_count:,}
Dimensions: {points.shape}
Memory: {points.nbytes / 1024 / 1024:.2f} MB"""
        self.basic_stats_label.setText(basic_info)
    
    def _update_geometric_stats(self, points: np.ndarray):
        """Update geometric statistics"""
        centroid = points.mean(axis=0)
        volume = self._calculate_volume(points)
        density = self._calculate_density(points, volume)
        
        geo_info = f"""Centroid: ({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})
Bounding Box Volume: {volume:.6f} units³
Point Density: {density:.2f} points/unit³

Coordinate Ranges:
X: {points[:, 0].min():.3f} to {points[:, 0].max():.3f}
Y: {points[:, 1].min():.3f} to {points[:, 1].max():.3f}
Z: {points[:, 2].min():.3f} to {points[:, 2].max():.3f}"""
        self.geo_stats_label.setText(geo_info)
    
    def _update_features_stats(self):
        """Update features statistics"""
        features_info = f"""Has Colors: {'Yes' if self.point_cloud.has_colors() else 'No'}
Has Normals: {'Yes' if self.point_cloud.has_normals() else 'No'}
Has Covariances: {'Yes' if self.point_cloud.has_covariances() else 'No'}"""
        
        # Add color statistics if available
        if self.point_cloud.has_colors():
            colors = np.asarray(self.point_cloud.colors)
            features_info += f"""

Color Statistics:
R: {colors[:, 0].mean():.3f} ± {colors[:, 0].std():.3f}
G: {colors[:, 1].mean():.3f} ± {colors[:, 1].std():.3f}
B: {colors[:, 2].mean():.3f} ± {colors[:, 2].std():.3f}"""
        
        self.features_stats_label.setText(features_info)
    
    def _update_additional_stats(self, points: np.ndarray):
        """Update additional statistics"""
        center = points.mean(axis=0)
        distances = np.linalg.norm(points - center, axis=1)
        
        additional_info = f"""Distance from Centroid:
Min: {distances.min():.6f}
Max: {distances.max():.6f}
Mean: {distances.mean():.6f}
Std: {distances.std():.6f}

Coordinate Statistics:
X: μ={points[:, 0].mean():.6f}, σ={points[:, 0].std():.6f}
Y: μ={points[:, 1].mean():.6f}, σ={points[:, 1].std():.6f}
Z: μ={points[:, 2].mean():.6f}, σ={points[:, 2].std():.6f}"""
        
        # Add normal statistics if available
        if self.point_cloud.has_normals():
            normals = np.asarray(self.point_cloud.normals)
            avg_magnitude = np.linalg.norm(normals, axis=1).mean()
            additional_info += f"""

Normal Vectors:
Count: {len(normals):,}
Average Magnitude: {avg_magnitude:.6f}"""
        
        self.additional_stats_label.setText(additional_info)
    
    def _calculate_volume(self, points: np.ndarray) -> float:
        """Calculate bounding box volume"""
        if len(points) == 0:
            return 0.0
        ranges = points.max(axis=0) - points.min(axis=0)
        return float(np.prod(ranges))
        
    def _calculate_density(self, points: np.ndarray, volume: float) -> float:
        """Calculate point density"""
        if volume == 0:
            return 0.0
        return len(points) / volume
    
    # Theme management
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(self.is_dark_mode)
        
    def apply_theme(self, is_dark: bool):
        """Apply dark or light theme to the application"""
        app = QApplication.instance()
        
        if is_dark:
            self._apply_dark_theme(app)
        else:
            self._apply_light_theme(app)
        
        # Apply comprehensive stylesheet
        self._apply_theme_stylesheet(is_dark)
        
        # Force update
        self.update()
        app.processEvents()
    
    def _apply_dark_theme(self, app):
        """Apply dark theme palette"""
        dark_palette = QPalette()
        
        # Define dark theme colors
        colors = {
            QPalette.ColorRole.Window: QColor(53, 53, 53),
            QPalette.ColorRole.WindowText: QColor(255, 255, 255),
            QPalette.ColorRole.Base: QColor(25, 25, 25),
            QPalette.ColorRole.AlternateBase: QColor(53, 53, 53),
            QPalette.ColorRole.Text: QColor(255, 255, 255),
            QPalette.ColorRole.BrightText: QColor(255, 0, 0),
            QPalette.ColorRole.Button: QColor(53, 53, 53),
            QPalette.ColorRole.ButtonText: QColor(255, 255, 255),
            QPalette.ColorRole.Highlight: QColor(42, 130, 218),
            QPalette.ColorRole.HighlightedText: QColor(0, 0, 0),
            QPalette.ColorRole.ToolTipBase: QColor(0, 0, 0),
            QPalette.ColorRole.ToolTipText: QColor(255, 255, 255),
        }
        
        # Apply colors to all color groups
        for group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled]:
            for role, color in colors.items():
                dark_palette.setColor(group, role, color)
        
        # Override disabled colors
        disabled_colors = {
            QPalette.ColorRole.WindowText: QColor(127, 127, 127),
            QPalette.ColorRole.Text: QColor(127, 127, 127),
            QPalette.ColorRole.ButtonText: QColor(127, 127, 127),
        }
        
        for role, color in disabled_colors.items():
            dark_palette.setColor(QPalette.ColorGroup.Disabled, role, color)
        
        app.setPalette(dark_palette)
        self.setPalette(dark_palette)
    
    def _apply_light_theme(self, app):
        """Apply light theme palette"""
        app.setPalette(app.style().standardPalette())
        self.setPalette(app.style().standardPalette())
        
    def _apply_theme_stylesheet(self, is_dark: bool):
        """Apply comprehensive stylesheet for the theme"""
        if is_dark:
            style = self._get_dark_stylesheet()
        else:
            style = self._get_light_stylesheet()
        
        self.setStyleSheet(style)
    
    def _get_dark_stylesheet(self) -> str:
        """Get dark theme stylesheet"""
        return """
            QMainWindow { background-color: #353535; color: #ffffff; }
            QWidget { background-color: #353535; color: #ffffff; }
            QGroupBox {
                font-weight: bold; border: 2px solid #5a5a5a; border-radius: 5px;
                margin-top: 1ex; padding-top: 5px; background-color: #353535; color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: #ffffff;
            }
            QPushButton {
                background-color: #454545; border: 1px solid #5a5a5a; border-radius: 3px;
                padding: 5px; color: #ffffff;
            }
            QPushButton:hover { background-color: #565656; }
            QPushButton:pressed { background-color: #2a82da; }
            QPushButton:disabled { background-color: #2a2a2a; color: #7f7f7f; }
            QLabel { color: #ffffff; background: transparent; }
            QSlider::groove:horizontal {
                border: 1px solid #5a5a5a; height: 8px; background: #353535;
                margin: 2px 0; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2a82da; border: 1px solid #5a5a5a; width: 18px;
                margin: -2px 0; border-radius: 3px;
            }
            QComboBox {
                background-color: #454545; border: 1px solid #5a5a5a; border-radius: 3px;
                padding: 5px; color: #ffffff;
            }
            QComboBox::drop-down { border-left: 1px solid #5a5a5a; width: 15px; background-color: #454545; }
            QComboBox::down-arrow {
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #ffffff; margin-left: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #454545; color: #ffffff; selection-background-color: #2a82da;
                border: 1px solid #5a5a5a;
            }
            QCheckBox { color: #ffffff; spacing: 5px; }
            QCheckBox::indicator { width: 13px; height: 13px; }
            QCheckBox::indicator:unchecked { background-color: #454545; border: 1px solid #5a5a5a; }
            QCheckBox::indicator:checked { background-color: #2a82da; border: 1px solid #5a5a5a; }
            QTabWidget::pane { border: 1px solid #5a5a5a; background-color: #353535; }
            QTabBar::tab {
                background-color: #454545; border: 1px solid #5a5a5a; padding: 8px 16px;
                margin-right: 2px; color: #ffffff;
            }
            QTabBar::tab:selected { background-color: #2a82da; border-bottom: 1px solid #2a82da; }
            QScrollArea { border: none; background-color: #353535; }
            QProgressBar {
                border: 1px solid #5a5a5a; border-radius: 3px; text-align: center;
                background-color: #353535; color: #ffffff;
            }
            QProgressBar::chunk { background-color: #2a82da; border-radius: 2px; }
            QMenuBar { background-color: #353535; color: #ffffff; border-bottom: 1px solid #5a5a5a; }
            QMenuBar::item { background: transparent; padding: 4px 8px; }
            QMenuBar::item:selected { background-color: #2a82da; }
            QMenu { background-color: #454545; color: #ffffff; border: 1px solid #5a5a5a; }
            QMenu::item { padding: 8px 32px 8px 16px; }
            QMenu::item:selected { background-color: #2a82da; }
            QStatusBar { background-color: #353535; color: #ffffff; border-top: 1px solid #5a5a5a; }
        """
    
    def _get_light_stylesheet(self) -> str:
        """Get light theme stylesheet"""
        return """
            QMainWindow { background-color: #f0f0f0; color: #000000; }
            QWidget { background-color: #f0f0f0; color: #000000; }
            QGroupBox {
                font-weight: bold; border: 2px solid #d0d0d0; border-radius: 5px;
                margin-top: 1ex; padding-top: 5px; background-color: #f0f0f0; color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0; border: 1px solid #b0b0b0; border-radius: 3px;
                padding: 5px; color: #000000;
            }
            QPushButton:hover { background-color: #d0d0d0; }
            QPushButton:pressed { background-color: #2a82da; color: #ffffff; }
            QPushButton:disabled { background-color: #f5f5f5; color: #999999; }
            QLabel { color: #000000; background: transparent; }
            QSlider::groove:horizontal {
                border: 1px solid #b0b0b0; height: 8px; background: #ffffff;
                margin: 2px 0; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2a82da; border: 1px solid #b0b0b0; width: 18px;
                margin: -2px 0; border-radius: 3px;
            }
            QComboBox {
                background-color: #ffffff; border: 1px solid #b0b0b0; border-radius: 3px;
                padding: 5px; color: #000000;
            }
            QComboBox::drop-down { border-left: 1px solid #b0b0b0; width: 15px; background-color: #e0e0e0; }
            QComboBox::down-arrow {
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #000000; margin-left: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff; color: #000000; selection-background-color: #2a82da;
                selection-color: #ffffff; border: 1px solid #b0b0b0;
            }
            QCheckBox { color: #000000; spacing: 5px; }
            QCheckBox::indicator { width: 13px; height: 13px; }
            QCheckBox::indicator:unchecked { background-color: #ffffff; border: 1px solid #b0b0b0; }
            QCheckBox::indicator:checked { background-color: #2a82da; border: 1px solid #b0b0b0; }
            QTabWidget::pane { border: 1px solid #d0d0d0; background-color: #ffffff; }
            QTabBar::tab {
                background-color: #f0f0f0; border: 1px solid #d0d0d0; padding: 8px 16px;
                margin-right: 2px; color: #000000;
            }
            QTabBar::tab:selected { background-color: #2a82da; color: white; border-bottom: 1px solid #2a82da; }
            QScrollArea { border: none; background-color: #ffffff; }
            QProgressBar {
                border: 1px solid #b0b0b0; border-radius: 3px; text-align: center;
                background-color: #ffffff; color: #000000;
            }
            QProgressBar::chunk { background-color: #2a82da; border-radius: 2px; }
            QMenuBar { background-color: #f0f0f0; color: #000000; border-bottom: 1px solid #d0d0d0; }
            QMenuBar::item { background: transparent; padding: 4px 8px; }
            QMenuBar::item:selected { background-color: #2a82da; color: #ffffff; }
            QMenu { background-color: #ffffff; color: #000000; border: 1px solid #d0d0d0; }
            QMenu::item { padding: 8px 32px 8px 16px; }
            QMenu::item:selected { background-color: #2a82da; color: #ffffff; }
            QStatusBar { background-color: #f0f0f0; color: #000000; border-top: 1px solid #d0d0d0; }
        """
    
    # Utility methods
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_about(self):
        """Shows a custom, resizable 'About' dialog."""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About PCD Visualizer")
        about_dialog.setMinimumSize(420, 380)

        about_text = """
        <h3>PCD Point Cloud Visualizer</h3>
        <p>A powerful tool for visualizing point cloud data, built with PyQt6, Open3D, and PyVista.</p>
        
        <h4>Key Features:</h4>
        <ul>
            <li>Point size control with smooth updates</li>
            <li>Multiple color modes and gradient backgrounds</li>
            <li>Dark/Light mode with system theme detection</li>
            <li>Detailed statistics display with sectioned layout</li>
            <li>Professional camera controls and view presets</li>
            <li>Export capabilities for screenshots and data</li>
        </ul>

        <p>Developed by: <b>Quantnueral Pvt. Ltd.</b></p>
        """

        layout = QVBoxLayout()
        
        # Add company logo with theme detection
        logo_label = QLabel()
        
        # Choose logo based on theme
        logo_filename = "logo_dark.png" if self.is_dark_mode else "logo_light.png"
        logo_path = SCRIPT_DIR / "assets" / logo_filename

        logo_label.setPixmap(QIcon(str(logo_path)).pixmap(140, 25))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(about_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(about_dialog.accept)
        
        layout.addWidget(logo_label)
        
        layout.addSpacing(5)
        separator = QWidget()
        separator.setFixedHeight(1)
        separator_color = "#5a5a5a" if self.is_dark_mode else "#d0d0d0"
        separator.setStyleSheet(f"background-color: {separator_color};")
        layout.addWidget(separator)
        layout.addSpacing(5)
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(ok_button)

        about_dialog.setLayout(layout)
        about_dialog.exec()
    
    def closeEvent(self, event):
        """Handle application closing with proper cleanup"""
        try:
            # Clean up PyVista widget
            if hasattr(self, 'pyvista_widget') and self.pyvista_widget.plotter:
                self.pyvista_widget.cleanup()
                    
            # Clean up thread if running
            if self.processor_thread and self.processor_thread.isRunning():
                self.processor_thread.quit()
                self.processor_thread.wait(1000)
                
        except Exception as e:
            print(f"Warning during application cleanup: {e}")
            
        event.accept()


def configure_environment():
    """Configure environment variables for better compatibility"""
    env_vars = {
        'QT_OPENGL': 'software',
        'PYVISTA_USE_PANEL': '0',
        'PYVISTA_OFF_SCREEN': 'false'
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value


def configure_pyvista():
    """Configure PyVista for better compatibility"""
    try:
        pv.set_plot_theme('document')
        pv.global_theme.multi_samples = 0
        pv.global_theme.depth_peeling.enabled = False
        pv.global_theme.silhouette.enabled = False
        pv.global_theme.lighting = True
        pv.global_theme.show_edges = False
        pv.global_theme.edge_color = 'black'
        pv.global_theme.line_width = 1
    except Exception as e:
        print(f"Warning: Could not configure PyVista theme: {e}")


def configure_opengl():
    """Configure OpenGL format for better compatibility"""
    try:
        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(2, 1)  # Use OpenGL 2.1 for better compatibility
        format.setSamples(0)  # Disable anti-aliasing
        QSurfaceFormat.setDefaultFormat(format)
    except Exception as e:
        print(f"Warning: Could not set OpenGL format: {e}")


def main():
    """Main application entry point with improved initialization"""
    # Configure environment
    configure_environment()
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("PCD Visualizer")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("PCDVisualizer")
    app.setStyle('Fusion')  # Modern look
    
    # Configure OpenGL and PyVista
    configure_opengl()
    configure_pyvista()
    
    # Check for command line arguments (file path to open)
    file_to_open = None
    if len(sys.argv) > 1:
        potential_file = sys.argv[1]
        if Path(potential_file).exists():
            file_to_open = potential_file
        else:
            print(f"Warning: File not found: {potential_file}")
    
    # Create and show main window
    window = PCDVisualizer(file_to_open)
    window.show()
    
    # Handle application exit with proper cleanup
    def cleanup_handler():
        """Clean up resources before exit"""
        try:
            if hasattr(window, 'pyvista_widget') and window.pyvista_widget:
                window.pyvista_widget.cleanup()
        except Exception as e:
            print(f"Warning during final cleanup: {e}")
    
    app.aboutToQuit.connect(cleanup_handler)
    
    try:
        return app.exec()
    except SystemExit:
        cleanup_handler()
        return 0


if __name__ == "__main__":
    sys.exit(main())


# Installation Requirements:
# pip install PyQt6 open3d pyvista pyvistaqt matplotlib numpy

# Usage:
# cd iwlars-core
# python pcd_visualizer.py