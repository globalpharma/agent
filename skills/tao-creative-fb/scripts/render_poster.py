#!/usr/bin/env python3
"""
render_poster.py - Trình tạo ấn phẩm quảng cáo Facebook Ads & Poster y khoa chuẩn mực
dành riêng cho GlobalPharma & B.Braun CHLB Đức.

Tuân thủ nghiêm ngặt chỉ đạo của Ban Lãnh đạo:
1. Nutricomp Plus: BẮT BUỘC dùng đúng ảnh 1 chai Plus 200ml (cut_nutricomp_plus_bottle.png),
   tông màu vàng cam ấm áp giàu năng lượng (1.5 kcal/ml, 300 kcal/chai).
2. Nutricomp Renal: BẮT BUỘC dùng đúng ảnh 1 chai Renal 200ml (cut_nutricomp_single_bottle.png),
   tông màu xanh ngọc y tế mát dịu (2.0 kcal/ml, 400 kcal/chai).
3. Nutricomp Combo: CHỈ KHI NÀO có yêu cầu 'combo' mới dùng ảnh hộp 12 chai (cut_nutricomp_box.png).
4. Prontosan: Dùng đúng ảnh chai dung dịch làm sạch vết thương (cut_prontosan_bottle.png).
5. Linh hoạt layout, màu sắc hài hòa, không cứng nhắc rập khuôn, giữ vững nhận diện thương hiệu.
"""

import sys
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# Resolve references directory across local and container paths
candidate_refs = [
    SKILL_DIR / "assets" / "references",
    Path("/app/data/skills/tao-creative-fb/assets/references"),
    Path("/app/workspace/skills/tao-creative-fb/assets/references"),
    SKILL_DIR.parent.parent / "skills" / "tao-creative-fb" / "assets" / "references",
]
REFS_DIR = SKILL_DIR / "assets" / "references"
for c in candidate_refs:
    if c.exists():
        REFS_DIR = c
        break

# Output directories
OUTPUT_DIR = Path("/app/workspace/output") if Path("/app/workspace").exists() else (SKILL_DIR / "output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BRAIN_DIR = Path("C:/Users/Surface/.gemini/antigravity/brain/552b4a88-d83e-4471-97a6-f32d72fa14d4")

def get_font(size: int, bold: bool = False):
    candidates = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_master_logo(target_h: int = 42):
    candidates = [
        REFS_DIR / "real_logo_globalpharma_banner.png",
        REFS_DIR / "real_logo_globalpharma_master.png",
        SKILL_DIR / "assets" / "globalpharma_logo.png",
    ]
    for p in candidates:
        if p.exists():
            try:
                logo = Image.open(p).convert("RGBA")
                ratio = target_h / logo.height
                new_w = int(logo.width * ratio)
                return logo.resize((new_w, target_h), Image.Resampling.LANCZOS)
            except Exception:
                continue
    return None

def draw_german_flag(draw, x, y, width=28, height=18):
    """Vẽ cờ Đức (Đen - Đỏ - Vàng) làm bảo chứng uy tín B.Braun"""
    h_stripe = height // 3
    draw.rectangle([(x, y), (x + width, y + h_stripe)], fill="#1E293B")
    draw.rectangle([(x, y + h_stripe), (x + width, y + 2 * h_stripe)], fill="#DC2626")
    draw.rectangle([(x, y + 2 * h_stripe), (x + width, y + height)], fill="#FBBF24")

def draw_text_with_shadow(draw, pos, text, fill, font, shadow_color=(0, 0, 0, 180), offset=(1, 2)):
    x, y = pos
    ox, oy = offset
    draw.text((x + ox, y + oy), text, fill=shadow_color, font=font)
    draw.text((x, y), text, fill=fill, font=font)

def create_drop_shadow(alpha_mask, offset=(10, 25), blur_radius=20, shadow_alpha=140):
    w, h = alpha_mask.size
    shadow = Image.new("RGBA", (w + abs(offset[0]) + blur_radius * 2, h + abs(offset[1]) + blur_radius * 2), (0, 0, 0, 0))
    black_obj = Image.new("RGBA", (w, h), (15, 20, 30, shadow_alpha))
    black_obj.putalpha(alpha_mask)
    paste_x = blur_radius + max(0, offset[0])
    paste_y = blur_radius + max(0, offset[1])
    shadow.paste(black_obj, (paste_x, paste_y), black_obj)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    return shadow, (paste_x, paste_y)

def draw_pill(draw, x, y, text, font, bg_color, text_color, padding=(18, 10), border_color=None):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pw, ph = padding
    box = [(x, y), (x + tw + pw * 2, y + th + ph * 2)]
    radius = (th + ph * 2) // 2
    draw.rounded_rectangle(box, radius=radius, fill=bg_color, outline=border_color, width=1 if border_color else 0)
    tx = x + pw - bbox[0]
    ty = y + ph - bbox[1]
    draw.text((tx, ty), text, fill=text_color, font=font)
    return x + tw + pw * 2 + 12

def draw_card(draw, box, fill_color, border_color=None, radius=16):
    draw.rounded_rectangle(box, radius=radius, fill=fill_color, outline=border_color, width=1 if border_color else 0)

# ==============================================================================
# 1. NUTRICOMP DRINK PLUS (1 CHAI LẺ 200ML, CAO NĂNG LƯỢNG, PHỤC HỒI THỂ TRẠNG)
# ==============================================================================
def render_pro_nutricomp_plus():
    w, h = 1080, 1080
    bg_candidates = [
        REFS_DIR / "bg_lifestyle_dining.jpg",
        BRAIN_DIR / "nutricomp_dining_scene_1791701099684.jpg",
    ]
    bg_img = None
    for p in bg_candidates:
        if p.exists():
            try:
                bg_img = Image.open(p).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
                # Apply warm subtle filter
                break
            except Exception:
                continue

    if bg_img is None:
        # High-end studio background: Warm Amber / Cream / Medical Sunrise
        bg_img = Image.new("RGBA", (w, h), (254, 252, 248, 255))
        draw_bg = ImageDraw.Draw(bg_img)
        for y in range(h):
            r = int(255 - (y / h) * 15)
            g = int(248 - (y / h) * 25)
            b = int(238 - (y / h) * 45)
            draw_bg.line([(0, y), (w, y)], fill=(r, g, b, 255))

    canvas = bg_img.copy()

    # Left vignette overlay to guarantee 100% crisp text readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for x in range(int(w * 0.65)):
        alpha = int(220 * (1 - (x / (w * 0.65)) ** 1.2))
        draw_ov.line([(x, 0), (x, h)], fill=(15, 23, 42, alpha))
    canvas = Image.alpha_composite(canvas, overlay)

    # 100% AUTHENTIC 1 SINGLE BOTTLE PLUS (NẮP VÀNG / CAM)
    prod_path = REFS_DIR / "cut_nutricomp_plus_bottle.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "real_nutricomp_drink_plus_vanilla.jpg"

    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_h = 700
        ratio = target_h / prod.height
        target_w = int(prod.width * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Enhance warm lighting on bottle
        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(15, 30), blur_radius=25, shadow_alpha=160)

        pos_x = int(w * 0.55)
        pos_y = h - target_h - 70

        canvas.paste(shadow, (pos_x - spx, pos_y - spy), shadow)
        canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)

    draw = ImageDraw.Draw(canvas)

    # HEADER BRANDING
    # Logo GlobalPharma in elegant translucent glass card
    logo = get_master_logo(target_h=42)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 45), (50 + card_w, 98)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 51), logo)

    # German Flag & B.Braun partner badge top right
    badge_x = w - 300
    draw.rounded_rectangle([(badge_x, 45), (w - 50, 98)], radius=12, fill=(15, 23, 42, 230), outline="#F59E0B", width=1)
    draw_german_flag(draw, badge_x + 14, 62, 26, 18)
    draw.text((badge_x + 48, 62), "CHLB ĐỨC • B.BRAUN", fill="#F8FAFC", font=get_font(14, bold=True))

    # PRODUCT HEADLINE & CLINICAL HOOK
    draw_text_with_shadow(draw, (50, 135), "DINH DƯỠNG Y HỌC CAO NĂNG LƯỢNG", "#FBBF24", get_font(18, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 170), "NUTRICOMP® PLUS", "#FFFFFF", get_font(52, bold=True), shadow_color=(0, 0, 0, 240))
    draw_text_with_shadow(draw, (50, 240), "1.5 KCAL / ML • 300 KCAL / CHAI", "#F59E0B", get_font(30, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 285), "PHỤC HỒI THỂ TRẠNG SUY KIỆT • SAU PHẪU THUẬT", "#F1F5F9", get_font(21, bold=True), shadow_color=(0, 0, 0, 200))

    # Sub-hook (thấu cảm y khoa)
    draw_text_with_shadow(draw, (50, 325), "Chuyên biệt cho người sau mổ, xạ trị, hóa trị & người suy mòn dinh dưỡng", "#CBD5E1", get_font(16, bold=False), shadow_color=(0, 0, 0, 200))

    # CLINICAL BENEFIT CARDS (3 Điểm tựa y khoa)
    card_y = 380
    benefits = [
        ("● ĐẠM CHẤT LƯỢNG CAO 12G", "Whey & Casein thủy phân hấp thu nhanh, tái tạo mô cơ"),
        ("● GIÀU EPA & DHA TỪ DẦU CÁ", "Chống viêm tế bào, cải thiện miễn dịch, kích thích ngon miệng"),
        ("● ĐẦY ĐỦ 28 VITAMIN & KHOÁNG", "Bù đắp vi chất thiếu hụt, nâng cao đề kháng toàn diện"),
    ]
    for title, desc in benefits:
        draw_card(draw, [(50, card_y), (540, card_y + 68)], (30, 41, 59, 210), border_color="#F59E0B", radius=12)
        draw.text((68, card_y + 12), title, fill="#FBBF24", font=get_font(16, bold=True))
        draw.text((68, card_y + 36), desc, fill="#E2E8F0", font=get_font(13, bold=False))
        card_y += 82

    # CALL TO ACTION BUTTON (TRANSLUCENT GOLDEN AMBER)
    draw_card(draw, [(50, h - 145), (460, h - 85)], "#D97706", border_color="#FDE68A", radius=30)
    draw.text((85, h - 123), "TƯ VẤN CÙNG DƯỢC SĨ GLOBALPHARMA", fill="#FFFFFF", font=get_font(16, bold=True))

    # Bottom commitment pill
    draw_text_with_shadow(draw, (50, h - 55), "Chai 200ml tiệt trùng • Nhập khẩu chính ngạch B.Braun CHLB Đức", "#94A3B8", get_font(14, bold=False))

    out_file = OUTPUT_DIR / "poster_nutricomp_drink_plus.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file

