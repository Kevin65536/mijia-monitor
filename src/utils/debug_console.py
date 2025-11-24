import threading
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

class DebugConsole(threading.Thread):
    """
    集成调试控制台
    在独立线程中运行，允许通过终端与正在运行的程序交互
    """
    
    def __init__(self, monitor, database):
        super().__init__()
        self.monitor = monitor
        self.database = database
        self.daemon = True  # 设置为守护线程，随主程序退出
        self.name = "DebugConsole"
        self.running = True
        
    def run(self):
        """线程主循环"""
        # 等待一点时间让主程序日志先输出完
        time.sleep(2)
        
        print("\n" + "=" * 60)
        print(" 调试控制台已就绪")
        print(" 输入 'help' 查看可用命令")
        print("=" * 60 + "\n")
        
        while self.running:
            try:
                # 使用 input 获取输入
                # 注意：这可能会与日志输出混杂，但在开发调试中通常可以接受
                cmd_line = input("debug> ").strip()
                
                if not cmd_line:
                    continue
                    
                parts = cmd_line.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                self._handle_command(cmd, args)
                
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _handle_command(self, cmd: str, args: List[str]):
        """处理命令"""
        if cmd in ('help', '?'):
            self._show_help()
        elif cmd in ('list', 'ls'):
            self._show_device_list()
        elif cmd == 'detail':
            self._show_device_detail(args)
        elif cmd == 'sim':
            self._simulate_detail_window(args)
        elif cmd == 'status':
            self._show_status()
        elif cmd == 'quit':
            print("调试控制台已停止 (主程序继续运行)")
            self.running = False
        else:
            print(f"未知命令: {cmd}")
            
    def _show_help(self):
        """显示帮助信息"""
        print("\n可用命令:")
        print("  list / ls       - 显示设备列表")
        print("  detail <ID/Idx> - 显示设备详细信息 (JSON)")
        print("  sim <ID/Idx>    - 模拟详情窗口数据")
        print("  status          - 显示系统状态")
        print("  help            - 显示此帮助")
        print("  quit            - 停止调试控制台")
        print()

    def _get_device_by_arg(self, arg: str) -> Optional[Dict[str, Any]]:
        """根据参数(ID或索引)获取设备"""
        devices = self.database.get_all_devices()
        
        # 尝试作为索引
        try:
            idx = int(arg)
            if 0 <= idx < len(devices):
                return devices[idx]
        except ValueError:
            pass
            
        # 尝试作为DID
        for device in devices:
            if device['did'] == arg:
                return device
                
        print(f"未找到设备: {arg}")
        return None

    def _format_device_status(self, did: str) -> str:
        """格式化设备状态 (复用逻辑)"""
        try:
            properties = self.database.get_latest_device_properties(did)
            if not properties:
                return "-"
            
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
        except Exception:
            return "-"

    def _show_device_list(self):
        """显示设备列表"""
        devices = self.database.get_all_devices()
        if not devices:
            print("暂无设备")
            return

        print("\n" + "=" * 140)
        print(f"{'Idx':<4} {'DID':<12} {'设备名称':<20} {'型号':<20} {'房间':<10} {'状态':<6} {'实时数据':<30} {'最后更新':<20}")
        print("=" * 140)
        
        for i, device in enumerate(devices):
            did = device['did'][:10] + ".."
            name = (device['name'] or '未知')[:18]
            model = (device['model'] or '-')[:18]
            room = (device['room_name'] or '-')[:8]
            status = "在线" if device['online'] else "离线"
            realtime = self._format_device_status(device['did'])[:28]
            
            last_seen = device['last_seen'] or '-'
            if last_seen != '-':
                try:
                    dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                    last_seen = dt.strftime('%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"{i:<4} {did:<12} {name:<20} {model:<20} {room:<10} {status:<6} {realtime:<30} {last_seen:<20}")
        print("=" * 140 + "\n")

    def _show_device_detail(self, args):
        """显示设备详情"""
        if not args:
            print("用法: detail <ID/Idx>")
            return
            
        device = self._get_device_by_arg(args[0])
        if not device:
            return
            
        print("\n设备基本信息:")
        print(json.dumps(dict(device), indent=2, default=str))
        
        print("\n最新属性数据:")
        props = self.database.get_latest_device_properties(device['did'])
        print(json.dumps(props, indent=2, default=str))
        print()

    def _simulate_detail_window(self, args):
        """模拟详情窗口"""
        if not args:
            print("用法: sim <ID/Idx>")
            return
            
        device = self._get_device_by_arg(args[0])
        if not device:
            return
            
        did = device['did']
        print("\n" + "=" * 60)
        print(f" 详情窗口模拟: {device['name']}")
        print("=" * 60)
        
        print(f"基本信息:")
        print(f"  DID:  {did}")
        print(f"  型号: {device['model']}")
        print(f"  IP:   {device.get('local_ip', 'N/A')}")
        print("-" * 60)
        
        print("实时属性:")
        props = self.database.get_latest_device_properties(did)
        if props:
            for name, data in props.items():
                print(f"  {name:<20}: {data['value']} ({data['value_type']})")
                print(f"    更新时间: {data['timestamp']}")
        else:
            print("  (无数据)")
        print("-" * 60)
        
        print("最近历史 (模拟图表数据源):")
        key_props = ['temperature', 'humidity', 'power', 'battery-level']
        found_history = False
        for prop in key_props:
            history = self.database.get_device_properties_history(did, prop, limit=3)
            if history:
                found_history = True
                print(f"  属性: {prop}")
                for h in history:
                    print(f"    {h['timestamp']}: {h['property_value']}")
        
        if not found_history:
            print("  (无历史数据)")
        print("=" * 60 + "\n")

    def _show_status(self):
        """显示系统状态"""
        stats = self.database.get_statistics()
        print("\n系统状态:")
        print(f"  监控运行中: {self.monitor.is_running}")
        print(f"  设备总数:   {stats['total_devices']}")
        print(f"  在线设备:   {stats['online_devices']}")
        print(f"  未解决报警: {stats['unresolved_alerts']}")
        print()
