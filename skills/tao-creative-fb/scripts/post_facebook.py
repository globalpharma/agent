#!/usr/bin/env python3
"""
post_facebook.py - Đăng hình ảnh và bài viết lên một hoặc HÀNG LOẠT (10+ Fanpage) của GlobalPharma.
Hỗ trợ file cấu hình danh sách page (JSON), kiểm thử an toàn DRY_RUN=true, delay chống spam,
và báo cáo bảng tổng kết trạng thái từng page.
"""

import os
import sys
import time
import json
import csv
import re
import argparse
from pathlib import Path
import requests
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        pass

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


def clean_facebook_caption(text: str) -> str:
    """Loại bỏ triệt để markdown bold/italic (***, **, *) và header (#) để caption Facebook không bị lỗi font hay rác dấu sao"""
    if not text:
        return ""
    # Strip bold-italic ***text***
    text = re.sub(r'\*\*\*([^\*\n\r]+)\*\*\*', r'\1', text)
    # Strip bold **text**
    text = re.sub(r'\*\*([^\*\n\r]+)\*\*', r'\1', text)
    # Strip italic *text*
    text = re.sub(r'(?:^|(?<=[\s\(]))\*([^\*\n\r]+)\*(?=$|[\s\)\.,!\?:;])', r'\1', text)
    # Strip ___text___ and __text__
    text = re.sub(r'___([^_\n\r]+)___', r'\1', text)
    text = re.sub(r'__([^_\n\r]+)__', r'\1', text)
    text = re.sub(r'(?:^|(?<=[\s\(]))_([^_\n\r]+)_(?=$|[\s\)\.,!\?:;])', r'\1', text)
    # Strip markdown headers (e.g. ## Title)
    text = re.sub(r'(?m)^#{1,6}\s+', '', text)
    # Remove any leftover asterisks
    text = text.replace('***', '').replace('**', '')
    return text.strip()


def post_single_page(image_path: Path, caption: str, page_id: str, page_token: str, page_name: str = "", graph_version: str = "v19.0", dry_run: bool = False):
    """Đăng bài lên 1 Fanpage cụ thể"""
    caption = clean_facebook_caption(caption)
    label = f"[{page_name} - {page_id}]" if page_name else f"[{page_id}]"
    
    if dry_run or not page_token or page_token.startswith("EAAV..."):
        token_preview = f"{page_token[:10]}...{page_token[-6:]}" if len(page_token) > 16 else "(Token chưa cấu hình)"
        simulated_res = {
            "status": "success",
            "page_id": page_id,
            "page_name": page_name or "N/A",
            "dry_run": True,
            "token_masked": token_preview,
            "simulated_post_id": f"{page_id}_mock_{int(time.time())}"
        }
        print(f"  ✔ [MÔ PHỎNG] {label}: Giả lập đăng thành công -> Post ID: {simulated_res['simulated_post_id']}")
        return simulated_res

    url = f"https://graph.facebook.com/{graph_version}/{page_id}/photos"
    mime_type = "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"

    try:
        with open(image_path, "rb") as f:
            files = {"source": (image_path.name, f, mime_type)}
            data = {"caption": caption, "message": caption, "access_token": page_token}
            response = requests.post(url, data=data, files=files, timeout=60)
            res_json = response.json()

            if response.status_code == 200 and "id" in res_json:
                post_id = res_json.get("post_id", res_json.get("id"))
                print(f"  ✔ [THÀNH CÔNG] {label}: Đã đăng bài -> Post ID: {post_id}")
                return {
                    "status": "success",
                    "page_id": page_id,
                    "page_name": page_name,
                    "photo_id": res_json.get("id"),
                    "post_id": post_id,
                    "dry_run": False
                }
            else:
                err_data = res_json.get("error", {})
                err_msg = err_data.get("message", "Lỗi không xác định")
                err_code = err_data.get("code", "N/A")
                print(f"  ✖ [THẤT BẠI] {label}: Mã lỗi {err_code} - {err_msg}")
                return {
                    "status": "error",
                    "page_id": page_id,
                    "page_name": page_name,
                    "error_code": err_code,
                    "error_message": err_msg,
                    "dry_run": False
                }
    except Exception as e:
        print(f"  ✖ [LỖI MẠNG] {label}: {e}")
        return {
            "status": "error",
            "page_id": page_id,
            "page_name": page_name,
            "error_code": "NETWORK_ERR",
            "error_message": str(e),
            "dry_run": False
        }