# ==============================================================================
# 2. NUTRICOMP DRINK RENAL (1 CHAI LẺ 200ML, KIỂM SOÁT ĐIỆN GIẢI CHO BỆNH THẬN)
# ==============================================================================
def render_pro_nutricomp_renal():
    w, h = 1080, 1080
    bg_candidates = [
        REFS_DIR / "bg_luxury_teal_podium.jpg",
        BRAIN_DIR / "luxury_teal_podium_1791617178766.jpg",
    ]
    bg_img = None
    for p in bg_candidates:
        if p.exists():
            try:
                bg_img = Image.open(p).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
                break
            except Exception:
                continue

    if bg_img is None:
        # Luxury Clinical Teal Studio
        bg_img = Image.new("RGBA", (w, h), (4, 47, 46, 255))
        draw_bg = ImageDraw.Draw(bg_img)
        for y in range(h):
            r = int(4 + (y / h) * 15)
            g = int(47 + (y / h) * 35)
            b = int(46 + (y / h) * 55)
            draw_bg.line([(0, y), (w, y)], fill=(r, g, b, 255))

    canvas = bg_img.copy()

    # Left vignette overlay to guarantee text readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for x in range(int(w * 0.65)):
        alpha = int(220 * (1 - (x / (w * 0.65)) ** 1.2))
        draw_ov.line([(x, 0), (x, h)], fill=(4, 30, 36, alpha))
    canvas = Image.alpha_composite(canvas, overlay)

    # 100% AUTHENTIC 1 SINGLE BOTTLE RENAL (NẮP TÍM ĐẶC TRƯNG B.BRAUN)
    prod_path = REFS_DIR / "cut_nutricomp_single_bottle.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "crop_nutricomp_bottle.png"

    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_h = 700
        ratio = target_h / prod.height
        target_w = int(prod.width * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)

        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(15, 30), blur_radius=25, shadow_alpha=160)

        pos_x = int(w * 0.55)
        pos_y = h - target_h - 70

        canvas.paste(shadow, (pos_x - spx, pos_y - spy), shadow)
        canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)

    draw = ImageDraw.Draw(canvas)

    # HEADER BRANDING
    logo = get_master_logo(target_h=42)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 45), (50 + card_w, 98)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 51), logo)

    badge_x = w - 300
    draw.rounded_rectangle([(badge_x, 45), (w - 50, 98)], radius=12, fill=(15, 23, 42, 230), outline="#0D9488", width=1)
    draw_german_flag(draw, badge_x + 14, 62, 26, 18)
    draw.text((badge_x + 48, 62), "CHLB ĐỨC • B.BRAUN", fill="#F8FAFC", font=get_font(14, bold=True))

    # PRODUCT HEADLINE & CLINICAL HOOK
    draw_text_with_shadow(draw, (50, 135), "DINH DƯỠNG LÂM SÀNG CHUYÊN BIỆT CHO BỆNH THẬN", "#38BDF8", get_font(18, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 170), "NUTRICOMP® RENAL", "#FFFFFF", get_font(52, bold=True), shadow_color=(0, 0, 0, 240))
    draw_text_with_shadow(draw, (50, 240), "2.0 KCAL / ML • 400 KCAL / CHAI", "#2DD4BF", get_font(30, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 285), "BẢO VỆ CHỨC NĂNG THẬN • KIỂM SOÁT ĐIỆN GIẢI", "#F1F5F9", get_font(21, bold=True), shadow_color=(0, 0, 0, 200))

    # Sub-hook (y khoa chuẩn xác)
    draw_text_with_shadow(draw, (50, 325), "Chuyên biệt cho bệnh nhân suy thận mạn & lọc máu chu kỳ theo chuẩn FSMP", "#94A3B8", get_font(16, bold=False), shadow_color=(0, 0, 0, 200))

    # CLINICAL BENEFIT CARDS (3 Điểm tựa y khoa)
    card_y = 380
    benefits = [
        ("● KIỂM SOÁT NGHIÊM NGẶT ĐIỆN GIẢI", "Tối ưu hóa Kali, Natri, Phospho giúp giảm gánh nặng lọc cho thận"),
        ("● ĐẠM SINH HỌC CAO 14G / CHAI", "Bù đắp protein mất qua lọc máu, ngăn ngừa teo cơ và suy kiệt"),
        ("● ĐẬM ĐẶC NĂNG LƯỢNG 2.0 KCAL/ML", "Hạn chế tối đa thể tích dịch đưa vào cơ thể, an toàn khi kiểm soát nước"),
    ]
    for title, desc in benefits:
        draw_card(draw, [(50, card_y), (540, card_y + 68)], (15, 35, 42, 220), border_color="#0D9488", radius=12)
        draw.text((68, card_y + 12), title, fill="#2DD4BF", font=get_font(16, bold=True))
        draw.text((68, card_y + 36), desc, fill="#E2E8F0", font=get_font(13, bold=False))
        card_y += 82

    # CALL TO ACTION BUTTON (TEAL GRADIENT)
    draw_card(draw, [(50, h - 145), (460, h - 85)], "#0D9488", border_color="#5EEAD4", radius=30)
    draw.text((85, h - 123), "TƯ VẤN CÙNG DƯỢC SĨ GLOBALPHARMA", fill="#FFFFFF", font=get_font(16, bold=True))

    draw_text_with_shadow(draw, (50, h - 55), "Chai 200ml tiệt trùng • Phân phối chính thức bởi GlobalPharma", "#64748B", get_font(14, bold=False))

    out_file = OUTPUT_DIR / "poster_nutricomp_renal.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file

