#!/usr/bin/env python3
"""
render_poster.py - Tạo hình ảnh poster bài post y tế chuẩn nhận diện GlobalPharma & B.Braun Đức
theo đúng quy chuẩn thiết kế từ bộ ảnh tham chiếu thực tế (Medical Advertising Poster Specification).

Bao gồm:
- Nutricomp Drink Renal (Hộp quà 12 chai, Combo 12 chai, Ảnh chạm cảm xúc người nhà, Phục hồi thể trạng)
- Prontosan Wound Care (Chai xịt Spray, Gel phá vỡ Biofilm, 3 bước chăm sóc loét tì đè)
- Affiliate GlobalPharma (Mô hình Kinh doanh một người / Solopreneur uy tín y khoa)
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

from PIL import Image, ImageDraw, ImageFont

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


def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)


def render_nutricomp_poster(output_path: str, variant: str = "box12"):
    """
    Tạo poster Nutricomp theo đúng chuẩn tham chiếu của Sếp:
    - variant='box12': Hộp quà 12 chai mở nắp + splash sữa 400 kcal
    - variant='combo12': Combo 12 chai + chai đứng nắp tím
    - variant='emotion': Chạm cảm xúc người nhà bệnh nhân suy kiệt
    - variant='bottles': Cặp 2 chai Nutricomp Renal + cặp vợ chồng vui khỏe
    """
    variant_map = {
        "box12": REFS_DIR / "ref_nutricomp_box12.jpg",
        "combo12": REFS_DIR / "ref_nutricomp_combo12.jpg",
        "emotion": REFS_DIR / "ref_nutricomp_emotion.jpg",
        "bottles": REFS_DIR / "ref_nutricomp_renal_bottles.jpg",
    }

    ref_file = variant_map.get(variant, variant_map["box12"])
    
    # Nếu có ảnh tham chiếu chuẩn, upscale hoặc convert sang output 1080x1080 chất lượng cao
    if ref_file.exists():
        img = Image.open(ref_file)
        if img.size != (1080, 1080):
            img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        print(f"[SUCCESS] Đã tạo poster Nutricomp ({variant}) theo đúng tham chiếu tại: {output_path}")
        return output_path

    # FALLBACK PROCEDURAL GENERATOR THEO ĐÚNG LAYOUT THAM CHIẾU
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#023D26")
    draw = ImageDraw.Draw(img)

    # 1. Background Gradient (Ngọc lục bảo sâu -> Trắng ngà phía trên)
    for y in range(h):
        ratio = y / h
        if ratio < 0.35:
            # Vùng trên: Trắng ngà pha vàng kem nhẹ
            r = int(250 - ratio * 100)
            g = int(248 - ratio * 80)
            b = int(242 - ratio * 100)
        else:
            # Vùng dưới: Xanh lục bảo đậm #013D29
            sub_ratio = (ratio - 0.35) / 0.65
            r = int(10 * (1 - sub_ratio) + 2 * sub_ratio)
            g = int(80 * (1 - sub_ratio) + 55 * sub_ratio)
            b = int(50 * (1 - sub_ratio) + 38 * sub_ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Header: Logo GP & Cờ Đức
    font_bold_sm = get_font(22, bold=True)
    draw.text((60, 45), "GLOBALPHARMA", fill="#E30613", font=get_font(26, bold=True))
    draw.line([(280, 40), (280, 80)], fill="#888888", width=2)
    # Cờ Đức tròn
    draw.ellipse([(305, 42), (345, 82)], fill="#000000", outline="#D4AF37", width=2)
    draw.chord([(305, 42), (345, 82)], start=0, end=180, fill="#DD0000")
    draw.chord([(305, 42), (345, 82)], start=60, end=120, fill="#FFCE00")
    draw.text((360, 48), "Nhập khẩu chính hãng từ Đức", fill="#1E2A38", font=font_bold_sm)

    # 3. Tiêu đề thương hiệu
    font_sub_title = get_font(28, bold=True)
    font_main_brand = get_font(68, bold=True)
    draw.text((60, 115), "SỮA DINH DƯỠNG Y HỌC", fill="#1E2A38", font=font_sub_title)
    draw.text((60, 155), "NUTRICOMP®", fill="#013D29", font=font_main_brand)

    # 4. Banner giải pháp chuyên biệt bo góc viền vàng
    draw_rounded_rect(draw, (60, 245, 560, 315), radius=16, fill="#F5A623", outline="#D4AF37", width=2)
    draw.text((75, 255), "GIẢI PHÁP DINH DƯỠNG CHUYÊN BIỆT", fill="#FFFFFF", font=get_font(22, bold=True))
    draw_rounded_rect(draw, (120, 280, 500, 310), radius=12, fill="#013D29")
    draw.text((150, 283), "CHO NGƯỜI BỆNH THẬN", fill="#FFFFFF", font=get_font(20, bold=True))

    # 5. Cột tính năng ưu việt (3 Icon tròn bên trái)
    features = [
        ("ÍT ĐIỆN GIẢI", "Kiểm soát Natri, Kali, Phospho"),
        ("GIÀU ĐẠM & NĂNG LƯỢNG", "14g Protein | 400 kcal trong 200ml"),
        ("DỄ UỐNG, DỄ TIÊU HÓA", "Hấp thu tốt, êm bụng, ngon miệng")
    ]
    y_feat = 345
    for title, desc in features:
        draw.ellipse([(60, y_feat), (120, y_feat + 60)], fill="#013D29", outline="#3BCFAF", width=2)
        draw.text((75, y_feat + 12), "★", fill="#3BCFAF", font=get_font(30, bold=True))
        draw.text((135, y_feat + 5), title, fill="#FFFFFF", font=get_font(22, bold=True))
        draw.text((135, y_feat + 32), desc, fill="#E0F2F1", font=get_font(19, bold=False))
        y_feat += 85

    # Khiên bảo chứng
    draw_rounded_rect(draw, (60, y_feat + 10, 520, y_feat + 75), radius=14, fill="#004D40", outline="#F5A623", width=2)
    draw.text((80, y_feat + 20), "✔ DINH DƯỠNG CHUẨN Y HỌC", fill="#F5A623", font=get_font(21, bold=True))
    draw.text((80, y_feat + 45), "CHĂM SÓC THẬN – NÂNG TẦM CUỘC SỐNG", fill="#FFFFFF", font=get_font(18, bold=False))

    # 6. Hero Visual giả lập (Khung sản phẩm 12 chai)
    draw_rounded_rect(draw, (560, 280, 1030, 720), radius=20, fill="#024D33", outline="#D4AF37", width=3)
    draw.text((610, 310), "HỘP QUÀ COMBO 12 CHAI", fill="#D4AF37", font=get_font(28, bold=True))
    draw.text((610, 350), "Nutricomp® Drink Renal 200ml", fill="#FFFFFF", font=get_font(22, bold=False))
    draw.text((610, 480), "400 kcal / 200ml", fill="#FFD54F", font=get_font(42, bold=True))
    draw.text((610, 535), "Năng lượng cao phục hồi thể trạng", fill="#E0F2F1", font=get_font(20, bold=False))

    # 7. Bottom Action Bar
    # Nút CTA Đỏ 3D
    draw_rounded_rect(draw, (60, h - 165, 520, h - 75), radius=45, fill="#D32F2F", outline="#FFCDD2", width=2)
    draw.text((100, h - 150), "🛒  ĐẶT MUA NGAY  >>", fill="#FFFFFF", font=get_font(28, bold=True))
    draw.text((140, h - 110), "TƯ VẤN DINH DƯỠNG MIỄN PHÍ", fill="#FFF9C4", font=get_font(18, bold=False))

    # 3 Badges uy tín bên phải
    draw.text((560, h - 145), "🇩🇪 Nhập khẩu Đức", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((750, h - 145), "👨‍⚕️ Khuyên dùng", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((910, h - 145), "⭐ Chuẩn quốc tế", fill="#FFFFFF", font=get_font(19, bold=True))

    # Disclaimer FSMP
    draw.rectangle([(0, h - 55), (w, h)], fill="#002517")
    draw.text((60, h - 42), "Thực phẩm dinh dưỡng y học (FSMP) – Không phải thuốc, không thay thế thuốc chữa bệnh. Dùng theo tư vấn của bác sĩ/chuyên gia.", fill="#A7D7C5", font=get_font(16, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Nutricomp chuẩn tại: {output_path}")
    return output_path


def render_prontosan_poster(output_path: str):
    """Tạo poster Prontosan theo quy chuẩn cao cấp nhận diện y tế B.Braun Đức"""
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#003E5C")
    draw = ImageDraw.Draw(img)

    # 1. Gradient Nền Y Tế B.Braun
    for y in range(h):
        ratio = y / h
        if ratio < 0.35:
            r = int(245 - ratio * 60)
            g = int(250 - ratio * 40)
            b = int(253 - ratio * 20)
        else:
            sub = (ratio - 0.35) / 0.65
            r = int(5 * (1 - sub) + 0 * sub)
            g = int(75 * (1 - sub) + 45 * sub)
            b = int(120 * (1 - sub) + 70 * sub)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # 2. Header
    draw.text((60, 45), "GLOBALPHARMA", fill="#E30613", font=get_font(26, bold=True))
    draw.line([(280, 40), (280, 80)], fill="#888888", width=2)
    draw.ellipse([(305, 42), (345, 82)], fill="#000000", outline="#D4AF37", width=2)
    draw.chord([(305, 42), (345, 82)], start=0, end=180, fill="#DD0000")
    draw.chord([(305, 42), (345, 82)], start=60, end=120, fill="#FFCE00")
    draw.text((360, 48), "B.Braun Melsungen AG - CHLB Đức", fill="#005B94", font=get_font(22, bold=True))

    # 3. Tiêu đề
    draw.text((60, 115), "DUNG DỊCH & GEL RỬA VẾT THƯƠNG CHUYÊN DỤNG", fill="#003E5C", font=get_font(26, bold=True))
    draw.text((60, 155), "PRONTOSAN®", fill="#005B94", font=get_font(68, bold=True))

    # Banner
    draw_rounded_rect(draw, (60, 245, 600, 315), radius=16, fill="#00A896", outline="#3BCFAF", width=2)
    draw.text((75, 255), "GIẢI PHÁP LÀM LÀNH VẾT THƯƠNG & LOÉT TÌ ĐÈ", fill="#FFFFFF", font=get_font(21, bold=True))
    draw_rounded_rect(draw, (120, 280, 540, 310), radius=12, fill="#003E5C")
    draw.text((150, 283), "PHÁ VỠ MÀNG BIOFILM KHÁNG KHUẨN", fill="#3BCFAF", font=get_font(19, bold=True))

    # 4. Tính năng
    features = [
        ("HOẠT CHẤT ĐỘC QUYỀN", "Polihexanide (PHMB) + Betaine kháng khuẩn"),
        ("KHÔNG GÂY ĐAU XÓT", "Dịu nhẹ mô hạt, bảo tồn tế bào mới hình thành"),
        ("LÀM LÀNH VẾT THƯƠNG NHANH", "Hiệu quả rõ rệt trên vết loét tiểu đường, bỏng, tì đè")
    ]
    y_feat = 345
    for title, desc in features:
        draw.ellipse([(60, y_feat), (120, y_feat + 60)], fill="#003E5C", outline="#3BCFAF", width=2)
        draw.text((75, y_feat + 12), "✦", fill="#3BCFAF", font=get_font(30, bold=True))
        draw.text((135, y_feat + 5), title, fill="#FFFFFF", font=get_font(22, bold=True))
        draw.text((135, y_feat + 32), desc, fill="#E0F7FA", font=get_font(19, bold=False))
        y_feat += 85

    # Khung sản phẩm
    draw_rounded_rect(draw, (620, 280, 1030, 720), radius=20, fill="#002D42", outline="#3BCFAF", width=3)
    draw.text((650, 310), "BỘ ĐÔI CHĂM SÓC TOÀN DIỆN", fill="#3BCFAF", font=get_font(24, bold=True))
    draw.text((650, 355), "• Prontosan® Wound Spray 75ml", fill="#FFFFFF", font=get_font(22, bold=False))
    draw.text((650, 395), "• Prontosan® Wound Gel 30g", fill="#FFFFFF", font=get_font(22, bold=False))
    draw.text((650, 480), "CHỨNG NHẬN CE", fill="#F5A623", font=get_font(36, bold=True))
    draw.text((650, 530), "Tiêu chuẩn Thiết bị y tế Châu Âu", fill="#E0F7FA", font=get_font(20, bold=False))

    # Chân trang CTA
    draw_rounded_rect(draw, (60, h - 165, 520, h - 75), radius=45, fill="#D32F2F", outline="#FFCDD2", width=2)
    draw.text((100, h - 150), "🛒  ĐẶT MUA NGAY  >>", fill="#FFFFFF", font=get_font(28, bold=True))
    draw.text((140, h - 110), "TƯ VẤN CHĂM SÓC VẾT THƯƠNG MIỄN PHÍ", fill="#FFF9C4", font=get_font(18, bold=False))

    draw.text((560, h - 145), "🇩🇪 Chuẩn CHLB Đức", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((750, h - 145), "🏥 Bệnh viện tin dùng", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((930, h - 145), "🛡️ Kháng khuẩn", fill="#FFFFFF", font=get_font(19, bold=True))

    draw.rectangle([(0, h - 55), (w, h)], fill="#001F2D")
    draw.text((60, h - 42), "Trang thiết bị y tế loại B – Đọc kỹ hướng dẫn sử dụng trước khi dùng. Nhập khẩu chính ngạch B.Braun CHLB Đức.", fill="#80DEEA", font=get_font(16, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Prontosan chuẩn tại: {output_path}")
    return output_path


def render_affiliate_poster(output_path: str):
    """Tạo poster Tuyển dụng Affiliate theo phong cách Trao giá trị - Solopreneur sang trọng"""
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#1A2530")
    draw = ImageDraw.Draw(img)

    for y in range(h):
        ratio = y / h
        if ratio < 0.35:
            r = int(248 - ratio * 40)
            g = int(246 - ratio * 40)
            b = int(240 - ratio * 50)
        else:
            sub = (ratio - 0.35) / 0.65
            r = int(26 * (1 - sub) + 15 * sub)
            g = int(37 * (1 - sub) + 20 * sub)
            b = int(48 * (1 - sub) + 30 * sub)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    draw.text((60, 45), "GLOBALPHARMA PARTNERS", fill="#D4AF37", font=get_font(26, bold=True))
    draw.line([(380, 40), (380, 80)], fill="#888888", width=2)
    draw.text((400, 48), "Mạng lưới đối tác y dược uy tín", fill="#1E2A38", font=get_font(22, bold=True))

    draw.text((60, 115), "MÔ HÌNH KINH DOANH MỘT NGƯỜI (SOLOPRENEUR)", fill="#1E2A38", font=get_font(26, bold=True))
    draw.text((60, 155), "AFFILIATE NGÀNH SỨC KHỎE", fill="#D4AF37", font=get_font(56, bold=True))

    draw_rounded_rect(draw, (60, 245, 680, 315), radius=16, fill="#2C3E50", outline="#D4AF37", width=2)
    draw.text((75, 255), "DÀNH RIÊNG CHO DƯỢC SĨ, PT & NHÂN SỰ Y TẾ", fill="#FFFFFF", font=get_font(21, bold=True))
    draw.text((75, 283), "Biến tri thức y khoa thành nguồn thu nhập bền vững", fill="#D4AF37", font=get_font(18, bold=False))

    features = [
        ("SẢN PHẨM CHÍNH HÃNG CHÂU ÂU", "B.Braun Đức – Uy tín y khoa được bảo chứng lâm sàng"),
        ("KHÔNG ÔM HÀNG - KHÔNG RỦI RO", "GlobalPharma xử lý kho vận, đóng gói và pháp lý 100%"),
        ("HỆ THỐNG AI & CONTENT ĐỒNG HÀNH", "Cung cấp sẵn kịch bản tư vấn, poster và video chuyên sâu")
    ]
    y_feat = 345
    for title, desc in features:
        draw.ellipse([(60, y_feat), (120, y_feat + 60)], fill="#1E2A38", outline="#D4AF37", width=2)
        draw.text((75, y_feat + 12), "★", fill="#D4AF37", font=get_font(30, bold=True))
        draw.text((135, y_feat + 5), title, fill="#FFFFFF", font=get_font(22, bold=True))
        draw.text((135, y_feat + 32), desc, fill="#D1D5DB", font=get_font(19, bold=False))
        y_feat += 85

    draw_rounded_rect(draw, (60, h - 165, 520, h - 75), radius=45, fill="#D4AF37", outline="#FDE68A", width=2)
    draw.text((100, h - 150), "🤝  GIA NHẬP ĐỐI TÁC  >>", fill="#1E2A38", font=get_font(26, bold=True))
    draw.text((140, h - 110), "ĐĂNG KÝ NHẬN TƯ VẤN MÔ HÌNH", fill="#374151", font=get_font(18, bold=False))

    draw.text((560, h - 145), "🛡️ Chính ngạch", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((740, h - 145), "📈 Thu nhập cao", fill="#FFFFFF", font=get_font(19, bold=True))
    draw.text((910, h - 145), "🤖 AI hỗ trợ", fill="#FFFFFF", font=get_font(19, bold=True))

    draw.rectangle([(0, h - 55), (w, h)], fill="#0D131A")
    draw.text((60, h - 42), "GlobalPharma Partner Program – Hợp tác minh bạch, tôn trọng uy tín người làm nghề y dược.", fill="#9CA3AF", font=get_font(16, bold=False))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Affiliate chuẩn tại: {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tạo poster chuẩn nhận diện y tế GlobalPharma")
    parser.add_argument("--type", choices=["nutricomp", "prontosan", "affiliate", "all"], default="all")
    parser.add_argument("--variant", choices=["box12", "combo12", "emotion", "bottles"], default="box12")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.type in ("nutricomp", "all"):
        render_nutricomp_poster(str(out_dir / "poster_nutricomp_drink_plus.png"), variant=args.variant)
    if args.type in ("prontosan", "all"):
        render_prontosan_poster(str(out_dir / "poster_prontosan_wound_spray.png"))
    if args.type in ("affiliate", "all"):
        render_affiliate_poster(str(out_dir / "poster_affiliate_partner.png"))


if __name__ == "__main__":
    main()
