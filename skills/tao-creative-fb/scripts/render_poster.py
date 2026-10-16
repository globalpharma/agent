#!/usr/bin/env python3
"""
render_poster.py - Master Template Engine cho ấn phẩm Facebook Ads & Poster y khoa
dành riêng cho GlobalPharma & B.Braun CHLB Đức.

Bám sát 100% thiết kế chuẩn tham chiếu (Master Reference Templates) của Ban Lãnh đạo:
1. Nutricomp Renal: Sử dụng phôi Master Renal (template_nutricomp_renal_master.png) -
   Gia đình chăm sóc người bệnh thận, chai Renal nắp tím trên nền sữa vani,
   4 icon thông số lâm sàng, nút CTA và 3 huy hiệu uy tín chân trang.
2. Nutricomp Plus: Sử dụng phôi Master Plus (template_nutricomp_plus_master.png) -
   Bục podium teal sang trọng, lốc 4 chai + 1 chai lẻ, ribbon Sữa dinh dưỡng y học Đức,
   300Kcal/200ml, Mua 1 lốc 4 tặng 1 chai lẻ.
3. Prontosan Spray: Sử dụng phôi Master Prontosan (template_prontosan_lifestyle_master.png) -
   Bối cảnh xịt trực tiếp vết thương trên cẳng tay, chữ 2 tông màu y khoa sắc nét.
4. Nutricomp Combo 12 chai: Hộp quà tiệt trùng B.Braun 12 chai.
"""

import sys
import os
import time
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

# Resolve bundled fonts directory
candidate_fonts = [
    SKILL_DIR / "assets" / "fonts",
    Path("/app/data/skills/tao-creative-fb/assets/fonts"),
    Path("/app/workspace/skills/tao-creative-fb/assets/fonts"),
    SKILL_DIR.parent.parent / "skills" / "tao-creative-fb" / "assets" / "fonts",
]
FONTS_DIR = SKILL_DIR / "assets" / "fonts"
for c in candidate_fonts:
    if c.exists():
        FONTS_DIR = c
        break

