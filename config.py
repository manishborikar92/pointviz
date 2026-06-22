import os
from pathlib import Path

# Project path resolution
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_PATH = ASSETS_DIR / "visualizer_icon.ico"

# Application Metadata
APP_NAME = "PCD Visualizer"
APP_VERSION = "2.0"
ORGANIZATION_NAME = "PCDVisualizer"

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
    'Gradient': ('white', 'lightblue'),
    'Dark Gradient': ('#1A1A26', '#212136'),
    'Sunset Gradient': ('#ffeaa7', '#fd79a8'),
    'White': 'white',
    'Black': 'black',
    'Gray': '#f0f0f0'
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
