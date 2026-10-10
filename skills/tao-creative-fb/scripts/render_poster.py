#!/usr/bin/env python3
"""
render_poster.py - Tạo hình ảnh poster bài post y tế chuẩn nhận diện GlobalPharma & B.Braun Đức.
Sử dụng Pillow để vẽ poster độ phân giải cao (1080x1080), phối màu #3BCFAF & #005B94,
có tiêu đề, huy hiệu B.Braun Đức, danh sách công dụng và chân trang thông tin thương hiệu.
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

# Khởi tạo thư mục output
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


def render_nutricomp_poster(output_path: str):
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#F4F8FA")
    draw = ImageDraw.Draw(img)

    # 1. Header Banner Gradient Top
    draw.rectangle([(0, 0), (w, 180)], fill="#005B94")
    draw.rectangle([(0, 172), (w, 180)], fill="#3BCFAF")

    font_header_sub = get_font(24, bold=True)
    font_header_title = get_font(42, bold=True)
    draw.text((60, 40), "GLOBALPHARMA  ✕  B.BRAUN CHLB ĐỨC", fill="#3BCFAF", font=font_header_sub)
    draw.text((60, 85), "GIẢI PHÁP DINH DƯỠNG Y HỌC LÂM SÀNG", fill="#FFFFFF", font=font_header_title)

    # 2. Main Card Body
    draw_rounded_rect(draw, (60, 220, w - 60, h - 160), radius=28, fill="#FFFFFF", outline="#D3E6F0", width=3)

    # Card Title
    font_prod_name = get_font(52, bold=True)
    draw.text((100, 260), "NUTRICOMP® DRINK PLUS", fill="#005B94", font=font_prod_name)
    
    font_prod_desc = get_font(26, bold=False)
    draw.text((100, 330), "Dinh dưỡng cao năng lượng dạng uống liền • Nhập khẩu trực tiếp CHLB Đức", fill="#556677", font=font_prod_desc)

    # Divider
    draw.line([(100, 380), (w - 100, 380)], fill="#E2EDF3", width=2)

    # Visual Highlights Box
    draw_rounded_rect(draw, (100, 410, w - 100, 680), radius=16, fill="#EBF6FA", outline="#3BCFAF", width=2)

    font_box_title = get_font(30, bold=True)
    draw.text((140, 440), "ƯU ĐIỂM VƯỢT TRỘI ĐÃ ĐƯỢC CHỨNG MINH LÂM SÀNG", fill="#005B94", font=font_box_title)

    bullets = [
        ("✔", "300 kcal / chai 200ml:", "Bù đắp năng lượng thiếu hụt, chống suy kiệt nhanh chóng."),
        ("✔", "Đạm sinh học chất lượng cao:", "Phục hồi cơ bắp, hỗ trợ lành vết mổ, tăng cường miễn dịch."),
        ("✔", "Giàu Omega-3 & Vi chất:", "Giảm phản ứng viêm, cải thiện chức năng tiêu hóa của người bệnh."),
        ("✔", "Hương vị thơm ngon, dễ uống:", "Tiện lợi mở nắp dùng ngay, phù hợp người chán ăn, người già yếu.")
    ]

    font_bullet_icon = get_font(26, bold=True)
    font_bullet_title = get_font(25, bold=True)
    font_bullet_text = get_font(24, bold=False)

    y_offset = 500
    for icon, b_title, b_desc in bullets:
        draw.text((140, y_offset), icon, fill="#3BCFAF", font=font_bullet_icon)
        draw.text((180, y_offset), b_title, fill="#005B94", font=font_bullet_title)
        draw.text((180, y_offset + 32), b_desc, fill="#334455", font=font_bullet_text)
        y_offset += 75

    # Target Audience Badge
    draw_rounded_rect(draw, (100, 715, w - 100, 880), radius=16, fill="#FFFFFF", outline="#005B94", width=2)
    font_aud_title = get_font(26, bold=True)
    draw.text((140, 735), "ĐỐI TƯỢNG SỬ DỤNG CHÍNH", fill="#005B94", font=font_aud_title)
    
    aud_items = [
        "• Người bệnh trước và sau phẫu thuật cần hồi phục thể trạng",
        "• Bệnh nhân ung thư, người đang hóa trị - xạ trị mệt mỏi, sút cân",
        "• Người cao tuổi ăn uống kém, người suy dinh dưỡng, suy nhược lâu ngày"
    ]
    font_aud_text = get_font(22, bold=False)
    y_aud = 780
    for item in aud_items:
        draw.text((140, y_aud), item, fill="#445566", font=font_aud_text)
        y_aud += 30

    # 3. Footer Banner
    draw.rectangle([(0, h - 130), (w, h)], fill="#005B94")
    font_footer_left = get_font(24, bold=True)
    font_footer_right = get_font(22, bold=False)
    draw.text((60, h - 90), "GLOBALPHARMA - NHÀ PHÂN PHỐI CHÍNH THỨC B.BRAUN TẠI VIỆT NAM", fill="#3BCFAF", font=font_footer_left)
    draw.text((60, h - 55), "Website: agent.globalpharma.vn  |  Tư vấn chuyên môn: Fanpage Sức Khỏe Cho Mọi Nhà", fill="#FFFFFF", font=font_footer_right)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Nutricomp tại: {output_path}")
    return output_path


def render_prontosan_poster(output_path: str):
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#F4F8FA")
    draw = ImageDraw.Draw(img)

    # 1. Header Banner Gradient Top
    draw.rectangle([(0, 0), (w, 180)], fill="#004D73")
    draw.rectangle([(0, 172), (w, 180)], fill="#3BCFAF")

    font_header_sub = get_font(24, bold=True)
    font_header_title = get_font(42, bold=True)
    draw.text((60, 40), "GLOBALPHARMA  ✕  B.BRAUN CHLB ĐỨC", fill="#3BCFAF", font=font_header_sub)
    draw.text((60, 85), "CHĂM SÓC & LÀM LÀNH VẾT THƯƠNG CHUYÊN SÂU", fill="#FFFFFF", font=font_header_title)

    # 2. Main Card Body
    draw_rounded_rect(draw, (60, 220, w - 60, h - 160), radius=28, fill="#FFFFFF", outline="#D3E6F0", width=3)

    # Card Title
    font_prod_name = get_font(52, bold=True)
    draw.text((100, 260), "PRONTOSAN® WOUND CARE", fill="#004D73", font=font_prod_name)
    
    font_prod_desc = get_font(26, bold=False)
    draw.text((100, 330), "Dung dịch & Gel rửa vết thương y tế • Kháng khuẩn & Phá vỡ màng Biofilm", fill="#556677", font=font_prod_desc)

    # Divider
    draw.line([(100, 380), (w - 100, 380)], fill="#E2EDF3", width=2)

    # Visual Highlights Box
    draw_rounded_rect(draw, (100, 410, w - 100, 680), radius=16, fill="#EBF9F7", outline="#3BCFAF", width=2)

    font_box_title = get_font(30, bold=True)
    draw.text((140, 440), "CƠ CHẾ TÁC ĐỘNG ĐỘT PHÁ TỪ CHLB ĐỨC", fill="#004D73", font=font_box_title)

    bullets = [
        ("✔", "Phá vỡ màng Biofilm vi khuẩn:", "Loại bỏ tận gốc nơi trú ẩn của vi khuẩn kháng kháng sinh."),
        ("✔", "Rửa êm dịu, hoàn toàn không xót:", "Không gây kích ứng mô non, bảo toàn quá trình lành vết thương."),
        ("✔", "Khử mùi hôi và dịch tiết nhanh:", "Giảm đau đớn cho người bệnh khi thay băng hàng ngày."),
        ("✔", "Ngừa nhiễm trùng tái phát:", "Bảo vệ bề mặt vết loét kéo dài lên tới nhiều giờ liên tục.")
    ]

    font_bullet_icon = get_font(26, bold=True)
    font_bullet_title = get_font(25, bold=True)
    font_bullet_text = get_font(24, bold=False)

    y_offset = 500
    for icon, b_title, b_desc in bullets:
        draw.text((140, y_offset), icon, fill="#3BCFAF", font=font_bullet_icon)
        draw.text((180, y_offset), b_title, fill="#004D73", font=font_bullet_title)
        draw.text((180, y_offset + 32), b_desc, fill="#334455", font=font_bullet_text)
        y_offset += 75

    # Target Audience Badge
    draw_rounded_rect(draw, (100, 715, w - 100, 880), radius=16, fill="#FFFFFF", outline="#004D73", width=2)
    font_aud_title = get_font(26, bold=True)
    draw.text((140, 735), "CHỈ ĐỊNH ĐẶC BIỆT HIỆU QUẢ CHO", fill="#004D73", font=font_aud_title)
    
    aud_items = [
        "• Loét tì đè ở người già, người tai biến, liệt nằm lâu ngày khó cử động",
        "• Loét bàn chân do đái tháo đường (bàn chân tiểu đường)",
        "• Vết bỏng, vết mổ ngoại khoa có nguy cơ nhiễm trùng hoặc lâu lành"
    ]
    font_aud_text = get_font(22, bold=False)
    y_aud = 780
    for item in aud_items:
        draw.text((140, y_aud), item, fill="#445566", font=font_aud_text)
        y_aud += 30

    # 3. Footer Banner
    draw.rectangle([(0, h - 130), (w, h)], fill="#004D73")
    font_footer_left = get_font(24, bold=True)
    font_footer_right = get_font(22, bold=False)
    draw.text((60, h - 90), "GLOBALPHARMA - CHĂM SÓC SỨC KHỎE TOÀN DIỆN CHO MỌI GIA ĐÌNH", fill="#3BCFAF", font=font_footer_left)
    draw.text((60, h - 55), "Website: agent.globalpharma.vn  |  Tư vấn chăm sóc vết thương: Hệ thống Fanpage Prontosan", fill="#FFFFFF", font=font_footer_right)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Prontosan tại: {output_path}")
    return output_path


def render_affiliate_poster(output_path: str):
    w, h = 1080, 1080
    img = Image.new("RGB", (w, h), color="#FAF7F2")
    draw = ImageDraw.Draw(img)

    # 1. Header Banner
    draw.rectangle([(0, 0), (w, 180)], fill="#1E2A38")
    draw.rectangle([(0, 172), (w, 180)], fill="#D4AF37")

    font_header_sub = get_font(24, bold=True)
    font_header_title = get_font(40, bold=True)
    draw.text((60, 40), "GLOBALPHARMA AFFILIATE NETWORK", fill="#D4AF37", font=font_header_sub)
    draw.text((60, 85), "CHUYỂN HÓA TRI THỨC Y DƯỢC THÀNH THU NHẬP BỀN VỮNG", fill="#FFFFFF", font=font_header_title)

    # 2. Main Card Body
    draw_rounded_rect(draw, (60, 220, w - 60, h - 160), radius=28, fill="#FFFFFF", outline="#EADBC8", width=3)

    font_prod_name = get_font(48, bold=True)
    draw.text((100, 260), "MÔ HÌNH KINH DOANH MỘT NGƯỜI", fill="#1E2A38", font=font_prod_name)
    
    font_prod_desc = get_font(26, bold=False)
    draw.text((100, 330), "Dành riêng cho Dược sĩ, PT, Chuyên gia dinh dưỡng & Người làm việc ngành sức khỏe", fill="#665544", font=font_prod_desc)

    draw.line([(100, 380), (w - 100, 380)], fill="#F0E6D8", width=2)

    draw_rounded_rect(draw, (100, 410, w - 100, 680), radius=16, fill="#FBF8F3", outline="#D4AF37", width=2)

    font_box_title = get_font(28, bold=True)
    draw.text((140, 440), "GIÁ TRỊ KHÁC BIỆT KHI ĐỒNG HÀNH CÙNG GLOBALPHARMA", fill="#1E2A38", font=font_box_title)

    bullets = [
        ("✦", "Sản phẩm chính ngạch tiêu chuẩn Châu Âu:", "B.Braun Đức - Uy tín y khoa được giới bác sĩ tin tưởng tuyệt đối."),
        ("✦", "Không ôm hàng, không rủi ro vận hành:", "GlobalPharma đóng gói, vận chuyển và bảo đảm pháp lý toàn diện."),
        ("✦", "Hệ thống AI & Công cụ số hỗ trợ:", "Cung cấp trọn bộ nội dung, poster, video truyền thông chuyên sâu."),
        ("✦", "Chiết khấu minh bạch, thanh toán đúng hẹn:", "Gia tăng thu nhập thứ hai dựa trên uy tín và sự phụng sự người bệnh.")
    ]

    font_bullet_icon = get_font(26, bold=True)
    font_bullet_title = get_font(25, bold=True)
    font_bullet_text = get_font(24, bold=False)

    y_offset = 500
    for icon, b_title, b_desc in bullets:
        draw.text((140, y_offset), icon, fill="#D4AF37", font=font_bullet_icon)
        draw.text((180, y_offset), b_title, fill="#1E2A38", font=font_bullet_title)
        draw.text((180, y_offset + 32), b_desc, fill="#554433", font=font_bullet_text)
        y_offset += 75

    draw_rounded_rect(draw, (100, 715, w - 100, 880), radius=16, fill="#FFFFFF", outline="#1E2A38", width=2)
    font_aud_title = get_font(26, bold=True)
    draw.text((140, 735), "THÔNG ĐIỆP ĐỒNG HÀNH", fill="#1E2A38", font=font_aud_title)
    
    aud_items = [
        "\"Bạn có chuyên môn và lòng nhân ái. Chúng tôi có nền tảng giải pháp y tế Châu Âu.",
        " Hãy cùng biến kiến thức y dược thành giá trị thiết thực cho cộng đồng và sự",
        " tự do tài chính bền vững của chính bạn.\""
    ]
    font_aud_text = get_font(22, bold=False)
    y_aud = 780
    for item in aud_items:
        draw.text((140, y_aud), item, fill="#554433", font=font_aud_text)
        y_aud += 30

    # 3. Footer
    draw.rectangle([(0, h - 130), (w, h)], fill="#1E2A38")
    font_footer_left = get_font(24, bold=True)
    font_footer_right = get_font(22, bold=False)
    draw.text((60, h - 90), "GLOBALPHARMA - ĐỐI TÁC Y TẾ TIN CẬY CỦA CHUYÊN GIA SỨC KHỎE", fill="#D4AF37", font=font_footer_left)
    draw.text((60, h - 55), "Đăng ký tham gia mạng lưới Affiliate: Fanpage Affiliate - GlobalPharma", fill="#FFFFFF", font=font_footer_right)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"[SUCCESS] Đã tạo poster Affiliate tại: {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tạo poster chuẩn nhận diện y tế GlobalPharma")
    parser.add_argument("--type", choices=["nutricomp", "prontosan", "affiliate", "all"], default="all")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.type in ("nutricomp", "all"):
        render_nutricomp_poster(str(out_dir / "poster_nutricomp_drink_plus.png"))
    if args.type in ("prontosan", "all"):
        render_prontosan_poster(str(out_dir / "poster_prontosan_wound_spray.png"))
    if args.type in ("affiliate", "all"):
        render_affiliate_poster(str(out_dir / "poster_affiliate_partner.png"))


if __name__ == "__main__":
    main()
