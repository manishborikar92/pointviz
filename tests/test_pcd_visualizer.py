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

from config import MAX_RECENT_FILES
from main import configure_environment
from core.point_cloud_processor import PointCloudProcessor
from gui.pyvista_widget import PyVistaWidget
from gui.control_panel import ControlPanel
from gui.main_window import PCDVisualizer, ActiveTool
from gui.dialogs import LoadOptionsDialog, AboutDialog
import core.statistics as stats
from core.measurement import MeasurementMode

from PyQt6.QtWidgets import QWidget

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

def test_set_loading_file_updates_labels(qapp):
    
    with mock.patch('gui.control_panel.ControlPanel.init_ui'):
        parent_widget = QWidget()
        panel = ControlPanel(parent_widget)
        
        panel.file_name_label = mock.Mock()
        panel.file_label = mock.Mock()
        
        panel.set_loading_file("some_directory/test_cloud.pcd")
        
        panel.file_name_label.setText.assert_called_once_with("File: test_cloud.pcd")
        panel.file_label.setText.assert_called_once_with("Loading: test_cloud.pcd")
        panel.file_label.setVisible.assert_called_once_with(True)

def test_on_point_cloud_loaded_hides_progress(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('gui.main_window.PCDVisualizer._update_statistics'), \
         mock.patch('gui.pyvista_widget.PyVistaWidget.update_point_cloud'):
        
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.pyvista_widget = mock.Mock()
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(np.random.rand(10, 3))
        
        visualizer._on_point_cloud_loaded(pcd, 10)
        
        visualizer.control_panel.set_progress_visible.assert_called_once_with(False)

def test_show_error_hides_progress_before_messagebox(qapp):
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'), \
         mock.patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_critical:
        
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        
        visualizer._show_error("Test failure message")
        
        visualizer.control_panel.set_progress_visible.assert_called_once_with(False)
        mock_critical.assert_called_once_with(visualizer, "Error", "Test failure message")

def test_active_tool_transitions_and_repeated_toggles(qapp):
    # Tests repeated enable/disable toggles, tool exclusivity, and transactional state
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.point_cloud = o3d.geometry.PointCloud()
        visualizer.point_cloud.points = o3d.utility.Vector3dVector(np.random.rand(10, 3))
        
        # Mock pyvista plotter and widget dependencies
        visualizer.pyvista_widget = mock.Mock()
        visualizer.pyvista_widget.pv_cloud = mock.Mock()
        visualizer.pyvista_widget.clipping_state = mock.Mock()
        visualizer.pyvista_widget.measurement_manager = mock.Mock()
        
        # Successful activations
        visualizer.pyvista_widget.enable_clipping.return_value = True
        visualizer.pyvista_widget.enable_measurement.return_value = True
        
        # 1. Enable clipping
        assert visualizer.set_active_tool(ActiveTool.CLIPPING)
        assert visualizer.active_tool == ActiveTool.CLIPPING
        visualizer.pyvista_widget.enable_clipping.assert_called_once()
        
        # 2. Repeated enable clipping (should be idempotent)
        visualizer.pyvista_widget.enable_clipping.reset_mock()
        assert visualizer.set_active_tool(ActiveTool.CLIPPING)
        visualizer.pyvista_widget.enable_clipping.assert_not_called()
        
        # 3. Toggle to measuring (clipping should deactivate first)
        assert visualizer.set_active_tool(ActiveTool.MEASURING)
        assert visualizer.active_tool == ActiveTool.MEASURING
        visualizer.pyvista_widget.disable_clipping.assert_called_once()
        visualizer.pyvista_widget.enable_measurement.assert_called_once()
        
        # 4. Deactivate (NONE)
        assert visualizer.set_active_tool(ActiveTool.NONE)
        assert visualizer.active_tool == ActiveTool.NONE
        visualizer.pyvista_widget.disable_measurement.assert_called_once()

def test_measurement_activation_failure_rollback(qapp):
    # Tests that if enabling measurement fails, the UI falls back to idle immediately
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.point_cloud = o3d.geometry.PointCloud()
        visualizer.pyvista_widget = mock.Mock()
        visualizer.pyvista_widget.enable_measurement.return_value = False
        
        # Attempt toggle
        visualizer._on_measure_toggled(True)
        
        # Should reset control panel and active tool to NONE
        assert visualizer.active_tool == ActiveTool.NONE
        visualizer.control_panel.set_measure_checked.assert_called_with(False)

def test_measurement_click_miss_handling(qapp):
    # Tests that click misses trigger the measurement_failed signal and notify the UI
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        widget.point_cloud_actor = mock.Mock()
        
        # Mock picker returning background click (where actor is None, indicating a miss)
        mock_picker = mock.Mock()
        mock_picker.GetActor.return_value = None
        mock_picker.GetDataSet.return_value = None
        mock_picker.GetPointId.return_value = -1
        
        widget.measurement_mode_changed = mock.Mock()
        widget.measurement_failed = mock.Mock()
        widget.measurement_manager = mock.Mock()
        widget.measurement_manager.mode = MeasurementMode.PICKING_FIRST
        
        widget._on_point_picked([1, 1, 1], picker=mock_picker)
        
        # Click miss should emit message, emit failed signal, and NOT progress state
        widget.measurement_mode_changed.emit.assert_called_with(
            "Click miss - click directly on the point cloud (ESC to cancel)"
        )
        widget.measurement_failed.emit.assert_called_once()
        widget.measurement_manager.set_first_point.assert_not_called()

def test_measurement_failed_signal_deactivates_tool(qapp):
    # Tests that measurement_failed signal transitions MainWindow to ActiveTool.NONE
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.point_cloud = o3d.geometry.PointCloud()
        
        with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
            widget = PyVistaWidget()
            visualizer.pyvista_widget = widget
            
            # Connect the signal in MainWindow
            visualizer.pyvista_widget.measurement_failed.connect(visualizer._on_measurement_failed)
            
            # Set active tool to MEASURING
            visualizer.active_tool = ActiveTool.MEASURING
            
            # Emit failed signal
            visualizer.pyvista_widget.measurement_failed.emit()
            
            # Active tool should roll back to NONE
            assert visualizer.active_tool == ActiveTool.NONE
            visualizer.control_panel.set_measure_checked.assert_called_with(False)

def test_measurement_state_recovery_on_deactivation_or_esc(qapp):
    # Tests that ESC or deactivation successfully resets the measurement mode/manager
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer.pyvista_widget = mock.Mock()
        visualizer.pyvista_widget.enable_measurement.return_value = True
        
        # 1. Activate measurement
        visualizer.set_active_tool(ActiveTool.MEASURING)
        assert visualizer.active_tool == ActiveTool.MEASURING
        
        # 2. Deactivate via ESC (ActiveTool.NONE)
        visualizer.set_active_tool(ActiveTool.NONE)
        assert visualizer.active_tool == ActiveTool.NONE
        visualizer.pyvista_widget.disable_measurement.assert_called_once()

def test_clipping_activation_deactivation(qapp):
    # Tests that enabling/disabling clipping correctly updates state and plotter
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        widget.plotter = mock.Mock()
        widget.point_cloud_actor = mock.Mock()
        widget.current_point_cloud = mock.Mock()
        widget.pv_cloud = mock.Mock()
        
        # Setup original points and bounds
        widget._original_points = np.random.rand(5, 3)
        widget._original_bounds = (0, 1, 0, 1, 0, 1)
        
        # 1. Enable clipping
        assert widget.enable_clipping()
        assert widget.clipping_state.is_active
        widget.plotter.add_box_widget.assert_called_once()
        
        # 2. Disable clipping
        widget.disable_clipping()
        assert not widget.clipping_state.is_active
        widget.plotter.clear_box_widgets.assert_called()

def test_clipping_widget_stability(qapp):
    # Tests that clipping callback does not recreate or resize the box widget
    with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
        widget = PyVistaWidget()
        widget.plotter = mock.Mock()
        widget.point_cloud_actor = mock.Mock()
        widget.current_point_cloud = mock.Mock()
        widget.pv_cloud = mock.Mock()
        
        # Setup original points and bounds
        widget._original_points = np.random.rand(5, 3)
        widget._original_bounds = (0, 1, 0, 1, 0, 1)
        
        # Enable clipping first (creates box widget once)
        widget.enable_clipping()
        widget.plotter.add_box_widget.assert_called_once()
        
        # Reset mock call count to verify no recreation in callback
        widget.plotter.reset_mock()
        
        # Create mock box polydata representing user dragging the box widget
        box_poly = mock.Mock()
        box_poly.bounds = (0.1, 0.9, 0.1, 0.9, 0.1, 0.9)
        
        # Execute the callback
        widget._on_box_clip(box_poly)
        
        # Verify that box widget is NOT cleared or re-added during interaction
        widget.plotter.clear_box_widgets.assert_not_called()
        widget.plotter.add_box_widget.assert_not_called()

def test_crop_clicked_direct(qapp):
    # Tests that _on_crop_clicked crops directly in-memory without a dialog,
    # mutating working_point_cloud while leaving original_point_cloud intact.
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer._update_statistics = mock.Mock()
        visualizer.current_file_path = "test.pcd"
        
        # Mock point cloud with 10 points
        pts = np.zeros((10, 3))
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pts)
        
        visualizer.original_point_cloud = pcd
        visualizer.working_point_cloud = o3d.geometry.PointCloud(pcd)
        visualizer.original_point_count = 10
        
        # Setup pyvista widget and clip mask (select first 3 points)
        visualizer.pyvista_widget = mock.Mock()
        visualizer.pyvista_widget._clip_mask = np.array([True, True, True, False, False, False, False, False, False, False])
        
        # Execute crop
        visualizer._on_crop_clicked()
        
        # original_point_cloud MUST remain untouched (10 points)
        assert len(visualizer.original_point_cloud.points) == 10
        # working_point_cloud MUST be cropped (3 points)
        assert len(visualizer.working_point_cloud.points) == 3
        
        visualizer.pyvista_widget.update_point_cloud.assert_called_once_with(
            visualizer.working_point_cloud, force_refresh=True, reset_camera=False
        )
        assert visualizer.active_tool == ActiveTool.NONE
        visualizer._update_statistics.assert_called_once()


