from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QFrame, QGroupBox, QLabel,
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
        
        # Day 5: Tools (Clipping & Measurement)
        layout.addWidget(self._create_tools_group())
        
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

    def _create_tools_group(self) -> QGroupBox:
        """Create the Day 5 Tools group: clipping and measurement controls."""
        tools_group = QGroupBox("Tools")
        tools_layout = QGridLayout()

        # --- Clipping Section ---
        clipping_title = QLabel("<b>Working Set Clipping</b>")
        tools_layout.addWidget(clipping_title, 0, 0, 1, 2)

        self.clipping_checkbox = QCheckBox("Enable Clip Box")
        self.clipping_checkbox.toggled.connect(self.main_window._on_clipping_toggled)
        self.clipping_checkbox.setEnabled(False)
        tools_layout.addWidget(self.clipping_checkbox, 1, 0, 1, 2)

        self.reset_clip_btn = QPushButton("Reset Clip Box")
        self.reset_clip_btn.clicked.connect(self.main_window._on_reset_action)
        self.reset_clip_btn.setEnabled(False)
        tools_layout.addWidget(self.reset_clip_btn, 2, 0, 1, 2)

        self.crop_btn = QPushButton("Crop Workspace")
        self.crop_btn.clicked.connect(self.main_window._on_crop_clicked)
        self.crop_btn.setEnabled(False)
        tools_layout.addWidget(self.crop_btn, 3, 0, 1, 2)

        self.clipping_info_label = QLabel("")
        self.clipping_info_label.setObjectName("clipping_info_label")
        self.clipping_info_label.setWordWrap(True)
        self.clipping_info_label.setVisible(False)
        tools_layout.addWidget(self.clipping_info_label, 4, 0, 1, 2)

        # --- Divider ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("margin: 6px 0;")
        tools_layout.addWidget(separator, 5, 0, 1, 2)

        # --- Measurement Section ---
        measurement_title = QLabel("<b>Point-to-Point Measurement</b>")
        tools_layout.addWidget(measurement_title, 6, 0, 1, 2)

        self.measure_btn = QPushButton("Measure Distance")
        self.measure_btn.setCheckable(True)
        self.measure_btn.toggled.connect(self.main_window._on_measure_toggled)
        self.measure_btn.setEnabled(False)
        tools_layout.addWidget(self.measure_btn, 7, 0, 1, 2)

        self.clear_measurements_btn = QPushButton("Clear Measurements")
        self.clear_measurements_btn.clicked.connect(self.main_window._on_clear_measurements)
        self.clear_measurements_btn.setEnabled(False)
        tools_layout.addWidget(self.clear_measurements_btn, 8, 0, 1, 2)

        tools_group.setLayout(tools_layout)
        return tools_group

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

    # --- Day 5: Tools API ---

    def set_tools_enabled(self, enabled: bool):
        """Enable or disable tools controls (requires loaded point cloud)."""
        self.clipping_checkbox.setEnabled(enabled)
        self.measure_btn.setEnabled(enabled)
        if not enabled:
            self.set_clipping_checked(False)
            self.set_measure_checked(False)
            self.reset_clip_btn.setText("Reset Clip Box")
            self.reset_clip_btn.setEnabled(False)
            self.crop_btn.setEnabled(False)
            self.clear_measurements_btn.setEnabled(False)
            self.update_clipping_info("")
        else:
            self.update_reset_button_state()

    def update_clipping_info(self, summary: str):
        """Update the clipping info label text."""
        self.clipping_info_label.setText(summary)
        self.clipping_info_label.setVisible(bool(summary))
        self.update_reset_button_state()

    def update_reset_button_state(self):
        """Update the context-sensitive Reset button based on crop and clipping states."""
        is_cropped = False
        if (hasattr(self.main_window, 'working_point_cloud') and 
            self.main_window.working_point_cloud is not None and 
            hasattr(self.main_window, 'original_point_cloud') and 
            self.main_window.original_point_cloud is not None):
            is_cropped = len(self.main_window.working_point_cloud.points) < len(self.main_window.original_point_cloud.points)
            
        is_clipping_active = (hasattr(self.main_window, 'pyvista_widget') and 
                              self.main_window.pyvista_widget is not None and 
                              self.main_window.pyvista_widget.clipping_state.is_active)
        
        if is_cropped:
            self.reset_clip_btn.setText("Reset Workspace")
            self.reset_clip_btn.setEnabled(True)
            self.crop_btn.setEnabled(False)  # Crop is disabled since clipping deactivates after crop
        else:
            self.reset_clip_btn.setText("Reset Clip Box")
            summary = self.main_window.pyvista_widget.clipping_state.summary if is_clipping_active else ""
            self.reset_clip_btn.setEnabled(is_clipping_active and bool(summary))
            self.crop_btn.setEnabled(is_clipping_active and bool(summary))

    def set_clear_measurements_enabled(self, enabled: bool):
        """Enable or disable the Clear All Measurements button."""
        self.clear_measurements_btn.setEnabled(enabled)

    def set_clipping_checked(self, checked: bool):
        """Programmatically set the clipping checkbox without emitting toggled."""
        self.clipping_checkbox.blockSignals(True)
        self.clipping_checkbox.setChecked(checked)
        self.clipping_checkbox.blockSignals(False)

    def set_measure_checked(self, checked: bool):
        """Programmatically set the measure button without emitting toggled."""
        self.measure_btn.blockSignals(True)
        self.measure_btn.setChecked(checked)
        self.measure_btn.blockSignals(False)
