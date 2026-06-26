import os
from pathlib import Path

# Project path resolution
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_PATH = ASSETS_DIR / "visualizer_icon.ico"

# Application Metadata
APP_NAME = "PCD Visualizer"
APP_VERSION = "2.0"
ORGANIZATION_NAME = "Quantnueral Pvt. Ltd."
ORGANIZATION_DOMAIN = "quantneural.com"

# Packaging parameters
EXECUTABLE_NAME = "PCDVisualizer"
INSTALLER_BASENAME = "PCDVisualizer_Setup"

# Logging settings
LOGGER_NAME = "pointviz"
LOG_SUBDIR = ".pointviz"
LOG_FILENAME = "pointviz.log"
LOG_MAX_BYTES = 5 * 1024 * 1024 # 5 MB
LOG_BACKUP_COUNT = 3

# File loading settings
SUPPORTED_EXTENSIONS = ['.pcd', '.ply']
LOAD_FILE_FILTER = "Point Cloud Data (*.pcd *.ply);;PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
SAVE_FILE_FILTER = "PCD Files (*.pcd);;PLY Files (*.ply);;All Files (*)"
SCREENSHOT_FILE_FILTER = "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"

# Default output names
DEFAULT_EXPORT_FILENAME = "exported_cloud.pcd"
DEFAULT_SCREENSHOT_FILENAME = "screenshot.png"

# Default rendering parameters
FALLBACK_POINT_COLOR = [128, 128, 255]

# Performance and Limits
LARGE_FILE_THRESHOLD_MB = 100
DEFAULT_VOXEL_SIZE = 0.05
DEFAULT_POINT_SIZE = 2
MAX_NORMALS_DISPLAY = 1000
NORMAL_ESTIMATION_RADIUS = 0.1
NORMAL_ESTIMATION_MAX_NN = 30

# OpenGL settings
OPENGL_DEPTH_BUFFER_SIZE = 24
OPENGL_STENCIL_BUFFER_SIZE = 8

# Visualization modes
BACKGROUND_STYLES = {
    # Gradients
    'Sky Horizon': ('white', 'lightblue'),
    'Golden Sunset': ('#ffeaa7', '#fd79a8'),
    'Midnight Void': ('#0a0a0a', '#1a1a2e'),
    # Solids
    'Black': 'black',
    'White': 'white',
}

COLOR_MODES = {
    'Original': 'original',
    'Height': 'height',
    'Elevation': 'elevation',
    'Distance': 'distance',
    'Normal': 'normal',
    'Curvature': 'curvature'
}

MAX_RECENT_FILES = 10