# ==============================================================================
# 3. NUTRICOMP COMBO 12 CHAI (HỘP QUÀ TIỆT TRÙNG B.BRAUN)
# ==============================================================================
def render_pro_nutricomp_combo():
    w, h = 1080, 1080
    bg_candidates = [
        REFS_DIR / "bg_luxury_teal_podium.jpg",
        BRAIN_DIR / "luxury_teal_podium_1791617178766.jpg",
    ]
    bg_img = None
    for p in bg_candidates:
        if p.exists():
            try:
                bg_img = Image.open(p).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
                break
            except Exception:
                continue

    if bg_img is None:
        bg_img = Image.new("RGBA", (w, h), (4, 47, 46, 255))

    canvas = bg_img.copy()

    # Darken top slightly for headline contrast
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(420):
        alpha = int(170 * (1 - y / 420))
        draw_ov.line([(0, y), (w, y)], fill=(3, 20, 24, alpha))
    canvas = Image.alpha_composite(canvas, overlay)

    # 100% AUTHENTIC 12-BOTTLE COMBO BOX
    prod_path = REFS_DIR / "cut_nutricomp_box.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "real_nutricomp_combo12_giftbox.png"

    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_w = 780
        ratio = target_w / prod.width
        target_h = int(prod.height * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)

        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(0, 25), blur_radius=22, shadow_alpha=160)

        pos_x = (w - target_w) // 2
        pos_y = 480

        canvas.paste(shadow, (pos_x - spx, pos_y - spy), shadow)
        canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)

    draw = ImageDraw.Draw(canvas)

    # HEADER BRANDING
    logo = get_master_logo(target_h=42)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 45), (50 + card_w, 98)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 51), logo)

    badge_x = w - 300
    draw.rounded_rectangle([(badge_x, 45), (w - 50, 98)], radius=12, fill=(15, 23, 42, 230), outline="#38BDF8", width=1)
    draw_german_flag(draw, badge_x + 14, 62, 26, 18)
    draw.text((badge_x + 48, 62), "CHLB ĐỨC • B.BRAUN", fill="#F8FAFC", font=get_font(14, bold=True))

    # HOOK & VALUE PROPOSITION
    draw_text_with_shadow(draw, (50, 130), "COMBO 12 CHAI TIỆT TRÙNG NGUYÊN SEAL", "#38BDF8", get_font(18, bold=True), shadow_color=(0, 0, 0, 200))
    draw_text_with_shadow(draw, (50, 160), "1.224.000 VNĐ / HỘP", "#FFFFFF", get_font(52, bold=True), shadow_color=(0, 0, 0, 240))
    draw_text_with_shadow(draw, (50, 230), "GIẢI PHÁP DINH DƯỠNG TIẾT KIỆM CHO LIỆU TRÌNH", "#F1F5F9", get_font(30, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 280), "Giá chỉ 102.000 VNĐ/chai • Liều dùng khuyến nghị 1-3 chai/ngày", "#94A3B8", get_font(17, bold=False), shadow_color=(0, 0, 0, 200))

    # 2 Feature Pills at bottom
    pill1_x = 50
    pill2_x = draw_pill(draw, pill1_x, h - 90, "● Tặng Kèm Cẩm Nang Dinh Dưỡng B.Braun", get_font(15, bold=True), (15, 23, 42, 220), "#FFFFFF", padding=(20, 10), border_color="#0D9488")
    draw_pill(draw, pill2_x + 10, h - 90, "● Miễn Phí Vận Chuyển Toàn Quốc", get_font(15, bold=True), (15, 23, 42, 220), "#38BDF8", padding=(20, 10), border_color="#0D9488")

    out_file = OUTPUT_DIR / "poster_nutricomp_combo12.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file

