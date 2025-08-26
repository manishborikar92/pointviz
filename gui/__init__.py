"""
PCD Visualizer GUI Package
==========================

A modular PyQt6-based GUI for point cloud visualization with LVX conversion capabilities.

Package Structure:
- main_window.py: Main application window and orchestration
- control_panel.py: Control panel with file loading and visualization settings
- visualization_panel.py: 3D visualization and statistics display
- pyvista_widget.py: PyVista 3D rendering widget
- menus.py: Menu management with LVX conversion integration
- lvx_converter.py: LVX to PCD conversion functionality
- point_cloud_processor.py: Asynchronous point cloud processing
- theme_manager.py: Dark/light theme management
- statusbar.py: Status bar management utilities

Usage:
    from gui.main_window import PCDVisualizer
    
Key Features:
- Modular, maintainable architecture
- LVX to PCD conversion integrated into Tools menu
- Asynchronous file loading with progress indication
- Multiple visualization modes and color schemes
- Professional dark/light theme switching
- Comprehensive statistics display
- Export capabilities for screenshots and data

Dependencies:
- PyQt6
- open3d
- pyvista
- pyvistaqt
- matplotlib
- numpy
"""

from .main_window import PCDVisualizer

__all__ = ['PCDVisualizer']
__version__ = '2.0.0'
