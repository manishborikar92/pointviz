from PyQt6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGridLayout, QGroupBox, QLabel, QProgressBar, 
                             QPushButton, QSlider, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt

from pointviz.config import BACKGROUND_STYLES, COLOR_MODES, DEFAULT_POINT_SIZE

class ControlPanel(QScrollArea):
    """Left control panel sidebar for visualizer settings and file information."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.init_ui()
        
    def init_ui(self):
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
        self.setWidget(panel)
        
    def _create_file_info_group(self) -> QGroupBox:
        """Create file information group."""
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
        load_btn.clicked.connect(self.main_window.load_file)
        load_btn.setMinimumHeight(35)
        file_layout.addWidget(load_btn)
        
        file_group.setLayout(file_layout)
        return file_group
        
    def _create_visualization_group(self) -> QGroupBox:
        """Create visualization settings group."""
        viz_group = QGroupBox("Visualization Settings")
        viz_layout = QGridLayout()
        
        # Point size with slider
        viz_layout.addWidget(QLabel("Point Size:"), 0, 0)
        self.point_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.point_size_slider.setRange(1, 20)
        self.point_size_slider.setValue(DEFAULT_POINT_SIZE)
        self.point_size_slider.valueChanged.connect(self.main_window._on_point_size_changed)
        viz_layout.addWidget(self.point_size_slider, 0, 1)
        
        self.point_size_label = QLabel(str(DEFAULT_POINT_SIZE))
        self.point_size_label.setMinimumWidth(25)
        viz_layout.addWidget(self.point_size_label, 0, 2)
        
        # Color mode
        viz_layout.addWidget(QLabel("Color Mode:"), 1, 0)
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(list(COLOR_MODES.keys()))
        self.color_mode_combo.currentTextChanged.connect(self.main_window._on_color_mode_changed)
        viz_layout.addWidget(self.color_mode_combo, 1, 1, 1, 2)
        
        # Background
        viz_layout.addWidget(QLabel("Background:"), 2, 0)
        self.background_combo = QComboBox()
        self.background_combo.addItems(list(BACKGROUND_STYLES.keys()))
        self.background_combo.currentTextChanged.connect(self.main_window._on_background_changed)
        viz_layout.addWidget(self.background_combo, 2, 1, 1, 2)
        
        # Show normals checkbox
        self.normals_checkbox = QCheckBox("Show Normal Vectors")
        self.normals_checkbox.toggled.connect(self.main_window._on_normals_toggled)
        viz_layout.addWidget(self.normals_checkbox, 3, 0, 1, 3)
        
        viz_group.setLayout(viz_layout)
        return viz_group
        
    def _create_camera_group(self) -> QGroupBox:
        """Create camera controls group."""
        camera_group = QGroupBox("Camera Controls")
        camera_layout = QGridLayout()
        
        # Create view buttons
        buttons = [
            ("Reset View", self.main_window.reset_view, 0, 0, 1, 2),
            ("Top View", self.main_window._set_top_view, 1, 0),
            ("Front View", self.main_window._set_front_view, 1, 1),
            ("Side View", self.main_window._set_side_view, 2, 0),
            ("Isometric", self.main_window._set_iso_view, 2, 1)
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
