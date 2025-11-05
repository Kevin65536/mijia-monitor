# 开发文档

## 开发环境搭建

### 前置要求
- Python 3.9+
- pip
- virtualenv (推荐)

### 安装步骤

1. 创建虚拟环境:
```bash
python -m venv venv
```

2. 激活虚拟环境:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

## 项目架构

### 核心模块

#### 1. Database Manager (`src/core/database.py`)
负责所有数据库操作:
- 设备信息管理
- 状态历史记录
- 属性数据存储
- 报警记录管理
- 数据清理和统计

主要方法:
- `add_or_update_device()` - 添加或更新设备
- `add_device_status()` - 记录设备状态
- `add_device_property()` - 记录设备属性
- `get_device_properties_history()` - 获取历史数据
- `cleanup_old_data()` - 清理过期数据

#### 2. Device Monitor (`src/core/monitor.py`)
设备监控核心:
- 米家API集成
- 多线程任务调度
- 设备状态采集
- 报警规则检查
- 事件回调机制

主要方法:
- `start_monitor()` - 启动监控
- `stop_monitor()` - 停止监控
- `fetch_devices()` - 获取设备列表
- `register_callback()` - 注册事件回调

#### 3. Main Window (`src/ui/main_window.py`)
主界面实现:
- 设备列表展示
- 报警记录查看
- 统计信息显示
- 系统托盘集成
- 用户交互处理

### 数据流

```
米家云端 → mijiaAPI → DeviceMonitor → DatabaseManager → SQLite
                          ↓
                     事件回调 → MainWindow → UI更新
```

### 线程模型

1. **主线程**: GUI界面和事件循环
2. **调度线程**: 任务调度和队列管理
3. **工作线程**: 设备监控和数据采集(多个)

## 配置系统

### config.yaml 结构

```yaml
app:           # 应用基本信息
mijia:         # 米家API配置
monitor:       # 监控配置
database:      # 数据库配置
logging:       # 日志配置
notification:  # 通知配置
alerts:        # 报警配置
ui:            # 界面配置
```

### 配置加载

使用 `ConfigLoader` 类:
```python
config = ConfigLoader()
value = config.get('monitor.default_interval', 60)
config.set('monitor.auto_start', True)
config.save()
```

## 数据库设计

### 表结构

#### devices - 设备表
- `did` (主键) - 设备ID
- `name` - 设备名称
- `model` - 设备型号
- `room_name` - 房间名称
- `online` - 在线状态
- `monitor_interval` - 监控间隔
- 时间戳字段

#### device_status - 状态历史
- `id` (主键)
- `did` (外键)
- `status_data` (JSON)
- `timestamp`

#### device_properties - 属性历史
- `id` (主键)
- `did` (外键)
- `property_name`
- `property_value`
- `timestamp`

#### alerts - 报警记录
- `id` (主键)
- `did` (外键)
- `alert_type`
- `severity`
- `title`
- `message`
- `resolved`
- `created_at`

## 扩展开发

### 添加新的设备类型

1. 在 `config.yaml` 中添加设备类型配置:
```yaml
monitor:
  device_intervals:
    new_device_type: 120
```

2. 在 `monitor.py` 的 `_get_device_type()` 方法中添加识别逻辑

### 添加新的报警规则

在 `config.yaml` 中添加:
```yaml
alerts:
  rules:
    - name: "自定义报警"
      device_type: "sensor"
      property: "property_name"
      condition: ">"
      threshold: 100
      enabled: true
```

### 添加新的界面功能

1. 在 `main_window.py` 中创建新的Tab
2. 实现对应的UI组件
3. 连接数据源和事件处理

## 调试技巧

### 启用调试模式

在 `config.yaml` 中:
```yaml
developer:
  debug: true
logging:
  level: "DEBUG"
```

### 查看日志

日志文件位于 `logs/mi-monitor.log`

### 数据库调试

使用SQLite工具查看数据库:
```bash
sqlite3 data/monitor.db
.tables
.schema devices
SELECT * FROM devices;
```

## 测试

### 单元测试
```bash
pytest tests/
```

### 手动测试清单
- [ ] 登录功能
- [ ] 设备列表刷新
- [ ] 启动/停止监控
- [ ] 系统托盘功能
- [ ] 报警触发
- [ ] 数据持久化

## 打包注意事项

### PyInstaller常见问题

1. **缺少模块**: 在 `mi-monitor.spec` 的 `hiddenimports` 中添加
2. **资源文件**: 使用 `datas` 参数包含
3. **路径问题**: 使用相对路径,考虑打包后的目录结构

### 测试打包版本

打包后务必测试:
- [ ] 程序能否正常启动
- [ ] 配置文件是否正确加载
- [ ] 数据库能否正常创建
- [ ] 所有功能是否正常工作

## 代码规范

### 命名约定
- 类名: `PascalCase`
- 函数/方法: `snake_case`
- 常量: `UPPER_CASE`
- 私有方法: `_private_method`

### 文档字符串
```python
def function_name(param1: str, param2: int) -> bool:
    """
    简短描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
    """
```

### 类型注解
尽可能使用类型注解提高代码可读性

## 发布流程

1. 更新版本号 (`src/__init__.py`, `pyproject.toml`)
2. 更新 CHANGELOG.md
3. 运行测试
4. 打包程序
5. 测试打包版本
6. 创建 GitHub Release
7. 上传打包文件

## 贡献指南

### 提交代码
1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

### 代码审查标准
- 代码符合规范
- 包含必要的测试
- 更新相关文档
- 通过CI检查

## 相关资源

- [mijiaAPI文档](https://github.com/Do1e/mijia-api)
- [PyQt6文档](https://doc.qt.io/qtforpython-6/)
- [SQLite文档](https://www.sqlite.org/docs.html)
- [PyInstaller文档](https://pyinstaller.org/)
