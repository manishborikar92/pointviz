import os
import sys
from pathlib import Path
from unittest import mock
import numpy as np
import open3d as o3d
import pytest
import pyvista as pv
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

# Add workspace to path to import flat packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import configure_environment
from core.point_cloud_processor import PointCloudProcessor
from gui.pyvista_widget import PyVistaWidget
from gui.main_window import PCDVisualizer
from gui.dialogs import LoadOptionsDialog, AboutDialog
import core.statistics as stats

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
        
        with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
             mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
            visualizer = PCDVisualizer()
            pref = visualizer._get_system_theme_preference()
            assert pref is True

def test_get_system_theme_preference_exception(qapp):
    with mock.patch.object(QApplication, 'instance') as mock_app:
        mock_app.return_value.palette.side_effect = Exception("Palette error")
        with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
             mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
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
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
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
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
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
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'), \
         mock.patch('gui.pyvista_widget.PyVistaWidget._clear_actors'), \
         mock.patch('gui.pyvista_widget.PyVistaWidget._apply_color_mode', return_value=None):
        
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

def test_deferred_normals_loading():
    # Verify that PointCloudProcessor does not estimate normals on load
    processor = PointCloudProcessor("dummy.pcd", {"method": "none", "value": None})
    pcd = o3d.geometry.PointCloud()
    pts = np.random.rand(10, 3)
    pcd.points = o3d.utility.Vector3dVector(pts)
    
    with mock.patch('open3d.io.read_point_cloud', return_value=pcd) as mock_read, \
         mock.patch('open3d.geometry.PointCloud.estimate_normals') as mock_estimate:
        
        processor.run()
        
        mock_read.assert_called_once()
        mock_estimate.assert_not_called()

def test_on_demand_normals_estimation(qapp):
    # Verify that normals are estimated on-demand when requested
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        pcd = o3d.geometry.PointCloud()
        pts = np.random.rand(10, 3)
        pcd.points = o3d.utility.Vector3dVector(pts)
        widget.current_point_cloud = pcd
        
        assert not pcd.has_normals()
        
        # Trigger normal color mode, which should trigger on-demand normal estimation
        colors = widget._color_by_normal()
        
        assert pcd.has_normals()
        assert colors.shape == (10, 3)

def test_color_cache(qapp):
    # Verify color cache lookup, storage, and invalidation
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        pcd = o3d.geometry.PointCloud()
        pts = np.random.rand(10, 3)
        pcd.points = o3d.utility.Vector3dVector(pts)
        widget.current_point_cloud = pcd
        
        # Initial state: cache is empty
        assert len(widget.color_cache) == 0
        
        # Color by height
        widget.current_color_mode = "Height"
        colors_1 = widget._apply_color_mode(pts)
        
        assert "Height" in widget.color_cache
        assert np.array_equal(widget.color_cache["Height"], colors_1)
        
        # Call it again; should return cached version
        colors_2 = widget._apply_color_mode(pts)
        assert colors_2 is colors_1
        
        # Change point cloud; cache should be cleared
        pcd2 = o3d.geometry.PointCloud()
        pcd2.points = o3d.utility.Vector3dVector(np.random.rand(10, 3))
        
        widget.update_point_cloud(pcd2)
        assert len(widget.color_cache) == 0

def test_inplace_scalar_update(qapp):
    # Verify in-place scalar updates in update_color_mode
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        widget.plotter = mock.Mock()
        widget.point_cloud_actor = mock.Mock()
        
        pcd = o3d.geometry.PointCloud()
        pts = np.random.rand(10, 3)
        pcd.points = o3d.utility.Vector3dVector(pts)
        widget.current_point_cloud = pcd
        
        # Simulate pv_cloud reference
        widget.pv_cloud = pv.PolyData(pts)
        
        # Initial color mode
        widget.current_color_mode = "Original"
        
        # Change color mode
        widget.update_color_mode("Height")
        
        # Check that plotter.render was called (meaning in-place update occurred)
        widget.plotter.render.assert_called_once()
        assert "colors" in widget.pv_cloud.point_data

def test_adaptive_point_size(qapp):
    # Verify adaptive point size selection on load
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('gui.main_window.PCDVisualizer._update_statistics'), \
         mock.patch('gui.pyvista_widget.PyVistaWidget.update_point_cloud'):
        
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.pyvista_widget = mock.Mock()
        
        # Case 1: Small point cloud (<5000 points)
        pcd1 = o3d.geometry.PointCloud()
        pcd1.points = o3d.utility.Vector3dVector(np.random.rand(100, 3))
        visualizer._on_point_cloud_loaded(pcd1, 100)
        visualizer.control_panel.set_point_size_value.assert_called_with(5)
        
        # Case 2: Medium-large point cloud (>100,000 points)
        pcd2 = o3d.geometry.PointCloud()
        pcd2.points = o3d.utility.Vector3dVector(np.random.rand(120000, 3))
        visualizer._on_point_cloud_loaded(pcd2, 120000)
        visualizer.control_panel.set_point_size_value.assert_called_with(1)

