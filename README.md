# 米家设备监控系统 (MiMonitor)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

米家智能设备实时监控系统,为Windows环境设计

</div>

## ✨ 功能特性

- 🔄 **实时监控** - 自动定期采集设备状态,支持自定义监控间隔
- 📊 **数据存储** - 使用SQLite本地存储历史数据
- 💻 **友好界面** - 基于PyQt6的现代化图形界面
- 🔐 **安全认证** - 使用二维码扫码登录

## 📋 系统要求

- **操作系统**: Windows 10/11 (64位)
- **Python版本**: 3.9 或更高版本 (开发环境)
- **内存**: 建议 4GB 以上
- **磁盘空间**: 至少 200MB 可用空间

## 🚀 快速开始

### 方式一: 使用发布压缩包 (推荐)

1. 从 [Releases](https://github.com/Kevin65536/mijia-monitor/releases) 下载最新的 `MiMonitor.zip`
2. 将压缩包完整解压到任意目录,确保 `MiMonitor.exe` 与 `config/`、`data/`、`logs/` 同级
3. 双击 `MiMonitor.exe` 启动程序
4. 首次运行会在 `config/config.yaml` 中保存本地配置,并需要通过二维码登录米家账号

### 方式二: 从源码运行 (开发者)

#### 1. 克隆项目

```bash
git clone https://github.com/Kevin65536/mijia-monitor.git
cd mijia-monitor
```

#### 2. 安装依赖

**Windows (PowerShell/CMD):**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 运行程序

```bash
python -m src.main
```

## 📖 使用说明

### 发布包结构

GitHub Release 中提供的 `MiMonitor.zip` 解压后包含以下内容:

| 路径 | 说明 |
| --- | --- |
| `MiMonitor.exe` | 主程序，双击直接运行 |
| `config/` | 默认配置与认证文件存放位置 (`config.yaml`, `mijia_auth.json`) |
| `data/` | SQLite 数据库存储目录，初始为空 |
| `logs/` | 日志输出目录，用于排查问题 |

发布压缩包已包含运行所需的全部文件,用户无需在 `AppData` 等位置写入数据,也不需要额外创建目录。更新程序时,只需备份当前目录(尤其是 `config/` 与 `data/`),替换 `MiMonitor.exe` 即可。

### 首次使用

1. **登录米家账号**
   - 点击"登录米家"按钮
   - 推荐使用"二维码登录"
   - 使用米家APP扫描二维码完成登录

2. **刷新设备列表**
   - 点击"刷新设备"按钮
   - 系统会从米家云端获取所有设备

3. **启动监控**
   - 点击"启动监控"按钮
   - 系统开始定期采集设备状态

### 界面功能

#### 设备列表

- 显示所有米家设备
- 实时状态显示(在线/离线)
- 点击"查看详情"查看设备信息
- 可自定义监控间隔

#### 统计信息

- 设备总数和在线数量
- 数据库记录统计
- 存储空间占用

## 🔮 未来计划

- [x] 图表可视化功能增强
- [ ] 设备控制功能
- [ ] 数据导出功能(CSV/Excel)
- [ ] 场景自动化触发

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

基于 [mijiaAPI](https://github.com/Do1e/mijia-api) 项目开发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## ⚠️ 免责声明

- 本项目仅供学习交流使用
- 请勿用于商业用途
- 使用本项目产生的任何后果由用户自行承担
