#!/usr/bin/env python
"""米家设备监控 - 命令行版本
这是一个简化的命令行版本,不需要GUI界面,可以直接在终端中运行
"""

import sys
import time
import signal
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mijia-api"))

from src.core.monitor import DeviceMonitor
from src.core.database import DatabaseManager
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

# 全局变量
monitor = None
running = True

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    global running, monitor
    print("\n\n正在停止监控...")
    running = False
    if monitor:
        monitor.stop_monitor()
    print("监控已停止,程序退出")
    sys.exit(0)

def print_banner():
    """打印欢迎信息"""
    print("=" * 60)
    print(" 米家设备监控系统 - 命令行版本")
    print("=" * 60)
    print()

def print_menu():
    """打印菜单"""
    print("\n" + "-" * 60)
    print("可用命令:")
    print("  1 - 登录米家账号")
    print("  2 - 获取设备列表")
    print("  3 - 显示设备列表")
    print("  4 - 启动监控")
    print("  5 - 停止监控")
    print("  6 - 查看统计信息")
    print("  7 - 查看报警记录")
    print("  0 - 退出程序")
    print("-" * 60)

def login_mijia(monitor):
    """登录米家账号"""
    print("\n登录米家账号")
    print("-" * 40)
    print("请选择登录方式:")
    print("  1 - 二维码登录 (推荐)")
    print("  2 - 账号密码登录")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == '1':
        print("\n使用二维码登录...")
        print("请在下方查看二维码,使用米家APP扫描:")
        print()
        success = monitor.login(use_qr=True)
    elif choice == '2':
        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
        success = monitor.login(use_qr=False, username=username, password=password)
    else:
        print("无效的选择")
        return False
    
    if success:
        print("\n✓ 登录成功!")
        return True
    else:
        print("\n✗ 登录失败,请重试")
        return False

def fetch_devices(monitor):
    """获取设备列表"""
    print("\n正在从米家云端获取设备列表...")
    success = monitor.fetch_devices()
    
    if success:
        devices = monitor.get_devices()
        print(f"✓ 成功获取 {len(devices)} 个设备")
        return True
    else:
        print("✗ 获取设备列表失败")
        return False

def show_devices(monitor, database):
    """显示设备列表"""
    devices = database.get_all_devices()
    
    if not devices:
        print("\n暂无设备数据,请先获取设备列表")
        return
    
    print("\n" + "=" * 80)
    print(f"{'设备名称':<20} {'型号':<25} {'房间':<15} {'状态':<8}")
    print("=" * 80)
    
    for device in devices:
        name = device['name'] or '未知'
        model = device['model'] or '-'
        room = device['room_name'] or '-'
        status = "在线" if device['online'] else "离线"
        
        print(f"{name:<20} {model:<25} {room:<15} {status:<8}")
    
    print("=" * 80)
    print(f"总计: {len(devices)} 个设备")

def start_monitoring(monitor):
    """启动监控"""
    if monitor.is_running:
        print("\n监控已在运行中")
        return
    
    print("\n正在启动监控...")
    success = monitor.start_monitor()
    
    if success:
        print("✓ 监控已启动")
        print("提示: 按 Ctrl+C 可以停止监控")
    else:
        print("✗ 启动监控失败,请先获取设备列表")

def stop_monitoring(monitor):
    """停止监控"""
    if not monitor.is_running:
        print("\n监控未运行")
        return
    
    print("\n正在停止监控...")
    monitor.stop_monitor()
    print("✓ 监控已停止")

def show_statistics(database):
    """显示统计信息"""
    stats = database.get_statistics()
    
    print("\n" + "=" * 60)
    print(" 统计信息")
    print("=" * 60)
    print(f"设备总数:     {stats['total_devices']}")
    print(f"在线设备:     {stats['online_devices']}")
    print(f"状态记录数:   {stats['total_status_records']}")
    print(f"属性记录数:   {stats['total_property_records']}")
    print(f"未解决报警:   {stats['unresolved_alerts']}")
    print(f"数据库大小:   {stats['db_size_mb']} MB")
    print("=" * 60)

def show_alerts(database):
    """显示报警记录"""
    alerts = database.get_unresolved_alerts()
    
    if not alerts:
        print("\n暂无未解决的报警")
        return
    
    print("\n" + "=" * 80)
    print(f"{'时间':<20} {'设备':<20} {'级别':<10} {'标题':<30}")
    print("=" * 80)
    
    for alert in alerts[:20]:  # 只显示最近20条
        created_at = alert['created_at'][:19]  # 截取日期时间部分
        device = database.get_device(alert['did'])
        device_name = device['name'] if device else alert['did'][:20]
        severity = alert['severity']
        title = alert['title'][:30]
        
        print(f"{created_at:<20} {device_name:<20} {severity:<10} {title:<30}")
    
    print("=" * 80)
    print(f"总计: {len(alerts)} 条未解决报警 (显示最近20条)")

def main():
    """主函数"""
    global monitor, running
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    # 打印欢迎信息
    print_banner()
    
    # 初始化
    print("正在初始化...")
    
    try:
        config = ConfigLoader()
        database = DatabaseManager(str(project_root / config.get('database.path')))
        monitor = DeviceMonitor(config, database)
        
        # 设置日志
        logger = setup_logger(
            name='cli-monitor',
            log_file=str(project_root / 'logs' / 'cli-monitor.log'),
            level='INFO',
            console=False
        )
        
        print("✓ 初始化完成")
        
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        sys.exit(1)
    
    # 主循环
    while running:
        print_menu()
        
        try:
            choice = input("\n请选择操作 (0-7): ").strip()
            
            if choice == '1':
                login_mijia(monitor)
            elif choice == '2':
                fetch_devices(monitor)
            elif choice == '3':
                show_devices(monitor, database)
            elif choice == '4':
                start_monitoring(monitor)
            elif choice == '5':
                stop_monitoring(monitor)
            elif choice == '6':
                show_statistics(database)
            elif choice == '7':
                show_alerts(database)
            elif choice == '0':
                print("\n正在退出...")
                if monitor.is_running:
                    monitor.stop_monitor()
                print("再见!")
                break
            else:
                print("\n无效的选择,请重试")
        
        except KeyboardInterrupt:
            print("\n\n检测到 Ctrl+C,正在退出...")
            if monitor.is_running:
                monitor.stop_monitor()
            print("再见!")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
