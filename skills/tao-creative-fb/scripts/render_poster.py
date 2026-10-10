#!/usr/bin/env python3
"""
render_poster.py - Thiết kế visual và poster y tế tự nhiên, chuẩn xác cho GlobalPharma.
Sử dụng 100% ẢNH SẢN PHẨM THẬT & LOGO CHÍNH THỨC từ Kho Tri Thức Dữ Liệu Công Ty.
Tuân thủ tuyệt đối quy chuẩn ads-image-architect (Zero brand CTA inside, bố cục thoáng đãng, lâm sàng).
"""

import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
ASSETS_DIR = SCRIPT_DIR.parent / "assets"
REFS_DIR = ASSETS_DIR / "references"


def get_font(size: int, bold: bool = False):
    candidates = [
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/etc/apk/fonts/arial.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def get_banner_logo(target_h: int = 55):
    logo_path = REFS_DIR / "real_logo_globalpharma_banner.png"
    if not logo_path.exists():
        logo_path = ASSETS_DIR / "globalpharma_logo.png"
    if not logo_path.exists():
        logo_path = Path("ui/web/public/globalpharma-logo.png")
    if logo_path.exists():
        logo = Image.open(logo_path).convert("RGBA")
        ratio = target_h / logo.height
        new_w = int(logo.width * ratio)
        return logo.resize((new_w, target_h), Image.Resampling.LANCZOS)
    return None


def render_nutricomp_poster(output_path: str, variant: str = "box12", force: bool = False):
    """
    Creative 1: Hộp quà 12 chai Nutricomp Drink Renal Vanilla (B.Braun CHLB Đức)
    Sử dụng 100% ảnh chụp thật studio hộp quà 12 chai & bao bì từ kho dữ liệu.
    """
    w, h = 1080, 1080
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    
    # 1. Gradient nền y tế cao cấp
    draw_canvas = ImageDraw.Draw(canvas)
    for y in range(h):
        ratio = y / h
        if ratio < 0.25:
            r = int(255 - ratio * 10)
            g = int(255 - ratio * 5)
            b = int(255 - ratio * 8)
        elif ratio < 0.75:
            r, g, b = 252, 254, 253
        else:
            sub = (ratio - 0.75) / 0.25
            r = int(252 - sub * 12)
            g = int(254 - sub * 8)
            b = int(253 - sub * 10)
        draw_canvas.line([(0, y), (w, y)], fill=(r, g, b, 255))
    
    draw = ImageDraw.Draw(canvas)
    
    # 2. Header: Logo GlobalPharma thật + Text đối tác B.Braun
    logo = get_banner_logo(target_h=52)
    if logo:
        canvas.paste(logo, (50, 38), logo)
        logo_end_x = 50 + logo.width
    else:
        logo_end_x = 240
        
    draw.line([(logo_end_x + 20, 42), (logo_end_x + 20, 88)], fill="#CBD5E1", width=2)
    draw.text((logo_end_x + 35, 46), "ĐỐI TÁC PHÂN PHỐI CHÍNH THỨC", fill="#64748B", font=get_font(13, bold=True))
    draw.text((logo_end_x + 35, 68), "B.BRAUN (CHLB ĐỨC) TẠI VIỆT NAM", fill="#005B94", font=get_font(15, bold=True))
    
    badge_x, badge_y = w - 210, 38
    draw.rounded_rectangle([(badge_x, badge_y), (w - 50, badge_y + 52)], radius=10, fill="#F8FAFC", outline="#E2E8F0", width=1)
    draw.text((badge_x + 18, badge_y + 8), "NHẬP KHẨU 100%", fill="#64748B", font=get_font(12, bold=True))
    draw.text((badge_x + 18, badge_y + 26), "CHLB ĐỨC", fill="#B91C1C", font=get_font(16, bold=True))
    
    # 3. Tiêu đề thương hiệu chuẩn kho tri thức
    draw.text((50, 118), "DINH DƯỠNG Y HỌC CHUYÊN BIỆT CHO NGƯỜI BỆNH THẬN", fill="#0F766E", font=get_font(19, bold=True))
    draw.text((50, 148), "COMBO HỘP QUÀ 12 CHAI NUTRICOMP® RENAL", fill="#0F172A", font=get_font(34, bold=True))
    draw.text((50, 198), "Năng lượng cao 400 kcal/chai • Kiểm soát nghiêm ngặt Natri, Kali & Phospho", fill="#475569", font=get_font(18, bold=False))
    
    # 4. CHÈN ẢNH SẢN PHẨM THẬT (Combo 12 chai studio)
    prod_path = REFS_DIR / "real_nutricomp_combo12_giftbox.png"
    if not prod_path.exists():
        prod_path = REFS_DIR / "ref_nutricomp_box12.jpg"
    
    if prod_path.exists():
        prod_img = Image.open(prod_path).convert("RGBA")
        target_prod_w = 980
        prod_ratio = target_prod_w / prod_img.width
        target_prod_h = int(prod_img.height * prod_ratio)
        if target_prod_h > 560:
            target_prod_h = 560
            prod_ratio = target_prod_h / prod_img.height
            target_prod_w = int(prod_img.width * prod_ratio)
            
        prod_resized = prod_img.resize((target_prod_w, target_prod_h), Image.Resampling.LANCZOS)
        prod_x = (w - target_prod_w) // 2
        prod_y = 238
        canvas.paste(prod_resized, (prod_x, prod_y), prod_resized if prod_resized.mode == "RGBA" else None)
    
    # 5. Các thẻ Callout y khoa chuẩn từ kho tri thức
    callouts = [
        ("400 KCAL / 200ML", "Năng lượng cao 2.0 kcal/ml", "Phục hồi thể trạng suy kiệt"),
        ("14G ĐẠM CHẤT LƯỢNG", "Đạm sinh học giá trị cao", "Bù đắp thiếu hụt lọc máu"),
        ("ÍT ĐIỆN GIẢI AN TOÀN", "Kiểm soát Natri, Kali, P", "Bảo vệ chức năng thận"),
        ("GIÀU OMEGA-3 & FOS", "Bổ sung EPA, DHA & FOS", "Dễ uống, êm bụng dễ tiêu")
    ]
    
    card_w = 230
    card_h = 110
    spacing = 16
    start_x = (w - (4 * card_w + 3 * spacing)) // 2
    card_y = 820
    
    for i, (title, l1, l2) in enumerate(callouts):
        cx = start_x + i * (card_w + spacing)
        draw.rounded_rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], radius=12, fill="#FFFFFF", outline="#0D9488", width=2)
        draw.text((cx + 14, card_y + 14), title, fill="#0F766E", font=get_font(14, bold=True))
        draw.text((cx + 14, card_y + 45), l1, fill="#334155", font=get_font(13, bold=False))
        draw.text((cx + 14, card_y + 72), l2, fill="#64748B", font=get_font(12, bold=False))
        
    # 6. Chân trang uy tín y khoa
    draw.line([(50, h - 110), (w - 50, h - 110)], fill="#E2E8F0", width=1)
    draw.text((50, h - 85), "CÔNG TY CỔ PHẦN GLOBALPHARMA • PHÂN PHỐI CHÍNH HÃNG B.BRAUN TẠI VIỆT NAM", fill="#0F172A", font=get_font(15, bold=True))
    draw.text((50, h - 55), "Thực phẩm dinh dưỡng y học (FSMP) • Sử dụng theo tư vấn của chuyên gia dinh dưỡng và y tế", fill="#64748B", font=get_font(13, bold=False))
    draw.text((w - 280, h - 72), "Hotline: 0783 114 115", fill="#005B94", font=get_font(18, bold=True))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo Creative 1 Nutricomp từ ảnh thật: {output_path}")
    return output_path


