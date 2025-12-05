"""配置文件加载器"""
import os
import yaml
from typing import Any, Dict
from pathlib import Path
from .path_utils import get_app_path


class ConfigLoader:
    """配置文件加载和管理类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径,默认为项目根目录下的config/config.yaml
        """
        if config_path is None:
            # 获取应用程序运行目录
            root_dir = get_app_path()
            config_path = root_dir / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"警告: 配置文件 {self.config_path} 不存在,使用默认配置")
            self.config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"错误: 配置文件解析失败: {e}")
            self.config = self._get_default_config()
    
    def save(self) -> None:
        """保存配置到文件"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"错误: 保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项(支持点号分隔的嵌套键)
        
        Args:
            key: 配置键,例如 "database.path"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项(支持点号分隔的嵌套键)
        
        Args:
            key: 配置键,例如 "database.path"
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到倒数第二个键
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最后一个键的值
        config[keys[-1]] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'app': {
                'name': '米家设备监控',
                'version': '1.0.0',
                'language': 'zh_CN',
                'theme': 'light'
            },
            'mijia': {
                'auth_file': 'config/mijia_auth.json',
                'timeout': 10,
                'retry': 3
            },
            'monitor': {
                'default_interval': 60,
                'auto_start': True,
                'worker_threads': 5
            },
            'database': {
                'path': 'data/monitor.db',
                'retention_days': 30,
                'auto_cleanup': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/mi-monitor.log',
                'max_size': 10,
                'backup_count': 5,
                'console': True
            },
            'notification': {
                'enabled': True,
                'types': {
                    'device_offline': True,
                    'device_online': True,
                    'property_alert': True
                }
            },
            'ui': {
                'main_window': {
                    'width': 1200,
                    'height': 800,
                    'start_minimized': False
                },
                'system_tray': {
                    'enabled': True,
                    'close_to_tray': True
                },
                'autostart': {
                    'enabled': False
                }
            }
        }
