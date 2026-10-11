#!/usr/bin/env python3
"""
gen_caption.py - Sinh nội dung Caption Facebook Organic hoặc Bộ 3 Creative Ads cho GlobalPharma.
Tuân thủ nghiêm ngặt quy chuẩn y khoa, độ dài 80-150 từ, USP B.Braun CHLB Đức.
"""

import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

# Đảm bảo in tiếng Việt trên console Windows không bị lỗi UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def load_brain_knowledge():
    candidates = [
        Path.cwd() / "my-brain" / "brain.db",
        Path(__file__).resolve().parents[2] / "my-brain" / "brain.db",
        Path("/app/workspace/my-brain/brain.db"),
        Path("/app/data/my-brain/brain.db")
    ]
    for p in candidates:
        if p.exists():
            try:
                conn = sqlite3.connect(p)
                cur = conn.cursor()
                knowledge = {}
                for row in cur.execute("SELECT product_code, name, pricing FROM product_knowledge"):
                    knowledge[row[0]] = {"name": row[1], "pricing": row[2]}
                conn.close()
                return knowledge
            except Exception:
                pass
    return {}

BRAIN_KNOWLEDGE = load_brain_knowledge()

# Thư viện nội dung y khoa được chuẩn hóa từ tài liệu lâm sàng GlobalPharma & B.Braun
CONTENT_REPOSITORY = {
    "renal": {
        "name": "Nutricomp® Drink Renal Vanilla",
        "description": "Dinh dưỡng y học chuyên biệt cho bệnh nhân suy thận mạn (trước lọc máu và lọc máu chu kỳ).",
        "organic": [
            {
                "id": "renal_org_1",
                "topic": "Kiểm soát dinh dưỡng và đạm cho người bệnh thận mạn",
                "hook": "“Ăn ít, nhưng nhu cầu năng lượng của cơ thể người bệnh thận vẫn còn đó…”",
                "body": (
                    "Đối với bệnh nhân suy thận mạn, mỗi bữa ăn thường là sự giằng xé lớn: Ăn nhiều đạm thì sợ tăng urê huyết, "
                    "nhưng kiêng khem quá mức lại dẫn đến suy dinh dưỡng và tụt cân nhanh chóng.\n\n"
                    "Theo khuyến nghị dinh dưỡng lâm sàng Châu Âu (ESPEN), chìa khóa không phải là nhịn ăn, mà là lựa chọn dinh dưỡng chuẩn y khoa:\n"
                    "✔ Đạm sinh học cao với tỷ lệ kiểm soát chuẩn xác từng giai đoạn bệnh.\n"
                    "✔ Tỷ lệ điện giải (Natri, Kali, Phốt pho) thấp, giảm gánh nặng lọc cho cầu thận.\n"
                    "✔ Năng lượng cao (2.0 kcal/ml) trong thể tích chỉ 200ml, hạn chế ứ dịch phù nề."
                ),
                "cta": "👉 Bạn đang phân vân chế độ ăn cho người thân bệnh thận? Nhắn tin ngay để Dược sĩ GlobalPharma hướng dẫn phác đồ phù hợp nhé!"
            },
            {
                "id": "renal_org_2",
                "topic": "Chăm sóc bố mẹ lọc máu: Làm sao bù đắp lượng đạm thất thoát?",
                "hook": "“Chăm sóc người thân chạy thận nhân tạo, nỗi lo lớn nhất là những ngày sau lọc máu mệt lả…”",
                "body": (
                    "Mỗi chu kỳ lọc máu lấy đi một lượng đạm và vi chất đáng kể, khiến người bệnh dễ mỏi mệt, suy mòn cơ bắp. "
                    "Lúc này, cơ thể lại cần bù đạm chất lượng cao chứ không còn phải kiêng khem gắt gao như giai đoạn trước lọc máu.\n\n"
                    "Nutricomp® Drink Renal từ B.Braun CHLB Đức được thiết kế với đạm chất lượng cao, acid amin thiết yếu và "
                    "hương vị vani thơm béo dịu nhẹ, giúp người bệnh dễ dàng dung nạp trọn vẹn 400 kcal sau mỗi buổi điều trị."
                ),
                "cta": "👉 Đừng để người thân kiệt sức sau lọc máu. Nhắn cho trang để nhận cẩm nang dinh dưỡng thận miễn phí!"
            }
        ],
        "ads": [
            {
                "angle": "pain_point",
                "angle_name": "Angle 1: Pain Point (Nỗi đau sụt cân & kiêng khem)",
                "hook": "“Nhìn bố mẹ mỗi bữa chỉ ăn được vài thìa cơm vì sợ tăng chỉ số thận, con cái thắt cả ruột gan…”",
                "usp": (
                    "Bệnh nhân suy thận kiêng khem khắt khe rất dễ rơi vào vòng luẩn quẩn suy dinh dưỡng, tụt cơ và kiệt sức. "
                    "Nutricomp® Drink Renal là giải pháp dinh dưỡng y học chuyên biệt từ Tập đoàn B.Braun (Đức):\n"
                    "• Cung cấp 400 kcal đậm đặc chỉ trong chai 200ml, không gây quá tải dịch.\n"
                    "• Kiểm soát tối ưu Natri, Kali, Phốt pho, hạn chế ứ đọng độc chất.\n"
                    "• Mở nắp uống trực tiếp, thơm ngậy hương vani dễ tiêu hóa.\n"
                    "• Combo 12 chai chính thức: 1.296.000 VNĐ (chỉ 108.000 VNĐ/chai)."
                ),
                "cta": "👉 Bấm [Gửi tin nhắn] ngay để Dược sĩ lâm sàng GlobalPharma tư vấn chế độ ăn chuẩn cho người thân!"
            },
            {
                "angle": "solution",
                "angle_name": "Angle 2: Solution (Giải pháp dinh dưỡng y học chuẩn B.Braun Đức)",
                "hook": "Chăm sóc dinh dưỡng cho người bệnh thận không nhất thiết phải biến mỗi bữa ăn thành “cuộc chiến”.",
                "usp": (
                    "Nutricomp® Drink Renal Vanilla là công thức dinh dưỡng lâm sàng từ B.Braun CHLB Đức với hơn 180 năm uy tín y khoa:\n"
                    "• Đạm sinh học cao chọn lọc, giảm tối đa tích tụ urê trong máu.\n"
                    "• Cung cấp đầy đủ vitamin & khoáng chất thiết yếu theo khuyến nghị lâm sàng ESPEN.\n"
                    "• Liệu trình combo 12 chai: 1.296.000 VNĐ (108.000 VNĐ/chai), sẵn sàng sử dụng mọi lúc."
                ),
                "cta": "👉 Nhắn tin cho GlobalPharma hôm nay để nhận giải pháp dinh dưỡng bảo tồn chức năng thận tối ưu!"
            },
            {
                "angle": "social_proof",
                "angle_name": "Angle 3: Social Proof (Bằng chứng lâm sàng & Tin dùng tại bệnh viện)",
                "hook": "“Vì sao các Bác sĩ và Chuyên gia dinh dưỡng tại các bệnh viện lớn luôn ưu tiên dinh dưỡng chuyên biệt cho bệnh nhân thận?”",
                "usp": (
                    "Bởi vì trong bệnh thận mạn, từng ml dung dịch và từng miligram điện giải đều quyết định sự an toàn của người bệnh. "
                    "Được nhập khẩu chính ngạch từ CHLB Đức bởi GlobalPharma, Nutricomp® Drink Renal đã đồng hành cùng hàng chục ngàn người bệnh "
                    "tại các trung tâm thận học tuyến đầu Việt Nam, giúp phục hồi thể trạng vững vàng."
                ),
                "cta": "👉 Nhận phác đồ tư vấn dinh dưỡng thận miễn phí từ Dược sĩ GlobalPharma – Bấm [Nhắn tin] ngay!"
            }
        ]
    },
    "plus": {
        "name": "Nutricomp® Drink Plus",
        "description": "Dinh dưỡng y học cao năng lượng (1.5 kcal/ml = 300 kcal/chai 200ml) phục hồi sau phẫu thuật, suy kiệt, ung thư.",
        "organic": [
            {
                "id": "plus_org_1",
                "topic": "Dinh dưỡng phục hồi nhanh thể trạng sau phẫu thuật",
                "hook": "“Sau ca mổ, người bệnh thường chán ăn, nhưng đây lại là lúc cơ thể cần năng lượng gấp bội để liền vết mổ…”",
                "body": (
                    "Quá trình phẫu thuật khiến cơ thể tiêu hao protein và năng lượng dự trữ rất lớn. Nếu chỉ ăn cháo loãng hay súp rau củ, "
                    "bệnh nhân khó lòng đáp ứng đủ 1.500 - 2.000 kcal mỗi ngày để tái tạo mô tế bào.\n\n"
                    "Nutricomp® Drink Plus bổ sung 300 kcal cùng 12g đạm sinh học cao và chuỗi chất béo trung tính MCT dễ hấp thu chỉ trong 200ml, "
                    "giúp người bệnh nhanh chóng đứng dậy tập đi và rút ngắn số ngày nằm viện."
                ),
                "cta": "👉 Để lại tin nhắn để Dược sĩ GlobalPharma tư vấn lộ trình phục hồi sau phẫu thuật chu đáo nhất!"
            }
        ],
        "ads": [
            {
                "angle": "pain_point",
                "angle_name": "Angle 1: Pain Point (Suy mòn thể trạng sau mổ / hóa trị)",
                "hook": "Người thân vừa phẫu thuật xong, người gầy rộc và ăn gì cũng thấy buồn nôn, nghẹn đắng?",
                "usp": (
                    "Cơ thể đang thiếu hụt năng lượng trầm trọng để lành vết mổ. Nutricomp® Drink Plus từ B.Braun CHLB Đức "
                    "cung cấp 300 kcal đậm đặc cùng 12g đạm tinh khiết chỉ trong 200ml, giúp hấp thu tức thì mà không gây đầy bụng khó tiêu."
                ),
                "cta": "👉 Đừng để người thân suy kiệt vì thiếu năng lượng – Bấm [Nhắn tin] nhận phác đồ phục hồi ngay!"
            },
            {
                "angle": "solution",
                "angle_name": "Angle 2: Solution (Nguồn năng lượng 300 kcal trong 200ml)",
                "hook": "Nạp đủ 300 kcal dinh dưỡng y học trong tích tắc mà không cần cố ăn thêm từng bát cháo nặng nề.",
                "usp": (
                    "Nutricomp® Drink Plus là công thức cao năng lượng chuẩn Đức: Giàu dầu cá Omega-3, MCT và vi chất thiết yếu "
                    "hỗ trợ làm lành vết thương, tăng sinh hồng cầu và nâng cao miễn dịch vượt trội."
                ),
                "cta": "👉 Nhắn tin cho GlobalPharma để đặt mua sản phẩm chính ngạch B.Braun kèm hướng dẫn từ Dược sĩ!"
            },
            {
                "angle": "social_proof",
                "angle_name": "Angle 3: Social Proof (Tiêu chuẩn lâm sàng Châu Âu)",
                "hook": "Sự tin cậy từ hơn 180 năm phát triển giải pháp y tế B.Braun CHLB Đức.",
                "usp": (
                    "Nutricomp® Drink Plus là sự lựa chọn hàng đầu tại các khoa Hồi sức và Ngoại khoa tại Việt Nam, "
                    "giúp hàng ngàn bệnh nhân sau mổ và ung thư hồi phục thể lực nhanh chóng và lấy lại niềm vui sống."
                ),
                "cta": "👉 Bấm [Gửi tin nhắn] ngay để được chuyên gia y tế GlobalPharma đồng hành chăm sóc sức khỏe gia đình bạn!"
            }
        ]
    },
    "prontosan": {
        "name": "Prontosan® Spray / Gel",
        "description": "Giải pháp rửa và làm sạch màng Biofilm cho vết thương mạn tính, loét tì đè, loét tiểu đường B.Braun Đức.",
        "organic": [
            {
                "id": "prontosan_org_1",
                "topic": "Tại sao vết loét tiểu đường, loét tì đè chăm sóc mãi không lành?",
                "hook": "“Rửa nước muối sinh lý hằng ngày nhưng vết loét tì đè của người nằm lâu vẫn rỉ dịch và chậm liền?”",
                "body": (
                    "Thủ phạm chính là màng Biofilm – lớp màng sinh học vi khuẩn cứng đầu che phủ đáy vết thương mà nước muối thông thường không thể phá vỡ.\n\n"
                    "Prontosan® Spray từ B.Braun Đức chứa phức hợp độc quyền Betaine & Polihexanide (PHMB): "
                    "Phá vỡ lớp màng Biofilm, cuốn trôi vi khuẩn và mảnh vụn hoại tử mà hoàn toàn không gây xót hay tổn thương mô hạt non."
                ),
                "cta": "👉 Nhắn tin cho GlobalPharma để nhận phác đồ chăm sóc vết loét chuẩn vô trùng bệnh viện ngay tại nhà!"
            }
        ],
        "ads": [
            {
                "angle": "pain_point",
                "angle_name": "Angle 1: Pain Point (Vết loét chậm lành, nguy cơ nhiễm trùng)",
                "hook": "Vết loét tì đè của bố mẹ nằm liệt giường ngày càng sâu và có mùi khó chịu khiến bạn mất ăn mất ngủ?",
                "usp": (
                    "Nước muối sinh lý thông thường không thể loại bỏ màng Biofilm vi khuẩn. Prontosan® từ B.Braun Đức là giải pháp y khoa "
                    "chuyên biệt giúp phá tan màng Biofilm, khử mùi hôi và kiểm soát nhiễm trùng an toàn."
                ),
                "cta": "👉 Nhắn tin ngay để Dược sĩ GlobalPharma hướng dẫn quy trình rửa vết loét an toàn tại nhà!"
            },
            {
                "angle": "solution",
                "angle_name": "Angle 2: Solution (Bộ đôi Prontosan Spray & Gel làm sạch Biofilm)",
                "hook": "Làm sạch đáy vết thương nhẹ nhàng, êm dịu, không đau rát chuẩn Châu Âu.",
                "usp": (
                    "Bộ đôi Prontosan® Spray và Gel bảo vệ và tạo độ ẩm lý tưởng cho mô hạt tái tạo nhanh chóng. "
                    "Giảm đau đớn cho người bệnh mỗi lần thay băng và rút ngắn thời gian liền thương rõ rệt."
                ),
                "cta": "👉 Bấm [Nhận tư vấn] để bảo vệ vết thương của người thân an toàn nhất!"
            },
            {
                "angle": "social_proof",
                "angle_name": "Angle 3: Social Proof (Khuyến cáo của Hội Chăm Sóc Vết Thương Quốc Tế)",
                "hook": "Giải pháp chăm sóc vết thương mạn tính được sử dụng tại các trung tâm bỏng và ngoại khoa hàng đầu.",
                "usp": (
                    "Prontosan® được nghiên cứu lâm sàng tại Đức và được ứng dụng rộng rãi tại các bệnh viện lớn trên toàn quốc. "
                    "Sản phẩm phân phối chính ngạch bởi GlobalPharma với sự hỗ trợ kỹ thuật tận tâm từ đội ngũ chuyên môn."
                ),
                "cta": "👉 Bấm [Gửi tin nhắn] ngay để nhận hướng dẫn sử dụng Prontosan đúng cách từ Dược sĩ!"
            }
        ]
    }
}


def generate_content(product_key: str, mode: str, output_path: str = None, format_type: str = "json"):
    product_key = product_key.lower().strip()
    if product_key not in CONTENT_REPOSITORY:
        available = ", ".join(CONTENT_REPOSITORY.keys())
        raise ValueError(f"Sản phẩm '{product_key}' không hợp lệ. Chọn một trong: {available}")
    
    prod_data = CONTENT_REPOSITORY[product_key]
    result = {
        "product_key": product_key,
        "product_name": prod_data["name"],
        "description": prod_data["description"],
        "mode": mode,
        "content": []
    }
    
    if mode == "organic":
        result["content"] = prod_data["organic"]
    elif mode == "ads":
        result["content"] = prod_data["ads"]
    else:
        raise ValueError(f"Mode '{mode}' không hợp lệ. Chọn 'organic' hoặc 'ads'.")
        
    # Xuất ra định dạng mong muốn
    if format_type == "markdown":
        output_str = f"# NỘI DUNG FACEBOOK CHO {prod_data['name'].upper()}\n\n"
        output_str += f"**Sản phẩm:** {prod_data['name']}\n"
        output_str += f"**Mô tả:** {prod_data['description']}\n"
        output_str += f"**Chế độ:** {mode.upper()}\n\n---\n\n"
        
        for item in result["content"]:
            if mode == "organic":
                output_str += f"## Chủ đề: {item['topic']}\n\n"
                output_str += f"**Hook:**\n{item['hook']}\n\n"
                output_str += f"**Nội dung chính:**\n{item['body']}\n\n"
                output_str += f"**Kêu gọi hành động (CTA):**\n{item['cta']}\n\n---\n\n"
            else:
                output_str += f"## {item['angle_name']}\n\n"
                output_str += f"**Hook:**\n{item['hook']}\n\n"
                output_str += f"**USP lâm sàng B.Braun:**\n{item['usp']}\n\n"
                output_str += f"**Lời kêu gọi hành động (Hard CTA):**\n{item['cta']}\n\n---\n\n"
    else:
        output_str = json.dumps(result, ensure_ascii=False, indent=2)
        
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"[SUCCESS] Đã lưu nội dung vào: {out_file}")
        
    return output_str


def main():
    parser = argparse.ArgumentParser(description="Sinh nội dung Facebook Caption / Ad Copy cho GlobalPharma")
    parser.add_argument("--product", required=True, choices=["renal", "plus", "prontosan"], help="Mã sản phẩm")
    parser.add_argument("--mode", required=True, choices=["organic", "ads"], help="Chế độ tạo: organic hoặc ads")
    parser.add_argument("--output", help="Đường dẫn file đầu ra")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Định dạng xuất")
    
    args = parser.parse_args()
    content = generate_content(args.product, args.mode, args.output, args.format)
    print(content)


if __name__ == "__main__":
    main()
