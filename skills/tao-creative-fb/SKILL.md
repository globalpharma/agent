---
name: tao-creative-fb
description: Tạo nội dung toàn diện (hình ảnh chuẩn y khoa + caption/ad copy) cho Facebook Fanpage và Facebook Ads của GlobalPharma. Hỗ trợ 2 chế độ: Chế độ 1 (Content Organic đăng tự động qua Graph API với DRY_RUN) và Chế độ 2 (Creative Ads 3 cặp Pain Point, Solution, Social Proof chuẩn bị cho Trình quản lý quảng cáo).
license: MIT
metadata:
  author: GlobalPharma AI Team
  version: "1.0.0"
  company: "Công Ty Cổ Phần Global Pharma"
  founder: "Anh Công Hùng"
  brand: "GlobalPharma & B.Braun CHLB Đức"
---

# Tao Creative Facebook - GlobalPharma (Level 3 Skill)

Skill cấp 3 chuyên trách sản xuất toàn diện nội dung Facebook (Hình ảnh + Caption/Ad Copy) cho **Công Ty Cổ Phần Global Pharma**, hỗ trợ các dòng sản phẩm y học lâm sàng B.Braun:
1. **Nutricomp® Drink Renal Vanilla:** Dinh dưỡng y học chuyên biệt cho bệnh nhân suy thận mạn (trước lọc máu và lọc máu chu kỳ).
2. **Nutricomp® Drink Plus:** Dinh dưỡng cao năng lượng (1.5 kcal/ml, 300 kcal/chai) phục hồi sau phẫu thuật, suy kiệt, ung thư.
3. **Prontosan Spray / Gel:** Rửa và chăm sóc vết thương mạn tính, phá vỡ màng Biofilm, ngừa nhiễm trùng cho vết loét tì đè, loét đái tháo đường.

---

## 1. Nguyên Tắc Cốt Lõi Về Brand Voice & Y Khoa

- **Doanh nghiệp:** Công Ty Cổ Phần Global Pharma (thành lập từ 2014, phân phối chính ngạch B.Braun CHLB Đức). Người sáng lập: **Anh Công Hùng**.
- **Chuẩn mực y khoa:** Thông tin y khoa chính xác, khách quan, dựa trên chứng cứ lâm sàng Châu Âu (ESPEN, B.Braun).
- **Đạo đức ngành y:** 
  - KHÔNG cam kết "chữa khỏi suy thận", "thuốc điều trị thận", hay "làm lành vết thương tức thì".
  - Định vị sản phẩm là: **Dinh dưỡng y học lâm sàng** bổ sung chuyên biệt theo từng bệnh lý, giúp bảo tồn chức năng thận, phục hồi thể trạng, hoặc dung dịch rửa vết thương chuẩn vô trùng.
- **Tone & Mood:** Đĩnh đạc, thấu hiểu, khoa học, tin cậy, ấm áp và hướng đến sức khỏe bền vững của người bệnh.

---

## 2. Hai Chế Độ Vận Hành

### 🌿 Chế độ 1: Content Free / Organic (Bài đăng thường nhật)
Mục tiêu: Cung cấp kiến thức chăm sóc sức khỏe, nuôi dưỡng tệp người theo dõi trang fanpage GlobalPharma.

**Quy trình 5 bước:**
1. **Đề xuất ý tưởng:** Đề xuất 3 chủ đề giáo dục sức khỏe/dinh dưỡng (tiêu đề + góc tiếp cận) dựa trên sản phẩm được yêu cầu.
2. **Người dùng chọn:** Chờ người dùng chọn 1 trong 3 ý tưởng.
3. **Sinh nội dung (BẮT BUỘC TẠO CẢ CAPTION LẪN HÌNH ẢNH TRONG CÙNG LƯỢT):**
   Ngay khi người dùng chọn 1 ý tưởng, bạn BẮT BUỘC thực hiện ĐỒNG THỜI cả hai việc trong cùng lượt trả lời này:
   - **Viết Caption (80–150 từ):** Gồm [Hook y khoa / thấu cảm] + [Kiến thức dinh dưỡng / cơ chế sản phẩm B.Braun] + [Soft CTA tư vấn hoặc chia sẻ].
   - **BẮT BUỘC GỌI TOOL `create_image` ĐỂ TẠO ẢNH:**
     Bạn PHẢI gọi công cụ `create_image(prompt: "...")` với prompt chi tiết mô tả hình ảnh y khoa chân thực, ấm áp, ánh sáng studio y tế, sản phẩm B.Braun chính hãng.
     ⚠️ **CẢNH BÁO QUAN TRỌNG:** TUYỆT ĐỐI KHÔNG được chỉ mô tả ý tưởng ảnh bằng lời văn hay chỉ trả về mỗi bài caption. BẮT BUỘC PHẢI GỌI TOOL `create_image` để tạo ra file ảnh thực tế!