def test_reset_workspace(qapp):
    # Tests that _on_reset_workspace restores working_point_cloud from original_point_cloud
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer._update_statistics = mock.Mock()
        visualizer.current_file_path = "test.pcd"
        
        # Setup original point cloud (10 points) and cropped working point cloud (3 points)
        pts_10 = np.zeros((10, 3))
        pcd_orig = o3d.geometry.PointCloud()
        pcd_orig.points = o3d.utility.Vector3dVector(pts_10)
        
        pts_3 = np.zeros((3, 3))
        pcd_work = o3d.geometry.PointCloud()
        pcd_work.points = o3d.utility.Vector3dVector(pts_3)
        
        visualizer.original_point_cloud = pcd_orig
        visualizer.working_point_cloud = pcd_work
        visualizer.original_point_count = 3
        
        visualizer.pyvista_widget = mock.Mock()
        
        # Execute Reset Workspace
        visualizer._on_reset_workspace()
        
        # working_point_cloud MUST be restored to original (10 points)
        assert len(visualizer.working_point_cloud.points) == 10
        assert len(visualizer.original_point_cloud.points) == 10
        
        visualizer.pyvista_widget.update_point_cloud.assert_called_once_with(
            visualizer.working_point_cloud, force_refresh=True, reset_camera=False
        )
        assert visualizer.active_tool == ActiveTool.NONE
        visualizer._update_statistics.assert_called_once()


