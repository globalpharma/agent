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
# 1. NUTRICOMP DRINK RENAL (MASTER TEMPLATE - DÀNH CHO NGƯỜI BỆNH THẬN)
# ==============================================================================
def render_pro_nutricomp_renal(headline: str = None, subline: str = None, output_path: Path = None):
    master_path = REFS_DIR / "template_nutricomp_renal_master.png"
    fallback_path = REFS_DIR / "style_nutricomp_renal_master.jpg"

    if master_path.exists():
        canvas = Image.open(master_path).convert("RGBA")
    elif fallback_path.exists():
        canvas = Image.open(fallback_path).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (1024, 1024), (244, 244, 244, 255))

    draw = ImageDraw.Draw(canvas)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        # Default Master Reference Typography
        f_hl = get_font(44, bold=True)
        f_sl = get_font(21, bold=True)
        draw.text((32, 142), "NUTRICOMP RENAL", fill="#044E3F", font=f_hl)
        draw.text((35, 212), "— DINH DƯỠNG CHUYÊN BIỆT —", fill="#065F46", font=f_sl)
    else:
        hl_upper = hl.upper()
        # Try single line or 2-line wrap within max_width = 455px
        font_size = 32 if len(hl_upper) <= 28 else (26 if len(hl_upper) <= 52 else 22)
        f_hl = get_font(font_size, bold=True)
        lines = wrap_text(hl_upper, f_hl, max_width=455)

        if len(lines) == 1:
            draw.text((32, 148), lines[0], fill="#044E3F", font=f_hl)
            sub_text = sl.upper() if sl else "DINH DƯỠNG Y HỌC CHUYÊN BIỆT"
            f_sl = get_font(17, bold=True)
            sl_lines = wrap_text(f"— {sub_text} —", f_sl, max_width=455)
            draw.text((32, 205), sl_lines[0], fill="#065F46", font=f_sl)
        else:
            y_cur = 138
            for line in lines[:2]:
                draw.text((32, y_cur), line, fill="#044E3F", font=f_hl)
                y_cur += font_size + 7
            sub_text = sl if sl else "Dinh dưỡng chuyên biệt kiểm soát điện giải"
            f_sl = get_font(15, bold=True)
            sl_lines = wrap_text(f"— {sub_text} —", f_sl, max_width=455)
            if y_cur <= 232 and sl_lines:
                draw.text((32, y_cur + 2), sl_lines[0], fill="#065F46", font=f_sl)

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_renal_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 2. NUTRICOMP DRINK PLUS (MASTER TEMPLATE - CAO NĂNG LƯỢNG / PHỤC HỒI)
# ==============================================================================
def render_pro_nutricomp_plus(headline: str = None, subline: str = None, output_path: Path = None):
    master_path = REFS_DIR / "template_nutricomp_plus_master.png"
    fallback_path = REFS_DIR / "style_nutricomp_plus_master_2.jpg"

    if master_path.exists():
        canvas = Image.open(master_path).convert("RGBA")
    elif fallback_path.exists():
        canvas = Image.open(fallback_path).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (1024, 1024), (231, 244, 237, 255))

    draw = ImageDraw.Draw(canvas)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        f_hl = get_font(38, bold=True)
        f_sl = get_font(22, bold=True)
        draw.text((35, 165), "SỰ THẬT VỀ CHĂM NGƯỜI BỆNH", fill="#0F766E", font=f_hl)
        draw.text((35, 225), "Càng ép ăn nhiều, bạn và người thân", fill="#334155", font=f_sl)
        draw.text((35, 260), "càng kiệt sức. Hãy làm ngược lại !", fill="#334155", font=f_sl)
    else:
        hl_upper = hl.upper()
        font_size = 34 if len(hl_upper) <= 32 else (28 if len(hl_upper) <= 62 else 24)
        f_hl = get_font(font_size, bold=True)
        lines = wrap_text(hl_upper, f_hl, max_width=630)

        y_cur = 160
        for line in lines[:2]:
            draw.text((35, y_cur), line, fill="#0F766E", font=f_hl)
            y_cur += font_size + 8

        sub_text = sl if sl else "Bổ sung dinh dưỡng cao năng lượng 300Kcal/200ml giúp phục hồi thể trạng nhanh chóng!"
        f_sl = get_font(19, bold=True)
        sl_lines = wrap_text(sub_text, f_sl, max_width=610)
        y_cur += 6
        for line in sl_lines[:2]:
            if y_cur <= 310:
                draw.text((35, y_cur), line, fill="#334155", font=f_sl)
                y_cur += 26

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_plus_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 3. PRONTOSAN WOUND SPRAY (MASTER TEMPLATE - LÀM SẠCH VẾT THƯƠNG)
# ==============================================================================
def render_pro_prontosan(headline: str = None, subline: str = None, output_path: Path = None):
    master_path = REFS_DIR / "template_prontosan_lifestyle_master.png"
    fallback_path = REFS_DIR / "style_prontosan_spray_lifestyle.png"

    if master_path.exists():
        canvas = Image.open(master_path).convert("RGBA")
    elif fallback_path.exists():
        canvas = Image.open(fallback_path).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (819, 1024), (249, 249, 249, 255))

    draw = ImageDraw.Draw(canvas)

    hl = clean_quote_str(headline) if headline else ""
    sl = clean_quote_str(subline) if subline else ""

    if not hl:
        draw.text((38, 110), "VẾT THƯƠNG NHỎ,", fill="#1E293B", font=get_font(40, bold=True))
        draw.text((38, 168), "NHƯNG BẠN", fill="#0D9488", font=get_font(44, bold=True))
        draw.text((38, 226), "ĐÃ LÀM SẠCH", fill="#0D9488", font=get_font(44, bold=True))
        draw.text((38, 284), "ĐÚNG CÁCH?", fill="#0D9488", font=get_font(44, bold=True))
    else:
        hl_upper = hl.upper()
        font_size = 38 if len(hl_upper) <= 45 else (32 if len(hl_upper) <= 70 else 28)
        f_hl = get_font(font_size, bold=True)
        lines = wrap_text(hl_upper, f_hl, max_width=480)

        y_cur = 112
        for idx, line in enumerate(lines[:4]):
            color = "#1E293B" if idx == 0 else "#0D9488"
            draw.text((38, y_cur), line, fill=color, font=f_hl)
            y_cur += font_size + 12

    sub_text = sl if (sl and len(sl) <= 42) else "Làm sạch  •  Rửa  •  Dưỡng ẩm"
    draw.text((38, 418), sub_text, fill="#1E293B", font=get_font(20, bold=False))

    out_file = output_path if output_path else (OUTPUT_DIR / f"creative_prontosan_{int(time.time()*1000)}.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out_file, "PNG", quality=95)
    print(f"MEDIA:{os.path.abspath(out_file)}")
    return out_file


# ==============================================================================
# 4. NUTRICOMP COMBO 12 CHAI
# ==============================================================================
def render_pro_nutricomp_combo(headline: str = None, subline: str = None, output_path: Path = None):
    return render_pro_nutricomp_plus(
        headline=headline or "COMBO 12 CHAI TIỆT TRÙNG NGUYÊN SEAL",
        subline=subline or "Giải pháp dinh dưỡng tiết kiệm cho liệu trình phục hồi toàn diện",
        output_path=output_path or (OUTPUT_DIR / f"creative_combo_{int(time.time()*1000)}.png"),
    )


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
