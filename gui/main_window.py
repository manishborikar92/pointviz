import sys
import numpy as np
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                             QStatusBar, QMessageBox, QFileDialog, QProgressDialog,
                             QApplication)
from PyQt6.QtCore import Qt, QTimer, QSettings, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor

import open3d as o3d

from config import LARGE_FILE_THRESHOLD_MB, ICON_PATH, APP_NAME, MAX_RECENT_FILES
from logger import logger
from core.point_cloud_processor import PointCloudProcessor
import core.statistics as statistics
from gui.control_panel import ControlPanel
from gui.visualization_panel import VisualizationPanel
from gui.dialogs import AboutDialog, LoadOptionsDialog
from gui.menus import setup_menus
from gui.theme_manager import apply_theme

class PCDVisualizer(QMainWindow):
    """Main application window for PCD visualization."""
    
    def __init__(self, initial_file_path: Optional[str] = None):
        super().__init__()
        self.point_cloud = None
        self.original_point_count = 0
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
        """Detect system theme preference."""
        try:
            palette = QApplication.instance().palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            return bg_color.lightness() < 128
        except Exception as e:
            logger.warning(f"Could not detect system theme preference: {e}. Defaulting to Light mode.")
            return False
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setAcceptDrops(True)
        self.resize(1000, 700)
        self._center_window()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Setup panels
        self.control_panel = ControlPanel(self)
        self.visualization_panel = VisualizationPanel(self)
        
        # Alias panel properties directly on MainWindow for backward compatibility
        self.pyvista_widget = self.visualization_panel.pyvista_widget
        self.file_label = self.control_panel.file_label
        self.progress_bar = self.control_panel.progress_bar
        self.point_size_slider = self.control_panel.point_size_slider
        self.point_size_label = self.control_panel.point_size_label
        self.color_mode_combo = self.control_panel.color_mode_combo
        self.background_combo = self.control_panel.background_combo
        self.normals_checkbox = self.control_panel.normals_checkbox
        
        # Add panels to splitter
        main_splitter.addWidget(self.control_panel)
        main_splitter.addWidget(self.visualization_panel)
        main_splitter.setSizes([250, 750])
        
        # Set main layout
        layout = QHBoxLayout()
        layout.addWidget(main_splitter)
        layout.setContentsMargins(5, 5, 5, 5)
        central_widget.setLayout(layout)
        
        # Setup menus and status bar
        setup_menus(self)
        self._setup_statusbar()
        
    def _center_window(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
        
    def _setup_statusbar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a point cloud file to begin")
        
    # Event handlers
    def _on_point_size_changed(self):
        """Handle point size slider changes."""
        size = self.point_size_slider.value()
        self.point_size_label.setText(str(size))
        
        if self.point_cloud:
            self.pyvista_widget.update_point_size(size)
        
    def _on_color_mode_changed(self):
        """Handle color mode changes."""
        if self.point_cloud:
            had_normals = self.point_cloud.has_normals()
            color_mode = self.color_mode_combo.currentText()
            self.pyvista_widget.update_color_mode(color_mode)
            if not had_normals and self.point_cloud.has_normals():
                self._update_statistics()
        
    def _on_background_changed(self):
        """Handle background changes."""
        bg_type = self.background_combo.currentText()
        self.pyvista_widget.update_background(bg_type)
        
    def _on_normals_toggled(self):
        """Handle normals toggle."""
        if self.point_cloud:
            had_normals = self.point_cloud.has_normals()
            show = self.normals_checkbox.isChecked()
            self.pyvista_widget.toggle_normals_display(show)
            if not had_normals and self.point_cloud.has_normals():
                self._update_statistics()
    
    # Camera view methods
    def reset_view(self):
        """Reset camera view."""
        if self.point_cloud:
            self.pyvista_widget.reset_camera()
        
    def _set_top_view(self):
        """Set top view."""
        self.pyvista_widget.set_view("top")
        
    def _set_front_view(self):
        """Set front view."""
        self.pyvista_widget.set_view("front")
        
    def _set_side_view(self):
        """Set side view."""
        self.pyvista_widget.set_view("side")
        
    def _set_iso_view(self):
        """Set isometric view."""
        self.pyvista_widget.set_view("iso")
    
    # File operations
    def load_file(self):
        """Load point cloud file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Point Cloud File", "", 
            "Point Cloud Data (*.pcd *.ply);;PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
        )
        
        if file_path:
            self._load_specific_file(file_path)
            
    def _load_initial_file(self):
        """Load the initial file provided via command line."""
        if self.initial_file_path:
            self._load_specific_file(self.initial_file_path)
    
    def _load_specific_file(self, file_path: str):
        """Load a specific file path with downsampling options for large files."""
        p_file = Path(file_path)
        if not p_file.exists():
            QMessageBox.warning(self, "File Not Found", f"File does not exist: {file_path}")
            return

        file_size_mb = p_file.stat().st_size / (1024 * 1024)
        load_options = {"method": "none", "value": None}

        # For large files (e.g., > 100MB), ask the user for loading options
        if file_size_mb > LARGE_FILE_THRESHOLD_MB:
            dialog = LoadOptionsDialog(file_size_mb, self)
            options = dialog.get_options()
            if options is None:  # User cancelled
                return
            load_options = options
            
        self.file_label.setText(f"Loading: {p_file.name}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Loading point cloud...")
        
        # Disable UI during loading
        self.setEnabled(False)
        
        # Start processing thread with load options
        self.processor_thread = PointCloudProcessor(file_path, load_options)
        self.processor_thread.progress.connect(self.progress_bar.setValue)
        self.processor_thread.error.connect(self._show_error)
        self.processor_thread.loaded.connect(self._on_point_cloud_loaded)
        self.processor_thread.finished.connect(self._on_processing_finished)
        self.processor_thread.start()
    
    def export_file(self):
        """Export point cloud to file in a background thread."""
        if not self.point_cloud:
            QMessageBox.warning(self, "Warning", "No point cloud loaded")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Point Cloud", "exported_cloud.pcd",
            "PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
        )
        
        if not file_path:
            return
            
        # Create progress dialog
        self.export_progress = QProgressDialog("Exporting point cloud...", "Cancel", 0, 100, self)
        self.export_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.export_progress.setAutoClose(True)
        self.export_progress.setValue(0)
        
        # Create thread
        self.export_thread = PointCloudProcessor(
            file_path=file_path,
            operation="export",
            point_cloud=self.point_cloud
        )
        
        # Connect signals
        self.export_thread.progress.connect(self.export_progress.setValue)
        self.export_thread.error.connect(self._on_export_error)
        self.export_thread.exported.connect(self._on_export_success)
        self.export_thread.finished.connect(self._on_export_finished)
        
        # If user clicks cancel on progress dialog, request thread interruption
        self.export_progress.canceled.connect(self.export_thread.requestInterruption)
        
        self.export_thread.start()

    @pyqtSlot(str)
    def _on_export_error(self, err_msg: str):
        QMessageBox.critical(self, "Export Error", f"Failed to export: {err_msg}")
        
    @pyqtSlot(str)
    def _on_export_success(self, file_path: str):
        QMessageBox.information(self, "Success", f"Point cloud exported successfully to:\n{file_path}")
        
    @pyqtSlot()
    def _on_export_finished(self):
        if hasattr(self, 'export_progress') and self.export_progress:
            self.export_progress.close()
            self.export_progress = None
        if hasattr(self, 'export_thread') and self.export_thread:
            self.export_thread.deleteLater()
            self.export_thread = None
    
    def take_screenshot(self):
        """Take a screenshot."""
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
    @pyqtSlot(object, int)
    def _on_point_cloud_loaded(self, point_cloud, original_point_count):
        """Handle successful point cloud loading, receiving original count."""
        self.point_cloud = point_cloud
        self.original_point_count = original_point_count
        
        # Add to recent files if loaded from a file
        if self.processor_thread and hasattr(self.processor_thread, 'file_path') and self.processor_thread.file_path:
            self._add_to_recent_files(self.processor_thread.file_path)
        
        # Update UI
        displayed_count = len(point_cloud.points)
        if displayed_count < original_point_count:
            self.file_label.setText(f"Loaded: {displayed_count:,} points\n"
                                    f"(Downsampled from {original_point_count:,})")
        else:
            self.file_label.setText(f"Loaded: {displayed_count:,} points")
            
        # Determine adaptive point size based on count
        if displayed_count < 5000:
            suggested_size = 5
        elif displayed_count < 25000:
            suggested_size = 3
        elif displayed_count < 100000:
            suggested_size = 2
        else:
            suggested_size = 1
            
        self.point_size_slider.setValue(suggested_size)
        self.point_size_label.setText(str(suggested_size))
        
        # Update statistics and visualization
        self._update_statistics()
        self.pyvista_widget.update_point_cloud(point_cloud, force_refresh=True)
        
        # Update status and enable controls
        self.status_bar.showMessage(f"Displayed {displayed_count:,} of {original_point_count:,} points successfully")
        self._enable_point_cloud_controls(True)
        
    def _on_processing_finished(self):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.setEnabled(True)
        
    def _show_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage("Error occurred - Ready")
        
    def _enable_point_cloud_controls(self, enabled: bool):
        """Enable/disable controls that require a loaded point cloud."""
        controls = [
            self.point_size_slider,
            self.color_mode_combo,
            self.normals_checkbox
        ]
        for control in controls:
            control.setEnabled(enabled)
    
    # Statistics and calculations
    def _update_statistics(self):
        """Update the statistics display."""
        if not self.point_cloud:
            self._clear_statistics()
            return
            
        points = np.asarray(self.point_cloud.points)
        
        self._update_basic_stats(points)
        self._update_geometric_stats(points)
        self._update_features_stats()
        self._update_additional_stats(points)
    
    def _clear_statistics(self):
        """Clear all statistics displays."""
        labels = [
            self.basic_stats_label,
            self.geo_stats_label, 
            self.features_stats_label,
            self.additional_stats_label
        ]
        for label in labels:
            label.setText("No point cloud loaded" if label == self.basic_stats_label else "No data available")
    
    def _update_basic_stats(self, points: np.ndarray):
        """Update basic statistics with original and displayed counts."""
        displayed_count = len(points)
        
        basic_info = f"""Displayed Points: {displayed_count:,}
Original Points:  {self.original_point_count:,}
Dimensions: {points.shape}
Memory (Displayed): {points.nbytes / 1024 / 1024:.2f} MB"""
        self.basic_stats_label.setText(basic_info)
    
    def _update_geometric_stats(self, points: np.ndarray):
        """Update geometric statistics."""
        centroid = statistics.compute_centroid(points)
        volume = statistics.calculate_volume(points)
        density = statistics.calculate_density(points, volume)
        ranges = statistics.compute_ranges(points)
        
        geo_info = f"""Centroid: ({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})
Bounding Box Volume: {volume:.6f} units³
Point Density: {density:.2f} points/unit³

Coordinate Ranges:
X: {ranges['x'][0]:.3f} to {ranges['x'][1]:.3f}
Y: {ranges['y'][0]:.3f} to {ranges['y'][1]:.3f}
Z: {ranges['z'][0]:.3f} to {ranges['z'][1]:.3f}"""
        self.geo_stats_label.setText(geo_info)
    
    def _update_features_stats(self):
        """Update features statistics."""
        features_info = f"""Has Colors: {'Yes' if self.point_cloud.has_colors() else 'No'}
Has Normals: {'Yes' if self.point_cloud.has_normals() else 'No'}
Has Covariances: {'Yes' if self.point_cloud.has_covariances() else 'No'}"""
        
        # Add color statistics if available
        if self.point_cloud.has_colors():
            colors = np.asarray(self.point_cloud.colors)
            color_stats = statistics.compute_color_stats(colors)
            features_info += f"""

Color Statistics:
R: {color_stats['r']['mean']:.3f} ± {color_stats['r']['std']:.3f}
G: {color_stats['g']['mean']:.3f} ± {color_stats['g']['std']:.3f}
B: {color_stats['b']['mean']:.3f} ± {color_stats['b']['std']:.3f}"""
        
        self.features_stats_label.setText(features_info)
    
    def _update_additional_stats(self, points: np.ndarray):
        """Update additional statistics."""
        centroid = statistics.compute_centroid(points)
        dist_stats = statistics.compute_distance_stats(points, centroid)
        coord_stats = statistics.compute_coordinate_stats(points)
        
        additional_info = f"""Distance from Centroid:
Min: {dist_stats['min']:.6f}
Max: {dist_stats['max']:.6f}
Mean: {dist_stats['mean']:.6f}
Std: {dist_stats['std']:.6f}

Coordinate Statistics:
X: μ={coord_stats['x']['mean']:.6f}, σ={coord_stats['x']['std']:.6f}
Y: μ={coord_stats['y']['mean']:.6f}, σ={coord_stats['y']['std']:.6f}
Z: μ={coord_stats['z']['mean']:.6f}, σ={coord_stats['z']['std']:.6f}"""
        
        # Add normal statistics if available
        if self.point_cloud.has_normals():
            normals = np.asarray(self.point_cloud.normals)
            avg_magnitude = np.linalg.norm(normals, axis=1).mean()
            additional_info += f"""

Normal Vectors:
Count: {len(normals):,}
Average Magnitude: {avg_magnitude:.6f}"""
        
        self.additional_stats_label.setText(additional_info)
    
    # Theme management
    def toggle_theme(self):
        """Toggle between dark and light mode."""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(self.is_dark_mode)
        
    def apply_theme(self, is_dark: bool):
        """Apply dark or light theme to the application."""
        apply_theme(self, is_dark)
    
    # Utility methods
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def show_about(self):
        """Shows custom About dialog."""
        dialog = AboutDialog(self.is_dark_mode, self)
        dialog.exec()
    
    # Drag and Drop Events
    def dragEnterEvent(self, event):
        """Accept drag enter event if it contains point cloud files."""
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.pcd', '.ply')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        """Handle dropped files by loading the first valid point cloud file."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.pcd', '.ply')):
                logger.info(f"File dropped: {file_path}")
                self._load_specific_file(file_path)
                break
        event.acceptProposedAction()

    # Recent Files Menu management
    def _add_to_recent_files(self, file_path: str):
        """Add a file path to the recent files list and persist it."""
        if not file_path:
            return
            
        try:
            resolved_path = str(Path(file_path).resolve())
        except Exception:
            resolved_path = str(file_path)
            
        recent_files = self.settings.value("recentFiles", [])
        if not isinstance(recent_files, list):
            recent_files = []
            
        # Remove if already exists to move to top
        if resolved_path in recent_files:
            recent_files.remove(resolved_path)
            
        # Insert at the beginning
        recent_files.insert(0, resolved_path)
        
        # Limit count
        recent_files = recent_files[:MAX_RECENT_FILES]
        
        self.settings.setValue("recentFiles", recent_files)

    def update_recent_files_menu(self):
        """Rebuild the recent files menu dynamically."""
        if not hasattr(self, 'recent_menu') or self.recent_menu is None:
            return
            
        self.recent_menu.clear()
        
        recent_files = self.settings.value("recentFiles", [])
        if not isinstance(recent_files, list):
            recent_files = []
            
        # Filter out files that no longer exist
        valid_recent = []
        for f in recent_files:
            try:
                if Path(f).exists():
                    valid_recent.append(str(Path(f).resolve()))
            except Exception:
                pass
                
        if len(valid_recent) != len(recent_files):
            self.settings.setValue("recentFiles", valid_recent)
            recent_files = valid_recent
            
        if not recent_files:
            no_recent_action = self.recent_menu.addAction("No Recent Files")
            no_recent_action.setEnabled(False)
            return
            
        # Add actions for each file path
        for path in recent_files:
            action_text = Path(path).name
            action = self.recent_menu.addAction(action_text)
            action.setToolTip(path)
            action.setStatusTip(f"Open recent file: {path}")
            # Bind the click to _load_specific_file
            action.triggered.connect(lambda checked=False, p=path: self._load_specific_file(p))
            
    def closeEvent(self, event):
        """Handle application closing with proper cleanup."""
        logger.info("Application closing event triggered.")
        try:
            # Clean up PyVista widget
            if hasattr(self, 'pyvista_widget') and self.pyvista_widget.plotter:
                self.pyvista_widget.cleanup()
                    
            # Clean up thread if running
            if self.processor_thread and self.processor_thread.isRunning():
                logger.info("Interrupting background thread during shutdown.")
                self.processor_thread.requestInterruption()
                self.processor_thread.wait(1000)
                
        except Exception as e:
            logger.warning(f"Warning during application cleanup: {e}")
            
        event.accept()
