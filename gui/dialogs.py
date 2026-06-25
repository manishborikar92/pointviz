from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QWidget, QButtonGroup, QRadioButton, 
                             QDoubleSpinBox, QTabWidget, QTextBrowser, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from config import ASSETS_DIR, DEFAULT_VOXEL_SIZE, APP_NAME, APP_VERSION, ORGANIZATION_NAME

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
        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumSize(420, 380)
        self.is_dark_mode = is_dark_mode
        self.init_ui()

    def init_ui(self):
        about_text = f"""
        <h3>{APP_NAME}</h3>
        <p><b>Version: {APP_VERSION}</b></p>
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

        <p>Developed by: <b>{ORGANIZATION_NAME}</b></p>
        """

        layout = QVBoxLayout()
        
        # Add company logo with theme detection
        logo_label = QLabel()
        
        # Choose logo based on theme
        logo_filename = "logo_dark.png" if self.is_dark_mode else "logo_light.png"
        logo_path = ASSETS_DIR / logo_filename

        logo_label.setPixmap(QIcon(str(logo_path)).pixmap(140, 25))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        label = QLabel(about_text)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        
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

        self.setLayout(layout)


class HowToUseDialog(QDialog):
    """A comprehensive interactive guide dialog documenting all implemented features in pointviz."""
    def __init__(self, is_dark_mode: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"How to Use - {APP_NAME}")
        self.setMinimumSize(780, 560)
        self.resize(800, 600)
        self.is_dark_mode = is_dark_mode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_filename = "logo_dark.png" if self.is_dark_mode else "logo_light.png"
        logo_path = ASSETS_DIR / logo_filename
        if logo_path.exists():
            logo_label.setPixmap(QIcon(str(logo_path)).pixmap(140, 25))
        
        title_label = QLabel(f"<h2>{APP_NAME} - User Guide</h2>")
        title_label.setTextFormat(Qt.TextFormat.RichText)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(logo_label)
        layout.addLayout(header_layout)
        
        # Separator line
        separator = QWidget()
        separator.setFixedHeight(1)
        separator_color = "#5a5a5a" if self.is_dark_mode else "#d0d0d0"
        separator.setStyleSheet(f"background-color: {separator_color};")
        layout.addWidget(separator)
        layout.addSpacing(5)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setExpanding(True)
        self.tab_widget.setUsesScrollButtons(False)
        
        # Define tabs content
        tabs_data = [
            ("Getting Started", self._get_getting_started_html()),
            ("Navigation && Views", self._get_navigation_html()),
            ("Visualization Settings", self._get_visualization_html()),
            ("Clipping && Cropping", self._get_clipping_html()),
            ("Measurements Settings", self._get_measurements_html())
        ]
        
        for title, html_content in tabs_data:
            # Text browser for each tab to wrap text perfectly and prevent horizontal scrolling
            text_browser = QTextBrowser()
            text_browser.setHtml(html_content)
            text_browser.setOpenExternalLinks(True)
            text_browser.setFrameShape(QFrame.Shape.NoFrame)
            text_browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            text_browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            text_browser.setStyleSheet("QTextBrowser { background-color: transparent; border: none; padding: 10px; }")
            self.tab_widget.addTab(text_browser, title)
            
        layout.addWidget(self.tab_widget)
        
        self.setLayout(layout)

    def _get_getting_started_html(self) -> str:
        return f"""
        <h2>Getting Started & File Management</h2>
        <p>Welcome to the <b>{APP_NAME}</b> user guide. This application is a high-performance interactive tool designed for visualizing, analyzing, and processing 3D point cloud data files.</p>

        <h3>1. Supported File Formats</h3>
        <ul>
            <li><b>.pcd</b> (Point Cloud Data): Native format for Point Cloud Library (PCL).</li>
            <li><b>.ply</b> (Polygon File Format): Standard format for storing 3D scan data.</li>
        </ul>

        <h3>2. Loading Point Cloud Files</h3>
        <p>You can load point clouds into the visualizer in four different ways:</p>
        <ul>
            <li><b>Menu Bar:</b> Go to <b>File &gt; Open Point Cloud File</b> or press <b>Ctrl+O</b>.</li>
            <li><b>Sidebar:</b> Click the <b>Load Point Cloud File</b> button in the "File Information" panel.</li>
            <li><b>Drag and Drop:</b> Drag a valid <code>.pcd</code> or <code>.ply</code> file from your file manager and drop it anywhere onto the application window.</li>
            <li><b>Open Recent:</b> Go to <b>File &gt; Open Recent</b> to quickly open any of the last 10 successfully loaded files.</li>
        </ul>

        <h3>3. Optimizing Large Files (Downsampling)</h3>
        <p>When loading files larger than <b>100 MB</b>, the application automatically prompts you with optimization options to prevent performance lag or out-of-memory crashes:</p>
        <ul>
            <li><b>Voxel Downsample (Recommended):</b> Groups points into a 3D grid of voxels (default size is <code>0.05</code> units, fully adjustable) and averages coordinates in each grid cell. This preserves the overall geometry while reducing the point count for smooth rendering.</li>
            <li><b>Load All Points (Not Recommended):</b> Loads every single point without downsampling. Use only on high-end hardware for small-to-medium files.</li>
        </ul>

        <h3>4. Exporting & Screenshots</h3>
        <ul>
            <li><b>Export Point Cloud:</b> Go to <b>File &gt; Export Point Cloud...</b> or press <b>Ctrl+E</b> to save your current working point cloud (including any crops) to a new file. The export runs asynchronously in the background.</li>
            <li><b>Take Screenshot:</b> Go to <b>File &gt; Take Screenshot...</b> or press <b>Ctrl+S</b> to save the current 3D canvas rendering as a <code>.png</code> or <code>.jpg</code> image.</li>
        </ul>
        """

    def _get_navigation_html(self) -> str:
        return """
        <h2>Canvas Navigation & View Controls</h2>
        <p>Use your mouse and keyboard to interact with the 3D canvas and inspect your point cloud from any angle.</p>

        <h3>1. Mouse Navigation Controls</h3>
        <p>To navigate the 3D space, click and drag directly on the 3D canvas background:</p>
        <ul>
            <li><b>Rotate/Orbit:</b> Press and hold the <b>Left Mouse Button</b>, then drag in any direction to orbit the camera around the point cloud's center.</li>
            <li><b>Pan/Translate:</b> Press and hold the <b>Shift Key + Left Mouse Button</b>, or hold the <b>Middle Mouse Button (Scroll Wheel Click)</b>, and drag to slide the view horizontally or vertically.</li>
            <li><b>Zoom:</b> Scroll the <b>Mouse Wheel</b> forward to zoom in, and backward to zoom out. Alternatively, hold the <b>Right Mouse Button</b> and drag up or down.</li>
        </ul>

        <h3>2. Camera View Presets</h3>
        <p>Quickly snap the camera to standard orthogonal and perspective view angles using the sidebar buttons or keyboard shortcuts:</p>
        <ul>
            <li><b>Reset View (Shortcut: 0):</b> Resets the camera position, zoom, and target focus to fit the entire point cloud inside the screen boundaries.</li>
            <li><b>Top View (Shortcut: 1):</b> Aligns the camera to look straight down from the positive Z-axis.</li>
            <li><b>Front View (Shortcut: 2):</b> Aligns the camera to look along the Y-axis.</li>
            <li><b>Side View (Shortcut: 3):</b> Aligns the camera to look along the X-axis.</li>
            <li><b>Isometric View (Shortcut: 4):</b> Angles the camera in a standard 3D perspective.</li>
        </ul>

        <h3>3. Interface Adjustments</h3>
        <ul>
            <li><b>Fullscreen (Shortcut: F11):</b> Toggles the application between windowed and fullscreen modes.</li>
            <li><b>Toggle Theme (Shortcut: Ctrl+T):</b> Instantly switches the entire user interface between Light Mode and Dark Mode. The visualizer also detects your operating system's default preference on startup.</li>
        </ul>
        """

    def _get_visualization_html(self) -> str:
        return """
        <h2>Visualization Settings</h2>
        <p>Customize how your point cloud is rendered using the "Visualization Settings" panel on the left sidebar.</p>

        <h3>1. Point Size Control</h3>
        <ul>
            <li>Use the <b>Point Size slider</b> (range: 1 to 20) to change the size of the rendered points.</li>
            <li><b>Adaptive Size:</b> On file load, the application automatically calculates and suggests an optimal point size based on the point density and spatial dimensions to ensure the best visual density.</li>
        </ul>

        <h3>2. Background Styles</h3>
        <p>Choose from the <b>Background</b> dropdown to change the canvas background. Styles include:</p>
        <ul>
            <li><b>Gradient:</b> A soft blue-to-white gradient.</li>
            <li><b>Dark Gradient:</b> A modern deep slate-to-navy gradient (recommended for dark mode).</li>
            <li><b>Sunset Gradient:</b> A vibrant warm peach-to-pink gradient.</li>
            <li><b>Solid Colors:</b> Solid White, Black, or Gray backgrounds to maximize contrast.</li>
        </ul>

        <h3>3. Color Modes</h3>
        <p>The <b>Color Mode</b> dropdown applies different scalar coloring algorithms to analyze point attributes:</p>
        <ul>
            <li><b>Original:</b> Renders points using their original RGB colors from the file. Falls back to solid gray if colors are not present.</li>
            <li><b>Height:</b> Maps the vertical Z-coordinate to the <i>viridis</i> colormap (purple to yellow). Perfect for height distribution.</li>
            <li><b>Elevation:</b> Maps the vertical Z-coordinate to the <i>terrain</i> colormap (green, brown, white) for geographic topography.</li>
            <li><b>Distance:</b> Colors points by their Euclidean distance from the point cloud's center of mass using the <i>plasma</i> colormap.</li>
            <li><b>Normal:</b> Maps the absolute values of the point normals (X, Y, Z coordinates) to the R, G, B channels. If the file lacks normal vectors, the application estimates them on-demand.</li>
            <li><b>Curvature:</b> Analyzes local surface curvature using local neighborhood covariance matrices (KNN=30). Sharp features and edges are highlighted using the <i>coolwarm</i> (blue-white-red) colormap. Estimations are computed on-demand.</li>
        </ul>

        <h3>4. Show Normal Vectors</h3>
        <ul>
            <li>Check the <b>Show Normal Vectors</b> box to render small line segments pointing in the direction of each point's surface normal.</li>
            <li><b>Performance Guard:</b> For rendering smoothness, normal vector indicators are limited to the first 1,000 points.</li>
        </ul>
        """

    def _get_clipping_html(self) -> str:
        return """
        <h2>Working Set Clipping & Cropping</h2>
        <p>Extract and isolate specific regions of interest from your point cloud using the 3D Clipping Box widget.</p>

        <h3>1. How to Enable the Clipping Box</h3>
        <ul>
            <li>Check the <b>Enable Clip Box</b> box in the sidebar, or press <b>Ctrl+B</b> (or select <b>Tools &gt; Toggle Clipping Box</b>).</li>
            <li>A semi-transparent 3D bounding box will appear around the point cloud. Points outside this box are dynamically hidden.</li>
        </ul>

        <h3>2. Interacting with the 3D Widget</h3>
        <ul>
            <li><b>Resizing:</b> Left-click and drag any of the red, green, or blue handle boxes located at the center of the box faces.</li>
            <li><b>Moving/Translating:</b> Left-click and drag the center handle or any of the gray box faces to move the entire clipping box in 3D space.</li>
            <li><b>Rotating:</b> Check the <b>Enable Rotation</b> box in the sidebar to reveal circular rotation handles. Left-click and drag these handles to rotate the clipping box around its axes.</li>
        </ul>

        <h3>3. Cropping the Workspace</h3>
        <p>Once you have aligned the clipping box to your region of interest, you can make the crop permanent in memory:</p>
        <ul>
            <li>Click the <b>Crop Workspace</b> button in the sidebar.</li>
            <li>The points outside the clipping box are permanently discarded from the current workspace memory.</li>
            <li>The clipping box widget is automatically turned off, and the window title will show <b>[Cropped]</b>.</li>
            <li><b>Note:</b> Cropping updates the statistics display in real-time to reflect only the remaining points.</li>
        </ul>

        <h3>4. Resetting Clipping & Workspace</h3>
        <p>The "Reset" button in the sidebar is context-sensitive and adapts to your current workflow state:</p>
        <ul>
            <li><b>Reset Clip Box:</b> If the clipping box is active but you haven't cropped yet, this button resets the box back to the full bounding box of the point cloud.</li>
            <li><b>Reset Workspace:</b> If you have cropped the point cloud, this button restores the original, full point cloud back into memory.</li>
        </ul>
        """

    def _get_measurements_html(self) -> str:
        return """
        <h2>Measurements, Shortcuts & Tips</h2>
        <p>Perform precise 3D distance measurements and utilize keyboard shortcuts for an efficient workflow.</p>

        <h3>1. Point-to-Point Distance Measurement</h3>
        <p>Measure the exact 3D distance between any two points in your point cloud:</p>
        <ul>
            <li><b>Activate:</b> Click the <b>Measure Distance</b> button in the sidebar, or press <b>Ctrl+M</b> (or select <b>Tools &gt; Measure Distance</b>). The button will lock into a checked state, and the status bar will guide you.</li>
            <li><b>Pick First Point:</b> Left-click directly on the point cloud. A yellow sphere marker will appear at the selected coordinate.</li>
            <li><b>Pick Second Point:</b> Left-click a second point on the point cloud. The application uses a KD-tree to automatically snap your click to the nearest actual point in the cloud.</li>
            <li><b>Result:</b> A red 3D line is rendered connecting the two points, labeled with the exact Euclidean distance in coordinate units.</li>
            <li><b>Multiple Measurements:</b> You can continue clicking pairs of points to add more measurements to the canvas.</li>
            <li><b>Exit/Cancel:</b> Press <b>ESC</b> or click <b>Stop Measuring</b> to exit the picker tool.</li>
            <li><b>Clear:</b> Click <b>Clear Measurements</b> in the sidebar (or <b>Tools &gt; Clear Measurements</b>) to remove all lines and labels from the screen.</li>
        </ul>

        <h3>2. Keyboard Shortcuts Quick Reference</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; border: 1px solid #5a5a5a; width: 100%; margin-top: 10px;">
            <tr style="background-color: #2a82da; color: white; font-weight: bold;">
                <th style="text-align: left; padding: 6px;">Action</th>
                <th style="text-align: left; padding: 6px;">Shortcut</th>
            </tr>
            <tr><td>Open Point Cloud File</td><td><b>Ctrl+O</b></td></tr>
            <tr><td>Export Point Cloud</td><td><b>Ctrl+E</b></td></tr>
            <tr><td>Take Screenshot</td><td><b>Ctrl+S</b></td></tr>
            <tr><td>Exit Application</td><td><b>Ctrl+Q</b></td></tr>
            <tr><td>Toggle User Guide</td><td><b>F1</b></td></tr>
            <tr><td>Toggle Theme (Light/Dark)</td><td><b>Ctrl+T</b></td></tr>
            <tr><td>Toggle Fullscreen</td><td><b>F11</b></td></tr>
            <tr><td>Toggle Clipping Box</td><td><b>Ctrl+B</b></td></tr>
            <tr><td>Toggle Measurement Mode</td><td><b>Ctrl+M</b></td></tr>
            <tr><td>Reset Camera View</td><td><b>0</b></td></tr>
            <tr><td>Top View Preset</td><td><b>1</b></td></tr>
            <tr><td>Front View Preset</td><td><b>2</b></td></tr>
            <tr><td>Side View Preset</td><td><b>3</b></td></tr>
            <tr><td>Isometric View Preset</td><td><b>4</b></td></tr>
            <tr><td>Cancel Active Tool / Stop Measuring</td><td><b>ESC</b></td></tr>
        </table>

        <h3>3. Best Practices & Pro-Tips</h3>
        <ul>
            <li><b>Performance:</b> If the 3D rendering feels sluggish, reduce the <b>Point Size</b> slider or reload the file using the <b>Voxel Downsample</b> option.</li>
            <li><b>Color Mode Analysis:</b> Use the <b>Curvature</b> color mode to highlight structural seams, cracks, or geometric edges in mechanical parts. Use the <b>Height</b> mode for terrain scan analysis.</li>
            <li><b>Statistics Panel:</b> The statistics panel at the bottom-right updates dynamically. Look at the <b>Geometric Stats</b> section to view real-time changes in bounding box volume and point density as you clip or crop the cloud.</li>
        </ul>
        """
