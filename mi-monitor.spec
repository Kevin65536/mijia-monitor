# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller打包配置文件
使用方法: pyinstaller mi-monitor.spec
"""

import sys
from pathlib import Path

# 项目路径
project_root = Path(SPECPATH)
src_path = project_root / 'src'

# 添加mijia-api路径
mijia_api_path = project_root.parent / 'mijia-api'

# 图标路径
icon_path = project_root / 'resources' / 'icons' / 'app.ico'

block_cipher = None

# 分析主程序
a = Analysis(
    ['src/main.py'],
    pathex=[
        str(src_path),
        str(mijia_api_path),
    ],
    binaries=[],
    datas=[
        # 包含配置文件
        ('config/config.yaml', 'config'),
        # 包含资源文件 (图标等)
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'mijiaAPI',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'pyqtgraph',
        'numpy',
        'pandas',
        'yaml',
        'colorlog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 打包资源
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 生成可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MiMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口以便查看日志和使用命令行二维码登录
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 图标
    icon=str(icon_path),
)

# 如果需要生成目录形式的分发版本,取消下面的注释
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MiMonitor',
# )
