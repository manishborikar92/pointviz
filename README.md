# PCD Point Cloud Visualizer

A PyQt6-based desktop application for visualizing and inspecting 3D point cloud data files (`.pcd`, `.ply`).

## Features

### Core Functionality
- **Point Cloud Visualization**: Load and render `.pcd` and `.ply` files in an interactive 3D viewport
- **Large File Handling**: Automatic voxel downsampling dialog for files exceeding 100 MB
- **Multiple Color Modes**: Original, Height, Elevation, Distance, Normal, and Curvature-based coloring
- **Interactive 3D Rendering**: Powered by PyVista/VTK with camera presets (Top, Front, Side, Isometric)
- **Comprehensive Statistics**: Point count, bounding box, centroid, density, coordinate ranges, and normal analysis

### User Interface
- **Dark/Light Themes**: Professional theme switching with automatic system preference detection
- **Responsive Controls**: Real-time point size, color mode, and background adjustments
- **Asynchronous Loading**: Non-blocking file loading with progress indication
- **Export Capabilities**: Screenshot capture and point cloud data export
- **Keyboard Shortcuts**: Full shortcut support for views, file operations, and theme toggle

## Project Structure

```
pointviz/
├── pcd_visualizer.py          # Thin wrapper compatibility entry point
├── main.py                    # Application entry point & configuration setup
├── config.py                  # Centralized UI & performance configurations
├── logger.py                  # Standard stdout & rotating file logger setup
├── core/                      # Core processing and calculations
│   ├── point_cloud_processor.py # Background QThread processing
│   └── statistics.py          # Geometrical statistics calculations
├── gui/                       # PyQt6 GUI views and sub-panels
│   ├── main_window.py         # Shell container PCDVisualizer class
│   ├── pyvista_widget.py      # Interactive 3D VTK viewer widget
│   ├── control_panel.py       # Sidebar settings widget
│   ├── visualization_panel.py # Main viewport tab container
│   ├── theme_manager.py       # Light/dark stylesheet compiler
│   ├── menus.py               # Menu bar construction
│   └── dialogs.py             # Options & custom About dialogs
├── assets/
│   ├── visualizer_icon.ico    # Application icon
│   ├── logo_dark.png          # Dark theme logo
│   └── logo_light.png         # Light theme logo
├── packaging/
│   ├── build_visualizer.bat   # Windows build script (venv + PyInstaller + Inno Setup)
│   ├── visualizer.spec        # PyInstaller specification
│   └── visualizer_installer.iss # Inno Setup installer configuration
├── requirements.txt           # Pinned dependencies
├── LICENSE                    # Apache 2.0
└── README.md
```

### Internal Architecture

The application is organized into modular directories and modules:

- **Entry Point**: [pcd_visualizer.py](pcd_visualizer.py) is a thin wrapper that invokes [main.py](main.py).
- **Configuration & Logging**: Centralized settings reside in [config.py](config.py), and log configurations are set up in [logger.py](logger.py).
- **Core Processing**: Background threaded operations live in [core/point_cloud_processor.py](core/point_cloud_processor.py), while pure statistical calculations are extracted into [core/statistics.py](core/statistics.py).
- **GUI Views**: Split into sub-components under `gui/`, with the main shell [gui/main_window.py](gui/main_window.py) connecting signals and coordinating panels.

## Installation

### Prerequisites

- Python 3.9 or later

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Version | Purpose |
|---|---|---|
| PyQt6 | 6.9.1 | GUI framework |
| Open3D | 0.19.0 | Point cloud I/O, downsampling, and normal estimation |
| PyVista | 0.46.0 | 3D visualization and rendering (VTK wrapper) |
| pyvistaqt | 0.11.3 | Qt integration for PyVista |
| matplotlib | 3.10.0 | Colormap utilities (`viridis`, `terrain`, `plasma`, `coolwarm`) |
| NumPy | 2.2.2 | Array operations |

## Usage

### Running the Application

```bash
# Launch with file dialog
python pcd_visualizer.py

# Open a specific file directly
python pcd_visualizer.py path/to/cloud.pcd
```

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file |
| `Ctrl+E` | Export point cloud |
| `Ctrl+S` | Take screenshot |
| `Ctrl+T` | Toggle dark/light theme |
| `Ctrl+Q` | Quit |
| `0` | Reset camera |
| `1` / `2` / `3` / `4` | Top / Front / Side / Isometric view |
| `F11` | Toggle fullscreen |

### Workflow

1. **Load**: Open a `.pcd` or `.ply` file. Files over 100 MB trigger a downsampling dialog.
2. **Visualize**: Adjust point size, color mode, and background in the control panel.
3. **Inspect**: Switch to the Statistics tab for geometric and feature analysis.
4. **Export**: Save screenshots (`Ctrl+S`) or export the point cloud (`Ctrl+E`).

## Color Modes

| Mode | Description | Colormap |
|---|---|---|
| Original | Embedded point colors, or uniform gray if none | — |
| Height | Z-coordinate mapping | `viridis` |
| Elevation | Terrain-style Z mapping | `terrain` |
| Distance | Radial distance from centroid | `plasma` |
| Normal | Surface normal direction as RGB | — |
| Curvature | Local curvature estimation | `coolwarm` |

## Building for Distribution (Windows)

The `packaging/` directory contains a complete Windows distribution pipeline. 

### Recommended Build Process
From the project root, execute the build script:
```bash
packaging\build_visualizer.bat
```

This script automates the following steps:
1. Creates/activates the local virtual environment.
2. Installs required python dependencies from `requirements.txt`.
3. Compiles a standalone executable via PyInstaller.
4. If Inno Setup is installed, compiles the Windows installer.

### Installer Compilation & Single Source of Truth
The Inno Setup script (`packaging/visualizer_installer.iss`) is **intentionally designed to be compiled exclusively via `packaging/build_visualizer.bat`**.

**Why this approach was chosen:**
Instead of duplicating application identity metadata (such as version or publisher details) directly in the `.iss` file, the build script extracts these constants dynamically from `config.py` (the single source of truth) and injects them as preprocessor variables (`/DAppName`, `/DAppVersion`, etc.) into Inno Setup (`ISCC.exe`) at build time. Compiling the `.iss` file directly outside the batch script will fail due to these missing definitions, guaranteeing metadata consistency across the executable and the installer.

### Application Identity Parameters
The following metadata configurations are defined in `config.py`:
* **`APP_NAME`**: The user-facing display name of the application (e.g., `"PCD Visualizer"`). This is used in shortcut titles, application window titles, and menus.
* **`EXECUTABLE_NAME`**: The file name of the generated standalone binary (without `.exe`, e.g., `"PCDVisualizer"`). This defines the process and system name for file associations and installation paths.
* **`INSTALLER_BASENAME`**: The filename prefix for the generated installer (e.g., `"PCDVisualizer_Setup"`), which will be output as `dist/[INSTALLER_BASENAME]_v[APP_VERSION].exe`.

Outputs will be generated under the `dist/` directory.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Version History

- **v2.0** — Large file handling with voxel downsampling, improved theming, statistics display
- **v1.0** — Initial implementation