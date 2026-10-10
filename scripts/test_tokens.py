import sys
import csv
import requests

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

with open('facebook_pages.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        pid = r['Page ID'].replace('=', '').replace('"', '').strip()
        name = r['Tên Fanpage'].strip()
        token = r['Page Access Token'].strip()
        try:
            res = requests.get(f'https://graph.facebook.com/v19.0/me?access_token={token}', timeout=10).json()
            if 'id' in res:
                print(f"[OK] {name} (ID: {pid}) -> API Name: {res.get('name')}")
            else:
                err = res.get('error', {}).get('message', 'Unknown error')
                print(f"[FAIL] {name} (ID: {pid}) -> {err}")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