4. **Xem trước (Preview):** Hiển thị đầy đủ cả bài viết Caption và bức ảnh vừa sinh (kèm cú pháp `MEDIA:<đường dẫn ảnh>`) để người dùng xem trước trọn vẹn cả bài lẫn ảnh.
5. **Đăng bài THÔNG MINH theo dòng sản phẩm (Product-Aware Broadcasting):**
   - Danh sách Fanpage được phân loại theo `product_group` (`nutricomp`, `prontosan`, hoặc `all`) trong `skills/tao-creative-fb/pages.json`.
   - **Tự động nhận diện dòng sản phẩm:** Script `scripts/post_facebook.py` tự động phân tích caption hoặc cờ `--product [nutricomp|prontosan|all|auto]`:
     - **Bài viết Nutricomp:** Tự động điều hướng đăng lên toàn bộ các Page chuyên biệt về sữa/dinh dưỡng Nutricomp + Page chung **Sức Khỏe Cho Mọi Nhà**.
     - **Bài viết Prontosan:** Tự động điều hướng đăng lên toàn bộ các Page chuyên biệt về chăm sóc/làm lành vết thương Prontosan + Page chung **Sức Khỏe Cho Mọi Nhà**.
     - **Page "Sức Khỏe Cho Mọi Nhà":** Là trang sức khỏe cộng đồng chung của GlobalPharma, tiếp nhận đăng song song cả bài viết Nutricomp lẫn Prontosan.
   - **Cơ chế chống Spam:** Tự động giãn cách 2 giây giữa mỗi Page để bảo vệ tài khoản khỏi thuật toán chống spam của Facebook.
   - **Tính chịu lỗi:** Nếu 1 trang bị lỗi (hết hạn token), script vẫn tiếp tục đăng bình thường cho các trang còn lại và xuất bảng báo cáo chi tiết từng page.
   - Hỗ trợ cờ `--dry-run` để kiểm thử toàn diện danh sách page mà không post thật.

---

### 🎯 Chế độ 2: Creative Ads (Bộ nội dung quảng cáo chuyển đổi)
Mục tiêu: Tạo bộ tài nguyên hoàn chỉnh gồm 3 cặp (Ảnh + Copy) phục vụ chạy chiến dịch quảng cáo Facebook Ads. **Tuyệt đối KHÔNG đăng tự động lên page.**

**Quy trình:**
Sinh đồng thời 3 bộ Creative theo 3 góc tiếp cận khác biệt:
- **Angle 1 - Pain Point (Nỗi đau):** Tập trung vào khó khăn trong ăn uống, sút cân, sự khắt khe của chế độ ăn kiêng thận, nỗi lo biến chứng hoặc mệt mỏi sau mổ.
- **Angle 2 - Solution (Giải pháp y học B.Braun):** Nhấn mạnh công thức chuyên biệt từ CHLB Đức, cân đối vi chất, tiện lợi mở nắp uống liền 200ml, bù đắp năng lượng chuẩn xác.
- **Angle 3 - Social Proof / Bằng chứng lâm sàng:** Độ tin cậy từ tập đoàn B.Braun 180+ năm lịch sử, tiêu chuẩn Châu Âu, được tin dùng tại các bệnh viện lớn và niềm tin của người nhà chăm sóc.

**Mỗi cặp Creative gồm:**
- **Hình ảnh quảng cáo:** Tỉ lệ 1:1 (1024x1024) hoặc 4:5, thiết kế có **khoảng trống sạch (negative space)** ở góc trên hoặc một bên để tiện chèn tiêu đề quảng cáo (headline).
- **Ad Copy (80–150 từ):**
  - **Hook:** Gây ấn tượng trực diện với người bệnh hoặc người thân chăm sóc.
  - **USP lâm sàng:** Điểm vượt trội về công thức hoặc chứng nhận của B.Braun Đức.
  - **Hard CTA:** Lời kêu gọi hành động dứt khoát: "Nhắn tin ngay để Dược sĩ GlobalPharma tư vấn chế độ dinh dưỡng phù hợp", "Để lại bình luận nhận tài liệu hướng dẫn".

Toàn bộ 3 cặp được lưu vào thư mục `output/creative_ads/` và hiển thị bản tổng hợp Markdown cho người dùng tải về đưa vào Ads Manager.

---

## 3. Cấu Trúc Tài Nguyên Skill

