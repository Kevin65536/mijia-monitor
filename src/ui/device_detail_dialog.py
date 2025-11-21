"""设备详情对话框"""
from datetime import datetime
from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DeviceDetailDialog(QDialog):
    """设备详情对话框"""
    
    def __init__(self, device: Dict[str, Any], database: DatabaseManager, parent=None):
        super().__init__(parent)
        
        self.device = device
        self.database = database
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle(f"设备详情 - {self.device['name']}")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 基本信息区域
        info_layout = self.create_basic_info_section()
        layout.addLayout(info_layout)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # 当前属性选项卡
        self.properties_tab = self.create_properties_tab()
        tab_widget.addTab(self.properties_tab, "当前属性")
        
        # 历史数据选项卡
        # TODO: 未来可以添加图表展示
        
        layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_basic_info_section(self) -> QHBoxLayout:
        """创建基本信息区域"""
        layout = QHBoxLayout()
        
        info_text = f"""
<b>设备名称:</b> {self.device['name']}<br>
<b>设备ID:</b> {self.device['did']}<br>
<b>设备型号:</b> {self.device['model']}<br>
<b>所在房间:</b> {self.device['room_name'] or '未分配'}<br>
<b>在线状态:</b> {'<span style="color: green;">在线</span>' if self.device['online'] else '<span style="color: red;">离线</span>'}<br>
<b>首次发现:</b> {self._format_datetime(self.device['first_seen'])}<br>
<b>最后更新:</b> {self._format_datetime(self.device['last_seen'])}<br>
<b>监控间隔:</b> {self.device.get('monitor_interval', 60)} 秒
        """
        
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        layout.addStretch()
        
        return layout
    
    def create_properties_tab(self) -> QWidget:
        """创建属性选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 属性表格
        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(4)
        self.properties_table.setHorizontalHeaderLabels([
            "属性名称", "当前值", "类型", "更新时间"
        ])
        
        # 设置表格属性
        header = self.properties_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.properties_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.properties_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        
        # 设置字体
        font = QFont()
        font.setPointSize(10)
        self.properties_table.setFont(font)
        
        layout.addWidget(self.properties_table)
        
        return widget
    
    def load_data(self) -> None:
        """加载数据"""
        try:
            # 获取最新属性
            properties = self.database.get_latest_device_properties(self.device['did'])
            
            self.properties_table.setRowCount(len(properties))
            
            # 定义属性的友好名称映射
            friendly_names = {
                'temperature': '温度',
                'relative-humidity': '相对湿度',
                'electric-power': '功率',
                'power': '功率',
                'electric-current': '电流',
                'voltage': '电压',
                'battery-level': '电池电量',
                'on': '开关状态',
                'brightness': '亮度',
                'color-temperature': '色温',
            }
            
            # 按属性名称排序
            sorted_props = sorted(properties.items())
            
            for row, (prop_name, prop_data) in enumerate(sorted_props):
                # 属性名称 (显示友好名称)
                display_name = friendly_names.get(prop_name, prop_name)
                name_item = QTableWidgetItem(display_name)
                name_item.setToolTip(f"原始名称: {prop_name}")
                self.properties_table.setItem(row, 0, name_item)
                
                # 当前值
                value = prop_data['value']
                formatted_value = self._format_property_value(prop_name, value)
                self.properties_table.setItem(row, 1, QTableWidgetItem(formatted_value))
                
                # 类型
                value_type = prop_data.get('value_type', '-')
                self.properties_table.setItem(row, 2, QTableWidgetItem(value_type))
                
                # 更新时间
                timestamp = self._format_datetime(prop_data['timestamp'])
                self.properties_table.setItem(row, 3, QTableWidgetItem(timestamp))
            
            # 如果没有属性,显示提示
            if not properties:
                self.properties_table.setRowCount(1)
                self.properties_table.setItem(0, 0, QTableWidgetItem("暂无属性数据"))
                self.properties_table.setSpan(0, 0, 1, 4)
        
        except Exception as e:
            logger.error(f"加载设备属性失败: {e}")
            self.properties_table.setRowCount(1)
            self.properties_table.setItem(0, 0, QTableWidgetItem(f"加载失败: {e}"))
            self.properties_table.setSpan(0, 0, 1, 4)
    
    def _format_property_value(self, prop_name: str, value: str) -> str:
        """格式化属性值"""
        try:
            # 针对特定属性添加单位
            if prop_name in ['temperature']:
                return f"{float(value):.1f}°C"
            elif prop_name in ['relative-humidity', 'battery-level']:
                return f"{int(float(value))}%"
            elif prop_name in ['electric-power', 'power']:
                return f"{float(value):.1f}W"
            elif prop_name in ['electric-current']:
                return f"{float(value):.2f}A"
            elif prop_name in ['voltage']:
                return f"{float(value):.1f}V"
            elif prop_name in ['brightness']:
                return f"{int(float(value))}%"
            elif prop_name in ['color-temperature']:
                return f"{int(float(value))}K"
            elif prop_name in ['on']:
                # 布尔值转换
                if value.lower() in ['true', '1', 'on']:
                    return "开启"
                else:
                    return "关闭"
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _format_datetime(self, dt_str: str) -> str:
        """格式化日期时间"""
        if not dt_str or dt_str == '-':
            return '-'
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(dt_str)
