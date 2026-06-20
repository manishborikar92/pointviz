from pathlib import Path
import open3d as o3d
from PyQt6.QtCore import QThread, pyqtSignal
from pointviz.logger import logger

class PointCloudProcessor(QThread):
    """Thread for processing point cloud operations with downsampling and export."""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    # Emits the processed (possibly downsampled) point cloud and the original point count
    loaded = pyqtSignal(object, int)
    exported = pyqtSignal(str)  # Emitted on successful export
    
    def __init__(self, file_path: str, load_options: dict = None, operation: str = "load", point_cloud = None):
        super().__init__()
        self.file_path = file_path
        self.operation = operation
        self.load_options = load_options or {}
        self.point_cloud = point_cloud
        
    def run(self):
        logger.info(f"Starting point cloud operation '{self.operation}' on: {self.file_path}")
        try:
            self.progress.emit(10)
            if self.isInterruptionRequested():
                logger.info("Operation interrupted at step 1")
                return
            
            if self.operation == "load":
                # Load the full point cloud
                file_ext = Path(self.file_path).suffix.lower()
                
                if file_ext in ['.pcd', '.ply']:
                    logger.debug(f"Reading point cloud file: {self.file_path}")
                    pcd = o3d.io.read_point_cloud(self.file_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: .pcd, .ply")
                
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted after file read")
                    return
                
                if len(pcd.points) == 0:
                    raise ValueError("No points found in the file")
                
                original_point_count = len(pcd.points)
                logger.info(f"Successfully read {original_point_count:,} points.")
                self.progress.emit(30)
                
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted before downsampling")
                    return
                
                # Apply downsampling based on options
                method = self.load_options.get("method", "none")
                value = self.load_options.get("value")
                
                processed_pcd = pcd
                if method == "voxel" and value > 0:
                    logger.info(f"Applying voxel downsampling with voxel_size={value}")
                    processed_pcd = pcd.voxel_down_sample(voxel_size=value)
                    logger.info(f"Downsampled point count: {len(processed_pcd.points):,}")
                
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted after downsampling")
                    return
                self.progress.emit(60)
                
                # Center the point cloud
                center = processed_pcd.get_center()
                logger.debug(f"Translating point cloud to center: {center}")
                processed_pcd.translate(-center)
                
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted after translation")
                    return
                self.progress.emit(90)
                
                # Emit the processed point cloud and original point count
                self.loaded.emit(processed_pcd, original_point_count)
                self.progress.emit(100)
                logger.info("Point cloud load operation completed successfully")
                
            elif self.operation == "export":
                if self.point_cloud is None:
                    raise ValueError("No point cloud data to export")
                self.progress.emit(30)
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted before export write")
                    return
                # Write point cloud to file
                logger.info(f"Writing point cloud to file: {self.file_path}")
                o3d.io.write_point_cloud(self.file_path, self.point_cloud)
                self.progress.emit(80)
                if self.isInterruptionRequested():
                    logger.info("Operation interrupted after export write")
                    return
                self.progress.emit(100)
                self.exported.emit(self.file_path)
                logger.info("Point cloud export operation completed successfully")
                
        except Exception as e:
            err_msg = f"Error during point cloud operation '{self.operation}': {str(e)}"
            logger.error(err_msg, exc_info=True)
            self.error.emit(err_msg)
        
        finally:
            self.finished.emit()
