# 设备配置文件指南 (Device Profiles Guide)

本文档介绍了如何使用和扩展设备配置文件系统 (`DeviceProfile`)，以便为不同型号的米家设备定制显示界面和图表配置。

## 概述

`DeviceProfile` 系统旨在解决不同设备具有不同属性、不同显示需求的问题。通过为特定设备型号创建配置文件，我们可以：

1. **定制显示的属性**：决定在详情页的"当前属性"列表中显示哪些属性，以及显示的顺序。
2. **定制属性名称**：将原始的英文属性名（如 `temperature`）映射为友好的中文名称（如 `温度`）。
3. **定制图表**：决定哪些属性需要在"历史趋势"图表中显示，以及曲线的颜色和名称。
4. **格式化数值**：为不同类型的属性值添加单位或进行格式转换（如布尔值转中文）。

## 核心类说明

### 1. DeviceProfile (基类)

位于 `src/core/device_profiles.py`。所有特定的设备配置都应继承自此类。

主要方法：

* `get_display_properties(properties)`: 处理并返回用于 UI 显示的属性列表。默认实现会显示所有属性。
* `get_chart_properties()`: 返回图表配置字典。默认实现包含常见的温湿度、功率等配置。
* `format_value(key, value)`: 格式化属性值（添加单位等）。
* `get_friendly_names()`: **(需要在子类中实现)** 返回属性名到中文名的映射字典。

### 2. DeviceProfileFactory (工厂类)

用于根据设备型号 (`model`) 创建对应的 `DeviceProfile` 实例。

## 如何添加新设备支持

假设我们要为一个新的灯具设备添加支持，型号为 `yeelink.light.lamp1`。

### 步骤 1: 创建子类

在 `src/core/device_profiles.py` 中创建一个新的类，继承自 `DeviceProfile`。

```python
class YeelinkLightProfile(DeviceProfile):
    """Profile for yeelink.light.lamp1"""
    
    def get_friendly_names(self) -> Dict[str, str]:
        """定义属性的中文名称"""
        return {
            'on': '开关',
            'brightness': '亮度',
            'color-temperature': '色温',
            'mode': '模式'
        }

    def get_display_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """定制显示的属性和顺序"""
        # 定义想要显示的属性及其顺序
        target_keys = ['on', 'brightness', 'color-temperature']
        display_props = []
        friendly_names = self.get_friendly_names()
        
        for key in target_keys:
            if key in properties:
                data = properties[key]
                display_props.append({
                    'key': key,
                    'name': friendly_names.get(key, key),
                    'value': self.format_value(key, data['value']),
                    'type': data.get('value_type', '-'),
                    'timestamp': data.get('timestamp', '-')
                })
                
        return display_props

    def get_chart_properties(self) -> Dict[str, Dict[str, Any]]:
        """定制图表显示"""
        # 只需要显示亮度和色温的历史趋势
        return {
            'brightness': {'color': '#FFE66D', 'name': '亮度 (%)'},
            'color-temperature': {'color': '#FF6B6B', 'name': '色温 (K)'}
        }
```

### 步骤 2: 注册到工厂

在 `src/core/device_profiles.py` 的 `DeviceProfileFactory.create_profile` 方法中添加新的判断分支。

```python
class DeviceProfileFactory:
    """Factory to create device profiles."""
    
    @staticmethod
    def create_profile(model: str) -> DeviceProfile:
        if model == 'miaomiaoce.sensor_ht.t2':
            return MiaoMiaoCeSensorHtT2Profile(model)
        elif model == 'yeelink.light.lamp1':  # 新增的设备
            return YeelinkLightProfile(model)
        
        # 默认返回基类
        return DeviceProfile(model)
```

## 现有设备支持

目前已支持以下设备：

* **miaomiaoce.sensor_ht.t2** (秒秒测温湿度计)
  * 显示属性：温度、湿度、电池电量
  * 图表属性：温度、湿度

## 常见属性键名参考

* `temperature`: 温度
* `relative-humidity`: 相对湿度
* `battery-level`: 电池电量
* `power` / `electric-power`: 功率
* `voltage`: 电压
* `electric-current`: 电流
* `on`: 开关状态 (bool)
* `brightness`: 亮度
* `color-temperature`: 色温
