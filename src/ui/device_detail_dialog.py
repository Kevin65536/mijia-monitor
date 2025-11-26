"""设备详情对话框"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QTabWidget, QWidget, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.database import DatabaseManager
from ..core.device_profiles import DeviceProfileFactory
from ..utils.logger import get_logger
from .charts import DeviceChartWidget

logger = get_logger(__name__)


class DeviceDetailDialog(QDialog):
    """设备详情对话框"""
    
    def __init__(self, device: Dict[str, Any], database: DatabaseManager, parent=None):
        super().__init__(parent)
        
        self.device = device
        self.database = database
        self.profile = DeviceProfileFactory.create_profile(device.get('model', ''))
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self) -> None:
        """初始化UI"""
        self.setWindowTitle(f"设备详情 - {self.device['name']}")
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        
        # 基本信息区域
        info_layout = self.create_basic_info_section()
        layout.addLayout(info_layout)
        
        # 选项卡
        tab_widget = QTabWidget()
        
        # 历史数据图表选项卡
        self.charts_tab = self.create_charts_tab()
        tab_widget.addTab(self.charts_tab, "历史趋势")
        
        # 当前属性选项卡
        self.properties_tab = self.create_properties_tab()
        tab_widget.addTab(self.properties_tab, "当前属性")
        
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
        <h3>{self.device['name']}</h3>
        <b>设备ID:</b> {self.device['did']}<br>
        <b>设备型号:</b> {self.device['model']}<br>
        <b>所在房间:</b> {self.device['room_name'] or '未分配'}<br>
        <b>在线状态:</b> {'<span style="color: green;">在线</span>' if self.device['online'] else '<span style="color: red;">离线</span>'}<br>
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

    def create_charts_tab(self) -> QWidget:
        """创建图表选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 时间范围选择
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("时间范围:"))
        
        self.range_combo = QComboBox()
        self.range_combo.addItems(["12小时", "24小时", "48小时"])
        self.range_combo.setCurrentIndex(1) # 默认24小时
        self.range_combo.currentIndexChanged.connect(self.load_data)
        range_layout.addWidget(self.range_combo)
        range_layout.addStretch()
        
        layout.addLayout(range_layout)
        
        self.chart_widget = DeviceChartWidget()
        layout.addWidget(self.chart_widget)
        
        return widget
    
    def load_data(self) -> None:
        """加载数据"""
        try:
            # 1. 加载当前属性
            properties = self.database.get_latest_device_properties(self.device['did'])
            self._update_properties_table(properties)
            
            # 2. 加载历史数据并更新图表
            self._update_charts()
            
        except Exception as e:
            logger.error(f"加载设备数据失败: {e}")
            self.properties_table.setRowCount(1)
            self.properties_table.setItem(0, 0, QTableWidgetItem(f"加载失败: {e}"))
            self.properties_table.setSpan(0, 0, 1, 4)

    def _update_properties_table(self, properties: Dict[str, Any]) -> None:
        """更新属性表格"""
        display_props = self.profile.get_display_properties(properties)
        self.properties_table.setRowCount(len(display_props))
        
        for row, prop_data in enumerate(display_props):
            # 属性名称
            name_item = QTableWidgetItem(prop_data['name'])
            name_item.setToolTip(f"原始名称: {prop_data['key']}")
            self.properties_table.setItem(row, 0, name_item)
            
            # 当前值
            self.properties_table.setItem(row, 1, QTableWidgetItem(prop_data['value']))
            
            # 类型
            self.properties_table.setItem(row, 2, QTableWidgetItem(prop_data['type']))
            
            # 更新时间
            timestamp = self._format_datetime(prop_data['timestamp'])
            self.properties_table.setItem(row, 3, QTableWidgetItem(timestamp))
        
        # 如果没有属性,显示提示
        if not display_props:
            self.properties_table.setRowCount(1)
            self.properties_table.setItem(0, 0, QTableWidgetItem("暂无属性数据"))
            self.properties_table.setSpan(0, 0, 1, 4)

    def _update_charts(self) -> None:
        """更新图表数据"""
        self.chart_widget.clear()
        
        # 获取时间范围
        range_text = self.range_combo.currentText()
        hours = 24
        if "12" in range_text:
            hours = 12
        elif "48" in range_text:
            hours = 48
            
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 获取需要绘图的属性配置
        chart_props = self.profile.get_chart_properties()
        
        has_data = False
        
        # 遍历可能的属性
        monitor_interval = self.device.get('monitor_interval', 60)
        gap_threshold = monitor_interval * 3 # 超过3倍监控间隔视为断点
        
        for prop_name, config in chart_props.items():
            # 获取数据
            history = self.database.get_device_properties_history(
                self.device['did'], 
                prop_name, 
                start_time=start_time,
                limit=5000  # 增加限制以容纳更多数据
            )
            
            timestamps = []
            values = []
            
            if history:
                has_data = True
                # 数据按时间正序排列
                last_ts = None
                for record in reversed(history):
                    try:
                        # 解析时间戳
                        dt = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                        ts = dt.timestamp()
                        val = float(record['property_value'])
                        
                        # 检查是否需要插入断点
                        if last_ts is not None and (ts - last_ts) > gap_threshold:
                            timestamps.append(last_ts + 1) # 插入一个微小偏移的时间点
                            values.append(float('nan'))    # 插入NaN值
                        
                        timestamps.append(ts)
                        values.append(val)
                        last_ts = ts
                    except (ValueError, TypeError):
                        continue
            
            # 即使没有数据，也添加图表(显示空白坐标轴)
            self.chart_widget.add_chart(
                name=config['name'],
                timestamps=timestamps,
                values=values,
                color=config['color'],
                x_range=(start_time.timestamp(), end_time.timestamp())
            )
    
    def _format_datetime(self, dt_str: str) -> str:
        """格式化日期时间"""
        if not dt_str or dt_str == '-':
            return '-'
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            # 如果是naive时间(没有时区信息)，假定为UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                
            # 转换为本地时间
            dt_local = dt.astimezone()
            return dt_local.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return str(dt_str)