def test_crop_crop_crop_reset_cycle(qapp):
    # Tests that repeated Crop -> Crop -> Crop -> Reset correctly updates all arrays,
    # KD-trees, clipping state, and measurement state without leaving stale references in memory.
    with mock.patch('gui.main_window.PCDVisualizer.init_ui'), \
         mock.patch('gui.main_window.PCDVisualizer.apply_theme'):
        visualizer = PCDVisualizer()
        visualizer.control_panel = mock.Mock()
        visualizer.status_bar = mock.Mock()
        visualizer._update_statistics = mock.Mock()
        visualizer.current_file_path = "test.pcd"

        # Initialize mock pyvista widget (we want real PyVistaWidget to test its state transitions)
        with mock.patch('gui.pyvista_widget.PyVistaWidget.setup_visualization'):
            widget = PyVistaWidget()
            widget.plotter = mock.Mock()
            visualizer.pyvista_widget = widget

            # Build a dataset with 10 points, colors, and normals
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(np.arange(30).reshape(10, 3).astype(np.float64))
            pcd.colors = o3d.utility.Vector3dVector(np.random.rand(10, 3))
            pcd.estimate_normals() # estimates dummy normals

            # Load it into visualizer
            visualizer._on_point_loaded = mock.Mock() # mock unused helper
            visualizer._on_point_cloud_loaded(pcd, 10)

            # Check initial state
            assert len(visualizer.original_point_cloud.points) == 10
            assert len(visualizer.working_point_cloud.points) == 10
            assert len(widget._original_points) == 10
            assert widget._original_colors is not None
            assert len(widget._original_colors) == 10
            assert widget.measurement_manager._points_array is not None
            assert len(widget.measurement_manager._points_array) == 10

            # First Crop (keep points 0..7)
            widget._clip_mask = np.array([True]*8 + [False]*2)
            visualizer._on_crop_clicked()
            assert len(visualizer.working_point_cloud.points) == 8
            assert len(widget._original_points) == 8
            assert len(widget._original_colors) == 8
            assert len(widget.measurement_manager._points_array) == 8
            assert widget._clip_mask is None

            # Second Crop (keep points 0..5 of the current working cloud)
            # Re-simulate clipping
            widget._clip_mask = np.array([True]*6 + [False]*2)
            visualizer._on_crop_clicked()
            assert len(visualizer.working_point_cloud.points) == 6
            assert len(widget._original_points) == 6
            assert len(widget._original_colors) == 6
            assert len(widget.measurement_manager._points_array) == 6

            # Third Crop (keep points 0..3 of the current working cloud)
            widget._clip_mask = np.array([True]*4 + [False]*2)
            visualizer._on_crop_clicked()
            assert len(visualizer.working_point_cloud.points) == 4
            assert len(widget._original_points) == 4
            assert len(widget._original_colors) == 4
            assert len(widget.measurement_manager._points_array) == 4

            # Verify original_point_cloud remains 10 points
            assert len(visualizer.original_point_cloud.points) == 10

            # Rebuild some mock measurements on the active working cloud
            widget.measurement_manager.activate()
            # Snap to a point
            _, coord_a = widget.measurement_manager.snap_to_point(widget.measurement_manager._points_array[0])
            widget.measurement_manager.set_first_point(coord_a)
            _, coord_b = widget.measurement_manager.snap_to_point(widget.measurement_manager._points_array[1])
            widget.measurement_manager.create_measurement(coord_a, coord_b)
            assert widget.measurement_manager.has_measurements

            # Reset Workspace
            visualizer._on_reset_workspace()

            # Verify working point cloud is fully restored to 10 points
            assert len(visualizer.working_point_cloud.points) == 10
            # original_points, colors, bounds, and KD-tree in widget are fully restored
            assert len(widget._original_points) == 10
            assert len(widget._original_colors) == 10
            assert len(widget.measurement_manager._points_array) == 10
            
            # Verify measurements are completely cleared on reset
            assert not widget.measurement_manager.has_measurements
            # Verify clipping is deactivated
            assert not widget.clipping_state.is_active
            assert widget._clip_mask is None


