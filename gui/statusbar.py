"""
Status Bar Manager for PCD Visualizer
Handles status bar setup and message management.
"""

from PyQt6.QtWidgets import QStatusBar


class StatusBarManager:
    """Manages the application status bar."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.status_bar = None
        
    def setup_statusbar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.main_window.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a point cloud file to begin")
        
    def set_message(self, message):
        """Set status bar message."""
        if self.status_bar:
            self.status_bar.showMessage(message)
            
    def clear_message(self):
        """Clear status bar message."""
        if self.status_bar:
            self.status_bar.clearMessage()
