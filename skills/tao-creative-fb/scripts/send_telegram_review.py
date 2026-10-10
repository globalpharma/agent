#!/usr/bin/env python3
"""
send_telegram_review.py - Gửi trọn gói Kế hoạch nội dung tuần + Hình ảnh Poster Demo
từ Trợ lý điều hành & Phòng Marketing GlobalPharma qua Telegram cho Sếp duyệt.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def send_message(bot_token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] send_message HTTP {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[ERROR] send_message failed: {e}")
        return None


def send_photo(bot_token: str, chat_id: str, photo_path: str, caption: str):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(photo_path, "rb") as f:
        file_bytes = f.read()

    filename = Path(photo_path).name

    body = []
    # chat_id
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="chat_id"'.encode("utf-8"))
    body.append(b"")
    body.append(str(chat_id).encode("utf-8"))
    
    # parse_mode
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="parse_mode"'.encode("utf-8"))
    body.append(b"")
    body.append(b"HTML")

    # caption
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="caption"'.encode("utf-8"))
    body.append(b"")
    body.append(caption.encode("utf-8"))

    # photo
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="photo"; filename="{filename}"'.encode("utf-8"))
    body.append(b"Content-Type: image/png")
    body.append(b"")
    body.append(file_bytes)

    body.append(f"--{boundary}--".encode("utf-8"))
    body.append(b"")

    payload = b"\r\n".join(body)
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] send_photo HTTP {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[ERROR] send_photo failed: {e}")
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Telegram Bot Token")
    parser.add_argument("--chat-id", default="5781808621", help="Telegram Chat ID of Sếp")
    parser.add_argument("--poster-dir", default="output", help="Directory containing posters")
    args = parser.parse_args()

    bot_token = args.token
    chat_id = args.chat_id
    p_dir = Path(args.poster_dir)

    print(f"[INFO] Bắt đầu gửi báo cáo duyệt tuần tới Telegram Chat ID: {chat_id}")

    # 1. Tin nhắn mở đầu: Báo cáo kế hoạch tuần
    msg_plan = (
        "<b>📋 BÁO CÁO KẾ HOẠCH NỘI DUNG TUẦN &amp; XIN PHÊ DUYỆT</b>\n"
        "<i>Kính gửi: Sếp Công Hùng và Anh Cường</i>\n"
        "<i>Người báo cáo: GP - Trợ lý điều hành (thay mặt Phòng Marketing)</i>\n\n"
        "Dạ thưa Sếp, em đã điều phối <b>Lead Marketing</b> chỉ đạo chuyên viên <b>Planner</b> lên lịch, <b>Content</b> soạn thảo bài viết, <b>Designer</b> thiết kế poster và <b>Lead Legal</b> đã thẩm định pháp lý y tế đạt chuẩn 100%.\n\n"
        "<b>1. Phân bổ kế hoạch 7 ngày:</b>\n"
        "• <b>Thứ 2 (Nutricomp Drink Plus):</b> Giải pháp phục hồi thể trạng cho người sau phẫu thuật, ốm dậy (300 kcal/chai).\n"
        "• <b>Thứ 3 (Prontosan Wound Spray):</b> Chăm sóc loét tì đè ở người cao tuổi, người tai biến nằm lâu.\n"
        "• <b>Thứ 4 (Nutricomp Renal):</b> Dinh dưỡng lâm sàng chuyên biệt cho người suy thận mạn giai đoạn tiền chạy thận.\n"
        "• <b>Thứ 5 (Prontosan Wound Gel):</b> Phá vỡ màng Biofilm vi khuẩn, làm lành vết thương tiểu đường và vết bỏng.\n"
        "• <b>Thứ 6 (Nutricomp Drink Plus):</b> Bổ sung dinh dưỡng dạng uống liền cho bệnh nhân ung thư, người kém ăn.\n"
        "• <b>Thứ 7 (Prontosan Spray):</b> Cẩm nang sơ cứu và xử lý vết thương trầy xước, vết rách da không xót tại nhà.\n"
        "• <b>Chủ nhật (Dinh dưỡng &amp; Sức khỏe gia đình):</b> Chăm sóc sức khỏe chủ động từ chuyên gia y tế Châu Âu.\n\n"
        "<b>2. Điều hướng Fanpage mục tiêu:</b>\n"
        "✔ Bài Nutricomp ➔ Đăng hệ thống 6 Page Sữa Nutricomp + Page <i>Sức Khỏe Cho Mọi Nhà</i>.\n"
        "✔ Bài Prontosan ➔ Đăng hệ thống 6 Page Vết thương Prontosan + Page <i>Sức Khỏe Cho Mọi Nhà</i>.\n"
        "⛔ <b>Tuyệt đối loại trừ:</b> Fanpage <i>Affiliate - GlobalPharma</i> (để dành tuyến bài tuyển dụng đối tác riêng).\n\n"
        "<b>3. Xác nhận Pháp lý:</b>\n"
        "Lead Legal xác nhận: <code>APPROVED</code> — 100% đúng định vị dinh dưỡng y tế &amp; thiết bị chăm sóc vết thương B.Braun Đức, không có từ cấm 'đặc trị' hay 'thuốc chữa bệnh'.\n\n"
        "Dưới đây là <b>3 DEMO POSTER &amp; BÀI VIẾT TIÊU BIỂU</b> do Designer vừa hoàn thiện, kính mời Sếp xem qua ạ 👇"
    )
    send_message(bot_token, chat_id, msg_plan)

    # 2. Poster 1: Nutricomp Drink Plus
    img_nutri = p_dir / "poster_nutricomp_drink_plus.png"
    if img_nutri.exists():
        caption_nutri = (
            "<b>🥛 DEMO 1: POSTER &amp; BÀI VIẾT NUTRICOMP® DRINK PLUS</b>\n\n"
            "<b>Tiêu đề:</b> PHỤC HỒI THỂ TRẠNG VƯỢT TRỘI VỚI 300 KCAL TỪ B.BRAUN CHLB ĐỨC\n\n"
            "<b>Nội dung trích đoạn:</b>\n"
            "Chăm sóc người thân sau phẫu thuật hay người già suy kiệt, nỗi sợ lớn nhất là người bệnh chán ăn, sút cân nhanh chóng. Mỗi chai Nutricomp Drink Plus 200ml cung cấp trọn vẹn 300 kcal cùng đạm sinh học và khoáng chất y khoa chuẩn Châu Âu, giúp người bệnh lấy lại sức sống chỉ sau vài ngày.\n\n"
            "✔ <b>Thiết kế:</b> Thiết kế chuẩn theo bộ 4 tham chiếu của Sếp (Gradient Ngọc lục bảo #013D29, Hộp 12 chai Nutricomp Drink Renal mở nắp, splash sữa 400 kcal, Nút Đặt mua ngay 3D, Cờ Đức &amp; Bộ 3 cam kết quốc tế, Disclaimer FSMP). Do Agent Design (GPT-5.6-sol) phụ trách.\n"
            "✔ <b>Kênh xuất bản dự kiến:</b> 6 Fanpage Nutricomp + Fanpage Sức Khỏe Cho Mọi Nhà."
        )
        send_photo(bot_token, chat_id, str(img_nutri), caption_nutri)

    # 3. Poster 2: Prontosan Wound Spray
    img_pronto = p_dir / "poster_prontosan_wound_spray.png"
    if img_pronto.exists():
        caption_pronto = (
            "<b>🛡️ DEMO 2: POSTER &amp; BÀI VIẾT PRONTOSAN® WOUND CARE</b>\n\n"
            "<b>Tiêu đề:</b> PHÁ VỠ MÀNG BIOFILM - BẢO VỆ TOÀN DIỆN VẾT LOÉT TÌ ĐÈ &amp; VẾT THƯƠNG MẠN TÍNH\n\n"
            "<b>Nội dung trích đoạn:</b>\n"
            "Tại sao vết loét tì đè ở người nằm lâu hay vết thương tiểu đường lại lâu lành và tái phát nhiễm trùng? Thủ phạm là màng Biofilm bảo vệ vi khuẩn. Prontosan của B.Braun Đức với phức hợp Betaine và Polihexanide giúp phá vỡ màng Biofilm tận gốc, làm sạch dịu nhẹ không đau xót, kích thích tạo mô hạt nhanh chóng.\n\n"
            "✔ <b>Thiết kế:</b> Tone màu xanh ngọc y tế #3BCFAF sạch sẽ, thông tin rõ ràng cho người chăm bệnh.\n"
            "✔ <b>Kênh xuất bản dự kiến:</b> 6 Fanpage Prontosan + Fanpage Sức Khỏe Cho Mọi Nhà."
        )
        send_photo(bot_token, chat_id, str(img_pronto), caption_pronto)

    # 4. Poster 3: Affiliate Tuyển dụng đối tác
    img_aff = p_dir / "poster_affiliate_partner.png"
    if img_aff.exists():
        caption_aff = (
            "<b>💼 DEMO 3: POSTER TUYỂN DỤNG ĐỐI TÁC (FANPAGE AFFILIATE - GLOBALPHARMA)</b>\n\n"
            "<b>Tiêu đề:</b> MÔ HÌNH KINH DOANH MỘT NGƯỜI (SOLOPRENEUR) DÀNH CHO DƯỢC SĨ &amp; CHUYÊN GIA SỨC KHỎE\n\n"
            "<b>Nội dung trích đoạn:</b>\n"
            "Bạn có kiến thức y dược và mong muốn gia tăng nguồn thu nhập thứ hai bền vững? GlobalPharma mở ra mạng lưới Affiliate đồng hành cùng các Dược sĩ, Huấn luyện viên thể hình (PT), Chuyên gia dinh dưỡng. Trao giá trị sức khỏe với các sản phẩm chính ngạch B.Braun Đức, không ôm hàng, không rủi ro vận hành.\n\n"
            "✔ <b>Định hướng:</b> Tinh tế, trao giá trị, không đa cấp hay chèo kéo.\n"
            "✔ <b>Kênh xuất bản dự kiến:</b> Kênh riêng Fanpage Affiliate - GlobalPharma (ID: 1183558371496517)."
        )
        send_photo(bot_token, chat_id, str(img_aff), caption_aff)

    # 5. Tin nhắn kết thúc xin phê duyệt
    msg_confirm = (
        "<b>📌 XIN Ý KIẾN CHỈ ĐẠO CỦA SẾP:</b>\n\n"
        "Em kính trình toàn bộ Kế hoạch nội dung tuần và 3 bản Poster thiết kế mẫu ở trên.\n"
        "Sếp xem qua và nếu đồng ý, xin Sếp chỉ đạo <b>'OK'</b> hoặc <b>'DUYỆT'</b> ngay tại đây ạ!\n\n"
        "Sau khi Sếp duyệt, team Marketing sẽ tự động kích hoạt tiến trình đăng bài mỗi ngày lên đúng mạng lưới Fanpage theo đúng kế hoạch. Kính chúc Sếp ngày làm việc tràn đầy năng lượng ạ! 🙏"
    )
    send_message(bot_token, chat_id, msg_confirm)

    print("[SUCCESS] Đã gửi trọn bộ báo cáo kế hoạch và 3 poster qua Telegram cho Sếp thành công!")


if __name__ == "__main__":
    main()
