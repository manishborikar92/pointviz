"""
Point Cloud Processing Thread
Handles asynchronous point cloud loading and processing operations.
"""

import open3d as o3d
from PyQt6.QtCore import QThread, pyqtSignal


class PointCloudProcessor(QThread):
    """Thread for processing point cloud operations."""
    
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    loaded = pyqtSignal(object)
    
    def __init__(self, file_path, operation="load"):
        super().__init__()
        self.file_path = file_path
        self.operation = operation
        self.point_cloud = None
        
    def run(self):
        """Execute the point cloud processing operation."""
        try:
            self.progress.emit(10)
            
            if self.operation == "load":
                self.load_point_cloud()
            else:
                raise ValueError(f"Unknown operation: {self.operation}")
                
        except Exception as e:
            self.error.emit(f"Error processing point cloud: {str(e)}")
        finally:
            self.finished.emit()
    
    def load_point_cloud(self):
        """Load point cloud from file."""
        # Validate file format
        if not self.file_path.lower().endswith(('.pcd', '.ply')):
            raise ValueError("Unsupported file format. Supported formats: .pcd, .ply")
        
        # Load the point cloud
        self.point_cloud = o3d.io.read_point_cloud(self.file_path)
        
        if len(self.point_cloud.points) == 0:
            raise ValueError("No points found in the file")
        
        self.progress.emit(30)
        
        # Estimate normals if not present
        if not self.point_cloud.has_normals():
            self.point_cloud.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(
                    radius=0.1, max_nn=30))
        
        self.progress.emit(60)
        
        # Center the point cloud
        center = self.point_cloud.get_center()
        self.point_cloud.translate(-center)
        
        self.progress.emit(90)
        
        # Emit the loaded point cloud
        self.loaded.emit(self.point_cloud)
        
        self.progress.emit(100)
