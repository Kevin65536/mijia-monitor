"""米家设备监控系统主程序"""
import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication

# 修复打包后的导入问题
if getattr(sys, 'frozen', False):
    # 打包后的环境
    application_path = Path(sys.executable).parent
    # 添加bundled目录到sys.path
    bundle_dir = getattr(sys, '_MEIPASS', None)
    if bundle_dir:
        sys.path.insert(0, bundle_dir)
else:
    # 开发环境
    application_path = Path(__file__).parent.parent

# 使用绝对导入
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger
from src.core.database import DatabaseManager
from src.core.monitor import DeviceMonitor
from src.ui.main_window import MainWindow


def main():
    """主函数"""
    # 获取项目根目录
    if getattr(sys, 'frozen', False):
        # 打包后，使用exe所在目录
        root_dir = Path(sys.executable).parent
    else:
        # 开发环境
        root_dir = Path(__file__).parent.parent
    
    # 加载配置
    config = ConfigLoader()
    
    # 设置日志 - 确保日志目录存在
    log_file = root_dir / config.get('logging.file', 'logs/mi-monitor.log')
    log_file.parent.mkdir(parents=True, exist_ok=True)  # 创建日志目录
    
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
    
    # 初始化数据库 - 确保数据目录存在
    db_path = root_dir / config.get('database.path', 'data/monitor.db')
    db_path.parent.mkdir(parents=True, exist_ok=True)  # 创建数据目录
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