def resolve_image_path(raw_path: str) -> Path:
    """Tìm file ảnh theo đường dẫn tuyệt đối hoặc tương đối trong các thư mục phổ biến"""
    clean_path = raw_path.strip()
    if clean_path.startswith("MEDIA:"):
        clean_path = clean_path[len("MEDIA:"):].strip()

    p = Path(clean_path)
    if p.exists() and p.is_file():
        return p

    candidates = [
        Path.cwd() / clean_path,
        Path("/app/workspace") / clean_path,
        Path("/app/workspace/output") / clean_path,
        Path("/app/workspace/output") / p.name,
        Path("/app/data/skills/tao-creative-fb/output") / p.name,
        Path(__file__).resolve().parents[1] / "output" / p.name,
        Path.cwd() / "skills/tao-creative-fb/output" / p.name,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c

    return p


def load_pages_from_csv(csv_path: Path) -> list:
    """Nạp danh sách Fanpage và Token từ file CSV facebook_pages.csv"""
    pages = []
    if not csv_path.exists():
        return pages

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if len(rows) < 2:
                return pages

            for row in rows[1:]:
                if len(row) < 6:
                    continue
                raw_id = row[1].strip()
                matches = re.findall(r"\d+", raw_id)
                page_id = matches[0] if matches else raw_id
                page_name = row[2].strip()
                category = row[3].strip()
                token = row[5].strip()

                if not page_id or not token:
                    continue

                lower_name = page_name.lower()
                pg = "nutricomp"
                if "affiliate" in lower_name:
                    pg = "affiliate"
                elif "prontosan" in lower_name or "vết thương" in lower_name:
                    pg = "prontosan"
                elif "sức khỏe cho mọi nhà" in lower_name:
                    pg = "all"

                pages.append({
                    "id": page_id,
                    "name": page_name,
                    "category": category,
                    "token": token,
                    "product_group": pg,
                    "enabled": True
                })
    except Exception as e:
        print(f"  [CẢNH BÁO] Lỗi đọc CSV {csv_path}: {e}")

    return pages


def post_to_facebook_multiple(image_path: str, caption: str, pages_config: list, delay_seconds: float = 2.0, dry_run: bool = False):
    """Đăng bài đồng loạt lên danh sách nhiều Fanpage kèm khoảng nghỉ tránh spam"""
    img_file = resolve_image_path(image_path)
    if not img_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file ảnh tại: {image_path}")

    graph_version = os.getenv("FB_GRAPH_VERSION", "v19.0").strip()
    active_pages = [p for p in pages_config if p.get("enabled", True)]
    total = len(active_pages)
    
    print("\n" + "="*75)
    print(f"🚀 BẮT ĐẦU ĐĂNG BÀI ĐỒNG LOẠT LÊN {total} FANPAGE")
    print(f"   Ảnh: {img_file.name} ({img_file.stat().st_size / 1024:.1f} KB)")
    print(f"   Độ dài bài viết: {len(caption.split())} từ")
    print(f"   Chế độ: {'DRY-RUN (MÔ PHỎNG AN TOÀN)' if dry_run else 'LIVE POST (ĐĂNG THẬT)'}")
    print("="*75)

    results = []
    for idx, p in enumerate(active_pages, 1):
        p_id = str(p.get("id", "")).strip()
        p_token = str(p.get("token", "")).strip()
        p_name = p.get("name", f"Fanpage {idx}")
        
        print(f"\n[{idx}/{total}] Đang xử lý: {p_name} (ID: {p_id})...")
        res = post_single_page(
            image_path=img_file,
            caption=caption,
            page_id=p_id,
            page_token=p_token,
            page_name=p_name,
            graph_version=graph_version,
            dry_run=dry_run
        )
        results.append(res)

        # Khoảng nghỉ nhẹ giữa các trang để tránh Facebook kích hoạt thuật toán chống spam
        if idx < total and not dry_run:
            print(f"  ...Nghỉ {delay_seconds}s trước khi chuyển sang page tiếp theo...")
            time.sleep(delay_seconds)

    # In bảng tổng kết
    print("\n" + "="*75)
    print("📊 BÁO CÁO TỔNG KẾT ĐĂNG BÀI")
    print("="*75)
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"Tổng số page xử lý: {total} | Thành công: {success_count} | Thất bại: {total - success_count}\n")
    print(f"{'STT':<4} | {'Tên Fanpage':<32} | {'Trạng Thái':<12} | {'Chi Tiết / Post ID'}")
    print("-" * 75)
    for idx, r in enumerate(results, 1):
        status_text = "Thành công" if r["status"] == "success" else "Lỗi"
        detail = r.get("post_id") or r.get("simulated_post_id") or r.get("error_message", "")
        print(f"{idx:<4} | {r.get('page_name', '')[:30]:<32} | {status_text:<12} | {detail}")
    print("="*75 + "\n")

    return results


