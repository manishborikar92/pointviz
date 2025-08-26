"""
Theme Manager for PCD Visualizer
Handles dark/light theme switching and styling.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


class ThemeManager:
    """Manages application themes and styling."""
    
    def __init__(self):
        self.is_dark_mode = False
        
    def toggle_theme(self, main_window):
        """Toggle between dark and light themes."""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(main_window, self.is_dark_mode)
        
    def apply_theme(self, main_window, is_dark):
        """Apply dark or light theme to the application."""
        app = QApplication.instance()
        self.is_dark_mode = is_dark
        
        if is_dark:
            self.apply_dark_theme(app, main_window)
        else:
            self.apply_light_theme(app, main_window)
        
        # Force update
        main_window.update()
        app.processEvents()
        
    def apply_dark_theme(self, app, main_window):
        """Apply dark theme."""
        dark_palette = QPalette()
        
        # Set colors for all groups
        for group in [QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled]:
            # Window colors
            dark_palette.setColor(group, QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(group, QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            
            # Base colors
            dark_palette.setColor(group, QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(group, QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            
            # Text colors
            dark_palette.setColor(group, QPalette.ColorRole.Text, QColor(255, 255, 255))
            dark_palette.setColor(group, QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            
            # Button colors
            dark_palette.setColor(group, QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(group, QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            
            # Highlight colors
            dark_palette.setColor(group, QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(group, QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
            
            # Tooltip colors
            dark_palette.setColor(group, QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
            dark_palette.setColor(group, QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        
        # Disabled colors
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        
        app.setPalette(dark_palette)
        main_window.setPalette(dark_palette)
        
        # Apply dark stylesheet
        main_window.setStyleSheet(self.get_dark_stylesheet())
        
    def apply_light_theme(self, app, main_window):
        """Apply light theme."""
        # Restore default palette
        app.setPalette(app.style().standardPalette())
        main_window.setPalette(app.style().standardPalette())
        
        # Apply light stylesheet
        main_window.setStyleSheet(self.get_light_stylesheet())
        
    def get_dark_stylesheet(self):
        """Get dark theme stylesheet."""
        return """
            QMainWindow {
                background-color: #353535;
                color: #ffffff;
            }
            QWidget {
                background-color: #353535;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #5a5a5a;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 5px;
                background-color: #353535;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QPushButton {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #565656;
            }
            QPushButton:pressed {
                background-color: #2a82da;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #7f7f7f;
            }
            QLabel {
                color: #ffffff;
                background: transparent;
            }
            QSlider::groove:horizontal {
                border: 1px solid #5a5a5a;
                height: 8px;
                background: #353535;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2a82da;
                border: 1px solid #5a5a5a;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QComboBox {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QComboBox::drop-down {
                border-left: 1px solid #5a5a5a;
                width: 15px;
                background-color: #454545;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-left: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #454545;
                color: #ffffff;
                selection-background-color: #2a82da;
                border: 1px solid #5a5a5a;
            }
            QCheckBox {
                color: #ffffff;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #454545;
                border: 1px solid #5a5a5a;
            }
            QCheckBox::indicator:checked {
                background-color: #2a82da;
                border: 1px solid #5a5a5a;
            }
            QTabWidget::pane {
                border: 1px solid #5a5a5a;
                background-color: #353535;
            }
            QTabBar::tab {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                padding: 8px 16px;
                margin-right: 2px;
                color: #ffffff;
            }
            QTabBar::tab:selected {
                background-color: #2a82da;
                border-bottom: 1px solid #2a82da;
            }
            QScrollArea {
                border: none;
                background-color: #353535;
            }
            QProgressBar {
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                text-align: center;
                background-color: #353535;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                border-radius: 2px;
            }
            QMenuBar {
                background-color: #353535;
                color: #ffffff;
                border-bottom: 1px solid #5a5a5a;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #2a82da;
            }
            QMenu {
                background-color: #454545;
                color: #ffffff;
                border: 1px solid #5a5a5a;
            }
            QMenu::item {
                padding: 8px 32px 8px 16px;
            }
            QMenu::item:selected {
                background-color: #2a82da;
            }
            QStatusBar {
                background-color: #353535;
                color: #ffffff;
                border-top: 1px solid #5a5a5a;
            }
            QLineEdit {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #2a82da;
            }
            QLineEdit:disabled {
                background-color: #2a2a2a;
                color: #7f7f7f;
            }
            QRadioButton {
                color: #ffffff;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #454545;
                border: 1px solid #5a5a5a;
            }
            QRadioButton::indicator:checked {
                background-color: #2a82da;
                border: 1px solid #5a5a5a;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #2a82da;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background-color: #565656;
                border: none;
                border-left: 1px solid #5a5a5a;
                border-bottom: 1px solid #5a5a5a;
                width: 16px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #565656;
                border: none;
                border-left: 1px solid #5a5a5a;
                width: 16px;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-bottom: 3px solid #ffffff;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #ffffff;
                width: 0px;
                height: 0px;
            }
            QTextEdit {
                background-color: #454545;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 5px;
                color: #ffffff;
            }
            QTextEdit:focus {
                border: 2px solid #2a82da;
            }
            QDialog {
                background-color: #353535;
                color: #ffffff;
            }
            QMessageBox {
                background-color: #353535;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
            }
            QFileDialog {
                background-color: #353535;
                color: #ffffff;
            }
            QTableWidget {
                background-color: #454545;
                alternate-background-color: #353535;
                border: 1px solid #5a5a5a;
                color: #ffffff;
                gridline-color: #5a5a5a;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2a82da;
            }
            QHeaderView::section {
                background-color: #353535;
                color: #ffffff;
                border: 1px solid #5a5a5a;
                padding: 4px;
            }
            QSplitter::handle {
                background-color: #5a5a5a;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """
        
    def get_light_stylesheet(self):
        """Get light theme stylesheet."""
        return """
            QMainWindow {
                background-color: #f0f0f0;
                color: #000000;
            }
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 5px;
                background-color: #f0f0f0;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #2a82da;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QLabel {
                color: #000000;
                background: transparent;
            }
            QSlider::groove:horizontal {
                border: 1px solid #b0b0b0;
                height: 8px;
                background: #ffffff;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2a82da;
                border: 1px solid #b0b0b0;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px;
                color: #000000;
            }
            QComboBox::drop-down {
                border-left: 1px solid #b0b0b0;
                width: 15px;
                background-color: #e0e0e0;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #000000;
                margin-left: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #2a82da;
                selection-color: #ffffff;
                border: 1px solid #b0b0b0;
            }
            QCheckBox {
                color: #000000;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 13px;
                height: 13px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
            }
            QCheckBox::indicator:checked {
                background-color: #2a82da;
                border: 1px solid #b0b0b0;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 8px 16px;
                margin-right: 2px;
                color: #000000;
            }
            QTabBar::tab:selected {
                background-color: #2a82da;
                color: white;
                border-bottom: 1px solid #2a82da;
            }
            QScrollArea {
                border: none;
                background-color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                text-align: center;
                background-color: #ffffff;
                color: #000000;
            }
            QProgressBar::chunk {
                background-color: #2a82da;
                border-radius: 2px;
            }
            QMenuBar {
                background-color: #f0f0f0;
                color: #000000;
                border-bottom: 1px solid #d0d0d0;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 8px;
            }
            QMenuBar::item:selected {
                background-color: #2a82da;
                color: #ffffff;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d0d0d0;
            }
            QMenu::item {
                padding: 8px 32px 8px 16px;
            }
            QMenu::item:selected {
                background-color: #2a82da;
                color: #ffffff;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #000000;
                border-top: 1px solid #d0d0d0;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px;
                color: #000000;
            }
            QLineEdit:focus {
                border: 2px solid #2a82da;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #999999;
            }
            QRadioButton {
                color: #000000;
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 13px;
                height: 13px;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
            }
            QRadioButton::indicator:checked {
                background-color: #2a82da;
                border: 1px solid #b0b0b0;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px;
                color: #000000;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #2a82da;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                background-color: #e0e0e0;
                border: none;
                border-left: 1px solid #b0b0b0;
                border-bottom: 1px solid #b0b0b0;
                width: 16px;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                background-color: #e0e0e0;
                border: none;
                border-left: 1px solid #b0b0b0;
                width: 16px;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-bottom: 3px solid #000000;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 3px solid #000000;
                width: 0px;
                height: 0px;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #b0b0b0;
                border-radius: 3px;
                padding: 5px;
                color: #000000;
            }
            QTextEdit:focus {
                border: 2px solid #2a82da;
            }
            QDialog {
                background-color: #f0f0f0;
                color: #000000;
            }
            QMessageBox {
                background-color: #f0f0f0;
                color: #000000;
            }
            QMessageBox QLabel {
                color: #000000;
            }
            QFileDialog {
                background-color: #f0f0f0;
                color: #000000;
            }
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                border: 1px solid #d0d0d0;
                color: #000000;
                gridline-color: #d0d0d0;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2a82da;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #d0d0d0;
                padding: 4px;
            }
            QSplitter::handle {
                background-color: #d0d0d0;
            }
            QSplitter::handle:horizontal {
                width: 2px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """