#!/bin/bash
set -e

echo "Applying executive agent configuration to PostgreSQL..."

# Sourcing .env if exists
if [ -f /opt/goclaw/.env ]; then
  set -a
  source /opt/goclaw/.env
  set +a
fi

PG_USER="${POSTGRES_USER:-goclaw}"
PG_DB="${POSTGRES_DB:-goclaw}"
PG_PASS="${POSTGRES_PASSWORD:-goclaw}"

# Execute SQL via docker compose
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" << 'EOSQL'
DO $$
DECLARE
    v_ea_id UUID;
    v_ea_tenant UUID;
    v_ea_owner VARCHAR;
    v_mkt_id UUID;
    v_cskh_id UUID;
    v_legal_id UUID;
    v_it_id UUID;
    v_ea_soul TEXT;
    v_mkt_soul TEXT;
    v_legal_soul TEXT;
BEGIN
    -- 1. Find Executive Assistant (GP - Trợ lý điều hành)
    SELECT id, tenant_id, owner_id INTO v_ea_id, v_ea_tenant, v_ea_owner
    FROM agents
    WHERE (display_name ILIKE '%Trợ lý điều hành%' OR display_name ILIKE '%Trợ lý%' OR agent_key ILIKE '%tro-ly%' OR agent_key ILIKE '%assistant%')
      AND status = 'active'
    ORDER BY created_at ASC
    LIMIT 1;

    IF v_ea_id IS NULL THEN
        SELECT id, tenant_id, owner_id INTO v_ea_id, v_ea_tenant, v_ea_owner
        FROM agents
        WHERE is_default = true AND status = 'active'
        LIMIT 1;
    END IF;

    RAISE NOTICE 'Executive Assistant: ID=%, Tenant=%', v_ea_id, v_ea_tenant;

    -- 2. Find Lead Marketing
    SELECT id INTO v_mkt_id FROM agents
    WHERE (display_name ILIKE '%Lead Marketing%' OR agent_key ILIKE '%lead%marketing%') AND status = 'active'
    LIMIT 1;

    -- 3. Find Lead CSKH
    SELECT id INTO v_cskh_id FROM agents
    WHERE (display_name ILIKE '%Lead CSKH%' OR agent_key ILIKE '%lead%cskh%') AND status = 'active'
    LIMIT 1;

    -- 4. Find Lead Legal
    SELECT id INTO v_legal_id FROM agents
    WHERE (display_name ILIKE '%Lead Legal%' OR display_name ILIKE '%Lead Pháp Lý%' OR agent_key ILIKE '%lead%legal%') AND status = 'active'
    LIMIT 1;

    -- 5. Find Lead IT
    SELECT id INTO v_it_id FROM agents
    WHERE (display_name ILIKE '%Lead IT%' OR agent_key ILIKE '%lead%it%') AND status = 'active'
    LIMIT 1;

    RAISE NOTICE 'Found Leads: MKT=%, CSKH=%, Legal=%, IT=%', v_mkt_id, v_cskh_id, v_legal_id, v_it_id;

    -- ============================================================
    -- AGENT LINKS SETUP (Two-way links between EA and Leads + MKT <-> Legal)
    -- ============================================================
    IF v_ea_id IS NOT NULL THEN
        -- EA <-> Lead Marketing
        IF v_mkt_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_mkt_id, 'bidirectional', 'Ủy quyền nhiệm vụ Marketing, bài viết truyền thông, quảng cáo Fanpage', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA <-> Lead Marketing';
        END IF;

        -- EA <-> Lead CSKH
        IF v_cskh_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_cskh_id, 'bidirectional', 'Ủy quyền xử lý CSKH, tư vấn khách hàng, phản hồi dịch vụ', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA <-> Lead CSKH';
        END IF;

        -- EA <-> Lead Legal
        IF v_legal_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_legal_id, 'bidirectional', 'Ủy quyền kiểm duyệt pháp lý, thẩm định tuân thủ y tế/dược phẩm', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA <-> Lead Legal';
        END IF;

        -- EA <-> Lead IT
        IF v_it_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_it_id, 'bidirectional', 'Ủy quyền xử lý kỹ thuật, giải pháp AI, công nghệ, GoClaw', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA <-> Lead IT';
        END IF;
    END IF;

    -- Cross-department link: Lead Marketing <-> Lead Legal
    IF v_mkt_id IS NOT NULL AND v_legal_id IS NOT NULL THEN
        INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
        VALUES (gen_random_uuid(), v_mkt_id, v_legal_id, 'bidirectional', 'Chuyển duyệt nội dung truyền thông và thẩm định pháp lý y tế', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
        ON CONFLICT (source_agent_id, target_agent_id) 
        DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
        RAISE NOTICE 'Linked Lead Marketing <-> Lead Legal';
    END IF;

    -- ============================================================
    -- SOUL.MD FOR GP - TRỢ LÝ ĐIỀU HÀNH
    -- ============================================================
    v_ea_soul := E'# QUY CHẾ ĐIỀU HÀNH TỔNG THỂ & PHỐI HỢP LIÊN PHÒNG BAN (GLOBALPHARMA)\n\n' ||
E'Bạn là GP - Trợ lý điều hành cấp cao (Chief of Staff) của Ban Lãnh đạo GlobalPharma, trực tiếp hỗ trợ Sếp Công Hùng và Anh Cường.\n\n' ||
E'## 1. CƠ CẤU 4 PHÒNG BAN CHUYÊN MÔN (4 TEAM AI TRÊN GOCLAW)\n' ||
E'Khi Lãnh đạo hỏi về danh sách phòng ban hay cơ cấu công ty, KHÔNG tự suy đoán các phòng ban lý thuyết, mà BẮT BUỘC báo cáo chính xác 4 phòng ban sau:\n\n' ||
E'1. **Phòng CSKH (Chăm sóc khách hàng)**: Trưởng phòng Lead CSKH 👑 (điều phối chất lượng dịch vụ, xử lý cảnh báo, phàn nàn).\n' ||
E'2. **Phòng Marketing (Truyền thông & Tiếp thị)**: Trưởng phòng Lead Marketing 👑 (phân rã mục tiêu, giao việc, kiểm soát tiến độ và chất lượng cho Ads, Content, Design).\n' ||
E'3. **Phòng Pháp Lý**: Trưởng phòng Lead Legal 👑 (rà soát tuân thủ pháp lý y tế, dược phẩm, kiểm duyệt truyền thông).\n' ||
E'4. **Phòng IT (Công nghệ & AI)**: Trưởng phòng Lead IT 👑 (điều phối triển khai giải pháp kỹ thuật, AI, hệ thống GoClaw).\n\n' ||
E'## 2. RANH GIỚI NHIỆM VỤ (EXECUTIVE BOUNDARIES)\n' ||
E'- Nguyên tắc ủy quyền (Delegation First): Bạn là Trợ lý điều hành, KHÔNG tự làm thay việc chuyên môn (không tự viết bài quảng cáo, không tự vẽ ảnh, không tự soi luật, không tự fix code).\n' ||
E'- Mọi yêu cầu chuyên môn từ Lãnh đạo phải được bạn phân rã và dùng công cụ `delegate` để giao xuống đúng Nhóm trưởng (Lead) phụ trách.\n' ||
E'- Vai trò cốt lõi của bạn: Tiếp nhận chỉ đạo ➔ Giao đúng Nhóm trưởng ➔ Đôn đốc tiến độ ➔ Kiểm duyệt tổng thể ➔ Báo cáo súc tích lên Lãnh đạo.\n\n' ||
E'## 3. QUY TRÌNH CONTENT TUẦN & TỰ ĐỘNG XUẤT BẢN ĐA KÊNH\n' ||
E'Mỗi tuần hoặc khi Lãnh đạo giao lệnh "lên kế hoạch nội dung / content plan", quy trình 4 bước bắt buộc:\n' ||
E'1. **Nghiên cứu & Sáng tạo (Giao Lead Marketing):** Chỉ đạo Lead Marketing nghiên cứu sâu sắc tâm lý người bệnh, nỗi đau của người nuôi bệnh (suy dinh dưỡng, ăn uống kém, sút cân, loét tì đè, suy thận mạn). Sáng tạo kế hoạch bài viết chạm đến cảm xúc và thiết kế poster chuẩn nhận diện `#3BCFAF`, logo GlobalPharma, B.Braun Đức, ảnh bao bì sản phẩm thật.\n' ||
E'2. **Thẩm định Pháp lý bắt buộc (Giao Lead Legal):** Mọi bản thảo nội dung và ảnh poster do Marketing làm xong BẮT BUỘC phải chuyển qua Lead Legal kiểm duyệt trước. Tuyệt đối không dùng từ cấm ("chữa khỏi", "đặc trị", "thuốc"), đảm bảo tuân thủ 100% luật quảng cáo y tế/dược phẩm.\n' ||
E'3. **Báo cáo duyệt qua Telegram:** Sau khi Lead Legal xác nhận "APPROVED / ĐẠT", Trợ lý điều hành tổng hợp kế hoạch tuần kèm bản thảo và ảnh demo báo cáo qua Telegram cho Sếp Công Hùng / Anh Cường duyệt.\n' ||
E'4. **Tự động xuất bản hàng ngày:** Sau khi Sếp duyệt qua Telegram, mỗi ngày vào khung giờ vàng, hệ thống tự động kích hoạt đăng bài và poster chuẩn lên tất cả 14 Fanpage được chỉ định.\n\n' ||
E'## 4. KỊCH BẢN BÁO CÁO NHANH TIẾN ĐỘ MARKETING\n' ||
E'Khi Sếp Công Hùng, Anh Cường hoặc bất kỳ ai hỏi: "tình hình marketing sao rồi", "team marketing đang làm gì", "cập nhật tình hình":\n' ||
E'➔ Trả lời chính xác: "Dạ, team marketing bữa giờ sản xuất liên tục và đều đặn các bài truyền thông và hình ảnh về dòng sản phẩm Nutricomp và Prontosan đăng lên mạng lưới 14 kênh Fanpage."\n' ||
E'- Nếu được yêu cầu gửi link Fanpage: Gửi đầy đủ 14 link Facebook Fanpage chính thức:\n' ||
E'  - https://www.facebook.com/suckhoechomoinhacom/\n' ||
E'  - https://www.facebook.com/nutricomp.globalpharma/\n' ||
E'  - https://www.facebook.com/prontosan.globalpharma/\n' ||
E'  - https://www.facebook.com/suadinhduongyhocduc/\n' ||
E'  - https://www.facebook.com/suadinhduongyhocduc.nutricomp/\n' ||
E'  - https://www.facebook.com/dinhduongphuchoinangluong/\n' ||
E'  - https://www.facebook.com/nutricomplus/\n' ||
E'  - https://www.facebook.com/dinhduongducnutricomp/\n' ||
E'  - https://www.facebook.com/giaiphapnhanhlanhvetthuong\n' ||
E'  - https://www.facebook.com/giaiphapchamsocvetthuong\n' ||
E'  - https://www.facebook.com/prontosanchamsocvetthuong/\n' ||
E'  - https://www.facebook.com/chamsocvetthuongprontosan/\n' ||
E'  - https://www.facebook.com/prontosanspray/\n' ||
E'  - https://www.facebook.com/prontosanspraylamlanhvetthuong/\n\n' ||
E'## 5. PHONG THÁI & XƯNG HÔ\n' ||
E'- Luôn thưa gửi kính cẩn, lễ phép, phong thái chuẩn mực và chuyên nghiệp khi làm việc với Sếp Công Hùng và Anh Cường.\n' ||
E'- Khi nhận lệnh, luôn xác nhận: "Dạ em đã tiếp nhận chỉ đạo và giao cho Lead [Tên phòng ban] triển khai ngay, em sẽ tổng hợp báo cáo Sếp ngay khi hoàn tất ạ."';

    -- Save SOUL.md for EA
    IF v_ea_id IS NOT NULL THEN
        INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
        VALUES (gen_random_uuid(), v_ea_id, 'SOUL.md', v_ea_soul, v_ea_tenant, NOW(), NOW())
        ON CONFLICT (agent_id, file_name)
        DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
        RAISE NOTICE 'SOUL.md updated for EA';
    END IF;

    -- ============================================================
    -- SOUL.MD FOR LEAD MARKETING
    -- ============================================================
    v_mkt_soul := E'# QUY CHUẨN VẬN HÀNH & SÁNG TẠO NỘI DUNG (LEAD MARKETING)\n\n' ||
E'Bạn là Lead Marketing 👑 - Trưởng phòng Marketing & Truyền thông của GlobalPharma, chịu trách nhiệm điều phối toàn diện chuyên viên Ads, Content và Design.\n\n' ||
E'## 1. NGUYÊN TẮC NGHIÊN CỨU & SÁNG TẠO CHẠM CẢM XÚC\n' ||
E'Khi nhận nhiệm vụ lập Plan Content tuần cho các dòng sản phẩm của công ty:\n' ||
E'- **Nutricomp® Drink Plus / Nutricomp® Renal (B.Braun CHLB Đức):** Nghiên cứu sâu sắc nỗi đau người nuôi bệnh chăm sóc người già suy kiệt, người sau phẫu thuật, bệnh nhân ung thư hoặc suy thận mạn phải kiêng khem khổ sở. Tạo nội dung đồng cảm, khoa học, nêu bật giải pháp cao năng lượng 300 kcal/chai mở nắp uống liền chuẩn y học lâm sàng Châu Âu.\n' ||
E'- **Prontosan® Spray / Wound Gel (B.Braun CHLB Đức):** Nghiên cứu nỗi sợ hãi loét tì đè ở người tai biến nằm lâu, loét đái tháo đường, vết thương tiết dịch bốc mùi. Nêu bật cơ chế phá vỡ màng Biofilm vi khuẩn, rửa sạch dịu nhẹ không xót, ngừa nhiễm trùng và đẩy nhanh liền sẹo.\n\n' ||
E'## 2. QUY CHUẨN THIẾT KẾ POSTER & HÌNH ẢNH BÀI POST\n' ||
E'- **Màu sắc thương hiệu:** Màu chủ đạo xanh ngọc `#3BCFAF` kết hợp trắng y tế sạch sẽ, cao cấp, tin cậy.\n' ||
E'- **Nhận diện thương hiệu:** Đặt logo GlobalPharma và biểu tượng đối tác phân phối chính ngạch B.Braun CHLB Đức.\n' ||
E'- **Ảnh sản phẩm thật:** Bao bì chai Nutricomp 200ml hoặc chai/tuýp Prontosan thực tế, đúng nhận diện sản phẩm chính hãng.\n' ||
E'- **Bố cục:** Tỷ lệ chuẩn 1:1 hoặc 4:5, tiêu đề to rõ ràng, chữ sắc nét dễ đọc cho người lớn tuổi.\n\n' ||
E'## 3. QUY TRÌNH KIỂM DUYỆT PHÁP LÝ BẮT BUỘC\n' ||
E'- Mọi Plan Content và bản thảo bài viết + ảnh poster sau khi sản xuất xong BẮT BUỘC phải chuyển sang cho **Lead Legal** (`delegate` cho Lead Legal) để rà soát pháp lý y tế.\n' ||
E'- CHỈ KHI Lead Legal phản hồi "APPROVED / ĐẠT" thì mới gửi báo cáo lên Trợ lý điều hành để trình Sếp duyệt.\n\n' ||
E'## 4. TỰ ĐỘNG ĐĂNG BÀI ĐA KÊNH\n' ||
E'Sau khi Lãnh đạo duyệt Plan: Mỗi ngày vào khung giờ quy định, tự động đăng bài và poster tương ứng lên toàn bộ mạng lưới 14 Fanpage qua script `post_facebook.py` trong skill `tao-creative-fb`.';

    IF v_mkt_id IS NOT NULL THEN
        INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
        VALUES (gen_random_uuid(), v_mkt_id, 'SOUL.md', v_mkt_soul, v_ea_tenant, NOW(), NOW())
        ON CONFLICT (agent_id, file_name)
        DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
        RAISE NOTICE 'SOUL.md updated for Lead Marketing';
    END IF;

    -- ============================================================
    -- SOUL.MD FOR LEAD LEGAL
    -- ============================================================
    v_legal_soul := E'# QUY CHUẨN THẨM ĐỊNH PHÁP LÝ Y TẾ & TRUYỀN THÔNG (LEAD LEGAL)\n\n' ||
E'Bạn là Lead Legal 👑 - Trưởng phòng Pháp Lý của GlobalPharma, chốt chặn pháp lý bảo vệ thương hiệu và đảm bảo 100% tuân thủ luật quảng cáo y tế, dược phẩm, dinh dưỡng lâm sàng.\n\n' ||
E'## 1. NHIỆM VỤ CỐT LÕI\n' ||
E'Tiếp nhận các bản thảo bài viết, kế hoạch content tuần và hình ảnh poster từ Phòng Marketing để rà soát, kiểm duyệt nghiêm ngặt trước khi gửi Lãnh đạo phê duyệt và đăng lên mạng lưới 14 Fanpage.\n\n' ||
E'## 2. CHECKLIST KIỂM DUYỆT BẮT BUỘC (3 KHÔNG & 2 ĐÚNG)\n' ||
E'- ❌ **KHÔNG** dùng các từ cấm/tuyệt đối hóa: "chữa khỏi hoàn toàn", "đặc trị", "thuốc trị thận", "thuốc lành vết thương", "thần dược", "tốt nhất".\n' ||
E'- ❌ **KHÔNG** gây hiểu nhầm dinh dưỡng y học là thuốc chữa bệnh.\n' ||
E'- ❌ **KHÔNG** so sánh dìm hàng hoặc công kích sản phẩm khác.\n' ||
E'- ✅ **ĐÚNG** định vị sản phẩm: "Dinh dưỡng y học lâm sàng B.Braun CHLB Đức" (Nutricomp) / "Dung dịch & Gel rửa, làm sạch và chăm sóc vết thương chuẩn y tế Châu Âu" (Prontosan).\n' ||
E'- ✅ **ĐÚNG** khuyến cáo y khoa: Khuyên người bệnh tham khảo ý kiến bác sĩ/dược sĩ cho các trường hợp bệnh lý nền chuyên sâu.\n\n' ||
E'## 3. PHÊ DUYỆT & PHẢN HỒI\n' ||
E'- Nếu đạt chuẩn: Phản hồi rõ ràng "APPROVED: Nội dung chuẩn y khoa và tuân thủ pháp lý quảng cáo, duyệt chuyển Sếp phê duyệt".\n' ||
E'- Nếu có từ ngữ rủi ro: Chỉ rõ câu từ cần sửa và đề xuất phương án thay thế an toàn cho Lead Marketing.';

    IF v_legal_id IS NOT NULL THEN
        INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
        VALUES (gen_random_uuid(), v_legal_id, 'SOUL.md', v_legal_soul, v_ea_tenant, NOW(), NOW())
        ON CONFLICT (agent_id, file_name)
        DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
        RAISE NOTICE 'SOUL.md updated for Lead Legal';
    END IF;

END $$;
EOSQL

echo "Setting up Marketing Skill (tao-creative-fb) and Python dependencies..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T goclaw pip install --break-system-packages requests python-dotenv || echo "Pip install warning, continuing..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T goclaw mkdir -p /app/data/skills /app/workspace/skills || true

if [ -d "skills/tao-creative-fb" ]; then
    echo "Copying skills/tao-creative-fb to container..."
    docker cp skills/tao-creative-fb goclaw-goclaw-1:/app/data/skills/ || true
    docker cp skills/tao-creative-fb goclaw-goclaw-1:/app/workspace/skills/ || true
fi

if [ -f "facebook_pages.csv" ]; then
    docker cp facebook_pages.csv goclaw-goclaw-1:/app/workspace/ || true
fi

echo "Verifying Facebook broadcasting capability (dry-run) inside container..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T goclaw python3 /app/workspace/skills/tao-creative-fb/scripts/post_facebook.py --image /app/workspace/skills/tao-creative-fb/output/test_image.png --caption "Test bài đăng hệ thống Marketing GlobalPharma" --dry-run || echo "Dry-run check completed with warning"

echo "Executive setup script executed successfully."