def detect_product(caption: str) -> str:
    """Tự động nhận diện dòng sản phẩm hoặc chủ đề bài viết dựa trên caption"""
    text = caption.lower()
    affiliate_keywords = [
        "affiliate", "tiếp thị liên kết", "kinh doanh một người", "solopreneur",
        "dược sĩ", "personal trainer", "pt", "thu nhập", "mô hình kinh doanh",
        "cộng tác viên", "kiếm thêm thu nhập", "tự do tài chính", "hoa hồng", "đối tác"
    ]
    nutricomp_keywords = [
        "nutricomp", "drink plus", "renal", "dinh dưỡng", "sữa dinh dưỡng",
        "suy thận", "thận mạn", "lọc máu", "suy kiệt", "hồi phục năng lượng",
        "năng lượng cao", "300 kcal", "đạm", "calo", "uống liền"
    ]
    prontosan_keywords = [
        "prontosan", "vết thương", "loét", "tì đè", "biofilm",
        "lành vết thương", "nhiễm trùng", "spray", "wound gel",
        "rửa vết thương", "hoại tử", "bỏng", "chăm sóc vết thương", "sát trùng"
    ]

    affiliate_score = sum(1 for kw in affiliate_keywords if kw in text)
    nutricomp_score = sum(1 for kw in nutricomp_keywords if kw in text)
    prontosan_score = sum(1 for kw in prontosan_keywords if kw in text)

    if affiliate_score > nutricomp_score and affiliate_score > prontosan_score:
        return "affiliate"
    elif nutricomp_score > prontosan_score and nutricomp_score > affiliate_score:
        return "nutricomp"
    elif prontosan_score > nutricomp_score and prontosan_score > affiliate_score:
        return "prontosan"
    elif affiliate_score > 0:
        return "affiliate"
    elif nutricomp_score > 0:
        return "nutricomp"
    elif prontosan_score > 0:
        return "prontosan"
    return "all"


