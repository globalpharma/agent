#!/usr/bin/env python3
"""
render_poster.py - Thiết kế visual và poster y tế tự nhiên, hiện đại bằng mô hình GPT-5.6 cho GlobalPharma.
Ưu tiên hình ảnh sản phẩm thực tế sắc nét, logo chuẩn GlobalPharma & B.Braun CHLB Đức,
bố cục thoáng đãng, sang trọng, tuyệt đối không dùng các khung hộp thô cứng hay chữ vẽ nguệch ngoạc.
"""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"
REFS_DIR = ASSETS_DIR / "references"


def get_font(size, bold=False):
    font_candidates = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/etc/apk/fonts/arial.ttf"
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def paste_globalpharma_logo(canvas: Image.Image, x: int = 50, y: int = 40, target_h: int = 50):
    """Gắn logo GlobalPharma chính thức sắc nét với kênh alpha trong suốt"""
    logo_path = ASSETS_DIR / "globalpharma_logo.png"
    if not logo_path.exists():
        logo_path = Path("ui/web/public/globalpharma-logo.png")
    
    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            target_w = int(logo.width * (target_h / logo.height))
            logo_resized = logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
            canvas.paste(logo_resized, (x, y), logo_resized)
            return target_w + x
        except Exception as e:
            print(f"[WARN] paste_logo error: {e}")
    return x


