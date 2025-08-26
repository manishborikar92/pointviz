#!/usr/bin/env python3
"""
Cross-platform build script for PCD Visualizer
Supports Windows (exe/msi) and macOS (app/dmg) packaging
"""

import os
import sys
import shutil
import subprocess
import platform
import argparse
from pathlib import Path

class BuildSystem:
    def __init__(self):
        self.platform = platform.system().lower()
        self.project_root = Path(__file__).parent.absolute()
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        
    def clean(self):
        """Clean build directories."""
        print("🧹 Cleaning build directories...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   Removed {dir_path}")
    
    def install_dependencies(self):
        """Install build dependencies."""
        print("📦 Installing build dependencies...")
        
        base_deps = ["setuptools", "wheel"]
        
        if self.platform == "windows":
            build_deps = ["cx_Freeze", "pyinstaller"]
        elif self.platform == "darwin":
            build_deps = ["py2app", "pyinstaller", "dmgbuild"]
        else:
            build_deps = ["pyinstaller"]
        
        all_deps = base_deps + build_deps
        
        for dep in all_deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"   ✓ {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ✗ Failed to install {dep}: {e}")
                return False
        return True
    
    def build_windows_exe(self):
        """Build Windows executable using PyInstaller."""
        print("🏗️ Building Windows executable...")
        
        spec_content = """
# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect all pyvista and open3d data
pyvista_datas = collect_data_files('pyvista')
open3d_datas = collect_data_files('open3d')

a = Analysis(
    ['pcd_visualizer/main.py'],
    pathex=[],
    binaries=[],
    datas=pyvista_datas + open3d_datas + [
        ('pcd_visualizer/gui', 'pcd_visualizer/gui'),
        ('pcd_visualizer/resources', 'pcd_visualizer/resources'),
    ],
    hiddenimports=[
        'pyvista', 'pyvistaqt', 'open3d', 'PyQt6', 'PyQt6.QtOpenGL',
        'vtk', 'matplotlib', 'scipy', 'numpy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PCD-Visualizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PCD-Visualizer',
)
"""
        
        spec_path = self.project_root / "pcd_visualizer.spec"
        with open(spec_path, "w") as f:
            f.write(spec_content)
        
        try:
            subprocess.run([
                sys.executable, "-m", "PyInstaller", 
                "--clean", str(spec_path)
            ], check=True, cwd=self.project_root)
            print("   ✓ Windows executable created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed to build Windows executable: {e}")
            return False
    
    def build_windows_msi(self):
        """Build Windows MSI installer using cx_Freeze."""
        print("🏗️ Building Windows MSI installer...")
        
        setup_content = """
import sys
from cx_Freeze import setup, Executable
import os

# Dependencies are automatically detected, but may need fine tuning.
build_options = {
    "packages": [
        "PyQt6", "pyvista", "pyvistaqt", "open3d", "matplotlib", 
        "numpy", "vtk", "scipy"
    ],
    "excludes": ["tkinter", "unittest"],
    "include_files": [
        ("pcd_visualizer/gui", "gui"),
        ("pcd_visualizer/resources", "resources"),
    ],
    "include_msvcrt": True,
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        "pcd_visualizer/main.py",
        base=base,
        target_name="PCD-Visualizer.exe",
        icon="resources/icon.ico"
    )
]

setup(
    name="PCD Visualizer",
    version="2.0.0",
    description="Point Cloud Data Visualizer",
    options={"build_exe": build_options, "bdist_msi": {"upgrade_code": "{12345678-1234-5678-90AB-123456789012}"}},
    executables=executables,
)
"""
        
        setup_cx_path = self.project_root / "setup_cx.py"
        with open(setup_cx_path, "w") as f:
            f.write(setup_content)
        
        try:
            subprocess.run([
                sys.executable, "setup_cx.py", "bdist_msi"
            ], check=True, cwd=self.project_root)
            print("   ✓ Windows MSI installer created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed to build Windows MSI: {e}")
            return False
    
    def build_macos_app(self):
        """Build macOS application bundle."""
        print("🏗️ Building macOS application bundle...")
        
        setup_content = """
from setuptools import setup
import py2app

APP = ['pcd_visualizer/main.py']
DATA_FILES = [
    ('gui', ['pcd_visualizer/gui']),
    ('resources', ['pcd_visualizer/resources']),
]

OPTIONS = {
    'iconfile': 'resources/icon.icns',
    'plist': {
        'CFBundleName': 'PCD Visualizer',
        'CFBundleDisplayName': 'PCD Visualizer',
        'CFBundleGetInfoString': "Point Cloud Data Visualizer",
        'CFBundleIdentifier': 'com.pcdvisualizer.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.14',
    },
    'packages': [
        'PyQt6', 'pyvista', 'pyvistaqt', 'open3d', 'matplotlib',
        'numpy', 'vtk', 'scipy'
    ],
    'includes': ['sip'],
    'excludes': ['tkinter'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
"""
        
        setup_py2app_path = self.project_root / "setup_py2app.py"
        with open(setup_py2app_path, "w") as f:
            f.write(setup_content)
        
        try:
            subprocess.run([
                sys.executable, "setup_py2app.py", "py2app"
            ], check=True, cwd=self.project_root)
            print("   ✓ macOS application bundle created")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed to build macOS app: {e}")
            return False
    
    def build_macos_dmg(self):
        """Build macOS DMG installer."""
        print("🏗️ Building macOS DMG installer...")
        
        dmg_settings = {
            'filename': 'PCD-Visualizer-2.0.0.dmg',
            'volume_name': 'PCD Visualizer',
            'files': [str(self.dist_dir / 'PCD Visualizer.app')],
            'symlinks': {'Applications': '/Applications'},
            'icon_locations': {
                'PCD Visualizer.app': (140, 120),
                'Applications': (500, 120),
            },
            'background': 'resources/dmg_background.png',
            'window_rect': ((100, 100), (640, 280)),
            'icon_size': 128,
            'text_size': 16,
        }
        
        try:
            import dmgbuild
            dmgbuild.build_dmg(
                str(self.dist_dir / 'PCD-Visualizer-2.0.0.dmg'),
                'PCD Visualizer',
                settings=dmg_settings
            )
            print("   ✓ macOS DMG installer created")
            return True
        except Exception as e:
            print(f"   ✗ Failed to build macOS DMG: {e}")
            return False
    
    def build(self, target=None):
        """Main build function."""
        print(f"🚀 Starting build for {self.platform}")
        
        # Clean previous builds
        self.clean()
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Create directories
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)
        
        success = False
        
        if self.platform == "windows":
            if target in [None, "exe", "all"]:
                success = self.build_windows_exe()
            if target in [None, "msi", "all"]:
                success = self.build_windows_msi() and success
        
        elif self.platform == "darwin":
            if target in [None, "app", "all"]:
                success = self.build_macos_app()
            if target in [None, "dmg", "all"]:
                success = self.build_macos_dmg() and success
        
        else:
            print(f"❌ Platform {self.platform} not supported for packaging")
            return False
        
        if success:
            print("✅ Build completed successfully!")
            print(f"📁 Output directory: {self.dist_dir}")
        else:
            print("❌ Build failed!")
        
        return success

def main():
    parser = argparse.ArgumentParser(description="Build PCD Visualizer packages")
    parser.add_argument("--clean", action="store_true", help="Clean build directories")
    parser.add_argument("--target", choices=["exe", "msi", "app", "dmg", "all"], 
                       help="Specific target to build")
    
    args = parser.parse_args()
    
    builder = BuildSystem()
    
    if args.clean:
        builder.clean()
        return
    
    return builder.build(args.target)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)