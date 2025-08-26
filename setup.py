#!/usr/bin/env python3
"""
Setup script for PCD Point Cloud Visualizer
Cross-platform packaging configuration for Windows and macOS
"""

import sys
import os
from setuptools import setup, find_packages
from pathlib import Path

# Read version from main.py or use default
VERSION = "2.0.0"

# Read long description from README
README_PATH = Path(__file__).parent / "README.md"
if README_PATH.exists():
    with open(README_PATH, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "A powerful tool for visualizing point cloud data with LVX conversion capabilities."

# Define dependencies
INSTALL_REQUIRES = [
    "PyQt6>=6.4.0",
    "open3d>=0.17.0",
    "pyvista>=0.42.0",
    "pyvistaqt>=0.11.0",
    "matplotlib>=3.6.0",
    "numpy>=1.21.0",
    "vtk>=9.2.0",
    "scipy>=1.9.0",
]

# Platform-specific dependencies
EXTRAS_REQUIRE = {
    "dev": [
        "pytest>=7.0",
        "pytest-qt>=4.2.0",
        "black>=22.0",
        "flake8>=5.0",
        "mypy>=0.991",
    ],
    "build": [
        "cx_Freeze>=6.13.1",
        "pyinstaller>=5.7.0",
        "py2app>=0.28.4;platform_system=='Darwin'",
    ]
}

# Entry points for the application
ENTRY_POINTS = {
    "console_scripts": [
        "pcd-visualizer=pcd_visualizer.main:main",
    ],
    "gui_scripts": [
        "pcd-visualizer-gui=pcd_visualizer.main:main",
    ],
}

# Data files to include
PACKAGE_DATA = {
    "pcd_visualizer": [
        "gui/*.py",
        "resources/*",
        "icons/*",
        "*.ui",
    ]
}

# Classifiers for PyPI
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Multimedia :: Graphics :: 3D Modeling",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

setup(
    name="pcd-visualizer",
    version=VERSION,
    author="PCD Visualizer Team",
    author_email="contact@pcdvisualizer.com",
    description="A powerful tool for visualizing point cloud data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pcdvisualizer/pcd-visualizer",
    packages=find_packages(),
    package_data=PACKAGE_DATA,
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points=ENTRY_POINTS,
    classifiers=CLASSIFIERS,
    python_requires=">=3.8",
    keywords="point-cloud visualization 3d pcd lvx open3d pyvista",
    project_urls={
        "Bug Reports": "https://github.com/pcdvisualizer/pcd-visualizer/issues",
        "Documentation": "https://pcdvisualizer.readthedocs.io/",
        "Source": "https://github.com/pcdvisualizer/pcd-visualizer",
    },
    zip_safe=False,
    platforms=["Windows", "macOS", "Linux"],
)