# Output directories
OUTPUT_DIR = Path("/app/workspace/output") if Path("/app/workspace").exists() else (SKILL_DIR / "output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_font(size: int, bold: bool = False):
    font_file = "segoeuib.ttf" if bold else "segoeui.ttf"
    candidates = [
        str(FONTS_DIR / font_file),
        f"C:\\Windows\\Fonts\\{font_file}",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
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


def wrap_text(text: str, font, max_width: int):
    """Chia dòng thông minh để vừa vặn chiều rộng đồ họa"""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = font.getbbox(test_line)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def clean_quote_str(s: str) -> str:
    if not s:
        return ""
    s = s.strip().strip('"').strip("'").strip("“").strip("”").strip("‘").strip("’").strip()
    return s


# ==============================================================================
# ==============================================================================
# 1. NUTRICOMP DRINK RENAL (CHUYÊN BIỆT CHO NGƯỜI BỆNH THẬN / LỌC MÁU)
# ==============================================================================
def render_pro_nutricomp_renal(headline: str = None, subline: str = None, output_path: Path = None):
    w, h = 1024, 1024
    canvas = Image.new("RGBA", (w, h), (246, 250, 248, 255))
    draw = ImageDraw.Draw(canvas)

    # Top brand header
    hdr_path = REFS_DIR / "brand_header_master.png"
    if hdr_path.exists():
        hdr = Image.open(hdr_path).convert("RGBA")
        canvas.paste(hdr, (48, 48), hdr)

    # Bottle cut on right: 1 chai Nutricomp Renal nắp tím chuẩn B.Braun
    bot_path = REFS_DIR / "cut_nutricomp_single_bottle.png"
    if bot_path.exists():
        bot = Image.open(bot_path).convert("RGBA")
        target_h = int(h * 0.68)
        target_w = int(bot.width * (target_h / bot.height))
        bot_scaled = bot.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Soft contact shadow
        shadow = Image.new("RGBA", (target_w + 60, 40), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.ellipse([10, 5, target_w + 50, 35], fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        
        bot_x = w - target_w - 70
        bot_y = h - target_h - 100
        canvas.paste(shadow, (bot_x - 30, bot_y + target_h - 25), shadow)
        canvas.paste(bot_scaled, (bot_x, bot_y), bot_scaled)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        dynamic_renal_headlines = [
            "BẢO TỒN CHỨC NĂNG THẬN",
            "KIỂM SOÁT ĐẠM & ĐIỆN GIẢI",
            "DINH DƯỠNG Y HỌC CHUYÊN BIỆT",
            "NĂNG LƯỢNG CAO 400 KCAL",
            "GIẢI PHÁP DINH DƯỠNG THẬN",
        ]
        import datetime
        hl = dynamic_renal_headlines[datetime.datetime.now().day % len(dynamic_renal_headlines)]

    hl_upper = hl.upper()
    font_size = 34 if len(hl_upper) <= 32 else (28 if len(hl_upper) <= 60 else 24)
    f_hl = get_font(font_size, bold=True)
    lines = wrap_text(hl_upper, f_hl, max_width=510)
    y_text = 200
    for line in lines[:3]:
        draw.text((48, y_text), line, fill="#044E3F", font=f_hl)
        y_text += font_size + 12

    # Subline
    sub_text = sl if sl else "Nutricomp Drink Renal • 400 kcal/200ml"
    f_sl = get_font(20, bold=False)
    draw.text((48, y_text + 10), sub_text, fill="#065F46", font=f_sl)
    y_text += 46

    # 3 Badges
    badges = ["2,0 kcal/ml", "Ít Natri - Kali - Photpho", "Hương vani thơm ngon"]
    f_bg = get_font(16, bold=True)
    y_badge = y_text + 15
    for b in badges:
        try:
            bbox = f_bg.getbbox(b)
            bw = bbox[2] - bbox[0] + 28
        except Exception:
            bw = len(b) * 10 + 28
        bh = 36
        draw.rounded_rectangle([48, y_badge, 48 + bw, y_badge + bh], radius=18, fill=(230, 243, 238, 255), outline=(180, 215, 202, 255), width=1)
        draw.text((48 + 14, y_badge + 7), b, fill="#044E3F", font=f_bg)
        y_badge += 48

    # CTA Button
    y_cta = y_badge + 25
    cta_text = "NHẮN TIN NHẬN TƯ VẤN"
    f_cta = get_font(18, bold=True)
    try:
        cbox = f_cta.getbbox(cta_text)
        cw = cbox[2] - cbox[0] + 48
    except Exception:
        cw = 260
    ch = 48
    draw.rounded_rectangle([48, y_cta, 48 + cw, y_cta + ch], radius=24, fill="#059669")
    draw.text((48 + 24, y_cta + 12), cta_text, fill="#FFFFFF", font=f_cta)

    # Disclaimer footer
    f_disc = get_font(13, bold=False)
    draw.text((48, h - 55), "Sản phẩm dinh dưỡng y học. Không phải là thuốc và không thay thế thuốc chữa bệnh.", fill="#64748B", font=f_disc)

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_renal_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 2. NUTRICOMP DRINK PLUS (CAO NĂNG LƯỢNG / PHỤC HỒI SAU PHẪU THUẬT)
# ==============================================================================
def render_pro_nutricomp_plus(headline: str = None, subline: str = None, output_path: Path = None):
    w, h = 1024, 1024
    canvas = Image.new("RGBA", (w, h), (255, 250, 246, 255))
    draw = ImageDraw.Draw(canvas)

    # Top brand header
    hdr_path = REFS_DIR / "brand_header_master.png"
    if hdr_path.exists():
        hdr = Image.open(hdr_path).convert("RGBA")
        canvas.paste(hdr, (48, 48), hdr)

    # Bottle cut on right: 1 chai Nutricomp Plus nắp tím kèm dải màu cam/hồng
    bot_path = REFS_DIR / "cut_nutricomp_plus_bottle.png"
    if not bot_path.exists():
        bot_path = REFS_DIR / "crop_nutricomp_bottle.png"
    if bot_path.exists():
        bot = Image.open(bot_path).convert("RGBA")
        target_h = int(h * 0.68)
        target_w = int(bot.width * (target_h / bot.height))
        bot_scaled = bot.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Soft contact shadow
        shadow = Image.new("RGBA", (target_w + 60, 40), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.ellipse([10, 5, target_w + 50, 35], fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        
        bot_x = w - target_w - 70
        bot_y = h - target_h - 100
        canvas.paste(shadow, (bot_x - 30, bot_y + target_h - 25), shadow)
        canvas.paste(bot_scaled, (bot_x, bot_y), bot_scaled)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        dynamic_plus_headlines = [
            "BÙ ĐẮP NĂNG LƯỢNG KỊP THỜI",
            "PHỤC HỒI THỂ TRẠNG VƯỢNG VÀNG",
            "300 KCAL CHỈ TRONG 200ML",
            "DINH DƯỠNG CAO NĂNG LƯỢNG",
            "GIẢI PHÁP HỒI PHỤC TOÀN DIỆN",
        ]
        import datetime
        hl = dynamic_plus_headlines[datetime.datetime.now().day % len(dynamic_plus_headlines)]

    hl_upper = hl.upper()
    font_size = 34 if len(hl_upper) <= 32 else (28 if len(hl_upper) <= 60 else 24)
    f_hl = get_font(font_size, bold=True)
    lines = wrap_text(hl_upper, f_hl, max_width=510)
    y_text = 200
    for line in lines[:3]:
        draw.text((48, y_text), line, fill="#0F766E", font=f_hl)
        y_text += font_size + 12

    # Subline
    sub_text = sl if sl else "Nutricomp Drink Plus • 300 kcal/200ml"
    f_sl = get_font(20, bold=False)
    draw.text((48, y_text + 10), sub_text, fill="#C2410C", font=f_sl)
    y_text += 46

    # 3 Badges
    badges = ["1,5 kcal/ml", "Dạng uống tiện dụng", "Hỗ trợ phục hồi nhanh"]
    f_bg = get_font(16, bold=True)
    y_badge = y_text + 15
    for b in badges:
        try:
            bbox = f_bg.getbbox(b)
            bw = bbox[2] - bbox[0] + 28
        except Exception:
            bw = len(b) * 10 + 28
        bh = 36
        draw.rounded_rectangle([48, y_badge, 48 + bw, y_badge + bh], radius=18, fill=(255, 241, 230, 255), outline=(254, 215, 170, 255), width=1)
        draw.text((48 + 14, y_badge + 7), b, fill="#9A3412", font=f_bg)
        y_badge += 48

    # CTA Button
    y_cta = y_badge + 25
    cta_text = "NHẮN TIN NHẬN TƯ VẤN"
    f_cta = get_font(18, bold=True)
    try:
        cbox = f_cta.getbbox(cta_text)
        cw = cbox[2] - cbox[0] + 48
    except Exception:
        cw = 260
    ch = 48
    draw.rounded_rectangle([48, y_cta, 48 + cw, y_cta + ch], radius=24, fill="#059669")
    draw.text((48 + 24, y_cta + 12), cta_text, fill="#FFFFFF", font=f_cta)

    # Disclaimer footer
    f_disc = get_font(13, bold=False)
    draw.text((48, h - 55), "Sản phẩm dinh dưỡng y học. Không phải là thuốc và không thay thế thuốc chữa bệnh.", fill="#64748B", font=f_disc)

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_plus_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 3. PRONTOSAN WOUND SPRAY (LÀM SẠCH VẾT THƯƠNG NGOÀI DA / KHÔNG MẠN TÍNH)
# ==============================================================================
def render_pro_prontosan(headline: str = None, subline: str = None, output_path: Path = None):
    w, h = 1024, 1024
    canvas = Image.new("RGBA", (w, h), (245, 251, 253, 255))
    draw = ImageDraw.Draw(canvas)

    # Top brand header
    hdr_path = REFS_DIR / "brand_header_master.png"
    if hdr_path.exists():
        hdr = Image.open(hdr_path).convert("RGBA")
        canvas.paste(hdr, (48, 48), hdr)

    # Bottle cut on right: 1 chai Prontosan Spray
    bot_path = REFS_DIR / "cut_prontosan_bottle.png"
    if bot_path.exists():
        bot = Image.open(bot_path).convert("RGBA")
        target_h = int(h * 0.70)
        target_w = int(bot.width * (target_h / bot.height))
        bot_scaled = bot.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Soft contact shadow
        shadow = Image.new("RGBA", (target_w + 60, 40), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.ellipse([10, 5, target_w + 50, 35], fill=(0, 0, 0, 45))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        
        bot_x = w - target_w - 70
        bot_y = h - target_h - 90
        canvas.paste(shadow, (bot_x - 30, bot_y + target_h - 25), shadow)
        canvas.paste(bot_scaled, (bot_x, bot_y), bot_scaled)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        dynamic_prontosan_headlines = [
            "LÀM SẠCH VẾT THƯƠNG ĐÚNG CÁCH",
            "HỖ TRỢ XỬ LÝ MÀNG BIOFILM",
            "GIẢI PHÁP CHĂM SÓC VẾT THƯƠNG",
            "LÀM SẠCH NHẸ NHÀNG KHÔNG XÓT",
            "BẢO VỆ NỀN VẾT THƯƠNG TỐI ƯU",
        ]
        import datetime
        hl = dynamic_prontosan_headlines[datetime.datetime.now().day % len(dynamic_prontosan_headlines)]

    hl_upper = hl.upper()
    font_size = 34 if len(hl_upper) <= 32 else (28 if len(hl_upper) <= 60 else 24)
    f_hl = get_font(font_size, bold=True)
    lines = wrap_text(hl_upper, f_hl, max_width=510)
    y_text = 200
    for line in lines[:3]:
        draw.text((48, y_text), line, fill="#0E7490", font=f_hl)
        y_text += font_size + 12

    # Subline
    sub_text = sl if sl else "Rửa, làm ẩm và hỗ trợ xử lý Biofilm"
    f_sl = get_font(20, bold=False)
    draw.text((48, y_text + 10), sub_text, fill="#0369A1", font=f_sl)
    y_text += 46

    # 3 Badges
    badges = ["0,1% PHMB & 0,1% Betaine", "Làm sạch không chà xát mạnh", "Chăm sóc da và vết khâu hở"]
    f_bg = get_font(16, bold=True)
    y_badge = y_text + 15
    for b in badges:
        try:
            bbox = f_bg.getbbox(b)
            bw = bbox[2] - bbox[0] + 28
        except Exception:
            bw = len(b) * 10 + 28
        bh = 36
        draw.rounded_rectangle([48, y_badge, 48 + bw, y_badge + bh], radius=18, fill=(224, 242, 254, 255), outline=(186, 230, 253, 255), width=1)
        draw.text((48 + 14, y_badge + 7), b, fill="#0369A1", font=f_bg)
        y_badge += 48

    # CTA Button
    y_cta = y_badge + 25
    cta_text = "NHẮN TIN NHẬN TƯ VẤN"
    f_cta = get_font(18, bold=True)
    try:
        cbox = f_cta.getbbox(cta_text)
        cw = cbox[2] - cbox[0] + 48
    except Exception:
        cw = 260
    ch = 48
    draw.rounded_rectangle([48, y_cta, 48 + cw, y_cta + ch], radius=24, fill="#059669")
    draw.text((48 + 24, y_cta + 12), cta_text, fill="#FFFFFF", font=f_cta)

    # Disclaimer footer
    f_disc = get_font(13, bold=False)
    draw.text((48, h - 55), "Dung dịch chăm sóc vết thương ngoài da. Đọc kỹ hướng dẫn sử dụng trước khi dùng.", fill="#64748B", font=f_disc)

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_prontosan_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 4. NUTRICOMP COMBO 12 CHAI
# ==============================================================================
def render_pro_nutricomp_combo(headline: str = None, subline: str = None, output_path: Path = None):
    w, h = 1024, 1024
    canvas = Image.new("RGBA", (w, h), (254, 249, 245, 255))
    draw = ImageDraw.Draw(canvas)

    hdr_path = REFS_DIR / "brand_header_master.png"
    if hdr_path.exists():
        hdr = Image.open(hdr_path).convert("RGBA")
        canvas.paste(hdr, (48, 48), hdr)

    box_path = REFS_DIR / "cut_nutricomp_box.png"
    if not box_path.exists():
        box_path = REFS_DIR / "real_nutricomp_combo12_giftbox.png"
    if box_path.exists():
        box = Image.open(box_path).convert("RGBA")
        target_h = int(h * 0.65)
        target_w = int(box.width * (target_h / box.height))
        box_scaled = box.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        shadow = Image.new("RGBA", (target_w + 60, 40), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.ellipse([10, 5, target_w + 50, 35], fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        
        box_x = w - target_w - 60
        box_y = h - target_h - 100
        canvas.paste(shadow, (box_x - 30, box_y + target_h - 25), shadow)
        canvas.paste(box_scaled, (box_x, box_y), box_scaled)

    hl = clean_quote_str(headline) if headline else "COMBO 12 CHAI TIỆT TRÙNG NGUYÊN SEAL"
    sl = clean_quote_str(subline) if subline else "Giải pháp dinh dưỡng tiết kiệm cho liệu trình phục hồi toàn diện"

    hl_upper = hl.upper()
    font_size = 32 if len(hl_upper) <= 35 else (26 if len(hl_upper) <= 65 else 22)
    f_hl = get_font(font_size, bold=True)
    lines = wrap_text(hl_upper, f_hl, max_width=510)
    y_text = 200
    for line in lines[:3]:
        draw.text((48, y_text), line, fill="#9A3412", font=f_hl)
        y_text += font_size + 12

    f_sl = get_font(18, bold=False)
    draw.text((48, y_text + 10), sl, fill="#B45309", font=f_sl)
    y_text += 46

    badges = ["12 chai x 200ml", "Tiết kiệm chi phí", "Đóng gói quà tặng trang nhã"]
    f_bg = get_font(16, bold=True)
    y_badge = y_text + 15
    for b in badges:
        try:
            bbox = f_bg.getbbox(b)
            bw = bbox[2] - bbox[0] + 28
        except Exception:
            bw = len(b) * 10 + 28
        bh = 36
        draw.rounded_rectangle([48, y_badge, 48 + bw, y_badge + bh], radius=18, fill=(254, 243, 199, 255), outline=(252, 211, 77, 255), width=1)
        draw.text((48 + 14, y_badge + 7), b, fill="#92400E", font=f_bg)
        y_badge += 48

    y_cta = y_badge + 25
    cta_text = "NHẮN TIN NHẬN TƯ VẤN"
    f_cta = get_font(18, bold=True)
    try:
        cbox = f_cta.getbbox(cta_text)
        cw = cbox[2] - cbox[0] + 48
    except Exception:
        cw = 260
    ch = 48
    draw.rounded_rectangle([48, y_cta, 48 + cw, y_cta + ch], radius=24, fill="#059669")
    draw.text((48 + 24, y_cta + 12), cta_text, fill="#FFFFFF", font=f_cta)

    f_disc = get_font(13, bold=False)
    draw.text((48, h - 55), "Sản phẩm dinh dưỡng y học. Không phải là thuốc và không thay thế thuốc chữa bệnh.", fill="#64748B", font=f_disc)

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_combo_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


def main():
    import argparse
    global OUTPUT_DIR

    parser = argparse.ArgumentParser(description="Render Master Reference Creatives - GlobalPharma")
    parser.add_argument("--type", choices=["plus", "nutricomp-plus", "renal", "nutricomp-renal", "combo", "nutricomp-combo", "nutricomp", "prontosan", "all"], default="all", help="Product creative type")
    parser.add_argument("--headline", default=None, help="Dynamic headline text from content")
    parser.add_argument("--subline", default=None, help="Dynamic subline / subtitle text from content")
    parser.add_argument("--output", default=None, help="Exact output file path")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args, _ = parser.parse_known_args()

    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    out_p = Path(args.output) if args.output else None

    t = args.type.lower()
    results = []

    if t in ("plus", "nutricomp-plus"):
        results.append(render_pro_nutricomp_plus(headline=args.headline, subline=args.subline, output_path=out_p))
    elif t in ("renal", "nutricomp-renal"):
        results.append(render_pro_nutricomp_renal(headline=args.headline, subline=args.subline, output_path=out_p))
    elif t in ("combo", "nutricomp-combo"):
        results.append(render_pro_nutricomp_combo(headline=args.headline, subline=args.subline, output_path=out_p))
    elif t in ("nutricomp",):
        results.append(render_pro_nutricomp_plus(headline=args.headline, subline=args.subline, output_path=out_p))
        results.append(render_pro_nutricomp_renal(headline=args.headline, subline=args.subline, output_path=out_p))
    elif t == "prontosan":
        results.append(render_pro_prontosan(headline=args.headline, subline=args.subline, output_path=out_p))
    elif t == "all":
        results.append(render_pro_nutricomp_plus(headline=args.headline, subline=args.subline, output_path=out_p))
        results.append(render_pro_nutricomp_renal(headline=args.headline, subline=args.subline, output_path=out_p))
        results.append(render_pro_nutricomp_combo(headline=args.headline, subline=args.subline, output_path=out_p))
        results.append(render_pro_prontosan(headline=args.headline, subline=args.subline, output_path=out_p))

    sync_targets = [Path("/app/workspace/output"), Path("/app/data/skills/tao-creative-fb/output")]
    for out_f in results:
        for st in sync_targets:
            if st.exists() and st != out_f.parent:
                try:
                    shutil.copy2(out_f, st / out_f.name)
                except Exception:
                    pass

    print(f"=== ĐÃ XUẤT THÀNH CÔNG {len(results)} POSTER CHUẨN THAM CHIẾU ===")


if __name__ == "__main__":
    main()