def render_prontosan_poster(output_path: str, force: bool = False):
    """
    Creative 2: Prontosan Wound Spray 75ml (B.Braun CHLB Đức)
    Sử dụng 100% ảnh chụp chai thật và ảnh ứng dụng lâm sàng thực tế của B.Braun.
    """
    w, h = 1080, 1080
    canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    
    # 1. Gradient nền y tế sạch sẽ Châu Âu
    draw_canvas = ImageDraw.Draw(canvas)
    for y in range(h):
        ratio = y / h
        r = int(246 + ratio * 7)
        g = int(251 + ratio * 3)
        b = int(255)
        draw_canvas.line([(0, y), (w, y)], fill=(r, g, b, 255))
    draw = ImageDraw.Draw(canvas)
    
    # 2. Header Logo
    logo = get_banner_logo(target_h=52)
    if logo:
        canvas.paste(logo, (50, 38), logo)
        logo_end_x = 50 + logo.width
    else:
        logo_end_x = 240
        
    draw.line([(logo_end_x + 20, 42), (logo_end_x + 20, 88)], fill="#CBD5E1", width=2)
    draw.text((logo_end_x + 35, 46), "GIẢI PHÁP CHĂM SÓC VẾT THƯƠNG CHUẨN CHÂU ÂU", fill="#64748B", font=get_font(13, bold=True))
    draw.text((logo_end_x + 35, 68), "B.BRAUN MEDICAL AG (CHLB ĐỨC)", fill="#005B94", font=get_font(15, bold=True))
    
    badge_x, badge_y = w - 210, 38
    draw.rounded_rectangle([(badge_x, badge_y), (w - 50, badge_y + 52)], radius=10, fill="#F0FDF4", outline="#BBF7D0", width=1)
    draw.text((badge_x + 18, badge_y + 8), "TIÊU CHUẨN Y KHOA", fill="#166534", font=get_font(12, bold=True))
    draw.text((badge_x + 18, badge_y + 26), "ISO 13485", fill="#047857", font=get_font(16, bold=True))
    
    # 3. Tiêu đề
    draw.text((50, 118), "CHUẨN BỊ NỀN VẾT THƯƠNG & PHÁ VỠ MÀNG BIOFILM TẬN GỐC", fill="#005B94", font=get_font(19, bold=True))
    draw.text((50, 148), "PRONTOSAN® WOUND SPRAY 75ML", fill="#0F172A", font=get_font(34, bold=True))
    draw.text((50, 198), "Đột phá kết hợp Betaine 0.1% & Polyhexanide (PHMB) 0.1% • Không đau rát, an toàn mô hạt", fill="#475569", font=get_font(18, bold=False))
    
    # 4. CHÈN 2 ẢNH THẬT: THAO TÁC XỊT LÂM SÀNG & CHAI SẢN PHẨM CHÍNH HÃNG
    action_path = REFS_DIR / "real_prontosan_wound_spray_action.jpg"
    bottle_path = REFS_DIR / "real_prontosan_wound_spray_bottle.webp"
    
    if action_path.exists():
        act_img = Image.open(action_path).convert("RGBA")
        act_resized = act_img.resize((480, 520), Image.Resampling.LANCZOS)
        mask = Image.new("L", (480, 520), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (480, 520)], radius=18, fill=255)
        
        draw.rounded_rectangle([(50, 250), (50 + 480, 250 + 520)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=2)
        canvas.paste(act_resized, (50, 250), mask)
        
        draw.rounded_rectangle([(70, 715), (410, 750)], radius=8, fill="#0F172ACC")
        draw.text((85, 725), "ỨNG DỤNG LÂM SÀNG BỞI CHUYÊN VIÊN Y TẾ", fill="#FFFFFF", font=get_font(12, bold=True))

    if bottle_path.exists():
        bot_img = Image.open(bottle_path).convert("RGBA")
        draw.rounded_rectangle([(560, 250), (w - 50, 250 + 520)], radius=20, fill="#FFFFFF", outline="#E2E8F0", width=2)
        bot_resized = bot_img.resize((430, 480), Image.Resampling.LANCZOS)
        canvas.paste(bot_resized, (580, 270), bot_resized)
        
        draw.rounded_rectangle([(580, 715), (920, 750)], radius=8, fill="#005B94CC")
        draw.text((595, 725), "CHAI XỊT 75ML VÔ TRÙNG B.BRAUN CHÍNH HÃNG", fill="#FFFFFF", font=get_font(12, bold=True))
        
    # 5. Các thẻ Callout cơ chế y khoa
    cards = [
        ("BETAINE 0.1%", "Phá vỡ màng Biofilm vi khuẩn", "Làm sạch sâu nền tổn thương"),
        ("PHMB 0.1%", "Kháng khuẩn phổ rộng (MRSA)", "Không độc hại mô hạt lành"),
        ("0% ĐAU RÁT", "Dịu nhẹ êm ái khi tiếp xúc", "Tối ưu cho loét tì đè, bỏng"),
        ("TIỆN LỢI TỦ THUỐC", "Dạng xịt 75ml vô trùng chuẩn", "Dùng an toàn 8 tuần sau mở")
    ]
    
    card_w = 230
    card_h = 110
    spacing = 16
    start_x = (w - (4 * card_w + 3 * spacing)) // 2
    card_y = 820
    
    for i, (title, l1, l2) in enumerate(cards):
        cx = start_x + i * (card_w + spacing)
        draw.rounded_rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], radius=12, fill="#FFFFFF", outline="#0284C7", width=2)
        draw.text((cx + 14, card_y + 14), title, fill="#0284C7", font=get_font(14, bold=True))
        draw.text((cx + 14, card_y + 45), l1, fill="#334155", font=get_font(13, bold=False))
        draw.text((cx + 14, card_y + 72), l2, fill="#64748B", font=get_font(12, bold=False))
        
    # 6. Chân trang
    draw.line([(50, h - 110), (w - 50, h - 110)], fill="#E2E8F0", width=1)
    draw.text((50, h - 85), "CÔNG TY CỔ PHẦN GLOBALPHARMA • ĐỐI TÁC PHÂN PHỐI CHÍNH THỨC B.BRAUN TẠI VIỆT NAM", fill="#0F172A", font=get_font(15, bold=True))
    draw.text((50, h - 55), "Trang thiết bị y tế chuẩn bị nền vết thương • Đọc kỹ hướng dẫn sử dụng trước khi dùng", fill="#64748B", font=get_font(13, bold=False))
    draw.text((w - 280, h - 72), "Hotline: 0783 114 115", fill="#005B94", font=get_font(18, bold=True))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo Creative 2 Prontosan từ ảnh thật: {output_path}")
    return output_path


