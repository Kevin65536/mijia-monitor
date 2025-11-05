"""米家设备监控系统主程序"""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from .utils.config_loader import ConfigLoader
from .utils.logger import setup_logger
from .core.database import DatabaseManager
from .core.monitor import DeviceMonitor
from .ui.main_window import MainWindow


def main():
    """主函数"""
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent
    
    # 加载配置
    config = ConfigLoader()
    
    # 设置日志
    log_file = root_dir / config.get('logging.file', 'logs/mi-monitor.log')
    logger = setup_logger(
        name='mi-monitor',
        log_file=str(log_file),
        level=config.get('logging.level', 'INFO'),
        max_size=config.get('logging.max_size', 10),
        backup_count=config.get('logging.backup_count', 5),
        console=config.get('logging.console', True)
    )
    
    logger.info("=" * 60)
    logger.info("米家设备监控系统启动")
    logger.info(f"版本: {config.get('app.version', '1.0.0')}")
    logger.info("=" * 60)
    
    # 初始化数据库
    db_path = root_dir / config.get('database.path', 'data/monitor.db')
    database = DatabaseManager(str(db_path))
    logger.info(f"数据库初始化完成: {db_path}")
    
    # 初始化监控器
    monitor = DeviceMonitor(config, database)
    logger.info("设备监控器初始化完成")
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName(config.get('app.name', '米家设备监控'))
    app.setApplicationVersion(config.get('app.version', '1.0.0'))
    
    # 创建主窗口
    window = MainWindow(config, database, monitor)
    
    # 检查是否启动时最小化
    if config.get('ui.main_window.start_minimized', False):
        window.hide()
    else:
        window.show()
    
    # 自动启动监控
    if config.get('monitor.auto_start', False):
        logger.info("自动启动监控...")
        monitor.start_monitor()
    
    # 运行应用
    logger.info("应用程序界面已启动")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
