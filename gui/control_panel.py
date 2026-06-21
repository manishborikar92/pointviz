from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QGroupBox, QLabel,
                             QProgressBar, QPushButton, QSlider, QComboBox, QCheckBox, QGridLayout)
from PyQt6.QtCore import Qt

from config import BACKGROUND_STYLES, COLOR_MODES, DEFAULT_POINT_SIZE

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
        
        self.file_name_label = QLabel("No file loaded")
        self.file_name_label.setWordWrap(True)
        self.file_name_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(self.file_name_label)
        
        self.file_label = QLabel("")
        self.file_label.setWordWrap(True)
        self.file_label.setVisible(False)
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
        self.point_size_slider.valueChanged.connect(self._on_point_size_slider_changed)
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

    def _on_point_size_slider_changed(self, value: int):
        """Update point size label internally and notify main window."""
        self.point_size_label.setText(str(value))
        self.main_window._on_point_size_changed(value)

    # --- Public Panel API ---
    def set_loading_file(self, file_path: str):
        """Set the panel state to loading a file."""
        p = Path(file_path)
        self.file_name_label.setText(f"File: {p.name}")
        try:
            self.file_name_label.setToolTip(str(p.resolve()))
        except Exception:
            self.file_name_label.setToolTip(str(file_path))
        self.file_label.setText(f"Loading: {p.name}")
        self.file_label.setVisible(True)

    def update_file_info(self, file_path: Optional[str] = None, displayed_points: int = 0, original_points: int = 0):
        """Update file information labels and tooltip."""
        if file_path is None:
            self.file_name_label.setText("No file loaded")
            self.file_name_label.setToolTip("")
            self.file_label.setText("")
            self.file_label.setVisible(False)
        else:
            p = Path(file_path)
            self.file_name_label.setText(f"File: {p.name}")
            try:
                self.file_name_label.setToolTip(str(p.resolve()))
            except Exception:
                self.file_name_label.setToolTip(str(file_path))
                
            if displayed_points < original_points:
                self.file_label.setText(f"Loaded: {displayed_points:,} points\n"
                                        f"(Downsampled from {original_points:,})")
            else:
                self.file_label.setText(f"Loaded: {displayed_points:,} points")
            self.file_label.setVisible(True)

    def set_controls_enabled(self, enabled: bool):
        """Enable or disable visual settings controls."""
        self.point_size_slider.setEnabled(enabled)
        self.color_mode_combo.setEnabled(enabled)
        self.normals_checkbox.setEnabled(enabled)

    def set_progress_value(self, value: int):
        """Set the progress bar value."""
        self.progress_bar.setValue(value)

    def set_progress_visible(self, visible: bool):
        """Show or hide the progress bar."""
        self.progress_bar.setVisible(visible)

    def set_point_size_value(self, value: int):
        """Programmatically set the point size slider value."""
        self.point_size_slider.setValue(value)
        self.point_size_label.setText(str(value))

    def get_point_size(self) -> int:
        """Return current point size."""
        return self.point_size_slider.value()

    def get_color_mode(self) -> str:
        """Return currently selected color mode name."""
        return self.color_mode_combo.currentText()

    def get_background(self) -> str:
        """Return currently selected background style name."""
        return self.background_combo.currentText()

    def is_normals_checked(self) -> bool:
        """Return whether normals display is checked."""
        return self.normals_checkbox.isChecked()

    def set_normals_checked(self, checked: bool):
        """Set normals checkbox checked state."""
        self.normals_checkbox.setChecked(checked)
