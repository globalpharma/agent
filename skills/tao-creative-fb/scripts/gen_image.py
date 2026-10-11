#!/usr/bin/env python3
"""
gen_image.py - Tạo hình ảnh y khoa chuẩn quảng cáo cho GlobalPharma qua OpenAI GPT Image API.
Hỗ trợ model gpt-image-1 (quality low / medium), retry 1 lần khi lỗi, và tự động ghép phôi chai thật & logo B.Braun/GlobalPharma.
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

# Import compose_placement nếu có
try:
    from compose_placement import create_placement
    HAS_COMPOSER = True
except ImportError:
    try:
        sys.path.append(str(Path(__file__).parent))
        from compose_placement import create_placement
        HAS_COMPOSER = True
    except Exception:
        HAS_COMPOSER = False


def create_local_placement(output_path: Path, product_type: str = "renal") -> str:
    """Tạo ảnh thành phẩm hoàn chỉnh bằng bộ ghép quang học với phôi chai thật B.Braun & logo"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if HAS_COMPOSER:
        try:
            return create_placement(bg_path="auto", product_type=product_type, output_path=str(output_path))
        except Exception as e:
            print(f"[WARN] compose_placement failed: {e}")
    # Fallback SVG/PNG nếu không có composer
    w, h = 1024, 1024
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="#F1F5F9"/>
  <rect x="60" y="60" width="{w-120}" height="{h-120}" rx="24" fill="#FFFFFF"/>
  <text x="100" y="140" font-family="Arial, sans-serif" font-size="32" font-weight="bold" fill="#005B94">
    GLOBALPHARMA &amp; B.BRAUN CHLB ĐỨC
  </text>
  <text x="100" y="190" font-family="Arial, sans-serif" font-size="22" fill="#555555">
    Sản phẩm: {product_type.upper()} • Dinh dưỡng y học chuẩn Châu Âu
  </text>
  <line x1="100" y1="220" x2="{w-100}" y2="220" stroke="#008080" stroke-width="3"/>
  <rect x="100" y="{h-140}" width="{w-200}" height="60" rx="10" fill="#005B94"/>
  <text x="{w/2}" y="{h-102}" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#FFFFFF" text-anchor="middle">
    Nhập khẩu chính ngạch từ CHLB Đức • Hotline: 0783 114 115
  </text>
</svg>"""
    svg_file = output_path.with_suffix(".svg")
    with open(svg_file, "w", encoding="utf-8") as f:
        f.write(svg_content)
    with open(output_path, "wb") as f:
        f.write(svg_content.encode("utf-8"))
    return str(output_path)


def generate_image(prompt: str, output_path: str, size: str = "1024x1024", quality: str = "low", product: str = "renal", mock: bool = False):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    dry_run = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")

    # Nếu chạy dry-run hoặc mock hoặc chưa cấu hình API key thực
    if mock or dry_run or not api_key or api_key.startswith("sk-proj-your"):
        print(f"[INFO] Chế độ MOCK/DRY-RUN: Tạo ảnh thành phẩm thương mại tại {output_file} (Product={product})")
        created_path = create_local_placement(output_file, product)
        meta = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "product": product,
            "mode": "dry_run" if dry_run else "mock",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "file": str(created_path)
        }
        with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"MEDIA:{Path(created_path).resolve()}")
        return str(created_path)

    if not HAS_OPENAI_LIB:
        print("[ERROR] Thư viện openai chưa được cài đặt. Chạy: pip install openai")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    
    # Map quality tương thích với từng model
    api_quality = quality
    if model in ("dall-e-3", "dall-e-2"):
        api_quality = "hd" if quality in ("medium", "hd", "high") else "standard"
    
    print(f"[INFO] Đang gọi OpenAI Image API (model={model}, size={size}, quality={api_quality})...")
    
    # Yêu cầu: nếu OpenAI fail → log + retry 1 lần (tổng 2 lần thử)
    max_retries = 2
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            try:
                response = client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=api_quality,
                    n=1,
                )
            except Exception as model_err:
                # Nếu model gpt-image-1 chưa hỗ trợ trên tài khoản này, fallback sang dall-e-3
                if "model" in str(model_err).lower() and model != "dall-e-3":
                    print(f"[WARN] Model {model} không khả dụng ({model_err}). Fallback sang dall-e-3...")
                    model = "dall-e-3"
                    api_quality = "standard"
                    response = client.images.generate(
                        model=model,
                        prompt=prompt,
                        size=size,
                        quality=api_quality,
                        n=1,
                    )
                else:
                    raise model_err

            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], "revised_prompt", prompt)
            
            # Tải ảnh về lưu vào output_path
            print(f"[INFO] Tải ảnh từ URL OpenAI về {output_file}...")
            img_res = requests.get(image_url, timeout=30)
            img_res.raise_for_status()
            with open(output_file, "wb") as f:
                f.write(img_res.content)
            
            # Tự động ghép quang học phôi chai B.Braun thật và logo chính hãng GlobalPharma
            if HAS_COMPOSER:
                try:
                    create_placement(bg_path=str(output_file), product_type=product, output_path=str(output_file))
                    print(f"[INFO] Đã ghép thành công phôi chai B.Braun ({product}) và logo chính hãng.")
                except Exception as comp_err:
                    print(f"[WARN] Lỗi ghép chai thật: {comp_err}")

            # Lưu metadata
            meta = {
                "original_prompt": prompt,
                "revised_prompt": revised_prompt,
                "model": model,
                "size": size,
                "quality": quality,
                "product": product,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file": str(output_file)
            }
            with open(output_file.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
            print(f"[SUCCESS] Tạo ảnh thành công: {output_file}")
            print(f"MEDIA:{output_file.resolve()}")
            return str(output_file)
            
        except Exception as e:
            last_err = e
            print(f"[WARN] Thử lần {attempt}/{max_retries} thất bại: {e}")
            if attempt < max_retries:
                print(f"[INFO] Đang retry lần 1...")
                time.sleep(2)
    
    # Nếu sau 1 lần retry vẫn thất bại
    print(f"[ERROR] OpenAI Image API thất bại sau {max_retries} lần thử: {last_err}. Kích hoạt fallback placement...")
    created_path = create_local_placement(output_file, product)
    print(f"MEDIA:{Path(created_path).resolve()}")
    return str(created_path)


def main():
    parser = argparse.ArgumentParser(description="Sinh hình ảnh y khoa cho GlobalPharma qua OpenAI GPT Image API")
    parser.add_argument("--prompt", required=True, help="Prompt mô tả hình ảnh")
    parser.add_argument("--output", default="skills/tao-creative-fb/output/generated_image.png", help="Đường dẫn file ảnh đầu ra")
    parser.add_argument("--size", default="1024x1024", choices=["1024x1024", "1024x1792", "1792x1024"], help="Kích thước ảnh")
    parser.add_argument("--quality", default="low", choices=["low", "medium", "standard", "hd"], help="Chất lượng ảnh (low cho Mode 1, medium cho Mode 2)")
    parser.add_argument("--product", default="renal", choices=["renal", "nutricomp", "plus", "combo", "prontosan"], help="Dòng sản phẩm")
    parser.add_argument("--mock", action="store_true", help="Chạy giả lập không gọi API tốn credit")
    
    args = parser.parse_args()
    generate_image(args.prompt, args.output, args.size, args.quality, args.product, args.mock)


if __name__ == "__main__":
    main()
