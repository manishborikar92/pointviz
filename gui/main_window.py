"""
Main Window class for PCD Visualizer
Orchestrates all GUI components and manages application state.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QSplitter, 
                            QApplication, QMessageBox)
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QPalette

import open3d as o3d
from control_panel import ControlPanel
from visualization_panel import VisualizationPanel
from menus import MenuManager
from statusbar import StatusBarManager
from theme_manager import ThemeManager
from point_cloud_processor import PointCloudProcessor


class PCDVisualizer(QMainWindow):
    """Main application window for PCD Visualizer."""
    
    def __init__(self):
        super().__init__()
        self.point_cloud = None
        self.original_point_cloud = None
        self.processor_thread = None
        self.settings = QSettings('PCDVisualizer', 'Settings')
        
        # Initialize managers
        self.theme_manager = ThemeManager()
        self.menu_manager = MenuManager(self)
        self.statusbar_manager = StatusBarManager(self)
        
        self.init_ui()
        self.theme_manager.apply_theme(self, self.get_system_theme_preference())
        
    def get_system_theme_preference(self):
        """Detect system theme preference."""
        try:
            palette = QApplication.instance().palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            return bg_color.lightness() < 128
        except:
            return False
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("PCD Point Cloud Visualizer")
        self.resize(1000, 700)
        
        # Center the window on the screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_geometry.center())
        self.move(frame_geometry.topLeft())
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main horizontal splitter
        main_splitter = QSplitter()
        
        # Setup panels
        self.control_panel = ControlPanel(self)
        self.visualization_panel = VisualizationPanel(self)
        
        # Connect signals
        self.control_panel.point_cloud_loaded.connect(self.on_point_cloud_loaded)
        self.control_panel.visualization_changed.connect(self.update_visualization)
        
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
        self.menu_manager.setup_menus()
        self.statusbar_manager.setup_statusbar()
        
    def load_file(self):
        """Load point cloud file."""
        self.control_panel.load_file()
        
    def on_point_cloud_loaded(self, point_cloud):
        """Handle successful point cloud loading."""
        self.point_cloud = point_cloud
        self.original_point_cloud = o3d.geometry.PointCloud(point_cloud)
        
        # Update visualization
        self.visualization_panel.set_point_cloud(point_cloud)
        
        # Update status
        point_count = len(point_cloud.points)
        self.statusbar_manager.set_message(f"Loaded {point_count:,} points successfully")
        
    def update_visualization(self, settings):
        """Update visualization with new settings."""
        if self.point_cloud:
            self.visualization_panel.update_visualization(settings)
            
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.theme_manager.toggle_theme(self)
        
    def take_screenshot(self):
        """Take a screenshot of the current view."""
        self.visualization_panel.take_screenshot()
        
    def export_file(self):
        """Export point cloud to file."""
        if not self.point_cloud:
            QMessageBox.warning(self, "Warning", "No point cloud loaded")
            return
            
        from PyQt6.QtWidgets import QFileDialog
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
                
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About PCD Visualizer",
                         "PCD Point Cloud Visualizer\n\n"
                         "A powerful tool for visualizing point cloud data\n"
                         "Built with PyQt6, Open3D, and PyVista\n\n"
                         "Key Features:\n"
                         "• LVX to PCD conversion capabilities\n"
                         "• Point size control with smooth updates\n"
                         "• Multiple color modes and gradient backgrounds\n"
                         "• Dark/Light mode with system theme detection\n"
                         "• Improved statistics display with sectioned layout\n"
                         "• Professional camera controls and view presets\n"
                         "• Export capabilities for screenshots and data\n"
                         "• Optimized performance for large datasets\n\n"
                         "Version: Edition 2.0 - PyQt6 Modular")
                         
    def closeEvent(self, event):
        """Handle application closing with proper cleanup."""
        try:
            # Clean up visualization
            if hasattr(self, 'visualization_panel'):
                self.visualization_panel.cleanup()
                
            # Clean up thread if running
            if self.processor_thread and self.processor_thread.isRunning():
                self.processor_thread.quit()
                self.processor_thread.wait(1000)
                
        except Exception as e:
            print(f"Warning during application cleanup: {e}")
            
        event.accept()