def render_affiliate_poster(output_path: str, force: bool = False):
    """
    Creative 3: Fanpage Tuyển Dụng Affiliate - GlobalPharma (Solopreneur)
    Sử dụng bức ảnh chân dung Dược sĩ uy tín kết hợp thay thế hoàn toàn Logo giả
    bằng LOGO CHÍNH THỨC GLOBALPHARMA từ kho dữ liệu và tinh chỉnh thẻ giá trị.
    """
    w, h = 1080, 1080
    base_portrait = REPO_ROOT / "affiliate_solopreneur_ad_1791614479171.jpg"
    if not base_portrait.exists():
        base_portrait = Path("C:/Users/Surface/.gemini/antigravity/brain/552b4a88-d83e-4471-97a6-f32d72fa14d4/affiliate_solopreneur_ad_1791614479171.jpg")
    
    if base_portrait.exists():
        canvas = Image.open(base_portrait).convert("RGBA")
        if canvas.size != (w, h):
            canvas = canvas.resize((w, h), Image.Resampling.LANCZOS)
    else:
        canvas = Image.new("RGBA", (w, h), (15, 23, 42, 255))
        
    draw = ImageDraw.Draw(canvas)
    
    # ĐÈ LÊN GÓC TRÊN TRÁI BẰNG LOGO MASTER GLOBALPHARMA CHÍNH THỨC
    logo = get_banner_logo(target_h=58)
    if logo:
        box_w = 450
        box_h = 105
        draw.rounded_rectangle([(35, 30), (35 + box_w, 30 + box_h)], radius=14, fill="#FFFFFF", outline="#E2E8F0", width=1)
        canvas.paste(logo, (50, 42), logo)
        draw.line([(50, 42 + logo.height + 6), (50 + box_w - 30, 42 + logo.height + 6)], fill="#E2E8F0", width=1)
        draw.text((50, 42 + logo.height + 10), "MẠNG LƯỚI ĐỐI TÁC Y TẾ & SỨC KHỎE • GLOBALPHARMA", fill="#0F766E", font=get_font(12, bold=True))
        
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo Creative 3 Affiliate với logo chuẩn công ty: {output_path}")
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
