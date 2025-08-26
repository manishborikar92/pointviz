# PCD Point Cloud Visualizer - Modular Edition

A powerful, modular PyQt6-based application for visualizing point cloud data with integrated LVX to PCD conversion capabilities.

## Features

### Core Functionality
- **Point Cloud Visualization**: Support for PCD and PLY file formats
- **LVX Conversion**: Integrated LVX to PCD converter accessible through Tools menu
- **Multiple Color Modes**: Original, Height, Elevation, Distance, Normal, and Curvature-based coloring
- **Interactive 3D Visualization**: Powered by PyVista with OpenGL compatibility
- **Comprehensive Statistics**: Detailed point cloud analysis and metrics

### User Interface
- **Modular Architecture**: Clean separation of concerns with organized component structure
- **Dark/Light Themes**: Professional theme switching with system detection
- **Responsive Controls**: Real-time visualization updates without performance impact
- **Asynchronous Loading**: Non-blocking file operations with progress indication
- **Export Capabilities**: Screenshot and point cloud data export

## Project Structure

```
pcd_visualizer/
├── main.py                          # Application entry point
├── gui/                             # Modular GUI components
│   ├── __init__.py                  # Package initialization
│   ├── main_window.py               # Main application window
│   ├── control_panel.py             # File loading and visualization controls
│   ├── visualization_panel.py       # 3D view and statistics display
│   ├── pyvista_widget.py           # PyVista 3D rendering widget
│   ├── menus.py                    # Menu management with LVX conversion
│   ├── lvx_converter.py            # LVX to PCD conversion functionality
│   ├── point_cloud_processor.py    # Asynchronous processing thread
│   ├── theme_manager.py            # Theme switching and styling
│   └── statusbar.py               # Status bar utilities
└── README.md                       # This file
```

## Installation

### Prerequisites
```bash
pip install PyQt6 open3d pyvista pyvistaqt matplotlib numpy
```

### Dependencies
- **PyQt6**: Modern GUI framework
- **Open3D**: Point cloud processing and I/O
- **PyVista**: 3D visualization and rendering
- **PyVistaQt**: Qt integration for PyVista
- **Matplotlib**: Color mapping and visualization utilities
- **NumPy**: Numerical computations

## Usage

### Running the Application
```bash
python main.py
```

### Basic Workflow
1. **Load Point Cloud**: Use File → Open or the Load button to import PCD/PLY files
2. **Convert LVX Files**: Access Tools → Convert LVX to PCD for file conversion
3. **Adjust Visualization**: Modify point size, color mode, and background in the control panel
4. **View Statistics**: Switch to the Statistics tab for detailed point cloud analysis
5. **Export Results**: Take screenshots or export processed point clouds

### LVX Conversion
The LVX converter supports:
- Multiple LVX data types (0, 1, 2, 3)
- Binary and ASCII PCD output formats
- Optional reflectivity data inclusion
- Batch processing capabilities
- Direct loading of converted files

## Key Improvements

### Code Organization
- **Modular Design**: Each component has a single responsibility
- **Clean Separation**: UI, logic, and data processing are properly separated
- **Reusable Components**: Individual modules can be easily maintained and extended
- **Reduced Coupling**: Components communicate through well-defined interfaces

### Performance Optimizations
- **Efficient Updates**: Visualization changes only re-render when necessary
- **Asynchronous Operations**: File loading doesn't block the UI
- **Memory Management**: Proper cleanup of PyVista resources
- **Optimized Rendering**: Smart actor management for smooth interactions

### User Experience
- **Professional Appearance**: Comprehensive dark/light theme support
- **Responsive Interface**: Real-time feedback for all controls
- **Error Handling**: Graceful handling of file loading and conversion errors
- **Progress Indication**: Clear feedback for long-running operations

## Technical Details

### LVX File Support
The converter handles various LVX data packet types:
- **Type 0**: Cartesian coordinates with reflectivity (13 bytes per point)
- **Type 1**: Spherical coordinates (8 bytes per point)
- **Type 2**: Extended cartesian with tags (14 bytes per point)
- **Type 3**: Spherical with reflectivity (9 bytes per point)
- **Type 6**: IMU data (24 bytes, processed but not converted)

### Visualization Features
- **Color Modes**: 
  - Original: Uses embedded colors or grayscale
  - Height: Z-coordinate based coloring with viridis colormap
  - Elevation: Terrain-style coloring for topographic data
  - Distance: Radial distance from centroid with plasma colormap
  - Normal: Surface normal direction visualization
  - Curvature: Local curvature estimation display

### Statistics Computation
- **Basic Information**: Point count, dimensions, memory usage
- **Geometric Properties**: Centroid, bounding box, density calculations
- **Feature Analysis**: Color, normal, and covariance detection
- **Statistical Metrics**: Coordinate ranges, distributions, and magnitudes

## Development

### Architecture Benefits
- **Maintainability**: Each module has clear responsibilities
- **Extensibility**: New features can be added without major refactoring
- **Testability**: Components can be tested independently
- **Reusability**: Modules can be used in other projects

### Code Quality Improvements
- **Removed Redundancy**: Eliminated duplicate code and unused imports
- **Improved Error Handling**: Comprehensive exception management
- **Better Documentation**: Clear docstrings and type hints
- **Consistent Styling**: Uniform code formatting and naming conventions

## Contributing

When adding new features or making modifications:

1. **Maintain Modularity**: Keep components focused and loosely coupled
2. **Follow Patterns**: Use established patterns for signal/slot connections
3. **Update Documentation**: Keep README and docstrings current
4. **Test Thoroughly**: Verify functionality across different file types and sizes
5. **Handle Errors Gracefully**: Provide meaningful error messages to users

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with all dependency licenses when distributing or modifying the code.

## Version History

- **v2.0** - Modular architecture with integrated LVX conversion
- **v1.0** - Original monolithic implementation

## Support

For issues or questions:
1. Check the comprehensive error messages and status bar feedback
2. Verify all dependencies are properly installed
3. Test with known-good point cloud files
4. Review the modular code structure for customization needs