# ==============================================================================
# 4. PRONTOSAN WOUND SPRAY (LÀM SẠCH VÀ CHĂM SÓC VẾT THƯƠNG CHÂU ÂU)
# ==============================================================================
def render_pro_prontosan():
    w, h = 1080, 1080
    bg_candidates = [
        REFS_DIR / "bg_prontosan_clinical.jpg",
        BRAIN_DIR / "prontosan_clinical_bg_1791617199866.jpg",
    ]
    bg_img = None
    for p in bg_candidates:
        if p.exists():
            try:
                bg_img = Image.open(p).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
                break
            except Exception:
                continue

    if bg_img is None:
        bg_img = Image.new("RGBA", (w, h), (240, 249, 255, 255))

    canvas = bg_img.copy()

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(400):
        alpha = int(180 * (1 - y / 400))
        draw_ov.line([(0, y), (w, y)], fill=(255, 255, 255, alpha))
    canvas = Image.alpha_composite(canvas, overlay)

    # PRODUCT PACKSHOT
    prod_path = REFS_DIR / "cut_prontosan_bottle.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "real_prontosan_wound_spray_bottle.webp"

    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_h = 580
        ratio = target_h / prod.height
        target_w = int(prod.width * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)

        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(5, 18), blur_radius=18, shadow_alpha=120)

        pos_x = (w - target_w) // 2 + 30
        pos_y = 390

        canvas.paste(shadow, (pos_x - spx, pos_y - spy), shadow)
        canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)

    # Inset photo: Real Clinical Application action (Circle Badge)
    action_path = REFS_DIR / "real_prontosan_wound_spray_action.jpg"
    if action_path.exists():
        act_img = Image.open(action_path).convert("RGBA")
        badge_size = 210
        act_resized = act_img.resize((badge_size, badge_size), Image.Resampling.LANCZOS)

        mask = Image.new("L", (badge_size, badge_size), 0)
        ImageDraw.Draw(mask).ellipse([(0, 0), (badge_size, badge_size)], fill=255)

        badge_x = 70
        badge_y = 520

        border_box = [(badge_x - 4, badge_y - 4), (badge_x + badge_size + 4, badge_y + badge_size + 4)]
        draw_border = ImageDraw.Draw(canvas)
        draw_border.ellipse(border_box, fill="#0284C7")
        canvas.paste(act_resized, (badge_x, badge_y), mask)

        draw_border.rounded_rectangle([(badge_x - 10, badge_y + badge_size - 20), (badge_x + badge_size + 10, badge_y + badge_size + 14)], radius=8, fill="#0F172A")
        draw_border.text((badge_x + 12, badge_y + badge_size - 13), "ỨNG DỤNG LÂM SÀNG", fill="#FFFFFF", font=get_font(12, bold=True))

    draw = ImageDraw.Draw(canvas)

    # HEADER BRANDING
    logo = get_master_logo(target_h=42)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 45), (50 + card_w, 98)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 51), logo)

    badge_x = w - 300
    draw.rounded_rectangle([(badge_x, 45), (w - 50, 98)], radius=12, fill="#0284C7")
    draw_german_flag(draw, badge_x + 14, 62, 26, 18)
    draw.text((badge_x + 48, 62), "TIÊU CHUẨN ISO 13485", fill="#FFFFFF", font=get_font(13, bold=True))

    # BIG BOLD HOOK
    draw.text((50, 125), "TIÊU CHUẨN CHĂM SÓC VẾT THƯƠNG CHÂU ÂU", fill="#0369A1", font=get_font(17, bold=True))
    draw.text((50, 155), "PHÁ VỠ MÀNG BIOFILM", fill="#0F172A", font=get_font(48, bold=True))
    draw.text((50, 220), "0% ĐAU RÁT • NHANH LÀNH GẤP 2 LẦN", fill="#0284C7", font=get_font(28, bold=True))
    draw.text((50, 268), "Dung dịch xịt 75ml vô trùng • Kháng khuẩn vượt trội Betaine & Polyhexanide", fill="#475569", font=get_font(16, bold=False))

    # 2 Sleek Value Pills at Bottom
    pill1_x = 50
    pill2_x = draw_pill(draw, pill1_x, h - 90, "● Betaine 0.1% + PHMB 0.1%", get_font(15, bold=True), "#0F172A", "#FFFFFF", padding=(20, 10))
    draw_pill(draw, pill2_x + 10, h - 90, "● Không Độc Hại Mô Hạt Lành", get_font(15, bold=True), "#FFFFFF", "#0284C7", padding=(20, 10), border_color="#0284C7")

    out_file = OUTPUT_DIR / "poster_prontosan_wound_spray.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file

