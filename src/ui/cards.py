from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class BaseCard(QFrame):
    """Base class for property cards"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            BaseCard {
                background-color: #2D2D2D;
                border-radius: 10px;
                border: 1px solid #3D3D3D;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #AAAAAA; font-size: 14px;")
        self.layout.addWidget(self.title_label)
        
        # Content container
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.layout.addWidget(self.content_widget)

    def set_value(self, value: str):
        pass

class InfoCard(BaseCard):
    """Card for displaying a value"""
    def __init__(self, title: str, unit: str = "", parent=None):
        super().__init__(title, parent)
        self.unit = unit
        
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("color: #FFFFFF; font-size: 24px; font-weight: bold;")
        self.content_layout.addWidget(self.value_label)
        
        if unit:
            unit_label = QLabel(unit)
            unit_label.setStyleSheet("color: #888888; font-size: 14px; margin-bottom: 4px;")
            unit_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            self.content_layout.addWidget(unit_label)
            
        self.content_layout.addStretch()

    def set_value(self, value: str):
        # Remove unit if it's already in the value string to avoid duplication
        if self.unit and value.endswith(self.unit):
            value = value[:-len(self.unit)].strip()
        self.value_label.setText(value)

class SwitchCard(BaseCard):
    """Card for boolean switch status"""
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        
        self.status_label = QLabel("未知")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            background-color: #444444;
            color: #FFFFFF;
            border-radius: 20px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
        """)
        self.status_label.setFixedWidth(100)
        
        self.content_layout.addStretch()
        self.content_layout.addWidget(self.status_label)
        self.content_layout.addStretch()

    def set_value(self, value: str):
        is_on = value in ["True", "true", "On", "on", "开启", "1"]
        
        if is_on:
            self.status_label.setText("开启")
            self.status_label.setStyleSheet("""
                background-color: #4ECDC4;
                color: #000000;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            """)
        else:
            self.status_label.setText("关闭")
            self.status_label.setStyleSheet("""
                background-color: #444444;
                color: #AAAAAA;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
            """)
