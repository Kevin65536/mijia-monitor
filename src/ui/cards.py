from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGridLayout,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QCursor


class DeviceCard(QFrame):
    """米家风格的设备卡片"""
    
    clicked = Signal(dict)  # 点击信号，传递设备信息
    
    def __init__(self, device: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.device = device
        self._overview_data = []  # 存储概览数据
        
        self.setFixedSize(200, 160)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("deviceCard")
        
        self._setup_style()
        self._setup_ui()
    
    def _setup_style(self):
        """设置卡片样式"""
        self.setStyleSheet("""
            QFrame#deviceCard {
                background-color: rgba(255, 255, 255, 0.6);
                border-radius: 16px;
                border: none;
            }
            QFrame#deviceCard:hover {
                background-color: rgba(255, 255, 255, 0.65);
            }
        """)
        
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 顶部区域：状态指示器
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 在线状态点
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self._update_status_dot()
        top_layout.addWidget(self.status_dot)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 中间区域：实时数据
        self.data_container = QWidget()
        self.data_layout = QVBoxLayout(self.data_container)
        self.data_layout.setContentsMargins(0, 0, 0, 0)
        self.data_layout.setSpacing(4)
        
        # 主数据标签（大字体）
        self.main_value_label = QLabel("-")
        self.main_value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #1a1a1a;
        """)
        self.data_layout.addWidget(self.main_value_label)
        
        # 次要数据标签
        self.secondary_value_label = QLabel("")
        self.secondary_value_label.setStyleSheet("""
            font-size: 14px;
            color: #666666;
        """)
        self.data_layout.addWidget(self.secondary_value_label)
        
        layout.addWidget(self.data_container)
        layout.addStretch()
        
        # 底部区域：设备名称和房间
        bottom_layout = QVBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(2)
        
        # 设备名称
        self.name_label = QLabel(self.device.get('name', '未知设备'))
        self.name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 500;
            color: #1a1a1a;
        """)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(36)
        bottom_layout.addWidget(self.name_label)
        
        # 房间名称
        room_name = self.device.get('room_name', '')
        self.room_label = QLabel(room_name if room_name else '')
        self.room_label.setStyleSheet("""
            font-size: 12px;
            color: #999999;
        """)
        bottom_layout.addWidget(self.room_label)
        
        layout.addLayout(bottom_layout)
    
    def _update_status_dot(self):
        """更新状态指示点"""
        is_online = self.device.get('online', False)
        color = "#4CD964" if is_online else "#cccccc"
        self.status_dot.setStyleSheet(f"""
            background-color: {color};
            border-radius: 4px;
        """)
    
    def update_device(self, device: Dict[str, Any]):
        """更新设备信息"""
        self.device = device
        self.name_label.setText(device.get('name', '未知设备'))
        room_name = device.get('room_name', '')
        self.room_label.setText(room_name if room_name else '')
        self._update_status_dot()
    
    def update_realtime_data(self, overview_data: list):
        """更新实时数据显示
        
        Args:
            overview_data: 设备概览属性列表，每个元素包含 name, value
        """
        self._overview_data = overview_data
        
        if not overview_data:
            self.main_value_label.setText("-")
            self.secondary_value_label.setText("")
            return
        
        # 第一个属性作为主数据
        main_data = overview_data[0]
        self.main_value_label.setText(str(main_data.get('value', '-')))
        
        # 其余属性作为次要数据
        if len(overview_data) > 1:
            secondary_parts = [str(d.get('value', '')) for d in overview_data[1:3]]  # 最多显示2个次要数据
            self.secondary_value_label.setText(' | '.join(secondary_parts))
        else:
            self.secondary_value_label.setText("")
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.device)
        super().mousePressEvent(event)


class DeviceCardGrid(QWidget):
    """设备卡片网格容器"""
    
    card_clicked = Signal(dict)  # 卡片点击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._cards: Dict[str, DeviceCard] = {}  # did -> DeviceCard
        self._columns = 5  # 默认列数
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 使用渐变背景模拟米家App风格
        self.setStyleSheet("""
            DeviceCardGrid {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #87CEEB,
                    stop: 0.5 #B0C4DE,
                    stop: 1 #E6E6FA
                );
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 卡片网格
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.main_layout.addWidget(self.grid_widget)
        self.main_layout.addStretch()
    
    def set_columns(self, columns: int):
        """设置列数"""
        self._columns = max(1, columns)
        self._relayout_cards()
    
    def _relayout_cards(self):
        """重新布局所有卡片"""
        # 从布局中移除所有卡片（但不删除）
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # 重新添加卡片
        for idx, (did, card) in enumerate(self._cards.items()):
            row = idx // self._columns
            col = idx % self._columns
            self.grid_layout.addWidget(card, row, col)
    
    def add_device(self, device: Dict[str, Any]) -> DeviceCard:
        """添加设备卡片"""
        did = device.get('did')
        if not did:
            return None
        
        # 如果已存在，更新
        if did in self._cards:
            self._cards[did].update_device(device)
            return self._cards[did]
        
        # 创建新卡片
        card = DeviceCard(device)
        card.clicked.connect(self._on_card_clicked)
        
        self._cards[did] = card
        
        # 添加到网格
        idx = len(self._cards) - 1
        row = idx // self._columns
        col = idx % self._columns
        self.grid_layout.addWidget(card, row, col)
        
        return card
    
    def remove_device(self, did: str):
        """移除设备卡片"""
        if did in self._cards:
            card = self._cards.pop(did)
            self.grid_layout.removeWidget(card)
            card.deleteLater()
            self._relayout_cards()
    
    def clear(self):
        """清空所有卡片"""
        for card in self._cards.values():
            self.grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
    
    def get_card(self, did: str) -> Optional[DeviceCard]:
        """获取指定设备的卡片"""
        return self._cards.get(did)
    
    def update_device_data(self, did: str, overview_data: list):
        """更新设备实时数据"""
        card = self._cards.get(did)
        if card:
            card.update_realtime_data(overview_data)
    
    def _on_card_clicked(self, device: Dict[str, Any]):
        """卡片点击处理"""
        self.card_clicked.emit(device)
    
    def resizeEvent(self, event):
        """窗口大小改变时自动调整列数"""
        super().resizeEvent(event)
        # 根据宽度自动计算列数（每个卡片200px + 16px间距）
        available_width = event.size().width() - 40  # 减去边距
        card_width = 200 + 16
        new_columns = max(1, available_width // card_width)
        
        if new_columns != self._columns:
            self._columns = new_columns
            self._relayout_cards()


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
