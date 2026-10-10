#!/usr/bin/env python3
"""
render_pro_creatives.py - Tạo 3 ấn phẩm quảng cáo Meta Ads đẳng cấp PRO, CHUYÊN NGHIỆP,
STOP-SCROLLING, HẠN CHẾ TEXT, TẬP TRUNG 1 THÔNG ĐIỆP CHÍNH THEO CHUẨN ADS-IMAGE-ARCHITECT.
Sử dụng hình nền studio/editorial cao cấp kết hợp 100% sản phẩm thật và logo chính thức.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent
REFS_DIR = REPO_ROOT / "skills" / "tao-creative-fb" / "assets" / "references"
OUTPUT_DIR = REPO_ROOT / "skills" / "tao-creative-fb" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BRAIN_DIR = Path("C:/Users/Surface/.gemini/antigravity/brain/552b4a88-d83e-4471-97a6-f32d72fa14d4")

def get_font(size: int, bold: bool = False):
    candidates = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibrib.ttf" if bold else "C:\\Windows\\Fonts\\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_master_logo(target_h: int = 38):
    p = REFS_DIR / "real_logo_globalpharma_banner.png"
    if not p.exists():
        p = REFS_DIR / "real_logo_globalpharma_master.png"
    if not p.exists():
        p = REPO_ROOT / "skills" / "tao-creative-fb" / "assets" / "globalpharma_logo.png"
    
    if p.exists():
        logo = Image.open(p).convert("RGBA")
        ratio = target_h / logo.height
        new_w = int(logo.width * ratio)
        return logo.resize((new_w, target_h), Image.Resampling.LANCZOS)
    return None

def draw_text_with_shadow(draw, pos, text, fill, font, shadow_color=(0, 0, 0, 180), offset=(1, 2)):
    x, y = pos
    ox, oy = offset
    draw.text((x + ox, y + oy), text, fill=shadow_color, font=font)
    draw.text((x, y), text, fill=fill, font=font)

def create_drop_shadow(alpha_mask, offset=(0, 20), blur_radius=25, shadow_alpha=120):
    """Tạo bóng đổ tự nhiên cho vật thể"""
    w, h = alpha_mask.size
    shadow = Image.new("RGBA", (w + abs(offset[0]) + blur_radius * 2, h + abs(offset[1]) + blur_radius * 2), (0, 0, 0, 0))
    # Place alpha mask in black
    black_obj = Image.new("RGBA", (w, h), (10, 15, 25, shadow_alpha))
    black_obj.putalpha(alpha_mask)
    
    paste_x = blur_radius + max(0, offset[0])
    paste_y = blur_radius + max(0, offset[1])
    shadow.paste(black_obj, (paste_x, paste_y), black_obj)
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
    return shadow, (paste_x, paste_y)

def draw_pill(draw, x, y, text, font, bg_color, text_color, padding=(16, 8), border_color=None):
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pw, ph = padding
    box = [(x, y), (x + tw + pw * 2, y + th + ph * 2)]
    radius = (th + ph * 2) // 2
    draw.rounded_rectangle(box, radius=radius, fill=bg_color, outline=border_color, width=1 if border_color else 0)
    # text vertical centering
    tx = x + pw - bbox[0]
    ty = y + ph - bbox[1]
    draw.text((tx, ty), text, fill=text_color, font=font)
    return x + tw + pw * 2 + 12  # return next x

# ==============================================================================
# 1. CREATIVE 1: NUTRICOMP RENAL (B.BRAUN CHLB ĐỨC) - LUXURY DARK TEAL STUDIO
# ==============================================================================
def render_pro_nutricomp():
    w, h = 1080, 1080
    bg_path = REFS_DIR / "bg_luxury_teal_podium.jpg"
    if not bg_path.exists():
        bg_path = BRAIN_DIR / "luxury_teal_podium_1791617178766.jpg"
    if bg_path.exists():
        canvas = Image.open(bg_path).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (w, h), (4, 47, 46, 255))
        
    # Darken top slightly for maximum text contrast
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(400):
        alpha = int(140 * (1 - y / 400))
        draw_ov.line([(0, y), (w, y)], fill=(3, 20, 24, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    
    # PRODUCT PACKSHOT: 12-Bottle Combo Box on Marble Podium
    prod_path = REFS_DIR / "cut_nutricomp_box.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "real_nutricomp_combo12_giftbox.png"
        
    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_w = 780
        ratio = target_w / prod.width
        target_h = int(prod.height * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Soft 3D cast shadow onto marble
        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(0, 25), blur_radius=20, shadow_alpha=160)
        
        pos_x = (w - target_w) // 2
        pos_y = 470  # Sits right atop marble pedestal
        
        canvas.paste(shadow, (pos_x - spx, pos_y - spy), shadow)
        canvas.paste(prod_resized, (pos_x, pos_y), prod_resized)

    draw = ImageDraw.Draw(canvas)
    
    # HEADER BRANDING
    # Logo GlobalPharma master in clean translucent glass card
    logo = get_master_logo(target_h=36)
    if logo:
        card_w = logo.width + 36
        card_h = 52
        draw.rounded_rectangle([(50, 42), (50 + card_w, 42 + card_h)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 50), logo)
    
    # Partner Badge top right
    draw_pill(draw, w - 280, 42, "CHLB ĐỨC • B.BRAUN", get_font(15, bold=True), (15, 23, 42, 220), "#F8FAFC", padding=(18, 10), border_color="#38BDF8")
    
    # HOOK & MAIN MESSAGE (TẬP TRUNG, ÍT CHỮ, BẮT MẮT TỐI ĐA)
    # Tagline nhỏ
    draw_text_with_shadow(draw, (50, 130), "DINH DƯỠNG Y HỌC LÂM SÀNG", "#38BDF8", get_font(18, bold=True), shadow_color=(0, 0, 0, 200))
    
    # Giant Punchy Hook
    draw_text_with_shadow(draw, (50, 160), "2.0 KCAL / ML", "#FFFFFF", get_font(52, bold=True), shadow_color=(0, 0, 0, 240))
    draw_text_with_shadow(draw, (50, 228), "HỒI PHỤC THỂ TRẠNG SUY KIỆT", "#F1F5F9", get_font(34, bold=True), shadow_color=(0, 0, 0, 220))
    
    # Sub-hook (1 dòng tinh tế)
    draw_text_with_shadow(draw, (50, 280), "Công thức chuyên biệt cho người bệnh thận • Kiểm soát nghiêm ngặt Điện giải", "#94A3B8", get_font(17, bold=False), shadow_color=(0, 0, 0, 200))
    
    # 2 Glassmorphism Feature Pills at bottom
    pill1_x = 50
    pill2_x = draw_pill(draw, pill1_x, h - 90, "● 12 Chai 200ml Tiệt Trùng Nguyên Seal", get_font(15, bold=True), (15, 23, 42, 210), "#FFFFFF", padding=(20, 10), border_color="#0D9488")
    draw_pill(draw, pill2_x + 10, h - 90, "● Đạm Chất Lượng Cao 14g/chai", get_font(15, bold=True), (15, 23, 42, 210), "#38BDF8", padding=(20, 10), border_color="#0D9488")

    out_file = OUTPUT_DIR / "poster_nutricomp_drink_plus.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"[PRO SUCCESS] Nutricomp Pro Creative: {out_file}")
    return out_file

# ==============================================================================
# 2. CREATIVE 2: PRONTOSAN WOUND SPRAY (B.BRAUN CHLB ĐỨC) - CLINICAL WATER WAVE
# ==============================================================================
def render_pro_prontosan():
    w, h = 1080, 1080
    bg_path = REFS_DIR / "bg_prontosan_clinical.jpg"
    if not bg_path.exists():
        bg_path = BRAIN_DIR / "prontosan_clinical_bg_1791617199866.jpg"
    if bg_path.exists():
        canvas = Image.open(bg_path).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (w, h), (240, 249, 255, 255))
        
    # Darken/gradient overlay at top for pristine white-medical readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(380):
        alpha = int(180 * (1 - y / 380))
        draw_ov.line([(0, y), (w, y)], fill=(255, 255, 255, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    
    # PRODUCT PACKSHOT: Authentic Prontosan Bottle standing on Pedestal
    prod_path = REFS_DIR / "cut_prontosan_bottle.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "real_prontosan_wound_spray_bottle.webp"
        
    if prod_path.exists():
        prod = Image.open(prod_path).convert("RGBA")
        target_h = 580
        ratio = target_h / prod.height
        target_w = int(prod.width * ratio)
        prod_resized = prod.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Soft shadow
        alpha = prod_resized.split()[3]
        shadow, (spx, spy) = create_drop_shadow(alpha, offset=(5, 18), blur_radius=15, shadow_alpha=120)
        
        pos_x = (w - target_w) // 2 + 30
        pos_y = 390  # Sits right on the marble pedestal
        
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
        
        # White border behind
        border_box = [(badge_x - 4, badge_y - 4), (badge_x + badge_size + 4, badge_y + badge_size + 4)]
        draw_border = ImageDraw.Draw(canvas)
        draw_border.ellipse(border_box, fill="#0284C7")
        canvas.paste(act_resized, (badge_x, badge_y), mask)
        
        # Small tag under badge
        draw_border.rounded_rectangle([(badge_x - 10, badge_y + badge_size - 20), (badge_x + badge_size + 10, badge_y + badge_size + 14)], radius=8, fill="#0F172A")
        draw_border.text((badge_x + 12, badge_y + badge_size - 13), "ỨNG DỤNG LÂM SÀNG", fill="#FFFFFF", font=get_font(12, bold=True))

    draw = ImageDraw.Draw(canvas)
    
    # HEADER BRANDING
    logo = get_master_logo(target_h=36)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 42), (50 + card_w, 94)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 50), logo)
        
    draw_pill(draw, w - 290, 42, "CHỨNG NHẬN ISO 13485", get_font(14, bold=True), "#0284C7", "#FFFFFF", padding=(18, 10))
    
    # BIG BOLD HOOK (TẬP TRUNG THÔNG ĐIỆP CHÍNH)
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
    print(f"[PRO SUCCESS] Prontosan Pro Creative: {out_file}")
    return out_file

# ==============================================================================
# 3. CREATIVE 3: DƯỢC SĨ SOLOPRENEUR (EDITORIAL / FORBES AESTHETIC)
# ==============================================================================
def render_pro_affiliate():
    w, h = 1080, 1080
    bg_path = REFS_DIR / "bg_pharmacist_editorial.jpg"
    if not bg_path.exists():
        bg_path = BRAIN_DIR / "pharmacist_editorial_1791617224959.jpg"
    if bg_path.exists():
        canvas = Image.open(bg_path).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        
    # Darker gradient banner across top for editorial branding and readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for y in range(380):
        alpha = int(220 * (1 - (y / 380) ** 1.3))
        draw_ov.line([(0, y), (w, y)], fill=(8, 16, 28, alpha))
    # Bottom gradient for bottom pills
    for y in range(h - 180, h):
        alpha = int(200 * ((y - (h - 180)) / 180))
        draw_ov.line([(0, y), (w, y)], fill=(5, 12, 22, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    
    draw = ImageDraw.Draw(canvas)
    
    # HEADER BRANDING
    logo = get_master_logo(target_h=36)
    if logo:
        card_w = logo.width + 36
        draw.rounded_rectangle([(50, 42), (50 + card_w, 94)], radius=12, fill=(255, 255, 255, 245))
        canvas.paste(logo, (68, 50), logo)
        
    draw_pill(draw, w - 280, 42, "HEALTHCARE SOLOPRENEUR", get_font(13, bold=True), (15, 23, 42, 220), "#38BDF8", padding=(18, 10), border_color="#0284C7")
    
    # BIG EDITORIAL HOOK
    draw_text_with_shadow(draw, (50, 125), "MÔ HÌNH HỢP TÁC DÀNH CHO DƯỢC SĨ & CHUYÊN GIA Y TẾ", "#38BDF8", get_font(16, bold=True), shadow_color=(0, 0, 0, 220))
    draw_text_with_shadow(draw, (50, 155), "DƯỢC SĨ SOLOPRENEUR", "#FFFFFF", get_font(48, bold=True), shadow_color=(0, 0, 0, 250))
    draw_text_with_shadow(draw, (50, 220), "XÂY THU NHẬP THỨ 2 TỪ UY TÍN Y KHOA", "#F1F5F9", get_font(28, bold=True), shadow_color=(0, 0, 0, 240))
    draw_text_with_shadow(draw, (50, 266), "Phân phối trực tiếp Dinh dưỡng y học & Thiết bị y tế B.Braun CHLB Đức", "#E2E8F0", get_font(17, bold=False), shadow_color=(0, 0, 0, 220))
    
    # 2 Sleek Value Pills at Bottom
    pill1_x = 50
    pill2_x = draw_pill(draw, pill1_x, h - 85, "● 0 Vốn Ôm Hàng • 0 Áp Doanh Số", get_font(15, bold=True), (15, 23, 42, 230), "#FFFFFF", padding=(20, 10), border_color="#38BDF8")
    draw_pill(draw, pill2_x + 10, h - 85, "● 100% Sản Phẩm Y Khoa Chính Hãng", get_font(15, bold=True), (15, 23, 42, 230), "#38BDF8", padding=(20, 10), border_color="#0D9488")

    out_file = OUTPUT_DIR / "poster_affiliate_partner.png"
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"[PRO SUCCESS] Affiliate Pro Creative: {out_file}")
    return out_file

def main():
    print("=== TẠO 3 CREATIVE ĐẲNG CẤP PRO, CHUYÊN NGHIỆP, STOP-SCROLLING ===")
    render_pro_nutricomp()
    render_pro_prontosan()
    render_pro_affiliate()
    print("=== HOÀN TẤT XUẤT 3 ẢNH PRO ===")

if __name__ == "__main__":
    main()
