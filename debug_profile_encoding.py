import json
import os
from datetime import datetime

file_path = r"c:\Users\swamp\OneDrive\デスクトップ\stella_all_in_one_20250614_201902\stella_bot\data\profiles\profile_643982855122321443_391844907465310218.json"

encodings = ['utf-8', 'cp932', 'shift_jis', 'utf-16']

print(f"Testing file: {file_path}")
if not os.path.exists(file_path):
    print("File not found!")
    exit()

for enc in encodings:
    print(f"\nTesting encoding: {enc}")
    try:
        with open(file_path, 'r', encoding=enc) as f:
            data = json.load(f)
        
        print("JSON Load: SUCCESS")
        print(f"Nickname: {data.get('nickname')}")
        
        # Test datetime parsing
        for date_field in ['created_at', 'updated_at', 'last_updated']:
            if data.get(date_field):
                try:
                    dt = datetime.fromisoformat(data[date_field])
                    print(f"{date_field}: {dt} (SUCCESS)")
                except ValueError as e:
                    print(f"{date_field}: FAILED ({e})")
                    
    except Exception as e:
        print(f"JSON Load: FAILED ({e})")
