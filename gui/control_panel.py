"""
Control Panel component for PCD Visualizer
Handles file loading, visualization settings, and camera controls.
"""

import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QLabel, QSlider, 
                            QComboBox, QPushButton, QCheckBox, QGridLayout, 
                            QScrollArea, QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from point_cloud_processor import PointCloudProcessor


class ControlPanel(QWidget):
    """Control panel widget for visualization settings and file operations."""
    
    point_cloud_loaded = pyqtSignal(object)  # Point cloud object
    visualization_changed = pyqtSignal(dict)  # Settings dictionary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.processor_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the control panel UI."""
        # Create scroll area for control panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        panel = QWidget()
        layout = QVBoxLayout()
        
        # File info section
        layout.addWidget(self.create_file_group())
        
        # Visualization settings
        layout.addWidget(self.create_visualization_group())
        
        # Camera controls
        layout.addWidget(self.create_camera_group())
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        panel.setLayout(layout)
        scroll_area.setWidget(panel)
        
        # Set main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        
    def create_file_group(self):
        """Create the file information group."""
        file_group = QGroupBox("File Information")
        layout = QVBoxLayout()
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Load button
        load_btn = QPushButton("Load Point Cloud File")
        load_btn.clicked.connect(self.load_file)
        load_btn.setMinimumHeight(35)
        layout.addWidget(load_btn)
        
        file_group.setLayout(layout)
        return file_group
        
    def create_visualization_group(self):
        """Create the visualization settings group."""
        viz_group = QGroupBox("Visualization Settings")
        layout = QGridLayout()
        
        # Point size
        layout.addWidget(QLabel("Point Size:"), 0, 0)
        self.point_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_size_slider.setRange(1, 20)
        self.point_size_slider.setValue(5)
        self.point_size_slider.valueChanged.connect(self.on_settings_changed)
        layout.addWidget(self.point_size_slider, 0, 1)
        
        self.point_size_label = QLabel("5")
        self.point_size_label.setMinimumWidth(25)
        layout.addWidget(self.point_size_label, 0, 2)
        
        # Color mode
        layout.addWidget(QLabel("Color Mode:"), 1, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Original", "Height", "Elevation", "Distance", "Normal", "Curvature"])
        self.color_mode_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.color_mode_combo, 1, 1, 1, 2)
        
        # Background
        layout.addWidget(QLabel("Background:"), 2, 0)
        self.background_combo = QComboBox()
        self.background_combo.addItems([
            "Gradient", "White", "Black", "Gray", 
            "Dark Gradient", "Sunset Gradient"
        ])
        self.background_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.background_combo, 2, 1, 1, 2)
        
        # Show normals checkbox
        self.normals_checkbox = QCheckBox("Show Normal Vectors")
        self.normals_checkbox.toggled.connect(self.on_settings_changed)
        layout.addWidget(self.normals_checkbox, 3, 0, 1, 3)
        
        viz_group.setLayout(layout)
        return viz_group
        
    def create_camera_group(self):
        """Create the camera controls group."""
        camera_group = QGroupBox("Camera Controls")
        layout = QGridLayout()
        
        # Reset view button
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.reset_view)
        reset_btn.setMinimumHeight(30)
        layout.addWidget(reset_btn, 0, 0, 1, 2)
        
        # View buttons
        view_buttons = [
            ("Top View", self.set_top_view),
            ("Front View", self.set_front_view),
            ("Side View", self.set_side_view),
            ("Isometric", self.set_iso_view)
        ]
        
        for i, (text, callback) in enumerate(view_buttons):
            row = 1 + i // 2
            col = i % 2
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            layout.addWidget(btn, row, col)
        
        camera_group.setLayout(layout)
        return camera_group
        
    def load_file(self):
        """Load point cloud file with error handling."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Point Cloud File", "", 
            "Point Cloud Data (*.pcd *.ply);;PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
        )
        
        if file_path:
            self.load_specific_file(file_path)
            
    def load_specific_file(self, file_path):
        """Load a specific file path."""
        if os.path.exists(file_path):
            self.file_label.setText(f"Loading: {os.path.basename(file_path)}")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            if self.parent_window:
                self.parent_window.statusbar_manager.set_message("Loading point cloud...")
                self.parent_window.setEnabled(False)
            
            # Start processing thread
            self.processor_thread = PointCloudProcessor(file_path)
            self.processor_thread.progress.connect(self.progress_bar.setValue)
            self.processor_thread.error.connect(self.show_error)
            self.processor_thread.loaded.connect(self.on_point_cloud_loaded)
            self.processor_thread.finished.connect(self.on_processing_finished)
            self.processor_thread.start()
            
    def on_point_cloud_loaded(self, point_cloud):
        """Handle successful point cloud loading."""
        point_count = len(point_cloud.points)
        self.file_label.setText(f"Loaded: {point_count:,} points")
        
        # Enable controls
        self.enable_controls(True)
        
        # Emit signal to main window
        self.point_cloud_loaded.emit(point_cloud)
        
    def on_processing_finished(self):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        if self.parent_window:
            self.parent_window.setEnabled(True)
            
    def show_error(self, message):
        """Show error message."""
        QMessageBox.critical(self, "Error", message)
        if self.parent_window:
            self.parent_window.statusbar_manager.set_message("Error occurred - Ready")
            
    def enable_controls(self, enabled):
        """Enable/disable controls that require a loaded point cloud."""
        self.point_size_slider.setEnabled(enabled)
        self.color_mode_combo.setEnabled(enabled)
        self.normals_checkbox.setEnabled(enabled)
        
    def on_settings_changed(self):
        """Handle visualization settings changes."""
        # Update point size label
        size = self.point_size_slider.value()
        self.point_size_label.setText(str(size))
        
        # Create settings dictionary
        settings = {
            'point_size': size,
            'color_mode': self.color_mode_combo.currentText(),
            'background': self.background_combo.currentText(),
            'show_normals': self.normals_checkbox.isChecked()
        }
        
        # Emit signal
        self.visualization_changed.emit(settings)
        
    def reset_view(self):
        """Reset camera view."""
        if self.parent_window and hasattr(self.parent_window, 'visualization_panel'):
            self.parent_window.visualization_panel.reset_view()
            
    def set_top_view(self):
        """Set top view."""
        if self.parent_window and hasattr(self.parent_window, 'visualization_panel'):
            self.parent_window.visualization_panel.set_view("top")
            
    def set_front_view(self):
        """Set front view."""
        if self.parent_window and hasattr(self.parent_window, 'visualization_panel'):
            self.parent_window.visualization_panel.set_view("front")
            
    def set_side_view(self):
        """Set side view."""
        if self.parent_window and hasattr(self.parent_window, 'visualization_panel'):
            self.parent_window.visualization_panel.set_view("side")
            
    def set_iso_view(self):
        """Set isometric view."""
        if self.parent_window and hasattr(self.parent_window, 'visualization_panel'):
            self.parent_window.visualization_panel.set_view("iso")
