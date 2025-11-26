# 设备配置文件指南 (Device Profiles Guide)

本文档介绍了如何使用和扩展设备配置文件系统 (`DeviceProfile`)，以便为不同型号的米家设备定制显示界面和图表配置。

## 概述

`DeviceProfile` 系统已升级为数据驱动架构。现在，您无需编写 Python 代码即可添加新设备支持。只需创建一个 JSON 配置文件即可定义：

1. **设备属性**：基于 MIOT Spec 的服务和属性定义。
2. **UI 配置**：定制属性的显示名称、顺序、单位和图表颜色。

## 如何添加新设备支持

假设我们要为一个新的插座设备添加支持，型号为 `qmi.plug.psv3`。

### 步骤 1: 获取 MIOT Spec

访问 [Xiaomi Miot Spec](https://home.miot-spec.com/)，搜索设备型号（如 `qmi.plug.psv3`），获取其服务和属性定义。

### 步骤 2: 创建 JSON 配置文件

在 `src/resources/profiles/` 目录下创建一个名为 `qmi.plug.psv3.json` 的文件。

文件结构如下：

```json
{
  "model": "qmi.plug.psv3",
  "name": "Xiaomi Smart Power Strip 2",
  "services": [
    {
      "siid": 2,
      "type": "urn:miot-spec-v2:service:switch:...",
      "description": "Switch",
      "properties": [
        {
          "piid": 1,
          "type": "urn:miot-spec-v2:property:on:...",
          "name": "on",
          "description": "Switch Status",
          "format": "bool",
          "access": ["read", "write", "notify"]
        }
      ]
    }
    // ... 其他服务
  ],
  "ui_config": {
    "dashboard": {
      "overview_properties": ["on", "electric-power"],
      "chart_properties": {
        "electric-power": {"color": "#FFE66D", "label": "功率 (W)"}
      }
    },
    "details": {
      "display_order": ["on", "electric-power", "electric-current"],
      "friendly_names": {
        "on": "开关",
        "electric-power": "功率",
        "electric-current": "电流"
      }
    }
  }
}
```

### 配置项说明

* **model**: 设备型号 ID。
* **services**: 直接复制或参考 MIOT Spec 的结构。关键是 `properties` 中的 `name`，它将作为 UI 中的键值。
* **ui_config**:
    * **dashboard.overview_properties**: 在设备列表页显示的属性。
    * **dashboard.chart_properties**: 需要绘制历史曲线的属性及其颜色。
    * **details.display_order**: 详情页属性显示的顺序。
    * **details.friendly_names**: 属性名到中文名的映射。

## 现有设备支持

目前已支持以下设备：

* **miaomiaoce.sensor_ht.t2** (秒秒测温湿度计)
* **qmi.plug.psv3** (小米智能插线板2)

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
