"""
LVX to PCD Conversion functionality
Handles LVX file parsing and conversion to PCD format.
"""

import os
import struct
import numpy as np
from typing import Optional
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
                            QLineEdit, QPushButton, QRadioButton, QButtonGroup, 
                            QCheckBox, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import open3d as o3d


class LVXConverterCore:
    """Core LVX conversion functionality."""

    def __init__(self):
        self.coord_limits = {
            'X': 600,  # meters
            'Y': 5,    # meters  
            'Z': 7     # meters 
        }

    def direct_parser(self, lvx_file_path: str) -> np.ndarray:
        """Direct binary parsing of an LVX file."""
        with open(lvx_file_path, 'rb') as rf:
            data = rf.read()

        file_size = len(data)
        
        # Parse public header
        idx = 28  # Start of device_count
        device_count = data[idx]
        idx += 1

        # Skip device info blocks (59 bytes each)
        idx = idx + 59 * device_count

        point_list = []
        frame_count = 0

        # Start reading frames
        while idx < file_size:
            # Read frame header (24 bytes)
            if idx + 24 > file_size:
                break

            current_offset = int.from_bytes(data[idx:idx+8], 'little')
            next_offset = int.from_bytes(data[idx+8:idx+16], 'little')
            frame_index = int.from_bytes(data[idx+16:idx+24], 'little')
            
            frame_count += 1
            
            if next_offset <= current_offset or next_offset > file_size:
                break

            idx += 24  # Move past frame header

            # Process all packets within this frame
            while idx < next_offset:
                # Eth packet header is 19 bytes
                if idx + 19 > file_size:
                    break
                
                dtype = data[idx + 10]  # data_type at offset 10
                idx += 19  # Move past packet header

                # Point cloud data type 0
                if dtype == 0:
                    points_per_packet = 100
                    point_size = 13
                    if idx + points_per_packet * point_size > next_offset: 
                        break
                    for _ in range(points_per_packet):
                        x, y, z, r = struct.unpack('<iiib', data[idx:idx+point_size])
                        if not (x == 0 and y == 0 and z == 0):
                            point_list.append([x/1000.0, y/1000.0, z/1000.0, r])
                        idx += point_size
                # Point cloud data type 1
                elif dtype == 1:
                    points_per_packet = 100
                    point_size = 8
                    if idx + points_per_packet * point_size > next_offset: 
                        break
                    for _ in range(points_per_packet):
                        depth, theta, phi = struct.unpack('<iHH', data[idx:idx+point_size])
                        if depth > 0:
                            theta_rad, phi_rad, depth_m = theta/10000.0, phi/10000.0, depth/1000.0
                            x = depth_m * np.sin(theta_rad) * np.cos(phi_rad)
                            y = depth_m * np.sin(theta_rad) * np.sin(phi_rad)
                            z = depth_m * np.cos(theta_rad)
                            point_list.append([x, y, z, 0])
                        idx += point_size
                # Point cloud data type 2
                elif dtype == 2:
                    points_per_packet = 96
                    point_size = 14
                    if idx + points_per_packet * point_size > next_offset: 
                        break
                    for _ in range(points_per_packet):
                        x, y, z, r, tag = struct.unpack('<iiibB', data[idx:idx+point_size])
                        if not (x == 0 and y == 0 and z == 0):
                            point_list.append([x/1000.0, y/1000.0, z/1000.0, r])
                        idx += point_size
                # Point cloud data type 3
                elif dtype == 3:
                    points_per_packet = 96
                    point_size = 9
                    if idx + points_per_packet * point_size > next_offset: 
                        break
                    for _ in range(points_per_packet):
                        depth, theta, phi, r = struct.unpack('<iHHB', data[idx:idx+point_size])
                        if depth > 0:
                            theta_rad, phi_rad, depth_m = theta/10000.0, phi/10000.0, depth/1000.0
                            x = depth_m * np.sin(theta_rad) * np.cos(phi_rad)
                            y = depth_m * np.sin(theta_rad) * np.sin(phi_rad)
                            z = depth_m * np.cos(theta_rad)
                            point_list.append([x, y, z, r])
                        idx += point_size
                # IMU data
                elif dtype == 6:
                    if idx + 24 <= next_offset: 
                        idx += 24
                # Unknown data type - skip to next frame
                else:
                    idx = next_offset
            idx = next_offset

        return np.array(point_list) if point_list else np.empty((0, 4))

    def convert_to_pcd(self, points: np.ndarray, output_path: str, 
                       include_reflectivity: bool = True, 
                       ascii_format: bool = False) -> bool:
        """Convert point cloud data to PCD format using Open3D."""
        if len(points) == 0:
            return False
            
        try:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points[:, :3])
            
            if include_reflectivity and points.shape[1] >= 4:
                reflectivity = points[:, 3] / 255.0
                colors = np.column_stack([reflectivity, reflectivity, reflectivity])
                pcd.colors = o3d.utility.Vector3dVector(colors)
            
            success = o3d.io.write_point_cloud(
                output_path, 
                pcd, 
                write_ascii=ascii_format,
                compressed=not ascii_format
            )
            
            return success
            
        except Exception as e:
            print(f"Error converting to PCD: {e}")
            return False