def main():
    parser = argparse.ArgumentParser(description="Đăng ảnh và bài viết lên một hoặc HÀNG LOẠT Fanpage GlobalPharma")
    parser.add_argument("--image", required=True, help="Đường dẫn file ảnh cần đăng")
    parser.add_argument("--caption", required=True, help="Nội dung bài viết hoặc file text chứa bài viết")
    parser.add_argument("--product", choices=["nutricomp", "prontosan", "affiliate", "all", "auto"], default="auto",
                        help="Dòng sản phẩm mục tiêu (nutricomp/prontosan/affiliate/all/auto - mặc định tự nhận diện)")
    parser.add_argument("--pages-file", help="File JSON chứa danh sách 10+ Fanpage (id, name, token)")
    parser.add_argument("--page-id", help="ID của 1 Fanpage cụ thể (nếu chỉ đăng 1 page)")
    parser.add_argument("--token", help="Page Access Token (nếu chỉ đăng 1 page)")
    parser.add_argument("--delay", type=float, default=2.0, help="Số giây nghỉ giữa các page (mặc định 2.0s)")
    parser.add_argument("--dry-run", action="store_true", help="Chạy chế độ mô phỏng kiểm thử an toàn")

    args = parser.parse_args()

    # Làm sạch đường dẫn ảnh nếu có tiền tố MEDIA:
    clean_image_arg = args.image.strip()
    if clean_image_arg.startswith("MEDIA:"):
        clean_image_arg = clean_image_arg[len("MEDIA:"):].strip()

    # Đọc caption nếu truyền file
    caption_text = args.caption
    if Path(caption_text).exists() and Path(caption_text).is_file():
        with open(caption_text, "r", encoding="utf-8") as f:
            caption_text = f.read()

    dry_run = args.dry_run
    if not dry_run:
        dry_run_env = os.getenv("DRY_RUN", "false").lower()
        dry_run = dry_run_env in ("true", "1", "yes")

    # Xác định danh sách pages
    pages_list = []

    # Ưu tiên 1: File chỉ định hoặc tìm trong các thư mục hệ thống
    json_candidates = []
    if args.pages_file:
        json_candidates.append(Path(args.pages_file))
    json_candidates.extend([
        Path(__file__).resolve().parents[1] / "pages.json",
        Path("/app/data/skills/tao-creative-fb/pages.json"),
        Path("/app/workspace/skills/tao-creative-fb/pages.json"),
        Path("/app/workspace/pages.json"),
        Path.cwd() / "pages.json",
        Path.cwd() / "skills/tao-creative-fb/pages.json",
    ])

    for jc in json_candidates:
        if jc.exists() and jc.is_file():
            try:
                with open(jc, "r", encoding="utf-8") as f:
                    pages_list = json.load(f)
                if pages_list:
                    break
            except Exception:
                pass

    # Nếu chưa tìm thấy JSON, tìm file CSV
    if not pages_list:
        csv_candidates = [
            Path("/app/workspace/facebook_pages.csv"),
            Path("/app/facebook_pages.csv"),
            Path.cwd() / "facebook_pages.csv",
            Path(__file__).resolve().parents[2] / "facebook_pages.csv",
            Path(__file__).resolve().parents[3] / "facebook_pages.csv",
        ]
        for cc in csv_candidates:
            if cc.exists() and cc.is_file():
                pages_list = load_pages_from_csv(cc)
                if pages_list:
                    break

    # Ưu tiên 2: Tham số dòng lệnh 1 page
    if not pages_list and getattr(args, "page_id", None) and getattr(args, "token", None):
        pages_list = [{"id": args.page_id, "token": args.token, "name": "Fanpage chỉ định", "product_group": "all", "enabled": True}]

    # Ưu tiên 3: Biến môi trường .env (1 page đơn lẻ)
    if not pages_list:
        env_page_id = os.getenv("FB_PAGE_ID", "").strip()
        env_token = os.getenv("FB_PAGE_TOKEN", "").strip()
        if env_page_id:
            pages_list = [{"id": env_page_id, "token": env_token, "name": "GlobalPharma Official Page", "product_group": "all", "enabled": True}]

    if not pages_list:
        print("[ERROR] Không tìm thấy thông tin Fanpage nào! Đã tìm trong pages.json và facebook_pages.csv.")
        sys.exit(1)

    # Nhận diện dòng sản phẩm và điều hướng Fanpage phù hợp
    target_product = args.product.lower()
    if target_product == "auto":
        target_product = detect_product(caption_text)
        print(f"\n🔍 [NHẬN DIỆN SẢN PHẨM TỰ ĐỘNG] Dòng sản phẩm / chủ đề nhận diện được: {target_product.upper()}")
    else:
        print(f"\n🎯 [CHỈ ĐỊNH DÒNG SẢN PHẨM] Dòng sản phẩm / chủ đề: {target_product.upper()}")

    if target_product in ("nutricomp", "prontosan"):
        filtered_pages = []
        for p in pages_list:
            pg = p.get("product_group", "general").lower()
            # Tuyệt đối KHÔNG đăng bài sản phẩm vào page affiliate!
            if pg == "affiliate":
                continue
            # Đăng lên page chuyên biệt của dòng sản phẩm HOẶC page chung ("Sức Khỏe Cho Mọi Nhà" / "all")
            if pg == target_product or pg in ("all", "general", "both"):
                filtered_pages.append(p)
        print(f"📌 Đã phân luồng {len(filtered_pages)}/{len(pages_list)} Fanpage mục tiêu cho [{target_product.upper()}]:")
        for fp in filtered_pages:
            badge = "★ (Page chung)" if fp.get("product_group") == "all" else "● (Page chuyên biệt)"
            print(f"   {badge} {fp.get('name')} (ID: {fp.get('id')})")
        pages_list = filtered_pages
    elif target_product == "affiliate":
        filtered_pages = [p for p in pages_list if p.get("product_group") == "affiliate"]
        print(f"📌 Đã phân luồng {len(filtered_pages)}/{len(pages_list)} Fanpage mục tiêu cho [AFFILIATE]:")
        for fp in filtered_pages:
            print(f"   🎯 [Page Tuyển dụng Affiliate riêng] {fp.get('name')} (ID: {fp.get('id')})")
        pages_list = filtered_pages

    post_to_facebook_multiple(
        image_path=clean_image_arg,
        caption=caption_text,
        pages_config=pages_list,
        delay_seconds=args.delay,
        dry_run=dry_run
    )


if __name__ == "__main__":
    main()
