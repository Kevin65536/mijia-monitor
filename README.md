# 米家设备监控系统 (MiMonitor)

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

一个功能强大的米家智能设备实时监控系统,专为Windows环境设计

</div>

## ✨ 功能特性

- 🔄 **实时监控** - 自动定期采集设备状态,支持自定义监控间隔
- 📊 **数据存储** - 使用SQLite本地存储历史数据,支持数据导出
- 🎯 **智能报警** - 可配置的报警规则,属性异常实时通知
- 💻 **友好界面** - 基于PyQt6的现代化图形界面
- 🔔 **系统托盘** - 最小化到托盘,后台静默运行
- 📦 **一键打包** - 可打包为独立exe文件,无需安装Python环境
- 🔐 **安全认证** - 支持二维码登录和账号密码登录
- 📈 **数据可视化** - 设备状态历史趋势图表展示

## 📋 系统要求

- **操作系统**: Windows 10/11 (64位)
- **Python版本**: 3.9 或更高版本 (开发环境)
- **内存**: 建议 4GB 以上
- **磁盘空间**: 至少 200MB 可用空间

## 🚀 快速开始

### 方式一: 使用已打包的exe文件 (推荐)

1. 从 [Releases](https://github.com/yourusername/mi-monitor/releases) 下载最新版本
2. 解压到任意目录
3. 双击 `启动监控.bat` 或直接运行 `MiMonitor.exe`
4. 首次运行需要登录米家账号

### 方式二: 从源码运行 (开发者)

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/mi-monitor.git
cd mi-monitor
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

**或者直接运行开发脚本:**
```bash
scripts\run_dev.bat
```

#### 3. 运行程序

```bash
python -m src.main
```

## 📖 使用说明

### 首次使用

1. **登录米家账号**
   - 点击"登录米家"按钮
   - 推荐使用"二维码登录"(更安全快捷)
   - 使用米家APP扫描二维码完成登录

2. **刷新设备列表**
   - 点击"刷新设备"按钮
   - 系统会从米家云端获取所有设备

3. **启动监控**
   - 点击"启动监控"按钮
   - 系统开始定期采集设备状态

### 配置说明

配置文件位于 `config/config.yaml`,可以自定义以下内容:

#### 监控间隔设置

```yaml
monitor:
  default_interval: 60  # 默认监控间隔(秒)
  device_intervals:
    sensor: 300        # 传感器类设备
    light: 60          # 灯具类设备
    airconditioner: 180 # 空调类设备
```

#### 报警规则设置

```yaml
alerts:
  enabled: true
  rules:
    - name: "温度过高"
      device_type: "sensor"
      property: "temperature"
      condition: ">"
      threshold: 35
      enabled: true
```

#### 数据保留设置

```yaml
database:
  retention_days: 30    # 数据保留天数(0表示永久)
  auto_cleanup: true    # 自动清理过期数据
```

### 界面功能

#### 设备列表
- 显示所有米家设备
- 实时状态显示(在线/离线)
- 点击"查看详情"查看设备信息
- 可自定义监控间隔

#### 报警记录
- 查看所有报警历史
- 按严重程度分类显示
- 支持标记为已解决

#### 统计信息
- 设备总数和在线数量
- 数据库记录统计
- 存储空间占用

## 🔧 打包发布

### 打包为独立exe文件

**Windows:**
```bash
# 方式1: 使用打包脚本(推荐)
scripts\build.bat

# 方式2: 手动打包
pyinstaller mi-monitor.spec
```

打包完成后,`dist` 目录下包含所有必要文件,可直接分发给用户。

### 发布清单

发布时需要包含以下文件:
- `MiMonitor.exe` - 主程序
- `config/` - 配置目录
- `启动监控.bat` - 快捷启动脚本
- `README.md` - 使用说明

## 📂 项目结构

```
mi-monitor/
├── src/                    # 源代码目录
│   ├── core/              # 核心功能模块
│   │   ├── database.py    # 数据库管理
│   │   └── monitor.py     # 设备监控
│   ├── ui/                # 界面模块
│   │   └── main_window.py # 主窗口
│   ├── utils/             # 工具模块
│   │   ├── config_loader.py  # 配置加载
│   │   └── logger.py      # 日志管理
│   └── main.py            # 程序入口
├── config/                # 配置文件
│   └── config.yaml        # 主配置文件
├── data/                  # 数据目录
│   └── monitor.db         # SQLite数据库
├── logs/                  # 日志目录
├── resources/             # 资源文件
│   └── icons/            # 图标资源
├── scripts/              # 脚本工具
│   ├── build.bat         # Windows打包脚本
│   └── run_dev.bat       # 开发运行脚本
├── requirements.txt      # Python依赖
├── pyproject.toml        # 项目配置
├── mi-monitor.spec       # PyInstaller配置
└── README.md            # 项目说明
```

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| **Python 3.9+** | 主要编程语言 |
| **PyQt6** | 跨平台GUI框架 |
| **mijiaAPI** | 米家设备API封装 |
| **SQLite** | 轻量级本地数据库 |
| **PyInstaller** | Python程序打包工具 |
| **PyYAML** | YAML配置文件解析 |
| **Pandas** | 数据处理和分析 |

## 🎯 设计优势

### 为什么选择这个技术栈?

1. **PyQt6/PySide6**
   - ✅ 原生Windows外观和性能
   - ✅ 完善的跨平台支持
   - ✅ 丰富的组件和成熟的生态

2. **PyInstaller打包**
   - ✅ 一键打包成单一exe文件
   - ✅ 用户无需安装Python环境
   - ✅ 发布部署极其简便

3. **SQLite数据库**
   - ✅ 零配置,嵌入式数据库
   - ✅ 无需额外服务,降低复杂度
   - ✅ 性能优秀,足够应对监控需求

4. **多线程架构**
   - ✅ UI界面不会卡顿
   - ✅ 多设备并行监控
   - ✅ 响应迅速,体验流畅

## ❓ 常见问题

### Q: 为什么推荐使用二维码登录?
A: 账号密码登录可能需要手机验证码验证,二维码登录更简单快捷且无需输入密码。

### Q: 可以监控多少个设备?
A: 理论上没有限制,默认配置可稳定监控100+设备。如需监控更多设备,可调整配置中的线程数量。

### Q: 数据会占用多少空间?
A: 取决于设备数量和属性数量,平均每个设备每天约1-5MB。可通过设置数据保留天数自动清理。

### Q: 可以在后台运行吗?
A: 可以。最小化窗口会自动缩小到系统托盘,程序继续在后台运行。

### Q: 如何导出数据?
A: 数据库文件位于 `data/monitor.db`,可以使用SQLite工具直接查看,或通过程序的导出功能(未来版本实现)。

## 🔮 未来计划

- [ ] 图表可视化功能增强
- [ ] 设备控制功能
- [ ] 更多报警方式(邮件、微信等)
- [ ] 数据导出功能(CSV/Excel)
- [ ] 场景自动化触发
- [ ] 多语言支持
- [ ] 跨平台支持(macOS/Linux)

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

基于 [mijiaAPI](https://github.com/Do1e/mijia-api) 项目开发。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## ⚠️ 免责声明

- 本项目仅供学习交流使用
- 请勿用于商业用途
- 使用本项目产生的任何后果由用户自行承担

## 📧 联系方式

如有问题或建议,请通过以下方式联系:
- GitHub Issues: [提交问题](https://github.com/yourusername/mi-monitor/issues)
- Email: your.email@example.com

---

<div align="center">

**如果这个项目对你有帮助,请给个 ⭐ Star 支持一下!**

Made with ❤️ by [Your Name]

</div>
