"""数据库管理模块"""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """SQLite数据库管理类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 支持字典式访问
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 设备表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    did TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    model TEXT NOT NULL,
                    room_name TEXT,
                    home_id TEXT,
                    device_type TEXT,
                    online BOOLEAN DEFAULT 1,
                    enabled BOOLEAN DEFAULT 1,
                    monitor_interval INTEGER DEFAULT 60,
                    properties TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 设备状态历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    did TEXT NOT NULL,
                    status_data TEXT NOT NULL,
                    online BOOLEAN DEFAULT 1,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (did) REFERENCES devices(did)
                )
            ''')
            
            # 设备属性历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    did TEXT NOT NULL,
                    property_name TEXT NOT NULL,
                    property_value TEXT NOT NULL,
                    value_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (did) REFERENCES devices(did)
                )
            ''')
            
            # 报警记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    did TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'INFO',
                    title TEXT NOT NULL,
                    message TEXT,
                    resolved BOOLEAN DEFAULT 0,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (did) REFERENCES devices(did)
                )
            ''')
            
            # 监控配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monitor_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    did TEXT NOT NULL,
                    property_name TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    alert_enabled BOOLEAN DEFAULT 0,
                    alert_condition TEXT,
                    alert_threshold REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (did) REFERENCES devices(did),
                    UNIQUE(did, property_name)
                )
            ''')
            
            # 系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    extra_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device_status_did_timestamp 
                ON device_status(did, timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device_properties_did_timestamp 
                ON device_properties(did, property_name, timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_did_created 
                ON alerts(did, created_at DESC)
            ''')
            
            logger.info("数据库初始化完成")
    
    def add_or_update_device(self, device_info: Dict[str, Any]) -> bool:
        """
        添加或更新设备信息
        
        Args:
            device_info: 设备信息字典
            
        Returns:
            是否成功
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查设备是否存在
                cursor.execute('SELECT did FROM devices WHERE did = ?', (device_info['did'],))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # 更新设备
                    cursor.execute('''
                        UPDATE devices SET 
                            name = ?, model = ?, room_name = ?, home_id = ?,
                            device_type = ?, online = ?, last_seen = ?, updated_at = ?
                        WHERE did = ?
                    ''', (
                        device_info.get('name'),
                        device_info.get('model'),
                        device_info.get('roomName'),
                        device_info.get('homeId'),
                        device_info.get('type'),
                        device_info.get('online', True),
                        datetime.now(),
                        datetime.now(),
                        device_info['did']
                    ))
                else:
                    # 插入新设备
                    cursor.execute('''
                        INSERT INTO devices 
                        (did, name, model, room_name, home_id, device_type, online, properties)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        device_info['did'],
                        device_info.get('name'),
                        device_info.get('model'),
                        device_info.get('roomName'),
                        device_info.get('homeId'),
                        device_info.get('type'),
                        device_info.get('online', True),
                        json.dumps(device_info.get('properties', {}))
                    ))
                
                return True
        except Exception as e:
            logger.error(f"添加/更新设备失败: {e}")
            return False
    
    def get_device(self, did: str) -> Optional[Dict[str, Any]]:
        """获取设备信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices WHERE did = ?', (did,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_all_devices(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """获取所有设备"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if enabled_only:
                cursor.execute('SELECT * FROM devices WHERE enabled = 1 ORDER BY name')
            else:
                cursor.execute('SELECT * FROM devices ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def add_device_status(self, did: str, status_data: Dict[str, Any], online: bool = True) -> bool:
        """添加设备状态记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO device_status (did, status_data, online)
                    VALUES (?, ?, ?)
                ''', (did, json.dumps(status_data), online))
                
                # 更新设备表的last_seen
                cursor.execute('''
                    UPDATE devices SET last_seen = ?, online = ? WHERE did = ?
                ''', (datetime.now(), online, did))
                
                return True
        except Exception as e:
            logger.error(f"添加设备状态失败: {e}")
            return False
    
    def add_device_property(
        self,
        did: str,
        property_name: str,
        property_value: Any,
        value_type: str = None
    ) -> bool:
        """添加设备属性记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 转换值为字符串存储
                if isinstance(property_value, (dict, list)):
                    value_str = json.dumps(property_value)
                else:
                    value_str = str(property_value)
                
                if value_type is None:
                    value_type = type(property_value).__name__
                
                cursor.execute('''
                    INSERT INTO device_properties 
                    (did, property_name, property_value, value_type)
                    VALUES (?, ?, ?, ?)
                ''', (did, property_name, value_str, value_type))
                
                return True
        except Exception as e:
            logger.error(f"添加设备属性失败: {e}")
            return False
    
    def get_device_properties_history(
        self,
        did: str,
        property_name: str,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取设备属性历史记录"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT property_value, value_type, timestamp 
                FROM device_properties 
                WHERE did = ? AND property_name = ?
            '''
            params = [did, property_name]
            
            if start_time:
                query += ' AND timestamp >= ?'
                params.append(start_time)
            
            if end_time:
                query += ' AND timestamp <= ?'
                params.append(end_time)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def add_alert(
        self,
        did: str,
        alert_type: str,
        title: str,
        message: str = None,
        severity: str = 'INFO'
    ) -> bool:
        """添加报警记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO alerts (did, alert_type, severity, title, message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (did, alert_type, severity, title, message))
                return True
        except Exception as e:
            logger.error(f"添加报警记录失败: {e}")
            return False
    
    def get_unresolved_alerts(self, did: str = None) -> List[Dict[str, Any]]:
        """获取未解决的报警"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if did:
                cursor.execute('''
                    SELECT * FROM alerts 
                    WHERE resolved = 0 AND did = ? 
                    ORDER BY created_at DESC
                ''', (did,))
            else:
                cursor.execute('''
                    SELECT * FROM alerts 
                    WHERE resolved = 0 
                    ORDER BY created_at DESC
                ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def resolve_alert(self, alert_id: int) -> bool:
        """标记报警为已解决"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE alerts 
                    SET resolved = 1, resolved_at = ? 
                    WHERE id = ?
                ''', (datetime.now(), alert_id))
                return True
        except Exception as e:
            logger.error(f"解决报警失败: {e}")
            return False
    
    def cleanup_old_data(self, retention_days: int) -> Tuple[int, int]:
        """
        清理过期数据
        
        Args:
            retention_days: 数据保留天数
            
        Returns:
            (删除的状态记录数, 删除的属性记录数)
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 清理设备状态历史
            cursor.execute('''
                DELETE FROM device_status WHERE timestamp < ?
            ''', (cutoff_date,))
            status_deleted = cursor.rowcount
            
            # 清理设备属性历史
            cursor.execute('''
                DELETE FROM device_properties WHERE timestamp < ?
            ''', (cutoff_date,))
            properties_deleted = cursor.rowcount
            
            logger.info(
                f"清理完成: 删除 {status_deleted} 条状态记录, "
                f"{properties_deleted} 条属性记录"
            )
            
            return status_deleted, properties_deleted
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 设备数量
            cursor.execute('SELECT COUNT(*) as count FROM devices')
            stats['total_devices'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM devices WHERE online = 1')
            stats['online_devices'] = cursor.fetchone()['count']
            
            # 状态记录数量
            cursor.execute('SELECT COUNT(*) as count FROM device_status')
            stats['total_status_records'] = cursor.fetchone()['count']
            
            # 属性记录数量
            cursor.execute('SELECT COUNT(*) as count FROM device_properties')
            stats['total_property_records'] = cursor.fetchone()['count']
            
            # 未解决的报警数量
            cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE resolved = 0')
            stats['unresolved_alerts'] = cursor.fetchone()['count']
            
            # 数据库大小
            stats['db_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
            
            return stats
