"""
Menu Manager for PCD Visualizer
Handles all menu creation and actions, including LVX conversion functionality.
"""

from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtGui import QAction
from lvx_converter import LVXConversionDialog


class MenuManager:
    """Manages all menu operations for the main window."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        
    def setup_menus(self):
        """Setup application menus."""
        menubar = self.main_window.menuBar()
        
        # File menu
        self.setup_file_menu(menubar)
        
        # Tools menu
        self.setup_tools_menu(menubar)
        
        # View menu
        self.setup_view_menu(menubar)
        
        # Help menu
        self.setup_help_menu(menubar)
        
    def setup_file_menu(self, menubar):
        """Setup the File menu."""
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open Point Cloud File', self.main_window)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.main_window.load_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Export action
        export_action = QAction('Export...', self.main_window)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.main_window.export_file)
        file_menu.addAction(export_action)
        
        # Screenshot action
        screenshot_action = QAction('Take Screenshot', self.main_window)
        screenshot_action.setShortcut('Ctrl+S')
        screenshot_action.triggered.connect(self.main_window.take_screenshot)
        file_menu.addAction(screenshot_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self.main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.main_window.close)
        file_menu.addAction(exit_action)
        
    def setup_tools_menu(self, menubar):
        """Setup the Tools menu with LVX conversion."""
        tools_menu = menubar.addMenu('Tools')
        
        # LVX to PCD Conversion action
        lvx_convert_action = QAction('Convert LVX to PCD...', self.main_window)
        lvx_convert_action.setShortcut('Ctrl+L')
        lvx_convert_action.triggered.connect(self.open_lvx_conversion_dialog)
        tools_menu.addAction(lvx_convert_action)
        
        tools_menu.addSeparator()
        
        # Additional tools can be added here in the future
        
    def setup_view_menu(self, menubar):
        """Setup the View menu."""
        view_menu = menubar.addMenu('View')
        
        # Fullscreen action
        fullscreen_action = QAction('Fullscreen', self.main_window)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.main_window.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        # Theme toggle action
        theme_action = QAction('Toggle Theme', self.main_window)
        theme_action.setShortcut('Ctrl+T')
        theme_action.triggered.connect(self.main_window.toggle_theme)
        view_menu.addAction(theme_action)
        
    def setup_help_menu(self, menubar):
        """Setup the Help menu."""
        help_menu = menubar.addMenu('Help')
        
        # About action
        about_action = QAction('About', self.main_window)
        about_action.triggered.connect(self.main_window.show_about)
        help_menu.addAction(about_action)
        
    def open_lvx_conversion_dialog(self):
        """Open the LVX to PCD conversion dialog."""
        dialog = LVXConversionDialog(self.main_window)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            # Ask if user wants to load the converted file
            reply = QMessageBox.question(
                self.main_window, "Load Converted File",
                "Would you like to load the converted PCD file for visualization?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get the output path from the dialog
                if hasattr(dialog, 'conversion_thread') and hasattr(dialog.conversion_thread, 'output_path'):
                    self.main_window.control_panel.load_specific_file(dialog.conversion_thread.output_path)
