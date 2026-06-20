from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QScrollArea, QGroupBox, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from gui.pyvista_widget import PyVistaWidget

class VisualizationPanel(QWidget):
    """Main visualization tab container, housing the 3D viewer and statistics tab."""
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # 3D Visualization tab
        self.pyvista_widget = PyVistaWidget()
        self.tab_widget.addTab(self.pyvista_widget, "3D View")
        
        # Statistics tab
        self.stats_widget = self._create_stats_tab()
        self.tab_widget.addTab(self.stats_widget, "Statistics")
        
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create scroll area for statistics content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Statistics content widget
        stats_content = QWidget()
        stats_layout = QVBoxLayout()
        
        # Create statistics groups
        stats_groups = [
            ("Basic Information", "basic_stats_label"),
            ("Geometric Properties", "geo_stats_label"),
            ("Features", "features_stats_label"),
            ("Additional Statistics", "additional_stats_label")
        ]
        
        for group_name, label_attr in stats_groups:
            group = QGroupBox(group_name)
            group_layout = QVBoxLayout()
            
            label = QLabel("No data available")
            label.setFont(QFont("Courier", 9))
            
            # Set the reference on both this panel and the main window for backward compatibility
            setattr(self, label_attr, label)
            if self.main_window is not None:
                setattr(self.main_window, label_attr, label)
            
            group_layout.addWidget(label)
            group.setLayout(group_layout)
            stats_layout.addWidget(group)
        
        stats_layout.addStretch()
        stats_content.setLayout(stats_layout)
        scroll_area.setWidget(stats_content)
        
        layout.addWidget(scroll_area)
        widget.setLayout(layout)
        return widget
