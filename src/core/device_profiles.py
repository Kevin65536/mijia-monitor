from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

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
        # Default implementation: return common chartable properties
        return {
            'temperature': {'color': '#FF6B6B', 'name': '温度 (°C)'},
            'relative-humidity': {'color': '#4ECDC4', 'name': '湿度 (%)'},
            'power': {'color': '#FFE66D', 'name': '功率 (W)'},
            'electric-power': {'color': '#FFE66D', 'name': '功率 (W)'},
            'battery-level': {'color': '#95E1D3', 'name': '电量 (%)'}
        }

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
        chart_config = self.ui_config.get('dashboard', {}).get('chart_properties', {})
        result = {}
        for key, config in chart_config.items():
            result[key] = {
                'color': config.get('color', '#888888'),
                'name': config.get('label', key)
            }
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
        # Try to load from JSON first
        try:
            # Look in src/resources/profiles
            # Assuming this file is in src/core, so we go up one level then to resources/profiles
            current_dir = Path(__file__).parent
            profile_path = current_dir.parent / 'resources' / 'profiles' / f"{model}.json"
            
            if profile_path.exists():
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    return JsonDeviceProfile(model, profile_data)
        except Exception as e:
            print(f"Error loading profile for {model}: {e}")

        # Fallback to base profile
        return DeviceProfile(model)

