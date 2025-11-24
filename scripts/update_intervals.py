import sys
from pathlib import Path
import sqlite3

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def update_intervals():
    db_path = project_root / 'data' / 'monitor.db'
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 查找所有传感器设备
        cursor.execute("SELECT did, model FROM devices")
        devices = cursor.fetchall()
        
        count = 0
        for did, model in devices:
            if 'sensor' in model.lower() or 'miaomiaoce' in model.lower():
                print(f"Updating interval for {model} ({did}) to 300s")
                cursor.execute("UPDATE devices SET monitor_interval = 300 WHERE did = ?", (did,))
                count += 1
        
        conn.commit()
        print(f"Updated {count} devices.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    update_intervals()
