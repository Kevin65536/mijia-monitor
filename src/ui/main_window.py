"""主窗口界面"""
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QTabWidget, QStatusBar,
    QMessageBox, QHeaderView, QSystemTrayIcon, QMenu, QDialog,
    QLineEdit, QCheckBox, QSpinBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QIcon, QAction

from ..core.database import DatabaseManager
from ..core.monitor import DeviceMonitor
from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from .device_detail_dialog import DeviceDetailDialog

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    device_update_signal = Signal(dict)
    device_offline_signal = Signal(dict)
    status_update_signal = Signal(str)
    
    def __init__(self, config: ConfigLoader, database: DatabaseManager, monitor: DeviceMonitor):
        super().__init__()
        
        self.config = config
        self.database = database
        self.monitor = monitor
        
        # 刷新锁，防止重复刷新
        self._is_refreshing = False
        
        # 属性缓存 - 避免频繁查询数据库
        self._property_cache: Dict[str, Dict[str, Any]] = {}
        
        # 设备ID到行号的映射缓存
        self._did_to_row: Dict[str, int] = {}
        
        # 注册监控回调
        self.monitor.register_callback('device_update', self._on_device_update)
        self.monitor.register_callback('device_offline', self._on_device_offline)
        self.monitor.register_callback('property_alert', self._on_property_alert)
        
        # 连接信号
        self.device_update_signal.connect(self._handle_device_update)
        self.device_offline_signal.connect(self._handle_device_offline)
        self.status_update_signal.connect(self._update_status_bar)
        
        self.init_ui()
        self.setup_system_tray()
        
        # 禁用自动刷新定时器，改为事件驱动更新
        # 自动刷新会导致UI卡顿，因为需要查询所有设备的属性
        # self.update_timer = QTimer()
        # self.update_timer.timeout.connect(self.refresh_device_list)
        # self.update_timer.start(5000)
    
    def init_ui(self) -> None:
        """初始化UI"""
        # 窗口设置
        self.setWindowTitle(self.config.get('app.name', '米家设备监控'))
        
        width = self.config.get('ui.main_window.width', 1200)
        height = self.config.get('ui.main_window.height', 800)
        self.resize(width, height)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 工具栏
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # 选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 设备列表选项卡
        self.device_tab = self.create_device_tab()
        self.tab_widget.addTab(self.device_tab, "设备列表")
        
        # 报警选项卡
        self.alert_tab = self.create_alert_tab()
        self.tab_widget.addTab(self.alert_tab, "报警记录")
        
        # 统计选项卡
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "统计信息")
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 加载设备列表
        self.refresh_device_list()
    
    def create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        toolbar = QHBoxLayout()
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新设备")
        self.refresh_btn.clicked.connect(self.on_refresh_devices)
        toolbar.addWidget(self.refresh_btn)
        
        # 启动/停止监控按钮
        self.monitor_btn = QPushButton("启动监控")
        self.monitor_btn.clicked.connect(self.on_toggle_monitor)
        toolbar.addWidget(self.monitor_btn)
        
        # 登录按钮
        self.login_btn = QPushButton("登录米家")
        self.login_btn.clicked.connect(self.on_login)
        toolbar.addWidget(self.login_btn)
        
        toolbar.addStretch()
        
        # 统计信息标签
        self.stats_label = QLabel("设备: 0 | 在线: 0 | 报警: 0")
        toolbar.addWidget(self.stats_label)
        
        return toolbar
    
    def create_device_tab(self) -> QWidget:
        """创建设备列表选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 设备表格
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(8)
        self.device_table.setHorizontalHeaderLabels([
            "设备名称", "型号", "房间", "状态", "实时数据", "最后更新", "监控间隔", "操作"
        ])
        
        # 设置表格属性
        header = self.device_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.device_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.device_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        
        layout.addWidget(self.device_table)
        
        return widget
    
    def create_alert_tab(self) -> QWidget:
        """创建报警选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 报警表格
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(6)
        self.alert_table.setHorizontalHeaderLabels([
            "时间", "设备", "类型", "级别", "标题", "状态"
        ])
        
        header = self.alert_table.horizontalHeader()
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.alert_table)
        
        # 刷新报警列表
        self.refresh_alert_list()
        
        return widget
    
    def create_stats_tab(self) -> QWidget:
        """创建统计信息选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.stats_text = QLabel()
        self.stats_text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.stats_text.setWordWrap(True)
        
        layout.addWidget(self.stats_text)
        layout.addStretch()
        
        # 刷新统计信息
        self.refresh_stats()
        
        return widget
    
    def setup_system_tray(self) -> None:
        """设置系统托盘"""
        if not self.config.get('ui.system_tray.enabled', True):
            return
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置图标 - 优先使用自定义图标，否则使用系统默认图标
        icon_path = Path("resources/icons/app.ico")
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            # 使用Qt内置图标作为后备
            from PySide6.QtWidgets import QStyle
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        
        self.tray_icon.show()
    
    def refresh_device_list(self) -> None:
        """刷新设备列表"""
        # 防止重复刷新
        if self._is_refreshing:
            return
        
        try:
            self._is_refreshing = True
            devices = self.database.get_all_devices()
            
            self.device_table.setRowCount(len(devices))
            
            # 重建 did 到行号的映射
            self._did_to_row.clear()
            
            for row, device in enumerate(devices):
                # 缓存 did 到行号的映射
                self._did_to_row[device['did']] = row
                
                # 设备名称
                self.device_table.setItem(row, 0, QTableWidgetItem(device['name'] or '未知'))
                
                # 型号
                self.device_table.setItem(row, 1, QTableWidgetItem(device['model'] or '-'))
                
                # 房间
                self.device_table.setItem(row, 2, QTableWidgetItem(device['room_name'] or '-'))
                
                # 状态
                status = "在线" if device['online'] else "离线"
                status_item = QTableWidgetItem(status)
                if device['online']:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.device_table.setItem(row, 3, status_item)
                
                # 实时数据 - 暂时显示为空，避免查询卡顿
                # 启动监控后会自动更新
                self.device_table.setItem(row, 4, QTableWidgetItem("-"))
                
                # 最后更新时间
                last_seen = device['last_seen'] or '-'
                if last_seen != '-':
                    try:
                        dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        last_seen = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                self.device_table.setItem(row, 5, QTableWidgetItem(last_seen))
                
                # 监控间隔
                interval = device.get('monitor_interval', 60)
                self.device_table.setItem(row, 6, QTableWidgetItem(f"{interval}秒"))
                
                # 操作按钮
                btn = QPushButton("查看详情")
                btn.clicked.connect(lambda checked, d=device: self.show_device_detail(d))
                self.device_table.setCellWidget(row, 7, btn)
            
            # 更新统计
            self.update_stats_label()
        finally:
            self._is_refreshing = False
    
    def refresh_alert_list(self) -> None:
        """刷新报警列表"""
        alerts = self.database.get_unresolved_alerts()
        
        self.alert_table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            # 时间
            created_at = alert['created_at']
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
            self.alert_table.setItem(row, 0, QTableWidgetItem(created_at))
            
            # 设备
            device = self.database.get_device(alert['did'])
            device_name = device['name'] if device else alert['did']
            self.alert_table.setItem(row, 1, QTableWidgetItem(device_name))
            
            # 类型
            self.alert_table.setItem(row, 2, QTableWidgetItem(alert['alert_type']))
            
            # 级别
            severity_item = QTableWidgetItem(alert['severity'])
            if alert['severity'] == 'WARNING':
                severity_item.setForeground(Qt.GlobalColor.darkYellow)
            elif alert['severity'] == 'ERROR':
                severity_item.setForeground(Qt.GlobalColor.red)
            self.alert_table.setItem(row, 3, severity_item)
            
            # 标题
            self.alert_table.setItem(row, 4, QTableWidgetItem(alert['title']))
            
            # 状态
            status = "未解决" if not alert['resolved'] else "已解决"
            self.alert_table.setItem(row, 5, QTableWidgetItem(status))
    
    def refresh_stats(self) -> None:
        """刷新统计信息"""
        stats = self.database.get_statistics()
        
        stats_text = f"""