```
skills/tao-creative-fb/
├── SKILL.md                          # File hướng dẫn trung tâm
├── assets/
│   ├── image-prompt-templates.md     # Mẫu prompt chi tiết cho hình ảnh Organic & Ads
│   └── caption-templates.md          # Mẫu cấu trúc copywriting chuẩn y khoa
└── scripts/
    ├── env.example                   # File mẫu cấu hình API keys
    ├── gen_image.py                  # Script gọi OpenAI DALL-E / gpt-image
    ├── gen_caption.py                # Script sinh caption & ad copy theo góc tiếp cận
    └── post_facebook.py              # Script đăng ảnh & caption qua Graph API (có DRY_RUN)
```

---

## 4. Cơ Chế Kết Nối Provider & Thực Thi

Skill hỗ trợ 2 phương thức vận hành linh hoạt:

### 🌟 Cách 1: Chạy trực tiếp qua Agent GoClaw (Khuyến nghị - Không cần nhập lại OpenAI Key)
Khi anh chat trực tiếp với Agent trên hệ thống GoClaw (`agent.globalpharma.vn`):
1. **Trí thông minh & Viết bài:** Agent dùng **chính tài khoản GPT đã kết nối trong menu "Providers"** của GoClaw để sáng tạo nội dung, lựa chọn angle và viết caption y khoa.
2. **Sinh hình ảnh:** Agent gọi trực tiếp công cụ tích hợp sẵn `create_image` của GoClaw. Công cụ này tự động điều hướng qua Provider GPT/OpenAI đã nối sẵn trong hệ thống để tạo ảnh y tế chuẩn và lưu vào workspace.
3. **Đăng Facebook:** Chỉ cần cấu hình `FB_PAGE_ID` và `FB_PAGE_TOKEN` để kết nối Fanpage (hoặc truyền qua chat).
👉 **Anh hoàn toàn KHÔNG CẦN nhập lại `OPENAI_API_KEY`!**

---

### 💻 Cách 2: Chạy độc lập bằng Script Python (Dành cho Developer / Tự động hóa ngoài Terminal)
Khi chạy độc lập ngoài dòng lệnh không qua Agent:
- Cấu hình file `.env` (theo mẫu `scripts/env.example`):
  ```bash
  OPENAI_API_KEY="sk-..."       # Khóa OpenAI riêng cho script Python
  FB_PAGE_ID="your_page_id"
  FB_PAGE_TOKEN="EAAV..."
  DRY_RUN=true                 # Test mô phỏng an toàn
  ```
- Lệnh chạy:
  ```bash
  # Sinh caption / 3 angles:
  python scripts/gen_caption.py --mode ads --product renal

  # Sinh ảnh độc lập:
  python scripts/gen_image.py --prompt "..." --output "output/sample.png"

  # Đăng Facebook:
  python scripts/post_facebook.py --image "output/sample.png" --caption "..."
  ```

---

## 5. Chiến Lược Nội Dung Riêng Kênh Affiliate - GlobalPharma (ID: 1183558371496517)

Fanpage **Affiliate - GlobalPharma** là kênh chiến lược chuyên biệt, vận hành theo quy tắc riêng biệt:
1. **NGUYÊN TẮC CÁCH LY:** Tuyệt đối KHÔNG đăng các bài giới thiệu sản phẩm sữa Nutricomp và gel/dung dịch Prontosan lên kênh này.
2. **ĐỊNH HƯỚNG NỘI DUNG (KHI ĐƯỢC YÊU CẦU CONTENT PLAN CHO KÊNH AFFILIATE):**
   - **Đối tượng mục tiêu:** Dược sĩ đứng quầy, Personal Trainer (PT), chuyên gia dinh dưỡng, nhân sự y tế, huấn luyện viên sức khỏe, và những người quan tâm đến việc gia tăng thu nhập từ kiến thức sức khỏe.
   - **Triết lý cốt lõi:** **Trao giá trị - Mô hình Kinh Doanh Một Người (Solopreneur) & Affiliate Marketing ngành y tế.**
   - **Chủ đề trụ cột:**
     - Tận dụng chuyên môn y dược / sức khỏe để xây dựng uy tín cá nhân và tạo dòng tiền thứ 2.
     - Mô hình phân phối sản phẩm chính ngạch Châu Âu không ôm hàng, không rủi ro vốn.
     - Đạo đức kinh doanh và nâng tầm giá trị tư vấn sức khỏe cho cộng đồng.
   - **Tone & Mood:** Tinh tế, trí tuệ, truyền cảm hứng, phong thái chuyên nghiệp. **Tuyệt đối KHÔNG** viết dạng tuyển dụng lộ liễu, đa cấp, chèo kéo hay giật gân.