def test_background_export(qapp):
    # Verify background threaded export initiates correctly
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("test_export.pcd", "PCD Files (*.pcd)")):
        
        visualizer = PCDVisualizer()
        visualizer.point_cloud = o3d.geometry.PointCloud()
        visualizer.point_cloud.points = o3d.utility.Vector3dVector(np.random.rand(10, 3))
        
        with mock.patch.object(PointCloudProcessor, 'start') as mock_start:
            visualizer.export_file()
            
            assert visualizer.export_thread is not None
            assert visualizer.export_thread.operation == "export"
            assert visualizer.export_thread.file_path == "test_export.pcd"
            mock_start.assert_called_once()
            
            # Clean up
            visualizer._on_export_finished()

# --- Unit Tests for extracted statistics computations ---

def test_statistics_calculate_volume():
    # Bounding box calculation on simple points
    points = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 2.0, 3.0]
    ])
    vol = stats.calculate_volume(points)
    assert vol == 6.0  # 1 * 2 * 3
    
    empty_points = np.empty((0, 3))
    assert stats.calculate_volume(empty_points) == 0.0

def test_statistics_calculate_density():
    points = np.random.rand(10, 3)
    assert stats.calculate_density(points, 2.0) == 5.0
    assert stats.calculate_density(points, 0.0) == 0.0

def test_statistics_compute_centroid():
    points = np.array([
        [1.0, 1.0, 1.0],
        [3.0, 3.0, 3.0]
    ])
    centroid = stats.compute_centroid(points)
    assert np.allclose(centroid, [2.0, 2.0, 2.0])
    
    empty_points = np.empty((0, 3))
    assert np.allclose(stats.compute_centroid(empty_points), [0.0, 0.0, 0.0])

def test_statistics_compute_ranges():
    points = np.array([
        [-1.0, 5.0, 2.0],
        [3.0, -2.0, 10.0]
    ])
    ranges = stats.compute_ranges(points)
    assert ranges["x"] == (-1.0, 3.0)
    assert ranges["y"] == (-2.0, 5.0)
    assert ranges["z"] == (2.0, 10.0)

def test_statistics_compute_distance_stats():
    points = np.array([
        [0.0, 0.0, 0.0],
        [0.0, 3.0, 0.0],
        [0.0, -3.0, 0.0]
    ])
    centroid = np.array([0.0, 0.0, 0.0])
    dist_stats = stats.compute_distance_stats(points, centroid)
    assert dist_stats["min"] == 0.0
    assert dist_stats["max"] == 3.0
    assert dist_stats["mean"] == 2.0  # (0 + 3 + 3) / 3

def test_statistics_compute_color_stats():
    colors = np.array([
        [0.1, 0.2, 0.3],
        [0.5, 0.6, 0.7]
    ])
    color_stats = stats.compute_color_stats(colors)
    assert color_stats["r"]["mean"] == 0.3
    assert color_stats["g"]["mean"] == 0.4
    assert color_stats["b"]["mean"] == 0.5

