from typing import Dict, Any, List, Optional

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


class MiaoMiaoCeSensorHtT2Profile(DeviceProfile):
    """Profile for miaomiaoce.sensor_ht.t2"""
    
    def get_friendly_names(self) -> Dict[str, str]:
        return {
            'temperature': '温度',
            'relative-humidity': '相对湿度',
            'battery-level': '电池电量',
        }

    def get_overview_properties(self, properties: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Only show temperature, humidity and battery
        target_keys = ['temperature', 'relative-humidity', 'battery-level']
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
        # Define specific order and filtering
        target_keys = ['temperature', 'relative-humidity', 'battery-level']
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
        # Only show temperature and humidity in charts
        return {
            'temperature': {'color': '#FF6B6B', 'name': '温度 (°C)'},
            'relative-humidity': {'color': '#4ECDC4', 'name': '湿度 (%)'}
        }


class DeviceProfileFactory:
    """Factory to create device profiles."""
    
    @staticmethod
    def create_profile(model: str) -> DeviceProfile:
        if model == 'miaomiaoce.sensor_ht.t2':
            return MiaoMiaoCeSensorHtT2Profile(model)
        # Add other specific profiles here
        
        return DeviceProfile(model)
