# -*- mode: python ; coding: utf-8 -*-
# PCD Visualizer Executable Specification

import sys
from pathlib import Path

# Get the directory containing this spec file
spec_root = Path(SPECPATH)

block_cipher = None

# Data files to include (e.g., an icon)
datas = [
    ('../assets', 'assets')
]

# Hidden imports for PyInstaller to find all necessary modules
hiddenimports = [
    # GUI frameworks
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtOpenGL',
    'PyQt6.sip',
    # Visualization
    'pyvista',
    'pyvistaqt',
    'matplotlib',
    'matplotlib.backends.backend_qt6agg',
    'matplotlib.figure',
    'matplotlib.pyplot',
    # Core processing
    'open3d',
    'numpy',
    # Additional GUI dependencies
    'sip',
    'OpenGL',
    'OpenGL.GL',
    'vtk',
    # Threading and system
    'threading',
    'pathlib',
    'typing',
    # Settings and configuration
    'PyQt6.QtCore.QSettings',
]

# Binaries to exclude (to reduce final executable size)
excludes = [
    'tkinter',
    'unittest',
    'test',
    'tests',
    'pytest',
    'IPython',
    'jupyter',
    'notebook',
    # Exclude PyQt5 to avoid conflicts with PyQt6
    'PyQt5',
]

a = Analysis(
    ['../pcd_visualizer.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PCDVisualizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # This is a GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Use a specific icon for the visualizer
    icon='../assets/visualizer_icon.ico'
)