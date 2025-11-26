import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame
from PySide6.QtGui import QColor, QLinearGradient, QBrush, QPen
from PySide6.QtCore import Qt
from datetime import datetime
import numpy as np

class DateAxisItem(pg.AxisItem):
    """自定义时间轴，显示可读的时间格式"""
    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            try:
                # 假设时间戳是Unix时间戳
                dt = datetime.fromtimestamp(v)
                if spacing >= 86400: # 刻度间隔超过1天
                    strings.append(dt.strftime('%m-%d'))
                else:
                    strings.append(dt.strftime('%H:%M'))
            except Exception:
                strings.append('')
        return strings

class ModernPlotItem(pg.PlotWidget):
    """单个属性的现代化图表"""
    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        
        # 基础配置
        self.setBackground('w')
        self.showGrid(x=True, y=True, alpha=0.15)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        
        # 坐标轴样式
        axis_pen = pg.mkPen(color='#EEEEEE', width=1)
        text_pen = pg.mkPen(color='#999999')
        
        # 左轴
        left_axis = self.getAxis('left')
        left_axis.setPen(axis_pen)
        left_axis.setTextPen(text_pen)
        left_axis.setStyle(tickLength=0)
        
        # 下轴
        bottom_axis = self.getAxis('bottom')
        bottom_axis.setPen(axis_pen)
        bottom_axis.setTextPen(text_pen)
        bottom_axis.setStyle(tickLength=0)
        bottom_axis.setHeight(30)
        
        # 替换为时间轴
        self.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})
        
        # 标题
        self.setTitle(title, color='#333333', size='11pt', bold=True)
        
        self.color = QColor(color)

    def set_data(self, timestamps, values):
        self.clear()
        if not timestamps or not values:
            return

        x = np.array(timestamps)
        y = np.array(values)
        
        # 1. 绘制曲线 (带阴影填充)
        pen = pg.mkPen(color=self.color, width=2.5)
        
        # 创建渐变填充
        grad = QLinearGradient(0, 0, 0, 1)
        grad.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        c_top = QColor(self.color)
        c_top.setAlpha(80)
        c_bottom = QColor(self.color)
        c_bottom.setAlpha(5)
        grad.setColorAt(0, c_top)
        grad.setColorAt(1, c_bottom)
        brush = QBrush(grad)
        
        # 计算填充基准线 (稍微在最小值下面一点，或者0)
        min_val = np.min(y)
        max_val = np.max(y)
        range_val = max_val - min_val if max_val != min_val else 1.0
        fill_level = min_val - range_val * 0.05
        
        self.plot(x, y, pen=pen, brush=brush, fillLevel=fill_level)
        
        # 2. 标记最大值和最小值
        if len(y) > 1:
            self._add_marker(x, y, np.argmax(y), 'max')
            self._add_marker(x, y, np.argmin(y), 'min')
        
        # 3. 标记最新值
        self._add_marker(x, y, -1, 'current')

    def _add_marker(self, x, y, index, type_):
        """添加数值标记"""
        ts = x[index]
        val = y[index]
        
        # 散点
        scatter = pg.ScatterPlotItem(
            [ts], [val], 
            size=10, 
            brush='w', 
            pen=pg.mkPen(self.color, width=2)
        )
        self.addItem(scatter)
        
        # 文本标签
        anchor = (0.5, 1.5) if type_ == 'max' else (0.5, -0.5)
        if type_ == 'current':
             anchor = (0, 1) # 最新值放在左上一点

        text = pg.TextItem(
            text=f"{val:.1f}", 
            color=self.color, 
            anchor=anchor
        )
        text.setPos(ts, val)
        self.addItem(text)

class DeviceChartWidget(QWidget):
    """设备数据图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: white;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(20)
        self.content_layout.addStretch() # 底部弹簧
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.charts = []
        
        # 配置PyQtGraph全局选项
        pg.setConfigOption('antialias', True)
        
    def add_chart(self, name: str, timestamps: list, values: list, color: str):
        """
        添加一个属性的图表
        """
        if not timestamps or not values:
            return
            
        # 确保数据是数值型
        try:
            values = [float(v) for v in values]
        except (ValueError, TypeError):
            return
            
        chart = ModernPlotItem(name, color)
        chart.setFixedHeight(220)
        chart.set_data(timestamps, values)
        
        # 插入到弹簧之前
        count = self.content_layout.count()
        self.content_layout.insertWidget(count - 1, chart)
        self.charts.append(chart)
            
    def clear(self):
        """清除所有图表"""
        for chart in self.charts:
            self.content_layout.removeWidget(chart)
            chart.deleteLater()
        self.charts = []
