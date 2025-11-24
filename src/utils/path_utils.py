import sys
import os
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    用于访问打包在exe内部的资源文件(如图标、默认配置等)
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境: src/utils/path_utils.py -> src/utils -> src -> project_root
        base_path = Path(__file__).parent.parent.parent
    
    return base_path / relative_path

def get_app_path() -> Path:
    """
    获取应用程序运行目录
    用于访问外部配置文件、日志、数据库等
    """
    if getattr(sys, 'frozen', False):
        # 打包后: exe所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境: src/utils/path_utils.py -> src/utils -> src -> project_root
        return Path(__file__).parent.parent.parent
