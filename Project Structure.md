#!/bin/bash
# Project Structure Setup Script
# Creates the proper directory structure for the PCD Visualizer application

echo "📁 Creating PCD Visualizer project structure..."

# Create main project directory
mkdir -p pcd-visualizer

# Navigate to project root
cd pcd-visualizer

# Create package structure
mkdir -p pcd_visualizer/{gui,resources,icons}
mkdir -p {build,dist,docs,tests}

# Create main package __init__.py files
cat > pcd_visualizer/__init__.py << 'EOF'
"""
PCD Visualizer - Point Cloud Data Visualization Tool
"""

__version__ = "2.0.0"
__author__ = "PCD Visualizer Team"
__email__ = "contact@pcdvisualizer.com"

from .main import main

__all__ = ["main"]
EOF

cat > pcd_visualizer/gui/__init__.py << 'EOF'
"""
GUI components for PCD Visualizer
"""
EOF

# Move your main.py to the package structure
cat > pcd_visualizer/main.py << 'EOF'
#!/usr/bin/env python3
"""
PCD Point Cloud Visualizer - Main Entry Point
A powerful tool for visualizing point cloud data with LVX conversion capabilities.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QSurfaceFormat
import pyvista as pv

# Add gui module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gui'))

try:
    from .gui.main_window import PCDVisualizer
except ImportError:
    # Fallback for direct execution
    from gui.main_window import PCDVisualizer


def setup_environment():
    """Setup environment variables and OpenGL compatibility."""
    os.environ['QT_OPENGL'] = 'software'
    os.environ['PYVISTA_USE_PANEL'] = '0'
    os.environ['PYVISTA_OFF_SCREEN'] = 'false'


def setup_opengl_format():
    """Configure OpenGL format for better compatibility."""
    try:
        format = QSurfaceFormat()
        format.setDepthBufferSize(24)
        format.setStencilBufferSize(8)
        format.setVersion(2, 1)  # Use OpenGL 2.1 for better compatibility
        format.setSamples(0)  # Disable anti-aliasing to avoid framebuffer issues
        QSurfaceFormat.setDefaultFormat(format)
    except Exception as e:
        print(f"Warning: Could not set OpenGL format: {e}")


def setup_pyvista():
    """Configure PyVista for better compatibility."""
    try:
        pv.set_plot_theme('document')
        pv.global_theme.multi_samples = 0
        pv.global_theme.depth_peeling.enabled = False
        pv.global_theme.silhouette.enabled = False
        pv.global_theme.lighting = True
        pv.global_theme.show_edges = False
        pv.global_theme.edge_color = 'black'
        pv.global_theme.line_width = 1
    except Exception as e:
        print(f"Warning: Could not configure PyVista theme: {e}")


def check_dependencies():
    """Check for required dependencies."""
    missing_deps = []
    
    try:
        import PyQt6
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import open3d
    except ImportError:
        missing_deps.append("open3d")
    
    try:
        import pyvista
    except ImportError:
        missing_deps.append("pyvista")
    
    try:
        import pyvistaqt
    except ImportError:
        missing_deps.append("pyvistaqt")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    if missing_deps:
        QMessageBox.critical(None, "Missing Dependencies", 
                           "The following dependencies are required but not installed:\n\n" +
                           "\n".join([f"• {dep}" for dep in missing_deps]) +
                           "\n\nPlease install them and try again.")
        return False
    
    return True


def main():
    """Main application entry point."""
    # Setup environment
    setup_environment()
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("PCD Visualizer")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("PCDVisualizer")
    app.setStyle('Fusion')  # Modern look
    
    # Configure OpenGL and PyVista
    setup_opengl_format()
    setup_pyvista()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create and show main window
    window = PCDVisualizer()
    window.show()
    
    # Handle application exit with proper cleanup
    def cleanup_handler():
        """Clean up resources before exit."""
        try:
            if hasattr(window, 'pyvista_widget') and window.pyvista_widget:
                window.pyvista_widget.cleanup()
        except Exception as e:
            print(f"Warning during final cleanup: {e}")
    
    app.aboutToQuit.connect(cleanup_handler)
    
    try:
        return app.exec()
    except SystemExit:
        cleanup_handler()
        return 0


if __name__ == "__main__":
    sys.exit(main())
EOF

# Create placeholder GUI module (you'll need to add your actual main_window.py)
cat > pcd_visualizer/gui/main_window.py << 'EOF'
"""
Main window implementation for PCD Visualizer
Replace this with your actual main_window.py file
"""

from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class PCDVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCD Visualizer")
        self.setGeometry(100, 100, 800, 600)
        
        # Placeholder content - replace with your actual implementation
        central_widget = QWidget()
        layout = QVBoxLayout()
        label = QLabel("PCD Visualizer - Replace with your main_window.py")
        layout.addWidget(label)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
EOF

# Create requirements files
cat > requirements.txt << 'EOF'
PyQt6>=6.4.0
open3d>=0.17.0
pyvista>=0.42.0
pyvistaqt>=0.11.0
matplotlib>=3.6.0
numpy>=1.21.0
vtk>=9.2.0
scipy>=1.9.0
EOF

cat > requirements-dev.txt << 'EOF'
-r requirements.txt
pytest>=7.0
pytest-qt>=4.2.0
black>=22.0
flake8>=5.0
mypy>=0.991
EOF

cat > requirements-build.txt << 'EOF'
-r requirements.txt
cx_Freeze>=6.13.1
pyinstaller>=5.7.0
py2app>=0.28.4; platform_system=="Darwin"
dmgbuild>=1.6.0; platform_system=="Darwin"
EOF

# Create README
cat > README.md << 'EOF'
# PCD Visualizer

A powerful cross-platform tool for visualizing point cloud data with LVX conversion capabilities.

## Features

- Cross-platform support (Windows, macOS, Linux)
- Point cloud visualization with PyVista and Open3D
- LVX file conversion capabilities
- Modern PyQt6 interface
- Installable packages for Windows (MSI) and macOS (DMG)

## Installation

### From Package

Download the appropriate installer for your platform:
- **Windows**: Download and run the MSI installer
- **macOS**: Download and install the DMG package

### From Source

```bash
git clone https://github.com/pcdvisualizer/pcd-visualizer.git
cd pcd-visualizer
pip install -r requirements.txt
python -m pcd_visualizer.main
```

## Building

To build installable packages:

```bash
# Install build dependencies
pip install -r requirements-build.txt

# Build for current platform
python build.py

# Build specific target
python build.py --target msi    # Windows MSI
python build.py --target exe    # Windows EXE
python build.py --target app    # macOS App Bundle
python build.py --target dmg    # macOS DMG
```

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black pcd_visualizer/

# Type checking
mypy pcd_visualizer/
```

## License

MIT License - see LICENSE file for details.
EOF

# Create LICENSE file
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 PCD Visualizer Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Create .gitignore
cat > .gitignore