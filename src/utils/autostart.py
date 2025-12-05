"""开机自启动管理模块"""
import sys
import winreg
from pathlib import Path
from typing import Optional

from .logger import get_logger
from .path_utils import get_app_path

logger = get_logger(__name__)

# 注册表路径
REGISTRY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "MiMonitor"


def _get_executable_path() -> str:
    """
    获取当前可执行文件的路径
    
    Returns:
        可执行文件的完整路径
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的可执行文件
        return sys.executable
    else:
        # 开发模式下，使用 pythonw.exe 来运行脚本
        app_path = get_app_path()
        venv_pythonw = app_path / "venv" / "Scripts" / "pythonw.exe"
        
        if venv_pythonw.exists():
            # 使用虚拟环境的 pythonw.exe
            return f'"{venv_pythonw}" -m src.main'
        else:
            # 使用系统 Python
            python_dir = Path(sys.executable).parent
            pythonw = python_dir / "pythonw.exe"
            if pythonw.exists():
                return f'"{pythonw}" -m src.main'
            return f'"{sys.executable}" -m src.main'


def is_autostart_enabled() -> bool:
    """
    检查开机自启动是否已启用
    
    Returns:
        如果已启用开机自启动返回 True，否则返回 False
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        logger.error(f"检查自启动状态失败: {e}")
        return False


def enable_autostart() -> bool:
    """
    启用开机自启动
    
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        executable_path = _get_executable_path()
        
        # 如果是打包后的应用，添加工作目录
        if getattr(sys, 'frozen', False):
            app_dir = Path(sys.executable).parent
            # 使用引号包裹路径以处理空格
            command = f'"{executable_path}"'
        else:
            # 开发模式需要在项目目录下运行
            app_dir = get_app_path()
            command = f'cd /d "{app_dir}" && {executable_path}'
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            logger.info(f"已启用开机自启动: {command}")
            return True
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        logger.error(f"启用自启动失败: {e}")
        return False


def disable_autostart() -> bool:
    """
    禁用开机自启动
    
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
            logger.info("已禁用开机自启动")
            return True
        except FileNotFoundError:
            # 值不存在，视为已禁用
            logger.info("自启动项不存在，无需禁用")
            return True
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        logger.error(f"禁用自启动失败: {e}")
        return False


def set_autostart(enabled: bool) -> bool:
    """
    设置开机自启动状态
    
    Args:
        enabled: True 启用，False 禁用
        
    Returns:
        成功返回 True，失败返回 False
    """
    if enabled:
        return enable_autostart()
    else:
        return disable_autostart()


def get_autostart_command() -> Optional[str]:
    """
    获取当前自启动命令
    
    Returns:
        自启动命令字符串，如果未设置则返回 None
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return value
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        logger.error(f"获取自启动命令失败: {e}")
        return None
