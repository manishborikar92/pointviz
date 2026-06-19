import os
import sys
from unittest import mock
import numpy as np
import open3d as o3d
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# Add workspace to path to import pcd_visualizer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pcd_visualizer
from pcd_visualizer import configure_environment, PointCloudProcessor, PyVistaWidget, PCDVisualizer

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_configure_environment():
    # Clear environment variables first if they exist
    os.environ.pop('QT_OPENGL', None)
    os.environ.pop('PYVISTA_USE_PANEL', None)
    os.environ.pop('PYVISTA_OFF_SCREEN', None)
    
    configure_environment()
    
    assert 'QT_OPENGL' not in os.environ
    assert os.environ.get('PYVISTA_USE_PANEL') == '0'
    assert os.environ.get('PYVISTA_OFF_SCREEN') == 'false'

def test_get_system_theme_preference_success(qapp):
    # Mock PCDVisualizer subclass or instance
    with mock.patch.object(QApplication, 'instance') as mock_app:
        mock_palette = mock.Mock()
        mock_color = mock.Mock()
        mock_color.lightness.return_value = 100 # Dark theme (< 128)
        mock_palette.color.return_value = mock_color
        mock_app.return_value.palette.return_value = mock_palette
        
        with mock.patch('pcd_visualizer.PCDVisualizer.init_ui'), \
             mock.patch('pcd_visualizer.PCDVisualizer.apply_theme'):
            visualizer = PCDVisualizer()
            pref = visualizer._get_system_theme_preference()
            assert pref is True

def test_get_system_theme_preference_exception(qapp):
    with mock.patch.object(QApplication, 'instance') as mock_app:
        mock_app.return_value.palette.side_effect = Exception("Palette error")
        with mock.patch('pcd_visualizer.PCDVisualizer.init_ui'), \
             mock.patch('pcd_visualizer.PCDVisualizer.apply_theme'):
            visualizer = PCDVisualizer()
            pref = visualizer._get_system_theme_preference()
            assert pref is False  # Safe fallback

def test_point_cloud_processor_interruption():
    # Mock the processor to always report interruption is requested
    processor = PointCloudProcessor("dummy.pcd", {"method": "none", "value": None})
    
    with mock.patch.object(processor, 'isInterruptionRequested', return_value=True):
        loaded_emitted = False
        def on_loaded(cloud, count):
            nonlocal loaded_emitted
            loaded_emitted = True
        processor.loaded.connect(on_loaded)
        
        # Run should exit early and not emit loaded
        processor.run()
        
        assert loaded_emitted is False

def test_color_by_curvature(qapp):
    with mock.patch('pcd_visualizer.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        
        pcd = o3d.geometry.PointCloud()
        pts = np.random.rand(100, 3)
        pcd.points = o3d.utility.Vector3dVector(pts)
        widget.current_point_cloud = pcd
        
        colors = widget._color_by_curvature(pts)
        
        assert colors.shape == (100, 3)
        assert colors.dtype == np.uint8
        assert pcd.has_covariances()

def test_color_by_curvature_error_fallback(qapp):
    with mock.patch('pcd_visualizer.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        
        # Use a mock object instead of a pybind PointCloud instance to safely mock estimate_covariances
        pcd = mock.Mock()
        pcd.has_covariances.return_value = False
        pcd.estimate_covariances.side_effect = Exception("Failed estimation")
        widget.current_point_cloud = pcd
        
        pts = np.random.rand(50, 3)
        colors = widget._color_by_curvature(pts)
        
        # Should fallback to uniform color [128, 128, 255]
        assert np.all(colors == [128, 128, 255])
        assert colors.shape == (50, 3)

def test_conditional_sphere_rendering(qapp):
    # Test C1 logic: spheres if points <= 50,000, flat points otherwise
    with mock.patch('pcd_visualizer.PyVistaWidget.setup_visualization'), \
         mock.patch('pcd_visualizer.PyVistaWidget._clear_actors'), \
         mock.patch('pcd_visualizer.PyVistaWidget._apply_color_mode', return_value=None):
        
        widget = PyVistaWidget()
        widget.plotter = mock.Mock()
        widget.current_point_size = 2
        widget.show_normals = False
        
        # Case 1: <= 50000 points
        pcd_small = o3d.geometry.PointCloud()
        pts_small = np.random.rand(10, 3)
        pcd_small.points = o3d.utility.Vector3dVector(pts_small)
        widget.current_point_cloud = pcd_small
        
        widget.render_point_cloud()
        
        args, kwargs = widget.plotter.add_mesh.call_args
        assert kwargs['render_points_as_spheres'] is True
        
        # Case 2: > 50000 points
        pcd_large = o3d.geometry.PointCloud()
        pts_large = np.random.rand(50005, 3)
        pcd_large.points = o3d.utility.Vector3dVector(pts_large)
        widget.current_point_cloud = pcd_large
        
        widget.render_point_cloud()
        args, kwargs = widget.plotter.add_mesh.call_args
        assert kwargs['render_points_as_spheres'] is False
