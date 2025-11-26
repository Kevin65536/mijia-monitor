import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QFrame
from PySide6.QtGui import QColor, QLinearGradient, QBrush, QPen
from PySide6.QtCore import Qt
from datetime import datetime
import numpy as np
import math

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
        self.setBackground(None) # 透明背景
        self.showGrid(x=True, y=True, alpha=0.15)
        self.setMouseEnabled(x=False, y=False)
        self.hideButtons()
        
        # 坐标轴样式 - 使用浅灰色以适应深色背景
        axis_pen = pg.mkPen(color='#CCCCCC', width=1)
        text_pen = pg.mkPen(color='#CCCCCC')
        
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
        
        # 标题 - 使用浅灰色
        self.setTitle(title, color='#DDDDDD', size='11pt', bold=True)
        
        self.color = QColor(color)

    def set_data(self, timestamps, values, x_range=None):
        self.clear()
        
        # 设置X轴范围
        if x_range:
            self.setXRange(x_range[0], x_range[1], padding=0)
        
        if not timestamps or not values:
            return

        x = np.array(timestamps)
        y = np.array(values)
        
        # 1. 准备样式
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
        valid_y = y[~np.isnan(y)]
        if len(valid_y) > 0:
            min_val = np.min(valid_y)
            max_val = np.max(valid_y)
            range_val = max_val - min_val if max_val != min_val else 1.0
            fill_level = min_val - range_val * 0.05
        else:
            fill_level = 0
            
        # 2. 分段绘制以正确处理填充
        # 寻找NaN的索引
        nan_indices = np.where(np.isnan(y))[0]
        
        # 如果没有NaN，直接绘制
        if len(nan_indices) == 0:
            self.plot(x, y, pen=pen, brush=brush, fillLevel=fill_level)
        else:
            # 有NaN，分段绘制
            start_idx = 0
            for nan_idx in nan_indices:
                if nan_idx > start_idx:
                    # 绘制这一段
                    seg_x = x[start_idx:nan_idx]
                    seg_y = y[start_idx:nan_idx]
                    self.plot(seg_x, seg_y, pen=pen, brush=brush, fillLevel=fill_level)
                start_idx = nan_idx + 1
            
            # 绘制最后一段
            if start_idx < len(x):
                seg_x = x[start_idx:]
                seg_y = y[start_idx:]
                self.plot(seg_x, seg_y, pen=pen, brush=brush, fillLevel=fill_level)
        
        # 3. 标记最大值和最小值
        if len(valid_y) > 1:
            self._add_marker(x, y, np.nanargmax(y), 'max')
            self._add_marker(x, y, np.nanargmin(y), 'min')
        
        # 4. 标记最新值
        if len(y) > 0 and not np.isnan(y[-1]):
            self._add_marker(x, y, -1, 'current')

    def _add_marker(self, x, y, index, type_):
        """添加数值标记"""
        ts = x[index]
        val = y[index]
        
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
        
        # 主布局 - 使用网格布局
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(20)
        
        self.charts = []
        
        # 配置PyQtGraph全局选项
        pg.setConfigOption('antialias', True)
        
    def add_chart(self, name: str, timestamps: list, values: list, color: str, x_range: tuple = None):
        """
        添加一个属性的图表
        """
        chart = ModernPlotItem(name, color)
        
        if not timestamps or not values:
            # 即使没有数据，如果指定了范围，也应该显示空图表
            if x_range:
                chart.set_data([], [], x_range)
            else:
                # 没有数据也没有范围，不添加
                chart.deleteLater()
                return
        else:
            # 确保数据是数值型
            try:
                values = [float(v) for v in values]
                chart.set_data(timestamps, values, x_range)
            except (ValueError, TypeError):
                chart.deleteLater()
                return
        
        self.charts.append(chart)
        self._update_layout()
            
    def _update_layout(self):
        """更新网格布局"""
        count = len(self.charts)
        if count == 0:
            return
            
        # 策略：
        # 1. <= 2个图：单列纵向排列
        # 2. > 2个图：双列排列
        # 3. 双列模式下，如果是奇数个，最后一个图跨两列
        
        is_single_col = count <= 2
        
        for i, chart in enumerate(self.charts):
            if is_single_col:
                # 单列模式，占满整行(跨2列以保持一致性)
                self.layout.addWidget(chart, i, 0, 1, 2)
            else:
                # 双列模式
                row = i // 2
                col = i % 2
                
                # 如果是最后一个且是奇数个，跨两列
                if i == count - 1 and count % 2 != 0:
                    self.layout.addWidget(chart, row, 0, 1, 2)
                else:
                    self.layout.addWidget(chart, row, col, 1, 1)
            
    def clear(self):
        """清除所有图表"""
        for chart in self.charts:
            self.layout.removeWidget(chart)
            chart.deleteLater()
        self.charts = []
