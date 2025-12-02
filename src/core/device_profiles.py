from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
from ..utils.path_utils import get_resource_path

class DeviceProfile:
    """Base class for device profiles."""
    
    def __init__(self, model: str):
        self.model = model

    def get_display_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get properties to display in the UI.
        Returns a list of dicts with keys: 'key', 'name', 'value', 'type', 'timestamp'.
        """
        # Default implementation: show all properties
        display_props = []
        
        for key, data in properties.items():
            display_props.append({
                'key': key,
                'name': key,
                'value': self.format_value(key, data['value']),
                'type': data.get('value_type', '-'),
                'timestamp': data.get('timestamp', '-')
            })
        return sorted(display_props, key=lambda x: x['name'])

    def get_overview_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get properties to display in the device list overview column.
        """
        # Default implementation: show common status properties
        target_keys = [
            'temperature', 'relative-humidity', 'electric-power', 'power',
            'electric-current', 'voltage', 'battery-level'
        ]
        
        display_props = []
        
        for key in target_keys:
            if key in properties:
                data = properties[key]
                display_props.append({
                    'key': key,
                    'name': key,
                    'value': self.format_value(key, data['value']),
                    'type': data.get('value_type', '-'),
                    'timestamp': data.get('timestamp', '-')
                })
        return display_props

    def get_chart_properties(self) -> Dict[str, Dict[str, Any]]:
        """
        Get configuration for properties to be charted.
        Returns a dict where key is property name and value is config dict (color, name).
        """
        # Default: no chart properties (device needs JSON profile to define charts)
        return {}

    def get_card_properties(self) -> List[Dict[str, Any]]:
        """Get properties to display as cards/controls."""
        # Default: no card properties
        return []

    def format_value(self, key: str, value: Any) -> str:
        """Format a property value for display."""
        try:
            if key == 'temperature':
                return f"{float(value):.1f}°C"
            elif key in ['relative-humidity', 'battery-level']:
                return f"{int(float(value))}%"
            elif key in ['electric-power', 'power']:
                return f"{float(value):.1f}W"
            elif key == 'electric-current':
                return f"{float(value):.2f}A"
            elif key == 'voltage':
                return f"{float(value):.1f}V"
            elif key == 'brightness':
                return f"{int(float(value))}%"
            elif key == 'color-temperature':
                return f"{int(float(value))}K"
            elif key == 'on':
                return "开启" if str(value).lower() in ['true', '1', 'on'] else "关闭"
            elif key == 'mute':
                return "静音" if str(value).lower() in ['true', '1', 'on'] else "未静音"
            elif key == 'volume':
                return f"🔊{int(float(value))}"
            elif key == 'playing-state':
                state_map = {0: "⏸暂停", 1: "▶播放中", 2: "⏳缓冲中"}
                return state_map.get(int(value), str(value))
            elif key == 'connected-device-count':
                return f"{int(value)}台设备"
            else:
                return str(value)
        except (ValueError, TypeError):
            return str(value)


class JsonDeviceProfile(DeviceProfile):
    """Device profile loaded from a JSON specification."""
    
    def __init__(self, model: str, profile_data: Dict[str, Any]):
        super().__init__(model)
        self.profile_data = profile_data
        self.ui_config = profile_data.get('ui_config', {})
        self.services = profile_data.get('services', [])
        
        # Build property map for quick lookup
        self.property_map = {}
        for service in self.services:
            for prop in service.get('properties', []):
                self.property_map[prop['name']] = prop

    def get_friendly_names(self) -> Dict[str, str]:
        return self.ui_config.get('details', {}).get('friendly_names', {})

    def get_overview_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_keys = self.ui_config.get('dashboard', {}).get('overview_properties', [])
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

    def get_display_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_keys = self.ui_config.get('details', {}).get('display_order', [])
        display_props = []
        friendly_names = self.get_friendly_names()
        
        # Add properties in defined order
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
        
        # Add any other properties that are not in the target list but exist
        for key, data in properties.items():
            if key not in target_keys:
                display_props.append({
                    'key': key,
                    'name': friendly_names.get(key, key),
                    'value': self.format_value(key, data['value']),
                    'type': data.get('value_type', '-'),
                    'timestamp': data.get('timestamp', '-')
                })
                
        return display_props

    def get_chart_properties(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for properties to be charted."""
        chart_config = self.ui_config.get('dashboard', {}).get('chart_properties', {})
        result = {}
        for key, config in chart_config.items():
            result[key] = {
                'color': config.get('color', '#888888'),
                'name': config.get('label', key),
                'style': config.get('style', 'line')
            }
        return result

    def get_card_properties(self) -> List[Dict[str, Any]]:
        """Get properties to display as cards/controls."""
        card_config = self.ui_config.get('details', {}).get('card_properties', [])
        # If it's a list of strings, convert to default config
        result = []
        for item in card_config:
            if isinstance(item, str):
                result.append({
                    'key': item,
                    'name': self.get_friendly_names().get(item, item),
                    'type': 'info' # default type
                })
            elif isinstance(item, dict):
                key = item.get('key')
                if key:
                    result.append({
                        'key': key,
                        'name': item.get('label', self.get_friendly_names().get(key, key)),
                        'type': item.get('type', 'info'),
                        'icon': item.get('icon'),
                        'color': item.get('color')
                    })
        return result


    def format_value(self, key: str, value: Any) -> str:
        # Try to use unit from property definition if available
        prop_def = self.property_map.get(key)
        if prop_def:
            # Apply scaling if defined
            scale = prop_def.get('scale')
            if scale is not None:
                try:
                    value = float(value) * float(scale)
                except (ValueError, TypeError):
                    pass

            unit = prop_def.get('unit', '')
            try:
                if unit == 'celsius':
                    return f"{float(value):.1f}°C"
                elif unit == 'percentage':
                    return f"{int(float(value))}%"
                elif unit == 'watt':
                    return f"{float(value):.1f}W"
                elif unit == 'ampere':
                    return f"{float(value):.2f}A"
                elif unit == 'volt':
                    return f"{float(value):.1f}V"
                elif unit == 'kelvin':
                    return f"{int(float(value))}K"
            except (ValueError, TypeError):
                pass
        
        # Fallback to base implementation
        return super().format_value(key, value)


class DeviceProfileFactory:
    """Factory to create device profiles."""
    
    @staticmethod
    def create_profile(model: str) -> DeviceProfile:
        search_paths = []

        # 开发环境: 直接访问 src/resources/profiles
        current_dir = Path(__file__).parent
        search_paths.append(current_dir.parent / 'resources' / 'profiles' / f"{model}.json")

        # 打包环境: 通过资源路径访问
        search_paths.append(get_resource_path(f"resources/profiles/{model}.json"))
        search_paths.append(get_resource_path(f"src/resources/profiles/{model}.json"))

        for profile_path in search_paths:
            try:
                if profile_path and profile_path.exists():
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        return JsonDeviceProfile(model, profile_data)
            except Exception as e:
                print(f"Error loading profile for {model}: {e}")

        # Fallback to base profile
        return DeviceProfile(model)