def render_nutricomp_poster(output_path: str, variant: str = "box12", force: bool = False):
    """
    Xuất poster Nutricomp sử dụng hình ảnh sản phẩm thực tế sắc nét, tự nhiên,
    không gò ép, đảm bảo hình ảnh chuẩn của B.Braun & GlobalPharma.
    """
    out = Path(output_path)
    if not force and out.exists() and out.stat().st_size > 200000:
        print(f"[SKIP] Đã có ảnh Nutricomp chất lượng cao (>200KB): {output_path}")
        return output_path

    variant_map = {
        "box12": REFS_DIR / "ref_nutricomp_box12.jpg",
        "combo12": REFS_DIR / "ref_nutricomp_combo12.jpg",
        "emotion": REFS_DIR / "ref_nutricomp_emotion.jpg",
        "bottles": REFS_DIR / "ref_nutricomp_renal_bottles.jpg",
    }

    ref_file = variant_map.get(variant, variant_map["box12"])
    
    # Nếu có file ảnh sản phẩm thực tế, xuất ảnh độ phân giải 1080x1080 sắc nét
    if ref_file.exists():
        img = Image.open(ref_file).convert("RGB")
        if img.size != (1080, 1080):
            img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        print(f"[SUCCESS] Đã tạo poster Nutricomp tự nhiên ({variant}) từ ảnh sản phẩm chuẩn tại: {output_path}")
        return output_path

    # Fallback thiết kế tối giản tự nhiên (Clean Editorial Style) nếu chưa có file ảnh gốc
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Nền chuyển sắc nhẹ nhàng tự nhiên
    for y in range(h):
        ratio = y / h
        r = int(255 - ratio * 15)
        g = int(255 - ratio * 8)
        b = int(255 - ratio * 12)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Gắn logo chuẩn
    end_x = paste_globalpharma_logo(img, x=70, y=60, target_h=55)

    # Đường phân cách & Cờ Đức
    draw.line([(end_x + 25, 60), (end_x + 25, 115)], fill="#CCCCCC", width=2)
    draw.text((end_x + 45, 75), "B.Braun Melsungen AG • CHLB Đức", fill="#005B94", font=get_font(22, bold=True))

    # Tiêu đề tự nhiên, thanh thoát
    draw.text((70, 180), "NUTRICOMP® DRINK RENAL", fill="#013D29", font=get_font(52, bold=True))
    draw.text((70, 245), "Dinh dưỡng y học chuyên biệt cho người suy thận và phục hồi thể trạng", fill="#4A5568", font=get_font(24, bold=False))

    # Chân trang tối giản
    draw.line([(70, h - 120), (w - 70, h - 120)], fill="#E2E8F0", width=1)
    draw.text((70, h - 85), "Thực phẩm dinh dưỡng y học (FSMP) • Nhập khẩu chính ngạch từ CHLB Đức", fill="#718096", font=get_font(20, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    return output_path


def render_prontosan_poster(output_path: str, force: bool = False):
    """
    Thiết kế poster Prontosan theo phong cách y tế tự nhiên, tinh tế chuẩn Châu Âu.
    Tone màu xanh ngọc y tế dịu mát (#EBF8FA / #00A896 / #005B94), không vẽ khung thô.
    """
    out = Path(output_path)
    if not force and out.exists() and out.stat().st_size > 200000:
        print(f"[SKIP] Đã có ảnh Prontosan chất lượng cao (>200KB): {output_path}")
        return output_path

    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#F4FAFB")
    draw = ImageDraw.Draw(img)

    # 1. Nền gradient dịu mát y tế (Fresh Clean Hospital / Clinic Aesthetic)
    for y in range(h):
        ratio = y / h
        r = int(244 * (1 - ratio * 0.15))
        g = int(250 * (1 - ratio * 0.08))
        b = int(252 * (1 - ratio * 0.05))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Logo GlobalPharma chính thức
    end_x = paste_globalpharma_logo(img, x=70, y=60, target_h=55)

    # 3. Đối tác B.Braun Đức
    draw.line([(end_x + 25, 60), (end_x + 25, 115)], fill="#BEE3F8", width=2)
    draw.text((end_x + 45, 75), "B.Braun Medical • CHLB Đức", fill="#005B94", font=get_font(22, bold=True))

    # 4. Tiêu đề thương hiệu thanh thoát, hiện đại
    draw.text((70, 180), "PRONTOSAN® WOUND CARE", fill="#005B94", font=get_font(52, bold=True))
    draw.text((70, 245), "Giải pháp làm sạch & làm lành vết thương mạn tính, loét tì đè", fill="#2D3748", font=get_font(24, bold=False))

    # 5. Điểm nhấn lâm sàng trình bày thoáng đãng (không đóng khung thô)
    draw.line([(70, 310), (w - 70, 310)], fill="#CBD5E0", width=1)

    points = [
        ("Phức hợp độc quyền Polihexanide (PHMB) & Betaine:", "Phá vỡ màng Biofilm bảo vệ vi khuẩn, làm sạch tận gốc ổ nhiễm."),
        ("Bảo tồn tối đa mô hạt mới hình thành:", "Không gây đau xót, không kích ứng da, tạo môi trường vi mô lý tưởng để lên da non."),
        ("Ứng dụng lâm sàng rộng rãi:", "Được hơn 100 bệnh viện lớn tin dùng trong điều trị loét tì đè, loét bàn chân đái tháo đường, bỏng.")
    ]
    y_p = 350
    for bold_txt, norm_txt in points:
        # Chấm tròn xanh ngọc tinh tế
        draw.ellipse([(70, y_p + 8), (86, y_p + 24)], fill="#00A896")
        draw.text((105, y_p), bold_txt, fill="#005B94", font=get_font(23, bold=True))
        draw.text((105, y_p + 35), norm_txt, fill="#4A5568", font=get_font(21, bold=False))
        y_p += 105

    # 6. Khối thông tin bộ đôi sản phẩm tự nhiên
    draw.line([(70, y_p + 20), (w - 70, y_p + 20)], fill="#E2E8F0", width=1)
    
    draw.text((70, y_p + 50), "BỘ ĐÔI CHĂM SÓC TOÀN DIỆN TẠI NHÀ & BỆNH VIỆN", fill="#00A896", font=get_font(22, bold=True))
    draw.text((70, y_p + 90), "• Prontosan® Wound Spray (75ml): Xịt rửa sát khuẩn vết thương nông, trầy xước.", fill="#2D3748", font=get_font(22, bold=False))
    draw.text((70, y_p + 130), "• Prontosan® Wound Gel (30g): Giữ ẩm liên tục, kháng khuẩn cho vết loét sâu, tì đè.", fill="#2D3748", font=get_font(22, bold=False))

    # 7. Chân trang tối giản, sang trọng
    draw.rectangle([(0, h - 110), (w, h)], fill="#003E5C")
    draw.text((70, h - 75), "GLOBALPHARMA • ĐỐI TÁC PHÂN PHỐI CHÍNH THỨC B.BRAUN TẠI VIỆT NAM", fill="#FFFFFF", font=get_font(20, bold=True))
    draw.text((70, h - 45), "Trang thiết bị y tế loại B • Tiêu chuẩn chất lượng Châu Âu (CE)", fill="#A0AEC0", font=get_font(16, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Prontosan tự nhiên tại: {output_path}")
    return output_path


def render_affiliate_poster(output_path: str, force: bool = False):
    """
    Thiết kế poster Tuyển dụng Affiliate theo phong cách Doanh nhân Sức khỏe (Solopreneur).
    Tối giản, đẳng cấp, tone màu xanh navy sang trọng (#0F172A) & vàng ánh kim (#D4AF37).
    """
    out = Path(output_path)
    if not force and out.exists() and out.stat().st_size > 200000:
        print(f"[SKIP] Đã có ảnh Affiliate chất lượng cao (>200KB): {output_path}")
        return output_path

    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#0F172A")
    draw = ImageDraw.Draw(img)

    # 1. Nền Gradient sang trọng
    for y in range(h):
        ratio = y / h
        r = int(15 + ratio * 15)
        g = int(23 + ratio * 20)
        b = int(42 + ratio * 25)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Gắn logo GlobalPharma
    end_x = paste_globalpharma_logo(img, x=70, y=60, target_h=55)

    draw.line([(end_x + 25, 60), (end_x + 25, 115)], fill="#334155", width=2)
    draw.text((end_x + 45, 75), "PARTNER NETWORK • AFFILIATE Y KHOA", fill="#D4AF37", font=get_font(22, bold=True))

    # 3. Tiêu đề
    draw.text((70, 180), "KINH DOANH MỘT NGƯỜI (SOLOPRENEUR)", fill="#FFFFFF", font=get_font(46, bold=True))
    draw.text((70, 240), "Dành riêng cho Dược sĩ, PT & Chuyên gia hoạt động trong ngành sức khỏe", fill="#94A3B8", font=get_font(23, bold=False))

    draw.line([(70, 300), (w - 70, 300)], fill="#334155", width=1)

    # 4. Giá trị cốt lõi
    values = [
        ("Chuyển hóa uy tín chuyên môn thành thu nhập bền vững:", "Không cần ôm hàng, không rủi ro tồn kho, GlobalPharma đảm nhiệm trọn gói vận hành và pháp lý."),
        ("Dải sản phẩm chính ngạch tiêu chuẩn Châu Âu:", "B.Braun CHLB Đức - Thương hiệu y tế toàn cầu được giới bác sĩ và dược sĩ tin dùng."),
        ("Đồng hành bằng hệ thống AI & Công nghệ số:", "Cung cấp trọn bộ tư liệu truyền thông, kịch bản tư vấn chuẩn lâm sàng giúp đối tác tự tin lan tỏa.")
    ]
    y_v = 345
    for title, desc in values:
        draw.ellipse([(70, y_v + 8), (86, y_v + 24)], fill="#D4AF37")
        draw.text((105, y_v), title, fill="#D4AF37", font=get_font(23, bold=True))
        draw.text((105, y_v + 35), desc, fill="#E2E8F0", font=get_font(20, bold=False))
        y_v += 110

    # 5. Thông điệp đối tác
    draw.line([(70, y_v + 20), (w - 70, y_v + 20)], fill="#334155", width=1)
    
    quote = (
        "\"Sứ mệnh của chúng tôi là đồng hành cùng những người làm chuyên môn y dược,\n"
        " cùng mang các giải pháp dinh dưỡng y học và chăm sóc vết thương chuẩn mực\n"
        " đến tận tay những người bệnh đang cần giúp đỡ nhất.\""
    )
    draw.text((70, y_v + 50), quote, fill="#94A3B8", font=get_font(21, bold=False))

    # 6. Chân trang
    draw.rectangle([(0, h - 110), (w, h)], fill="#020617")
    draw.text((70, h - 75), "GLOBALPHARMA • ĐỐI TÁC CHIẾN LƯỢC CỦA CHUYÊN GIA SỨC KHỎE", fill="#D4AF37", font=get_font(20, bold=True))
    draw.text((70, h - 45), "Tham gia cộng đồng đối tác: Fanpage Affiliate - GlobalPharma", fill="#64748B", font=get_font(16, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Affiliate tự nhiên tại: {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tạo poster tự nhiên chuẩn nhận diện y tế GlobalPharma")
    parser.add_argument("--type", choices=["nutricomp", "prontosan", "affiliate", "all"], default="all")
    parser.add_argument("--variant", choices=["box12", "combo12", "emotion", "bottles"], default="box12")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--force", action="store_true", help="Buộc render đè ảnh cũ")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.type in ("nutricomp", "all"):
        render_nutricomp_poster(str(out_dir / "poster_nutricomp_drink_plus.png"), variant=args.variant, force=args.force)
    if args.type in ("prontosan", "all"):
        render_prontosan_poster(str(out_dir / "poster_prontosan_wound_spray.png"), force=args.force)
    if args.type in ("affiliate", "all"):
        render_affiliate_poster(str(out_dir / "poster_affiliate_partner.png"), force=args.force)


if __name__ == "__main__":
    main()
