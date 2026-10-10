import csv
import json
from pathlib import Path

csv_path = Path("facebook_pages.csv")
json_path = Path("skills/tao-creative-fb/pages.json")

pages = []
with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        pid = r["Page ID"].replace("=", "").replace('"', "").strip()
        name = r["Tên Fanpage"].strip()
        cat = r["Danh mục (Category)"].strip()
        token = r["Page Access Token"].strip()
        pages.append({
            "id": pid,
            "name": name,
            "category": cat,
            "token": token,
            "enabled": True
        })

with open(json_path, "w", encoding="utf-8") as out:
    json.dump(pages, out, ensure_ascii=False, indent=2)

print(f"Successfully generated {json_path} with {len(pages)} pages.")
