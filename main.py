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

from main_window import PCDVisualizer


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

# python main.py