<h3>数据库统计信息</h3>
<ul>
<li><b>设备总数:</b> {stats['total_devices']}</li>
<li><b>在线设备:</b> {stats['online_devices']}</li>
<li><b>状态记录数:</b> {stats['total_status_records']}</li>
<li><b>属性记录数:</b> {stats['total_property_records']}</li>
<li><b>未解决报警:</b> {stats['unresolved_alerts']}</li>
<li><b>数据库大小:</b> {stats['db_size_mb']} MB</li>
</ul>

<h3>监控状态</h3>
<ul>
<li><b>监控状态:</b> {'运行中' if self.monitor.is_running else '已停止'}</li>
<li><b>默认监控间隔:</b> {self.config.get('monitor.default_interval', 60)} 秒</li>
</ul>
        """
        
        self.stats_text.setText(stats_text)
    
    def update_stats_label(self) -> None:
        """更新统计标签"""
        stats = self.database.get_statistics()
        self.stats_label.setText(
            f"设备: {stats['total_devices']} | "
            f"在线: {stats['online_devices']} | "
            f"报警: {stats['unresolved_alerts']}"
        )
    
    def on_refresh_devices(self) -> None:
        """刷新设备列表按钮点击"""
        self.status_bar.showMessage("正在从米家云端获取设备列表...")
        
        if self.monitor.fetch_devices():
            self.refresh_device_list()
            self.status_bar.showMessage("设备列表刷新成功", 3000)
            QMessageBox.information(self, "成功", "设备列表已更新")
        else:
            self.status_bar.showMessage("设备列表刷新失败", 3000)
            QMessageBox.warning(self, "失败", "获取设备列表失败,请检查网络连接和登录状态")
    
    def on_toggle_monitor(self) -> None:
        """启动/停止监控"""
        if self.monitor.is_running:
            self.monitor.stop_monitor()
            self.monitor_btn.setText("启动监控")
            self.status_bar.showMessage("监控已停止")
        else:
            if self.monitor.start_monitor():
                self.monitor_btn.setText("停止监控")
                self.status_bar.showMessage("监控已启动")
            else:
                QMessageBox.warning(self, "失败", "启动监控失败,请先刷新设备列表")
    
    def on_login(self) -> None:
        """登录米家账号"""
        reply = QMessageBox.question(
            self,
            "登录方式",
            "使用二维码登录?\n\n点击Yes使用二维码登录\n点击No使用账号密码登录",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 二维码登录
            QMessageBox.information(
                self,
                "二维码登录",
                "请在控制台查看二维码并使用米家APP扫描"
            )
            
            if self.monitor.login(use_qr=True):
                QMessageBox.information(self, "成功", "登录成功!")
                self.on_refresh_devices()
            else:
                QMessageBox.warning(self, "失败", "登录失败")
        
        elif reply == QMessageBox.StandardButton.No:
            # 账号密码登录
            QMessageBox.warning(
                self,
                "提示",
                "账号密码登录可能需要手机验证码,建议使用二维码登录"
            )
    
    def _format_device_status(self, did: str) -> str:
        """格式化设备状态信息"""
        try:
            properties = self.database.get_latest_device_properties(did)
            
            if not properties:
                return "-"
            
            # 定义关键属性及其显示格式
            key_props = {
                'temperature': ('{}°C', 1),
                'relative-humidity': ('{}%', 0),
                'electric-power': ('{}W', 1),
                'power': ('{}W', 1),
                'electric-current': ('{}A', 2),
                'voltage': ('{}V', 1),
                'battery-level': ('电量{}%', 0),
            }
            
            status_parts = []
            
            for prop_name, (fmt, precision) in key_props.items():
                if prop_name in properties:
                    try:
                        value = float(properties[prop_name]['value'])
                        if precision == 0:
                            value = int(value)
                        else:
                            value = round(value, precision)
                        status_parts.append(fmt.format(value))
                    except (ValueError, TypeError):
                        continue
            
            return ' | '.join(status_parts) if status_parts else "-"
            
        except Exception as e:
            logger.error(f"格式化设备状态失败: {e}")
            return "-"
    
    def show_device_detail(self, device: Dict[str, Any]) -> None:
        """显示设备详情"""
        # 使用新的详情对话框
        dialog = DeviceDetailDialog(device, self.database, self)
        dialog.exec()
    
    def _on_device_update(self, data: Dict[str, Any]) -> None:
        """设备更新回调"""
        self.device_update_signal.emit(data)
    
    def _on_device_offline(self, data: Dict[str, Any]) -> None:
        """设备离线回调"""
        self.device_offline_signal.emit(data)
    
    def _on_property_alert(self, data: Dict[str, Any]) -> None:
        """属性报警回调"""
        if self.config.get('notification.enabled', True):
            device_name = data['device']['name']
            prop_name = data['property']
            value = data['value']
            
            if self.tray_icon:
                self.tray_icon.showMessage(
                    "设备报警",
                    f"{device_name}: {prop_name} = {value}",
                    QSystemTrayIcon.MessageIcon.Warning,
                    3000
                )
    
    def _handle_device_update(self, data: Dict[str, Any]) -> None:
        """处理设备更新信号"""
        # 更新缓存
        did = data.get('did')
        properties = data.get('properties', {})
        
        if did and properties:
            # 更新缓存
            if did not in self._property_cache:
                self._property_cache[did] = {}
            
            for prop_name, value in properties.items():
                self._property_cache[did][prop_name] = {
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                }
        
        # 更新特定设备的实时数据显示
        if not did:
            return
        
        try:
            # 使用缓存的映射直接找到行号，避免数据库查询
            row = self._did_to_row.get(did)
            if row is not None and row < self.device_table.rowCount():
                # 更新实时数据列 - 使用缓存
                status_info = self._format_device_status(did)
                self.device_table.setItem(row, 4, QTableWidgetItem(status_info))
        except Exception as e:
            logger.error(f"更新设备显示失败: {e}")
    
    def _handle_device_offline(self, data: Dict[str, Any]) -> None:
        """处理设备离线信号"""
        device_name = data['device']['name']
        self.status_update_signal.emit(f"设备 {device_name} 离线")
        
        if self.tray_icon and self.config.get('notification.types.device_offline', True):
            self.tray_icon.showMessage(
                "设备离线",
                f"{device_name} 已离线",
                QSystemTrayIcon.MessageIcon.Warning,
                3000
            )
    
    def _update_status_bar(self, message: str) -> None:
        """更新状态栏"""
        self.status_bar.showMessage(message, 3000)
    
    def on_tray_activated(self, reason) -> None:
        """托盘图标激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event) -> None:
        """关闭事件"""
        if self.config.get('ui.system_tray.close_to_tray', True) and self.tray_icon:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "米家设备监控",
                "程序已最小化到系统托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.quit_application()
    
    def quit_application(self) -> None:
        """退出应用程序"""
        self.monitor.stop_monitor()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()


# 需要在顶部导入
from PySide6.QtWidgets import QApplication
