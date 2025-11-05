"""设备监控核心模块"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from threading import Thread, Event, Lock
from queue import Queue, Empty
import sys

# 添加mijia-api到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "mijia-api"))

from mijiaAPI import mijiaAPI, mijiaDevice, mijiaLogin

from .database import DatabaseManager
from ..utils.logger import get_logger
from ..utils.config_loader import ConfigLoader

logger = get_logger(__name__)


class DeviceMonitor:
    """设备监控管理类"""
    
    def __init__(self, config: ConfigLoader, database: DatabaseManager):
        """
        初始化设备监控器
        
        Args:
            config: 配置加载器
            database: 数据库管理器
        """
        self.config = config
        self.database = database
        self.api: Optional[mijiaAPI] = None
        self.devices: Dict[str, Dict[str, Any]] = {}  # did -> device_info
        self.monitored_devices: Dict[str, mijiaDevice] = {}  # did -> mijiaDevice
        
        self.is_running = False
        self.stop_event = Event()
        self.monitor_threads: List[Thread] = []
        self.task_queue = Queue()
        self.lock = Lock()
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'device_update': [],
            'device_offline': [],
            'device_online': [],
            'property_alert': [],
            'error': []
        }
        
        # 初始化米家API
        self._init_mijia_api()
    
    def _init_mijia_api(self) -> bool:
        """初始化米家API"""
        try:
            auth_file = self.config.get('mijia.auth_file', 'config/mijia_auth.json')
            auth_path = Path(auth_file)
            
            if not auth_path.exists():
                logger.warning(f"认证文件不存在: {auth_path}")
                return False
            
            with open(auth_path, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            self.api = mijiaAPI(auth_data)
            
            if not self.api.available:
                logger.error("米家API认证已过期,请重新登录")
                return False
            
            logger.info("米家API初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化米家API失败: {e}")
            return False
    
    def login(self, use_qr: bool = True, username: str = None, password: str = None) -> bool:
        """
        登录米家账号
        
        Args:
            use_qr: 是否使用二维码登录
            username: 用户名(账号密码登录时使用)
            password: 密码(账号密码登录时使用)
            
        Returns:
            是否登录成功
        """
        try:
            login = mijiaLogin()
            
            if use_qr:
                logger.info("请使用米家APP扫描二维码登录")
                auth_data = login.QRlogin()
            else:
                if not username or not password:
                    logger.error("账号密码登录需要提供用户名和密码")
                    return False
                auth_data = login.login(username, password)
            
            if auth_data:
                # 保存认证信息
                auth_file = self.config.get('mijia.auth_file', 'config/mijia_auth.json')
                auth_path = Path(auth_file)
                auth_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(auth_path, 'w', encoding='utf-8') as f:
                    json.dump(auth_data, f, indent=2)
                
                logger.info("登录成功,认证信息已保存")
                
                # 重新初始化API
                return self._init_mijia_api()
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录过程出错: {e}")
            return False
    
    def fetch_devices(self) -> bool:
        """从米家云端获取设备列表"""
        if not self.api:
            logger.error("米家API未初始化")
            return False
        
        try:
            devices_list = self.api.get_devices_list()
            logger.info(f"获取到 {len(devices_list)} 个设备")
            
            with self.lock:
                for device in devices_list:
                    did = device['did']
                    self.devices[did] = device
                    
                    # 保存到数据库
                    self.database.add_or_update_device(device)
            
            return True
            
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")
            return False
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """获取所有设备列表"""
        return list(self.devices.values())
    
    def get_device(self, did: str) -> Optional[Dict[str, Any]]:
        """获取指定设备信息"""
        return self.devices.get(did)
    
    def start_monitor(self, device_ids: List[str] = None) -> bool:
        """
        启动设备监控
        
        Args:
            device_ids: 要监控的设备ID列表,为None则监控所有设备
            
        Returns:
            是否启动成功
        """
        if not self.api:
            logger.error("米家API未初始化")
            return False
        
        if self.is_running:
            logger.warning("监控已在运行中")
            return False
        
        try:
            # 确定要监控的设备
            if device_ids is None:
                monitor_list = list(self.devices.keys())
            else:
                monitor_list = [did for did in device_ids if did in self.devices]
            
            if not monitor_list:
                logger.error("没有可监控的设备")
                return False
            
            logger.info(f"开始监控 {len(monitor_list)} 个设备")
            
            self.is_running = True
            self.stop_event.clear()
            
            # 启动工作线程
            worker_count = self.config.get('monitor.worker_threads', 5)
            for i in range(worker_count):
                thread = Thread(target=self._monitor_worker, name=f"Monitor-Worker-{i}")
                thread.daemon = True
                thread.start()
                self.monitor_threads.append(thread)
            
            # 启动任务调度线程
            scheduler_thread = Thread(target=self._task_scheduler, args=(monitor_list,))
            scheduler_thread.daemon = True
            scheduler_thread.start()
            self.monitor_threads.append(scheduler_thread)
            
            logger.info("监控线程已启动")
            return True
            
        except Exception as e:
            logger.error(f"启动监控失败: {e}")
            self.is_running = False
            return False
    
    def stop_monitor(self) -> None:
        """停止设备监控"""
        if not self.is_running:
            return
        
        logger.info("正在停止监控...")
        self.is_running = False
        self.stop_event.set()
        
        # 等待所有线程结束
        for thread in self.monitor_threads:
            thread.join(timeout=5)
        
        self.monitor_threads.clear()
        logger.info("监控已停止")
    
    def _task_scheduler(self, device_ids: List[str]) -> None:
        """任务调度器"""
        last_check = {}
        
        while self.is_running and not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                for did in device_ids:
                    if did not in self.devices:
                        continue
                    
                    device = self.devices[did]
                    
                    # 获取设备的监控间隔
                    interval = self._get_device_interval(device)
                    
                    # 检查是否需要监控
                    if did not in last_check or current_time - last_check[did] >= interval:
                        self.task_queue.put({'did': did, 'device': device})
                        last_check[did] = current_time
                
                # 等待一段时间
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"任务调度出错: {e}")
                time.sleep(5)
    
    def _monitor_worker(self) -> None:
        """监控工作线程"""
        while self.is_running and not self.stop_event.is_set():
            try:
                # 从队列获取任务
                task = self.task_queue.get(timeout=1)
                
                if task:
                    self._monitor_device(task['did'], task['device'])
                
                self.task_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"监控工作线程出错: {e}")
    
    def _monitor_device(self, did: str, device_info: Dict[str, Any]) -> None:
        """监控单个设备"""
        try:
            # 获取设备属性
            model = device_info.get('model')
            if not model:
                return
            
            # 尝试获取设备的属性定义
            try:
                from mijiaAPI import get_device_info
                dev_spec = get_device_info(model)
            except Exception:
                logger.debug(f"无法获取设备 {device_info['name']} 的属性定义")
                return
            
            # 获取所有可读属性
            properties = {}
            for prop in dev_spec.get('properties', []):
                if 'r' in prop.get('rw', ''):
                    try:
                        prop_name = prop['name']
                        method = prop['method'].copy()
                        method['did'] = did
                        
                        result = self.api.get_devices_prop([method])
                        if result and result[0].get('code') == 0:
                            properties[prop_name] = result[0].get('value')
                            
                            # 保存属性到数据库
                            self.database.add_device_property(
                                did, prop_name, result[0].get('value')
                            )
                    except Exception:
                        continue
            
            # 保存设备状态
            if properties:
                self.database.add_device_status(did, properties, online=True)
                
                # 触发回调
                self._trigger_callback('device_update', {
                    'did': did,
                    'device': device_info,
                    'properties': properties
                })
                
                # 检查报警规则
                self._check_alerts(did, device_info, properties)
            
        except Exception as e:
            logger.error(f"监控设备 {device_info.get('name', did)} 失败: {e}")
            
            # 记录设备离线
            self.database.add_device_status(did, {}, online=False)
            self._trigger_callback('device_offline', {'did': did, 'device': device_info})
    
    def _get_device_interval(self, device: Dict[str, Any]) -> int:
        """获取设备的监控间隔"""
        # 从数据库获取自定义间隔
        db_device = self.database.get_device(device['did'])
        if db_device and db_device.get('monitor_interval'):
            return db_device['monitor_interval']
        
        # 根据设备类型获取间隔
        device_type = self._get_device_type(device['model'])
        intervals = self.config.get('monitor.device_intervals', {})
        
        return intervals.get(device_type, self.config.get('monitor.default_interval', 60))
    
    def _get_device_type(self, model: str) -> str:
        """根据model判断设备类型"""
        model_lower = model.lower()
        
        if 'sensor' in model_lower or 'miaomiaoce' in model_lower:
            return 'sensor'
        elif 'light' in model_lower or 'yeelink' in model_lower:
            return 'light'
        elif 'aircondition' in model_lower or 'acpartner' in model_lower:
            return 'airconditioner'
        elif 'plug' in model_lower or 'chuangmi' in model_lower:
            return 'plug'
        elif 'vacuum' in model_lower or 'roborock' in model_lower:
            return 'vacuum'
        else:
            return 'default'
    
    def _check_alerts(
        self,
        did: str,
        device_info: Dict[str, Any],
        properties: Dict[str, Any]
    ) -> None:
        """检查报警规则"""
        alert_rules = self.config.get('alerts.rules', [])
        
        if not self.config.get('alerts.enabled', True):
            return
        
        device_type = self._get_device_type(device_info['model'])
        
        for rule in alert_rules:
            if not rule.get('enabled', True):
                continue
            
            if rule.get('device_type') != device_type:
                continue
            
            prop_name = rule.get('property')
            if prop_name not in properties:
                continue
            
            value = properties[prop_name]
            condition = rule.get('condition')
            threshold = rule.get('threshold')
            
            triggered = False
            if condition == '>' and value > threshold:
                triggered = True
            elif condition == '<' and value < threshold:
                triggered = True
            elif condition == '==' and value == threshold:
                triggered = True
            elif condition == '>=' and value >= threshold:
                triggered = True
            elif condition == '<=' and value <= threshold:
                triggered = True
            
            if triggered:
                alert_title = f"{device_info['name']} - {rule['name']}"
                alert_message = (
                    f"属性 {prop_name} 的值为 {value}, "
                    f"触发条件: {condition} {threshold}"
                )
                
                self.database.add_alert(
                    did, 'property_alert', alert_title, alert_message, 'WARNING'
                )
                
                self._trigger_callback('property_alert', {
                    'did': did,
                    'device': device_info,
                    'rule': rule,
                    'property': prop_name,
                    'value': value
                })
    
    def register_callback(self, event: str, callback: Callable) -> None:
        """
        注册回调函数
        
        Args:
            event: 事件类型 (device_update, device_offline, device_online, property_alert, error)
            callback: 回调函数
        """
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, data: Dict[str, Any]) -> None:
        """触发回调函数"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"回调函数执行失败: {e}")