class LVXConversionThread(QThread):
    """Thread for LVX to PCD conversion operations."""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    success = pyqtSignal(str, int)  # output_path, point_count
    status_update = pyqtSignal(str)
    
    def __init__(self, input_path, output_path, include_reflectivity=True, ascii_format=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.include_reflectivity = include_reflectivity
        self.ascii_format = ascii_format
        self.converter = LVXConverterCore()
        
    def run(self):
        try:
            self.progress.emit(10)
            self.status_update.emit("Reading LVX file...")
            
            # Parse LVX file
            points = self.converter.direct_parser(self.input_path)
            
            self.progress.emit(60)
            
            if len(points) == 0:
                self.error.emit("No valid points found in LVX file.")
                return
                
            self.status_update.emit(f"Parsed {len(points):,} points. Converting to PCD...")
            self.progress.emit(80)
            
            # Convert to PCD
            success = self.converter.convert_to_pcd(
                points, 
                self.output_path, 
                self.include_reflectivity, 
                self.ascii_format
            )
            
            self.progress.emit(100)
            
            if success:
                self.success.emit(self.output_path, len(points))
            else:
                self.error.emit("Failed to save PCD file.")
                
        except Exception as e:
            self.error.emit(f"Conversion failed: {str(e)}")
        finally:
            self.finished.emit()


class LVXConversionDialog(QDialog):
    """Dialog window for LVX to PCD conversion."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conversion_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the conversion dialog UI."""
        self.setWindowTitle("Convert LVX to PCD")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("LVX to PCD Converter")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Input/Output sections
        layout.addWidget(self.create_input_group())
        layout.addWidget(self.create_output_group())
        layout.addWidget(self.create_options_group())
        layout.addWidget(self.create_progress_group())
        
        # Buttons
        layout.addLayout(self.create_button_layout())
        
        self.setLayout(layout)
        
    def create_input_group(self):
        """Create input file selection group."""
        input_group = QGroupBox("Input LVX File")
        layout = QVBoxLayout()
        
        file_layout = QHBoxLayout()
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("Select an LVX file...")
        self.input_path_edit.setReadOnly(True)
        self.input_path_edit.textChanged.connect(self.validate_inputs)
        file_layout.addWidget(self.input_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_input_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        input_group.setLayout(layout)
        return input_group
        
    def create_output_group(self):
        """Create output destination group."""
        output_group = QGroupBox("Output Destination")
        layout = QVBoxLayout()
        
        # Output directory
        dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        self.output_dir_edit.setReadOnly(True)
        self.output_dir_edit.textChanged.connect(self.validate_inputs)
        dir_layout.addWidget(self.output_dir_edit)
        
        dir_btn = QPushButton("Browse...")
        dir_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(dir_btn)
        
        layout.addLayout(dir_layout)
        
        # Filename
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel("Filename:"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setPlaceholderText("output.pcd")
        self.filename_edit.textChanged.connect(self.validate_inputs)
        filename_layout.addWidget(self.filename_edit)
        
        layout.addLayout(filename_layout)
        output_group.setLayout(layout)
        return output_group
        
    def create_options_group(self):
        """Create conversion options group."""
        options_group = QGroupBox("Conversion Options")
        layout = QVBoxLayout()
        
        # Format options
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.format_group = QButtonGroup()
        self.binary_radio = QRadioButton("Binary (Compressed)")
        self.ascii_radio = QRadioButton("ASCII")
        self.binary_radio.setChecked(True)
        
        self.format_group.addButton(self.binary_radio)
        self.format_group.addButton(self.ascii_radio)
        
        format_layout.addWidget(self.binary_radio)
        format_layout.addWidget(self.ascii_radio)
        format_layout.addStretch()
        
        layout.addLayout(format_layout)
        
        # Reflectivity option
        self.reflectivity_checkbox = QCheckBox("Include Reflectivity Data")
        self.reflectivity_checkbox.setChecked(True)
        layout.addWidget(self.reflectivity_checkbox)
        
        options_group.setLayout(layout)
        return options_group
        
    def create_progress_group(self):
        """Create progress display group."""
        progress_group = QGroupBox("Conversion Progress")
        layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to convert")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        progress_group.setLayout(layout)
        return progress_group
        
    def create_button_layout(self):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)

        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setMinimumHeight(35)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)
        button_layout.addWidget(self.convert_btn)
        
        return button_layout
        
    def browse_input_file(self):
        """Browse for input LVX file."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select LVX File", "", 
            "LVX Files (*.lvx);;All Files (*)"
        )
        
        if file_path:
            self.input_path_edit.setText(file_path)
            # Auto-generate output filename
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.filename_edit.setText(f"{base_name}.pcd")
        
    def browse_output_dir(self):
        """Browse for output directory."""
        from PyQt6.QtWidgets import QFileDialog
        
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory"
        )
        
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def validate_inputs(self):
        """Validate inputs and enable/disable convert button."""
        input_valid = bool(self.input_path_edit.text().strip())
        output_dir_valid = bool(self.output_dir_edit.text().strip())
        filename_valid = bool(self.filename_edit.text().strip())
        
        self.convert_btn.setEnabled(input_valid and output_dir_valid and filename_valid)
    
    def start_conversion(self):
        """Start the conversion process."""
        input_path = self.input_path_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()
        filename = self.filename_edit.text().strip()
        
        if not filename.lower().endswith('.pcd'):
            filename += '.pcd'
            
        output_path = os.path.join(output_dir, filename)
        
        # Check if file exists
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self, "File Exists", 
                f"The file '{filename}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Start conversion
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setText("Stop")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        include_reflectivity = self.reflectivity_checkbox.isChecked()
        ascii_format = self.ascii_radio.isChecked()
        
        self.conversion_thread = LVXConversionThread(
            input_path, output_path, include_reflectivity, ascii_format
        )
        
        # Connect signals
        self.conversion_thread.progress.connect(self.progress_bar.setValue)
        self.conversion_thread.status_update.connect(self.status_label.setText)
        self.conversion_thread.success.connect(self.on_conversion_success)
        self.conversion_thread.error.connect(self.on_conversion_error)
        self.conversion_thread.finished.connect(self.on_conversion_finished)
        
        self.conversion_thread.start()
    
    def on_conversion_success(self, output_path, point_count):
        """Handle successful conversion."""
        QMessageBox.information(
            self, "Conversion Complete",
            f"Successfully converted {point_count:,} points to PCD format.\n\n"
            f"Output file: {output_path}"
        )
        self.accept()
    
    def on_conversion_error(self, error_message):
        """Handle conversion error."""
        QMessageBox.critical(
            self, "Conversion Error", 
            f"Conversion failed:\n\n{error_message}"
        )
    
    def on_conversion_finished(self):
        """Handle conversion completion."""
        self.progress_bar.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setText("Cancel")
        self.status_label.setText("Ready to convert")
        self.validate_inputs()
    
    def closeEvent(self, event):
        """Handle dialog closing."""
        if self.conversion_thread and self.conversion_thread.isRunning():
            reply = QMessageBox.question(
                self, "Conversion in Progress",
                "Cancel the ongoing conversion?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.conversion_thread.terminate()
                self.conversion_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()