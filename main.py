import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QSurfaceFormat

import pyvista as pv

from config import (
    OPENGL_DEPTH_BUFFER_SIZE,
    OPENGL_STENCIL_BUFFER_SIZE,
    APP_NAME,
    APP_VERSION,
    ORGANIZATION_NAME,
    ORGANIZATION_DOMAIN
)
from logger import setup_logging, logger
from gui.main_window import PCDVisualizer

def configure_environment():
    """Configure environment variables for better compatibility."""
    env_vars = {
        'PYVISTA_USE_PANEL': '0',
        'PYVISTA_OFF_SCREEN': 'false'
    }
    
    for var, value in env_vars.items():
        os.environ[var] = value

def configure_pyvista():
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
        logger.warning(f"Could not configure PyVista theme: {e}")

def configure_opengl():
    """Configure OpenGL format for better compatibility."""
    try:
        q_format = QSurfaceFormat()
        q_format.setDepthBufferSize(OPENGL_DEPTH_BUFFER_SIZE)
        q_format.setStencilBufferSize(OPENGL_STENCIL_BUFFER_SIZE)
        q_format.setVersion(2, 1)  # Use OpenGL 2.1 for better compatibility
        q_format.setSamples(0)  # Disable anti-aliasing
        QSurfaceFormat.setDefaultFormat(q_format)
    except Exception as e:
        logger.warning(f"Could not set OpenGL format: {e}")

def main():
    """Main application entry point with improved initialization."""
    # 1. Initialize Logging framework first
    setup_logging()
    logger.info("Initializing PCD Point Cloud Visualizer...")
    
    # 2. Configure environment
    configure_environment()
    
    # 3. Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setOrganizationDomain(ORGANIZATION_DOMAIN)
    app.setStyle('Fusion')  # Modern look
    
    # 4. Configure OpenGL and PyVista
    configure_opengl()
    configure_pyvista()
    
    # 5. Check for command line arguments (file path to open)
    file_to_open = None
    if len(sys.argv) > 1:
        potential_file = sys.argv[1]
        if Path(potential_file).exists():
            file_to_open = potential_file
            logger.info(f"Opening file requested via command line: {file_to_open}")
        else:
            logger.warning(f"File not found: {potential_file}")
    
    # 6. Create and show main window
    window = PCDVisualizer(file_to_open)
    window.show()
    
    # 7. Handle application exit with proper cleanup
    def cleanup_handler():
        """Clean up resources before exit."""
        logger.info("Final cleanup before quitting...")
        try:
            if hasattr(window, 'pyvista_widget') and window.pyvista_widget:
                window.pyvista_widget.cleanup()
        except Exception as e:
            logger.warning(f"Warning during final cleanup: {e}")
            
    app.aboutToQuit.connect(cleanup_handler)
    
    try:
        exit_code = app.exec()
        logger.info(f"Application exiting cleanly with code {exit_code}")
        return exit_code
    except SystemExit:
        cleanup_handler()
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception in main execution loop: {e}", exc_info=True)
        cleanup_handler()
        return 1

if __name__ == "__main__":
    sys.exit(main())