def test_add_to_recent_files(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        
        # Mock settings
        mock_settings = mock.Mock()
        stored_recent = []
        def get_val(key, default=None):
            return stored_recent
        def set_val(key, val):
            nonlocal stored_recent
            stored_recent = val
        mock_settings.value.side_effect = get_val
        mock_settings.setValue.side_effect = set_val
        visualizer.settings = mock_settings
        
        path1 = str(Path("test1.pcd").resolve())
        path2 = str(Path("test2.pcd").resolve())
        
        # Test adding a file
        visualizer._add_to_recent_files("test1.pcd")
        assert path1 in stored_recent
        assert stored_recent[0] == path1
        
        # Test moving to top and removing duplicates
        visualizer._add_to_recent_files("test2.pcd")
        visualizer._add_to_recent_files("test1.pcd")
        assert len(stored_recent) == 2
        assert stored_recent[0] == path1
        
        # Test max recent limit
        from config import MAX_RECENT_FILES
        for i in range(MAX_RECENT_FILES + 5):
            visualizer._add_to_recent_files(f"limit_{i}.pcd")
        assert len(stored_recent) == MAX_RECENT_FILES
        expected_top = str(Path(f"limit_{MAX_RECENT_FILES + 4}.pcd").resolve())
        assert stored_recent[0] == expected_top

def test_update_recent_files_menu_empty(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        
        # Mock settings to return empty
        mock_settings = mock.Mock()
        mock_settings.value.return_value = []
        visualizer.settings = mock_settings
        
        # Mock QMenu
        mock_menu = mock.Mock()
        mock_action = mock.Mock()
        mock_menu.addAction.return_value = mock_action
        visualizer.recent_menu = mock_menu
        
        visualizer.update_recent_files_menu()
        
        mock_menu.clear.assert_called_once()
        mock_menu.addAction.assert_called_once_with("No Recent Files")
        mock_action.setEnabled.assert_called_once_with(False)

def test_update_recent_files_menu_with_files(qapp, tmp_path):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        
        # Create temp files that exist
        f1 = tmp_path / "valid1.pcd"
        f1.touch()
        f2 = tmp_path / "valid2.ply"
        f2.touch()
        
        # Mock settings to return these files (and one non-existent file)
        mock_settings = mock.Mock()
        mock_settings.value.return_value = [str(f1), "nonexistent.pcd", str(f2)]
        visualizer.settings = mock_settings
        
        # Mock QMenu
        mock_menu = mock.Mock()
        visualizer.recent_menu = mock_menu
        
        visualizer.update_recent_files_menu()
        
        # Verify clear was called, settings were updated to remove nonexistent
        mock_menu.clear.assert_called_once()
        mock_settings.setValue.assert_called_once_with("recentFiles", [str(f1.resolve()), str(f2.resolve())])
        
        # Verify correct number of actions added
        assert mock_menu.addAction.call_count == 2
        mock_menu.addAction.assert_any_call("valid1.pcd")
        mock_menu.addAction.assert_any_call("valid2.ply")

def test_drag_enter_event(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        
        # Mock drag event
        mock_event = mock.Mock()
        mock_mime = mock.Mock()
        mock_url1 = mock.Mock()
        mock_url1.toLocalFile.return_value = "file.pcd"
        mock_mime.hasUrls.return_value = True
        mock_mime.urls.return_value = [mock_url1]
        mock_event.mimeData.return_value = mock_mime
        
        # Test PCD
        visualizer.dragEnterEvent(mock_event)
        mock_event.acceptProposedAction.assert_called_once()
        
        # Test PLY
        mock_event.reset_mock()
        mock_url1.toLocalFile.return_value = "file.PLY"
        visualizer.dragEnterEvent(mock_event)
        mock_event.acceptProposedAction.assert_called_once()
        
        # Test invalid extension
        mock_event.reset_mock()
        mock_url1.toLocalFile.return_value = "file.txt"
        visualizer.dragEnterEvent(mock_event)
        mock_event.acceptProposedAction.assert_not_called()
        mock_event.ignore.assert_called_once()

def test_drop_event(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('gui.main_window.PCDVisualizer._load_specific_file') as mock_load:
        visualizer = PCDVisualizer()
        
        # Mock drop event
        mock_event = mock.Mock()
        mock_mime = mock.Mock()
        mock_url = mock.Mock()
        mock_url.toLocalFile.return_value = "dropped_file.pcd"
        mock_mime.urls.return_value = [mock_url]
        mock_event.mimeData.return_value = mock_mime
        
        visualizer.dropEvent(mock_event)
        
        mock_load.assert_called_once_with("dropped_file.pcd")
        mock_event.acceptProposedAction.assert_called_once()

def test_on_point_cloud_loaded_updates_title_and_label(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('gui.main_window.PCDVisualizer._update_statistics'), \
         mock.patch('gui.pyvista_widget.PyVistaWidget.update_point_cloud'), \
         mock.patch('gui.main_window.PCDVisualizer.setWindowTitle') as mock_set_title:
        
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.pyvista_widget = mock.Mock()
        
        # Setup mock thread
        mock_thread = mock.Mock()
        mock_thread.file_path = str(Path("some_directory/test_cloud.pcd"))
        visualizer.processor_thread = mock_thread
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.random.rand(10, 3))
        
        visualizer._on_point_cloud_loaded(pcd, 10)
        
        mock_set_title.assert_called_once_with("test_cloud.pcd - PCD Visualizer")
        visualizer.control_panel.update_file_info.assert_called_once_with(
            file_path=str(Path("some_directory/test_cloud.pcd")),
            displayed_points=10,
            original_points=10
        )

def test_load_concurrency_guard(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        
        visualizer = PCDVisualizer()
        
        # Setup running thread
        mock_thread = mock.Mock()
        mock_thread.isRunning.return_value = True
        visualizer.processor_thread = mock_thread
        
        # Attempt to load a file
        visualizer._load_specific_file("nonexistent.pcd")
        
        # Warning should be displayed
        mock_warning.assert_called_once()
        assert "is already loading" in mock_warning.call_args[0][2]

def test_export_concurrency_guard(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
        
        visualizer = PCDVisualizer()
        visualizer.point_cloud = mock.Mock()
        
        # Setup running export thread
        mock_export_thread = mock.Mock()
        mock_export_thread.isRunning.return_value = True
        visualizer.export_thread = mock_export_thread
        
        visualizer.export_file()
        
        mock_warning.assert_called_once()
        assert "export is already in progress" in mock_warning.call_args[0][2]

def test_invalid_file_removes_from_recent(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('gui.main_window.PCDVisualizer._remove_from_recent_files') as mock_remove, \
         mock.patch('PyQt6.QtWidgets.QMessageBox.warning'):
        
        visualizer = PCDVisualizer()
        
        # Try loading non-existent file
        visualizer._load_specific_file("completely_missing.pcd")
        
        mock_remove.assert_called_once_with("completely_missing.pcd")