def main():
    import argparse
    global OUTPUT_DIR

    parser = argparse.ArgumentParser(description="Render Pro Meta Creatives - GlobalPharma")
    parser.add_argument("--type", choices=["plus", "nutricomp-plus", "renal", "nutricomp-renal", "combo", "nutricomp-combo", "nutricomp", "prontosan", "all"], default="all", help="Product creative type")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args, _ = parser.parse_known_args()

    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    t = args.type.lower()
    print(f"=== GLOBALPHARMA PRO CREATIVE ENGINE (TYPE: {t.upper()}) ===")
    results = []

    if t in ("plus", "nutricomp-plus"):
        results.append(render_pro_nutricomp_plus())
    elif t in ("renal", "nutricomp-renal"):
        results.append(render_pro_nutricomp_renal())
    elif t in ("combo", "nutricomp-combo"):
        results.append(render_pro_nutricomp_combo())
    elif t in ("nutricomp",):
        # Default nutricomp: render both Plus and Renal
        results.append(render_pro_nutricomp_plus())
        results.append(render_pro_nutricomp_renal())
    elif t == "prontosan":
        results.append(render_pro_prontosan())
    elif t == "all":
        results.append(render_pro_nutricomp_plus())
        results.append(render_pro_nutricomp_renal())
        results.append(render_pro_nutricomp_combo())
        results.append(render_pro_prontosan())

    # Sync to standard paths
    sync_targets = [Path("/app/workspace/output"), Path("/app/data/skills/tao-creative-fb/output")]
    for out_f in results:
        for st in sync_targets:
            if st.exists() and st != OUTPUT_DIR:
                try:
                    shutil.copy2(out_f, st / out_f.name)
                except Exception:
                    pass

    print(f"=== ĐÃ XUẤT THÀNH CÔNG {len(results)} POSTER CHUYÊN NGHIỆP ===")

if __name__ == "__main__":
    main()
