"""
Visualization Panel component for PCD Visualizer
Handles 3D visualization and statistics display.
"""

import numpy as np
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QScrollArea, 
                            QGroupBox, QLabel, QFileDialog, QMessageBox)
from PyQt6.QtGui import QFont
from pyvista_widget import PyVistaWidget


class VisualizationPanel(QWidget):
    """Main visualization panel with 3D view and statistics tabs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.point_cloud = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the visualization panel UI."""
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 3D Visualization tab
        self.pyvista_widget = PyVistaWidget()
        self.tab_widget.addTab(self.pyvista_widget, "3D View")
        
        # Statistics tab
        self.stats_widget = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_widget, "Statistics")
        
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def create_stats_tab(self):
        """Create the statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Scroll area for statistics
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        stats_content = QWidget()
        stats_layout = QVBoxLayout()
        
        # Statistics sections
        self.create_stats_sections(stats_layout)
        
        stats_layout.addStretch()
        stats_content.setLayout(stats_layout)
        scroll_area.setWidget(stats_content)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
        
    def create_stats_sections(self, layout):
        """Create statistics display sections."""
        # Basic info section
        basic_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout()
        self.basic_stats_label = QLabel("No point cloud loaded")
        self.basic_stats_label.setFont(QFont("Courier", 9))
        basic_layout.addWidget(self.basic_stats_label)
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Geometric properties section
        geo_group = QGroupBox("Geometric Properties")
        geo_layout = QVBoxLayout()
        self.geo_stats_label = QLabel("No data available")
        self.geo_stats_label.setFont(QFont("Courier", 9))
        geo_layout.addWidget(self.geo_stats_label)
        geo_group.setLayout(geo_layout)
        layout.addWidget(geo_group)
        
        # Features section
        features_group = QGroupBox("Features")
        features_layout = QVBoxLayout()
        self.features_stats_label = QLabel("No data available")
        self.features_stats_label.setFont(QFont("Courier", 9))
        features_layout.addWidget(self.features_stats_label)
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Additional stats section
        additional_group = QGroupBox("Additional Statistics")
        additional_layout = QVBoxLayout()
        self.additional_stats_label = QLabel("No data available")
        self.additional_stats_label.setFont(QFont("Courier", 9))
        additional_layout.addWidget(self.additional_stats_label)
        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)
        
    def set_point_cloud(self, point_cloud):
        """Set the point cloud for visualization."""
        self.point_cloud = point_cloud
        self.update_statistics()
        self.pyvista_widget.update_point_cloud(point_cloud, force_refresh=True)
        
    def update_visualization(self, settings):
        """Update visualization with new settings."""
        if not self.point_cloud:
            return
            
        # Update PyVista widget with settings
        self.pyvista_widget.update_point_size(settings.get('point_size', 5))
        self.pyvista_widget.update_color_mode(settings.get('color_mode', 'Original'))
        self.pyvista_widget.update_background(settings.get('background', 'Gradient'))
        self.pyvista_widget.toggle_normals_display(settings.get('show_normals', False))
        
    def update_statistics(self):
        """Update the statistics display."""
        if not self.point_cloud:
            self.clear_statistics()
            return
            
        points = np.asarray(self.point_cloud.points)
        point_count = len(points)
        
        # Update each statistics section
        self.update_basic_info(points, point_count)
        self.update_geometric_properties(points)
        self.update_features_info()
        self.update_additional_stats(points)
        
    def clear_statistics(self):
        """Clear all statistics displays."""
        no_data_text = "No point cloud loaded"
        self.basic_stats_label.setText(no_data_text)
        self.geo_stats_label.setText("No data available")
        self.features_stats_label.setText("No data available")
        self.additional_stats_label.setText("No data available")
        
    def update_basic_info(self, points, point_count):
        """Update basic information section."""
        basic_info = f"""Points: {point_count:,}
Dimensions: {points.shape}
Memory: {points.nbytes / 1024 / 1024:.2f} MB"""
        self.basic_stats_label.setText(basic_info)
        
    def update_geometric_properties(self, points):
        """Update geometric properties section."""
        centroid = points.mean(axis=0)
        volume = self.calculate_volume(points)
        density = self.calculate_density(points, volume)
        
        geo_info = f"""Centroid: ({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})
Bounding Box Volume: {volume:.6f} units³
Point Density: {density:.2f} points/unit³

Coordinate Ranges:
X: {points[:, 0].min():.3f} to {points[:, 0].max():.3f}
Y: {points[:, 1].min():.3f} to {points[:, 1].max():.3f}
Z: {points[:, 2].min():.3f} to {points[:, 2].max():.3f}"""
        self.geo_stats_label.setText(geo_info)
        
    def update_features_info(self):
        """Update features information section."""
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
        
    def update_additional_stats(self, points):
        """Update additional statistics section."""
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
        
    def calculate_volume(self, points):
        """Calculate bounding box volume."""
        if len(points) == 0:
            return 0.0
        ranges = points.max(axis=0) - points.min(axis=0)
        return ranges[0] * ranges[1] * ranges[2]
        
    def calculate_density(self, points, volume):
        """Calculate point density."""
        if volume == 0:
            return 0.0
        return len(points) / volume
        
    def reset_view(self):
        """Reset camera view."""
        self.pyvista_widget.reset_camera()
        
    def set_view(self, view_type):
        """Set specific camera view."""
        self.pyvista_widget.set_view(view_type)
        
    def take_screenshot(self):
        """Take a screenshot with file dialog."""
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
                
    def cleanup(self):
        """Clean up visualization resources."""
        if hasattr(self, 'pyvista_widget'):
            self.pyvista_widget.cleanup()
