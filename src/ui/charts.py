import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from datetime import datetime
import time

class DateAxisItem(pg.AxisItem):
    """自定义时间轴，显示可读的时间格式"""
    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            try:
                # 假设时间戳是Unix时间戳
                dt = datetime.fromtimestamp(v)
                strings.append(dt.strftime('%H:%M'))
            except Exception:
                strings.append('')
        return strings

class DeviceChartWidget(QWidget):
    """设备数据图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # 配置PyQtGraph
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOption('antialias', True)
        
        # 创建绘图部件
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': DateAxisItem(orientation='bottom')})
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        
        self.layout.addWidget(self.plot_widget)
        
        # 存储曲线引用
        self.curves = {}
        
    def plot_data(self, name: str, timestamps: list, values: list, color: str, symbol: str = 'o'):
        """
        绘制数据
        
        Args:
            name: 数据系列名称 (显示在图例中)
            timestamps: 时间戳列表 (Unix timestamp float)
            values: 数值列表
            color: 颜色 (hex string or 'r', 'g', 'b' etc)
            symbol: 数据点符号 ('o', 's', 't', etc. or None)
        """
        if not timestamps or not values:
            return
            
        # 确保数据是数值型
        try:
            values = [float(v) for v in values]
        except (ValueError, TypeError):
            return
            
        if name in self.curves:
            # 更新现有曲线
            self.curves[name].setData(timestamps, values)
        else:
            # 创建新曲线
            pen = pg.mkPen(color=color, width=2)
            curve = self.plot_widget.plot(
                timestamps, values, 
                name=name, 
                pen=pen, 
                symbol=symbol, 
                symbolSize=5,
                symbolBrush=color
            )
            self.curves[name] = curve
            
    def clear(self):
        """清除所有图表"""
        self.plot_widget.clear()
        self.curves.clear()
