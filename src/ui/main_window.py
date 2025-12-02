"""主窗口界面"""
import sys
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QTabWidget, QStatusBar,
    QMessageBox, QHeaderView, QSystemTrayIcon, QMenu, QDialog,
    QLineEdit, QCheckBox, QSpinBox, QFormLayout, QProgressDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QIcon, QAction

from ..core.database import DatabaseManager
from ..core.monitor import DeviceMonitor
from ..core.device_profiles import DeviceProfileFactory
from ..utils.config_loader import ConfigLoader
from ..utils.logger import get_logger
from ..utils.path_utils import get_resource_path
from .device_detail_dialog import DeviceDetailDialog
from .qr_login_dialog import QRLoginDialog
from .cards import DeviceCardGrid

logger = get_logger(__name__)


class LogoutWorker(QThread):
    """退出登录工作线程"""
    finished_signal = Signal()
    
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        
    def run(self):
        """执行退出操作"""
        if self.monitor.is_running:
            self.monitor.stop_monitor()
        self.finished_signal.emit()

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
        
        # 如果已登录,自动刷新设备并启动监控
        QTimer.singleShot(100, self.auto_refresh_and_start)
    
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
        # self.alert_tab = self.create_alert_tab()
        # self.tab_widget.addTab(self.alert_tab, "报警记录")
        
        # 统计选项卡
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "统计信息")
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 加载设备列表
        self.refresh_device_list()
        
        # 更新登录按钮状态
        self.update_login_button()
    
    def create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        toolbar = QHBoxLayout()
        
        # 登录按钮 - 根据登录状态显示不同文本
        self.login_btn = QPushButton()
        self.login_btn.clicked.connect(self.on_login_logout)
        self.update_login_button()
        toolbar.addWidget(self.login_btn)
        
        toolbar.addStretch()
        
        # 统计信息标签
        self.stats_label = QLabel("设备: 0 | 在线: 0 | 报警: 0")
        toolbar.addWidget(self.stats_label)
        
        return toolbar
    
    def create_device_tab(self) -> QWidget:
        """创建设备列表选项卡 - 卡片网格布局"""
        from PySide6.QtWidgets import QScrollArea
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(0, 0, 0, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # 设备卡片网格
        self.device_card_grid = DeviceCardGrid()
        self.device_card_grid.card_clicked.connect(self.show_device_detail)
        
        scroll_area.setWidget(self.device_card_grid)
        
        return scroll_area
    
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
        icon_path = get_resource_path("resources/icons/app.ico")
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
            
            # 清空现有卡片
            self.device_card_grid.clear()
            
            # 重建 did 到行号的映射（用于兼容性）
            self._did_to_row.clear()
            
            for idx, device in enumerate(devices):
                # 缓存 did 到索引的映射
                self._did_to_row[device['did']] = idx
                
                # 添加设备卡片
                card = self.device_card_grid.add_device(device)
                
                # 尝试加载实时数据
                if card:
                    overview_data = self._get_device_overview_data(device['did'])
                    card.update_realtime_data(overview_data)
            
            # 更新统计
            self.update_stats_label()
        finally:
            self._is_refreshing = False
    
    def _get_device_overview_data(self, did: str) -> list:
        """获取设备概览数据"""
        try:
            device = self.database.get_device(did)
            if not device:
                return []
            
            properties = self.database.get_latest_device_properties(did)
            if not properties:
                return []
            
            profile = DeviceProfileFactory.create_profile(device.get('model', ''))
            return profile.get_overview_properties(properties)
        except Exception as e:
            logger.error(f"获取设备概览数据失败: {e}")
            return []
    
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
    
    def update_login_button(self) -> None:
        """更新登录按钮的文本和状态"""
        if self.monitor.api and self.monitor.api.available:
            self.login_btn.setText("退出登录")
        else:
            self.login_btn.setText("米家登录")
    
    def auto_refresh_and_start(self) -> bool:
        """自动刷新设备并启动监控"""
        # 检查是否已登录
        if not self.monitor.api or not self.monitor.api.available:
            logger.info("未登录,跳过自动启动")
            return False
        
        logger.info("检测到已登录,开始自动刷新设备...")
        self.status_bar.showMessage("正在从米家云端获取设备列表...")
        
        # 刷新设备列表
        if self.monitor.fetch_devices():
            self.refresh_device_list()
            self.status_bar.showMessage("设备列表刷新成功,正在启动监控...", 2000)
            logger.info("设备列表刷新成功")
            
            # 启动监控
            if self.monitor.start_monitor():
                self.status_bar.showMessage("监控已启动", 3000)
                logger.info("监控已自动启动")
                return True
            else:
                self.status_bar.showMessage("启动监控失败", 3000)
                logger.error("启动监控失败")
                return False
        else:
            self.status_bar.showMessage("设备列表刷新失败", 3000)
            logger.error("获取设备列表失败")
            return False
    
    def on_login_logout(self) -> None:
        """处理登录/退出登录"""
        if self.monitor.api and self.monitor.api.available:
            # 已登录，执行退出登录
            self.logout()
        else:
            # 未登录，执行登录
            self.login()
    
    def login(self) -> None:
        """登录米家账号"""
        # 使用GUI二维码登录
        dialog = QRLoginDialog(self.monitor, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 登录成功
            auth_data = dialog.get_auth_data()
            if auth_data:
                # 重新初始化API
                self.monitor._init_mijia_api()
                
                # 更新登录按钮
                self.update_login_button()
                
                QMessageBox.information(self, "成功", "登录成功!")
                
                # 自动刷新设备并启动监控
                self.auto_refresh_and_start()
        else:
            # 登录取消或失败
            logger.info("用户取消登录或登录失败")
    
    def logout(self) -> None:
        """退出登录"""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出登录吗？\n\n退出后将停止监控所有设备。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 显示进度对话框
            self.progress_dialog = QProgressDialog("正在停止监控...", None, 0, 0, self)
            self.progress_dialog.setWindowTitle("请稍候")
            self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            self.progress_dialog.setCancelButton(None)  # 禁用取消按钮
            self.progress_dialog.show()
            
            # 启动后台线程执行退出操作
            self.logout_worker = LogoutWorker(self.monitor)
            self.logout_worker.finished_signal.connect(self._on_logout_finished)
            self.logout_worker.start()
    
    def _on_logout_finished(self):
        """退出操作完成回调"""
        # 关闭进度对话框
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            
        logger.info("监控已停止")
        
        # 删除认证文件
        auth_file = self.config.get('mijia.auth_file', 'config/mijia_auth.json')
        auth_path = Path(auth_file)
        
        if auth_path.exists():
            try:
                auth_path.unlink()
                logger.info("认证文件已删除")
            except Exception as e:
                logger.error(f"删除认证文件失败: {e}")
        
        # 清空API
        self.monitor.api = None
        
        # 更新登录按钮
        self.update_login_button()
        
        QMessageBox.information(self, "成功", "已退出登录")
        self.status_bar.showMessage("已退出登录", 3000)
    
    def _format_device_status(self, did: str) -> str:
        """格式化设备状态信息"""
        try:
            device = self.database.get_device(did)
            if not device:
                return "-"
                
            properties = self.database.get_latest_device_properties(did)
            if not properties:
                return "-"
            
            profile = DeviceProfileFactory.create_profile(device.get('model', ''))
            overview_props = profile.get_overview_properties(properties)
            
            status_parts = [prop['value'] for prop in overview_props]
            
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
        
        # 更新特定设备的卡片实时数据
        if not did:
            return
        
        try:
            # 获取设备概览数据并更新卡片
            overview_data = self._get_device_overview_data(did)
            self.device_card_grid.update_device_data(did, overview_data)
        except Exception as e:
            logger.error(f"更新设备卡片失败: {e}")
    
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
