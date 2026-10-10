#!/usr/bin/env python3
"""
send_telegram_review.py - Gửi Kế hoạch nội dung tuần (file Markdown để đọc online)
kèm 3 bản Poster Pro (Stop-scrolling, minimal text) qua Telegram cho Sếp duyệt.
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
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] send_message HTTP {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[ERROR] send_message failed: {e}")
        return None


def send_document(bot_token: str, chat_id: str, doc_path: str, caption: str = ""):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(doc_path, "rb") as f:
        file_bytes = f.read()

    filename = Path(doc_path).name

    body = []
    # chat_id
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="chat_id"'.encode("utf-8"))
    body.append(b"")
    body.append(str(chat_id).encode("utf-8"))
    
    # caption
    if caption:
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="caption"'.encode("utf-8"))
        body.append(b"")
        body.append(caption.encode("utf-8"))

        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="parse_mode"'.encode("utf-8"))
        body.append(b"")
        body.append(b"HTML")

    # document
    body.append(f"--{boundary}".encode("utf-8"))
    body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode("utf-8"))
    body.append(b"Content-Type: text/markdown")
    body.append(b"")
    body.append(file_bytes)

    body.append(f"--{boundary}--".encode("utf-8"))
    body.append(b"")

    payload = b"\r\n".join(body)
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] send_document HTTP {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[ERROR] send_document failed: {e}")
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"[OK] Đã gửi ảnh {filename} thành công! Message ID: {data.get('result', {}).get('message_id')}")
            return data
    except urllib.error.HTTPError as e:
        print(f"[ERROR] send_photo {filename} HTTP {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"[ERROR] send_photo {filename} failed: {e}")
        return None


def resolve_file(candidate_dirs, filename):
    for d in candidate_dirs:
        p = Path(d) / filename
        if p.exists() and p.stat().st_size > 0:
            return p
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
    search_dirs = [
        args.poster_dir,
        "skills/tao-creative-fb/output",
        "/opt/goclaw/skills/tao-creative-fb/output",
        "/app/workspace/output"
    ]

    print(f"[INFO] Bắt đầu gửi báo cáo duyệt tuần tới Telegram Chat ID: {chat_id}")
    print(f"[INFO] Thư mục tìm kiếm file: {search_dirs}")

    # 1. Tin nhắn tóm tắt súc tích mở đầu (Không tràn lan toàn văn)
    msg_intro = (
        "<b>📋 BÁO CÁO KẾ HOẠCH NỘI DUNG TUẦN & XIN PHÊ DUYỆT</b>\n"
        "<i>Kính gửi: Sếp Công Hùng và Anh Cường</i>\n"
        "<i>Người báo cáo: GP - Trợ lý điều hành (thay mặt Phòng Marketing)</i>\n\n"
        "Dạ thưa Sếp, toàn bộ chi tiết <b>Kế hoạch nội dung 7 ngày</b>, phân bổ 14 kênh Fanpage và báo cáo thẩm định Pháp lý y tế (APPROVED 100%) đã được đóng gói thành file markdown đính kèm dưới đây để Sếp có thể <b>nhấn mở đọc online trực tiếp ngay trên Telegram</b> tiện lợi, không bị rối màn hình chat:\n\n"
        "📄 <b>File chi tiết:</b> <code>KE_HOACH_NOI_DUNG_TUAN.md</code> (Đính kèm ngay dưới)\n"
        "🎨 <b>Hình ảnh:</b> 3 bản thiết kế Poster Pro mới (Stop-scrolling, tối giản text, 100% ảnh thật & logo chuẩn).\n\n"
        "Kính mời Sếp mở file đọc online và xem các bản poster ở dưới ạ 👇"
    )
    r_intro = send_message(bot_token, chat_id, msg_intro)
    if r_intro and r_intro.get("ok"):
        print(f"[OK] Đã gửi tin nhắn mở đầu thành công! Msg ID: {r_intro.get('result', {}).get('message_id')}")
    else:
        print(f"[WARN] Gửi tin mở đầu thất bại: {r_intro}")

    # 2. Gửi file Markdown đính kèm để đọc online trực tiếp trên Telegram
    doc_path = resolve_file(search_dirs, "KE_HOACH_NOI_DUNG_TUAN.md")
    if doc_path:
        doc_caption = (
            "📄 <b>KẾ HOẠCH NỘI DUNG TUẦN (7 NGÀY CHI TIẾT & 14 FANPAGE)</b>\n"
            "<i>Nhấn vào file để xem trực tiếp online trên Telegram</i>"
        )
        print(f"[INFO] Đang gửi file document {doc_path} ({doc_path.stat().st_size} bytes)...")
        res_doc = send_document(bot_token, chat_id, str(doc_path), doc_caption)
        if res_doc and res_doc.get("ok"):
            print(f"[OK] Đã gửi file KE_HOACH_NOI_DUNG_TUAN.md thành công! Msg ID: {res_doc.get('result', {}).get('message_id')}")
        else:
            print(f"[WARN] send_document response: {res_doc}")
    else:
        print(f"[ERROR] Không tìm thấy file KE_HOACH_NOI_DUNG_TUAN.md trong {search_dirs}")

    # 3. Poster 1: Nutricomp Drink Renal Combo 12 Chai
    img_nutri = resolve_file(search_dirs, "poster_nutricomp_drink_plus.png")
    if img_nutri:
        print(f"[INFO] Đang gửi poster Nutricomp: {img_nutri} ({img_nutri.stat().st_size} bytes)...")
        caption_nutri = (
            "<b>🥛 CREATIVE 1 (PRO): COMBO 12 CHAI NUTRICOMP® RENAL (B.BRAUN CHLB ĐỨC)</b>\n\n"
            "🔥 <b>Big Hook:</b> <code>2.0 KCAL / ML — HỒI PHỤC THỂ TRẠNG SUY KIỆT</code>\n"
            "✨ <b>Visual:</b> Bục Marble Studio cao cấp, ánh sáng y tế Dark Teal sang trọng, ảnh chụp thật combo 12 chai nguyên seal.\n"
            "💎 <b>Định vị:</b> Dinh dưỡng y học lâm sàng cho người bệnh thận & suy kiệt dinh dưỡng.\n\n"
            "✔ <i>Chuẩn Meta Ads: Không chèn nút CTA giả trong ảnh, tập trung thị giác tối đa.</i>"
        )
        send_photo(bot_token, chat_id, str(img_nutri), caption_nutri)
    else:
        print(f"[ERROR] Không tìm thấy poster_nutricomp_drink_plus.png trong {search_dirs}")

    # 4. Poster 2: Prontosan Wound Spray
    img_pronto = resolve_file(search_dirs, "poster_prontosan_wound_spray.png")
    if img_pronto:
        print(f"[INFO] Đang gửi poster Prontosan: {img_pronto} ({img_pronto.stat().st_size} bytes)...")
        caption_pronto = (
            "<b>🛡️ CREATIVE 2 (PRO): PRONTOSAN® WOUND SPRAY 75ML (B.BRAUN CHLB ĐỨC)</b>\n\n"
            "🔥 <b>Big Hook:</b> <code>PHÁ VỠ MÀNG BIOFILM — 0% ĐAU RÁT • NHANH LÀNH GẤP 2 LẦN</code>\n"
            "✨ <b>Visual:</b> Làn sóng nước tinh khiết y khoa & phòng lab vô trùng, chai xịt thật 75ml trên bục pedestal kèm huy hiệu thao tác lâm sàng.\n"
            "💎 <b>Đột phá:</b> Phức hợp Betaine 0.1% & Polyhexanide (PHMB) 0.1% chuẩn Châu Âu ISO 13485.\n\n"
            "✔ <i>Chuẩn Meta Ads: Gây ấn tượng mạnh mẽ cho người nhà bệnh nhân loét mạn tính & vết thương lâu lành.</i>"
        )
        send_photo(bot_token, chat_id, str(img_pronto), caption_pronto)
    else:
        print(f"[ERROR] Không tìm thấy poster_prontosan_wound_spray.png trong {search_dirs}")

    # 5. Poster 3: Affiliate Tuyển dụng đối tác
    img_aff = resolve_file(search_dirs, "poster_affiliate_partner.png")
    if img_aff:
        print(f"[INFO] Đang gửi poster Affiliate: {img_aff} ({img_aff.stat().st_size} bytes)...")
        caption_aff = (
            "<b>💼 CREATIVE 3 (PRO): DƯỢC SĨ SOLOPRENEUR (ĐỐI TÁC Y TẾ GLOBALPHARMA)</b>\n\n"
            "🔥 <b>Big Hook:</b> <code>DƯỢC SĨ SOLOPRENEUR — XÂY THU NHẬP THỨ 2 TỪ UY TÍN Y KHOA</code>\n"
            "✨ <b>Visual:</b> Phong cách chân dung tạp chí Forbes/Bloomberg đẳng cấp, Dược sĩ chuyên nghiệp, không gian y tế kính hiện đại.\n"
            "💎 <b>Giá trị cốt lõi:</b> 0 vốn ôm hàng • 0 áp doanh số • 100% Sản phẩm Y khoa chính ngạch B.Braun Đức.\n\n"
            "✔ <i>Chuẩn Meta Ads: Tôn vinh uy tín chuyên gia y tế, loại bỏ hoàn toàn cảm giác đa cấp/tuyển dụng thô.</i>"
        )
        send_photo(bot_token, chat_id, str(img_aff), caption_aff)
    else:
        print(f"[ERROR] Không tìm thấy poster_affiliate_partner.png trong {search_dirs}")

    # 6. Tin nhắn kết thúc xin phê duyệt
    msg_confirm = (
        "<b>📌 XIN Ý KIẾN CHỈ ĐẠO CỦA SẾP:</b>\n\n"
        "Em kính trình toàn bộ Kế hoạch nội dung tuần (trong file <code>KE_HOACH_NOI_DUNG_TUAN.md</code> ở trên) và 3 bản Poster thiết kế Pro.\n"
        "Sếp xem qua và nếu đồng ý, xin Sếp chỉ đạo <b>'OK'</b> hoặc <b>'DUYỆT'</b> ngay tại đây ạ!\n\n"
        "Sau khi Sếp duyệt, team Marketing sẽ tự động kích hoạt tiến trình đăng bài mỗi ngày lên đúng mạng lưới Fanpage theo đúng kế hoạch. Kính chúc Sếp ngày làm việc tràn đầy năng lượng ạ! 🙏"
    )
    r_conf = send_message(bot_token, chat_id, msg_confirm)
    if r_conf and r_conf.get("ok"):
        print(f"[OK] Đã gửi tin nhắn kết thúc xin phê duyệt! Msg ID: {r_conf.get('result', {}).get('message_id')}")

    print("[SUCCESS] Hoàn thành quy trình gửi duyệt Telegram!")


if __name__ == "__main__":
    main()
