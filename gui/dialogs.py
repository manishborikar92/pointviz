from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QButtonGroup, QRadioButton, 
                             QDoubleSpinBox)
from PyQt6.QtCore import Qt

from config import DEFAULT_VOXEL_SIZE

class LoadOptionsDialog(QDialog):
    """A dialog to get downsampling options from the user for large files."""
    def __init__(self, file_size_mb: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Large File Options")
        self.setMinimumWidth(350)

        layout = QVBoxLayout()
        
        info_label = QLabel(f"This file is large (~{file_size_mb:.2f} MB).\n"
                            "Loading all points may cause performance issues or crashes.\n"
                            "Please choose a loading method:")
        layout.addWidget(info_label)

        # Method selection
        self.button_group = QButtonGroup(self)
        self.voxel_radio = QRadioButton("Voxel Downsample (Recommended)")
        self.load_all_radio = QRadioButton("Load All Points (Not Recommended)")
        
        self.button_group.addButton(self.voxel_radio, 1)
        self.button_group.addButton(self.load_all_radio, 2)
        self.voxel_radio.setChecked(True)

        # Voxel options
        voxel_layout = QHBoxLayout()
        self.voxel_size_input = QDoubleSpinBox()
        self.voxel_size_input.setDecimals(3)
        self.voxel_size_input.setSingleStep(0.01)
        self.voxel_size_input.setRange(0.001, 100.0)
        self.voxel_size_input.setValue(DEFAULT_VOXEL_SIZE)
        voxel_layout.addWidget(QLabel("Voxel Size:"))
        voxel_layout.addWidget(self.voxel_size_input)
        voxel_widget = QWidget()
        voxel_widget.setLayout(voxel_layout)

        # Connect radio buttons to enable/disable options
        self.voxel_radio.toggled.connect(voxel_widget.setEnabled)
        self.load_all_radio.toggled.connect(lambda checked: voxel_widget.setEnabled(not checked))

        layout.addWidget(self.voxel_radio)
        layout.addWidget(voxel_widget)
        layout.addWidget(self.load_all_radio)

        # OK and Cancel buttons
        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        self.setLayout(layout)

    def get_options(self) -> Optional[dict]:
        """Return the selected options or None if canceled."""
        if self.exec() == QDialog.DialogCode.Accepted:
            method_id = self.button_group.checkedId()
            if method_id == 1:  # Voxel
                return {"method": "voxel", "value": self.voxel_size_input.value()}
            else:  # Load all
                return {"method": "none", "value": None}
        return None


class AboutDialog(QDialog):
    """Shows a custom, resizable 'About' dialog."""
    def __init__(self, is_dark_mode: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PCD Visualizer")
        self.setMinimumSize(420, 380)
        self.is_dark_mode = is_dark_mode
        self.init_ui()

    def init_ui(self):
        about_text = """
        <h3>PCD Point Cloud Visualizer</h3>
        <p>A powerful and responsive tool for visualizing 3D point cloud data files (e.g., .pcd, .ply).</p>
        <p>This visualizer is designed to handle large datasets efficiently, providing a smooth user experience for inspection and analysis.</p>
        
        <h4>Key Features:</h4>
        <ul>
            <li><b>Optimized for Large Datasets</b> with Voxel downsampling</li>
            <li>Point size control with smooth updates</li>
            <li>Multiple color modes and gradient backgrounds</li>
            <li>Dark/Light mode with system theme detection</li>
            <li>Detailed statistics display with sectioned layout</li>
            <li>Professional camera controls and view presets</li>
            <li>Export capabilities for screenshots and data</li>
        </ul>

        <!-- <p>Developed by: <b>Quantnueral Pvt. Ltd.</b></p> -->
        """

        layout = QVBoxLayout()
        
        # Add company logo with theme detection
        # logo_label = QLabel()
        
        # Choose logo based on theme
        # logo_filename = "logo_dark.png" if self.is_dark_mode else "logo_light.png"
        # from config import ASSETS_DIR
        # logo_path = ASSETS_DIR / logo_filename

        # from PyQt6.QtGui import QIcon
        # logo_label.setPixmap(QIcon(str(logo_path)).pixmap(140, 25))
        # logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(about_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
        # layout.addWidget(logo_label)
        
        # layout.addSpacing(5)
        # separator = QWidget()
        # separator.setFixedHeight(1)
        # separator_color = "#5a5a5a" if self.is_dark_mode else "#d0d0d0"
        # separator.setStyleSheet(f"background-color: {separator_color};")
        # layout.addWidget(separator)
        # layout.addSpacing(5)
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(ok_button)

        self.setLayout(layout)
