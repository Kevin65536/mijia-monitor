import sys
import os
from pathlib import Path

# Add src to path
import importlib.util

# Load device_profiles.py directly to avoid triggering core.__init__
spec = importlib.util.spec_from_file_location(
    "device_profiles", 
    str(Path(__file__).parent.parent / 'src' / 'core' / 'device_profiles.py')
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
DeviceProfileFactory = module.DeviceProfileFactory

def test_profile_loading():
    # Test miaomiaoce.sensor_ht.t2
    model1 = 'miaomiaoce.sensor_ht.t2'
    print(f"Testing profile loading for {model1}...")
    profile1 = DeviceProfileFactory.create_profile(model1)
    if not hasattr(profile1, 'profile_data'):
        print(f"FAILED: {model1} is not a JsonDeviceProfile")
        return False
    print(f"{model1} loaded successfully.")

    # Test qmi.plug.psv3
    model2 = 'qmi.plug.psv3'
    print(f"\nTesting profile loading for {model2}...")
    profile2 = DeviceProfileFactory.create_profile(model2)
    
    if not hasattr(profile2, 'profile_data'):
        print(f"FAILED: {model2} is not a JsonDeviceProfile")
        return False
        
    print(f"{model2} loaded successfully.")
    
    # Test friendly names for plug
    names = profile2.get_friendly_names()
    print(f"Friendly names: {names}")
    if names.get('electric-power') != '当前功率':
        print("FAILED: Incorrect friendly name for electric-power")
        return False
        
    # Test display properties for plug
    props = {
        'on': {'value': True, 'value_type': 'bool'},
        'electric-power': {'value': 123.45, 'value_type': 'float'},
        'voltage': {'value': 220.1, 'value_type': 'uint32'},
        'temperature': {'value': 35.5, 'value_type': 'float'}
    }
    
    display_props = profile2.get_display_properties(props)
    print("\nDisplay properties:")
    for p in display_props:
        print(f"  {p['name']}: {p['value']}")
        
    # Verify formatting
    power_prop = next((p for p in display_props if p['key'] == 'electric-power'), None)
    if not power_prop or 'W' not in power_prop['value']:
        print("FAILED: Incorrect formatting for electric-power")
        return False
        
    print("\nPASSED: All checks passed.")
    return True

if __name__ == '__main__':
    if test_profile_loading():
        sys.exit(0)
    else:
        sys.exit(1)
