import csv
import json
from pathlib import Path

csv_path = Path("facebook_pages.csv")
json_path = Path("skills/tao-creative-fb/pages.json")

def classify_product_group(name: str) -> str:
    name_lower = name.lower()
    if "sức khỏe cho mọi nhà" in name_lower or "affiliate" in name_lower:
        return "all"
    elif "nutricomp" in name_lower or "dinh dưỡng" in name_lower:
        return "nutricomp"
    elif "prontosan" in name_lower or "vết thương" in name_lower:
        return "prontosan"
    return "all"

pages = []
with open(csv_path, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        pid = r["Page ID"].replace("=", "").replace('"', "").strip()
        name = r["Tên Fanpage"].strip()
        cat = r["Danh mục (Category)"].strip()
        token = r["Page Access Token"].strip()
        pgroup = classify_product_group(name)
        pages.append({
            "id": pid,
            "name": name,
            "category": cat,
            "token": token,
            "product_group": pgroup,
            "enabled": True
        })

with open(json_path, "w", encoding="utf-8") as out:
    json.dump(pages, out, ensure_ascii=False, indent=2)

print(f"Successfully generated {json_path} with {len(pages)} pages.")
