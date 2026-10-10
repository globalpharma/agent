#!/usr/bin/env python3
"""
gen_image.py - Tạo hình ảnh y khoa chuẩn quảng cáo cho GlobalPharma qua OpenAI DALL-E / gpt-image.
Hỗ trợ lưu ảnh, metadata, retry tự động và chế độ mock/dry-run.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Tìm và nạp file .env từ thư mục hiện tại hoặc thư mục cha
env_paths = [
    Path.cwd() / ".env",
    Path(__file__).parent / ".env",
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[3] / ".env.local"
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break

try:
    from openai import OpenAI
    HAS_OPENAI_LIB = True
except ImportError:
    HAS_OPENAI_LIB = False


def create_placeholder_image(output_path: Path, prompt: str, size: str = "1024x1024"):
    """Tạo ảnh SVG/PNG minh họa mô phỏng nếu chạy mock hoặc chưa có API Key"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Tạo file SVG chất lượng cao tượng trưng cho ảnh y tế B.Braun/GlobalPharma
    w, h = (1024, 1024) if size == "1024x1024" else (1024, 1024)
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs>
    <linearGradient id="medGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#005B94"/>
      <stop offset="50%" stop-color="#008080"/>
      <stop offset="100%" stop-color="#E8F4F8"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#medGrad)"/>
  <rect x="60" y="60" width="{w-120}" height="{h-120}" rx="24" fill="#FFFFFF" fill-opacity="0.92"/>
  <text x="100" y="140" font-family="Arial, sans-serif" font-size="34" font-weight="bold" fill="#005B94">
    GLOBALPHARMA &amp; B.BRAUN CHLB ĐỨC
  </text>
  <text x="100" y="190" font-family="Arial, sans-serif" font-size="22" fill="#555555">
    Mô phỏng hình ảnh y khoa chuẩn lâm sàng (Creative Visual)
  </text>
  <line x1="100" y1="220" x2="{w-100}" y2="220" stroke="#008080" stroke-width="3"/>
  <foreignObject x="100" y="260" width="{w-200}" height="500">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: Arial, sans-serif; font-size: 20px; color: #222; line-height: 1.6;">
      <p style="font-weight: bold; color: #005B94;">Prompt chi tiết đã sinh:</p>
      <p style="background: #F0F7FA; padding: 15px; border-radius: 8px; border-left: 5px solid #005B94;">
        {prompt[:350]}...
      </p>
      <p style="margin-top: 25px; color: #666; font-size: 18px;">
        ✔ Tỉ lệ: {size} | Negative Space: Thiết kế chuẩn cho Text Overlay<br/>
        ✔ Tiêu chuẩn y tế: B.Braun Germany | Phân phối chính ngạch bởi GlobalPharma
      </p>
    </div>
  </foreignObject>
  <rect x="100" y="{h-160}" width="{w-200}" height="70" rx="12" fill="#005B94"/>
  <text x="{w/2}" y="{h-115}" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#FFFFFF" text-anchor="middle">
    Dinh dưỡng y học chuyên biệt &amp; Chăm sóc vết thương chuẩn Châu Âu
  </text>
</svg>"""
    # Nếu đuôi là svg lưu svg, nếu png thì có thể lưu file mô phỏng
    if output_path.suffix.lower() == ".svg":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
    else:
        # Nếu output là png, cũng ghi file svg hoặc bytes tượng trưng nếu không có cairosvg
        svg_file = output_path.with_suffix(".svg")
        with open(svg_file, "w", encoding="utf-8") as f:
            f.write(svg_content)
        # Đồng thời tạo file png placeholder text để không bị gãy đường dẫn
        with open(output_path, "wb") as f:
            f.write(svg_content.encode("utf-8"))
    return str(output_path)


def generate_image(prompt: str, output_path: str, size: str = "1024x1024", quality: str = "standard", mock: bool = False):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

    if mock or dry_run or not api_key or api_key.startswith("sk-proj-your"):
        print(f"[INFO] Chế độ MOCK/DRY-RUN: Tạo ảnh placeholder y khoa tại {output_file}")
        created_path = create_placeholder_image(output_file, prompt, size)
        meta = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "mode": "mock",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file": str(created_path)
        }
        with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        return str(output_file)

    if not HAS_OPENAI_LIB:
        print("[ERROR] Thư viện openai chưa được cài đặt. Chạy: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    
    print(f"[INFO] Đang gọi OpenAI Image API ({model}) với size={size}, quality={quality}...")
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], "revised_prompt", prompt)
            
            # Tải ảnh về lưu vào output_path
            print(f"[INFO] Tải ảnh từ URL OpenAI về {output_file}...")
            img_res = requests.get(image_url, timeout=30)
            img_res.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(img_res.content)
            
            # Lưu metadata
            meta = {
                "original_prompt": prompt,
                "revised_prompt": revised_prompt,
                "model": model,
                "size": size,
                "quality": quality,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file": str(output_file)
            }
            with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
            print(f"[SUCCESS] Tạo ảnh thành công: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"[WARN] Thử lần {attempt}/{max_retries} thất bại: {e}")
            if attempt == max_retries:
                print(f"[ERROR] Không thể tạo ảnh sau {max_retries} lần. Chuyển sang fallback placeholder.")
                return create_placeholder_image(output_file, prompt, size)
            time.sleep(2 * attempt)


def main():
    parser = argparse.ArgumentParser(description="Sinh hình ảnh y khoa cho GlobalPharma qua OpenAI")
    parser.add_argument("--prompt", required=True, help="Prompt mô tả hình ảnh")
    parser.add_argument("--output", default="output/generated_image.png", help="Đường dẫn file ảnh đầu ra")
    parser.add_argument("--size", default="1024x1024", choices=["1024x1024", "1024x1792", "1792x1024"], help="Kích thước ảnh")
    parser.add_argument("--quality", default="standard", choices=["standard", "hd"], help="Chất lượng ảnh")
    parser.add_argument("--mock", action="store_true", help="Chạy giả lập không gọi API tốn credit")
    
    args = parser.parse_args()
    generate_image(args.prompt, args.output, args.size, args.quality, args.mock)


if __name__ == "__main__":
    main()
