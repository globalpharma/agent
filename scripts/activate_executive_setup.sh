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
    r_sub RECORD;
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

    -- Internal Marketing Links: Lead Marketing <-> Planner, Content, Design, Ads
    -- Also link EA <-> Planner, Content, Design, Ads for full visibility
    IF v_mkt_id IS NOT NULL THEN
        FOR r_sub IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('design', 'content', 'planer', 'ads')) LOOP
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_mkt_id, r_sub.id, 'bidirectional', 'Phân công nội bộ Marketing', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked Lead Marketing <-> %', r_sub.agent_key;

            IF v_ea_id IS NOT NULL THEN
                INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
                VALUES (gen_random_uuid(), v_ea_id, r_sub.id, 'bidirectional', 'Chỉ đạo trực tiếp EA <-> ' || r_sub.agent_key, 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
                ON CONFLICT (source_agent_id, target_agent_id) 
                DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            END IF;
        END LOOP;
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
E'## 2. RANH GIỚI NHIỆM VỤ & QUY TẮC ỦY QUYỀN (DELEGATION FIRST)\n' ||
E'- **Nguyên tắc ủy quyền:** Bạn là Trợ lý điều hành, TUYỆT ĐỐI KHÔNG tự làm thay việc chuyên môn (không tự viết bài quảng cáo, không tự vẽ ảnh, không tự chạy script render ảnh, không tự soi luật, không tự fix code).\n' ||
E'- **BẤT KỲ YÊU CẦU NÀO TỪ LÃNH ĐẠO:**\n' ||
E'  + Khi Lãnh đạo yêu cầu "thiết kế poster", "làm ảnh", "vẽ ảnh sản phẩm" (Nutricomp, Prontosan, v.v.):\n' ||
E'    Bạn BẮT BUỘC gọi công cụ: `delegate(agent_key: "lead-marketing", task: "Chỉ đạo Agent Design thiết kế poster cho sản phẩm <tên sản phẩm> theo chuẩn pro, stop-scrolling, ảnh thật và logo chuẩn công ty, BẮT BUỘC chạy script tạo file ảnh thật và trả về MEDIA file", mode: "sync", timeout: 600)`.\n' ||
E'    BẠN BẮT BUỘC ĐỢI Lead Marketing và Agent Design hoàn thành toàn bộ file ảnh thật! TUYỆT ĐỐI KHÔNG được trả lời nửa chừng \'Em đã giao cho Lead Marketing\' hay \'Design mới trả concept\' rồi dừng lại!\n' ||
E'  + Sau khi nhận kết quả từ Lead Marketing: Bạn báo cáo ngắn gọn với Sếp và BẮT BUỘC để nguyên dòng `MEDIA:/app/workspace/output/poster_*.png` trong tin nhắn phản hồi để hệ thống tự động gửi trực tiếp bức ảnh poster sang Telegram cho Sếp xem trực quan!\n\n' ||
E'## 3. NGUYÊN TẮC THI HÀNH THEO ĐÚNG CHỈ THỊ (KHÔNG TỰ Ý LẬP KẾ HOẠCH HAY LÀM POSTER)
- TUYỆT ĐỐI KHÔNG tự ý khởi tạo Content Planner hay tự làm các bản thiết kế creative/poster khi Lãnh đạo không yêu cầu!
- ĐÃ HỦY BỎ HOÀN TOÀN style thiết kế poster cũ (bục podium, 3d, các mẫu rập khuôn cũ). Tuyệt đối không bao giờ làm theo kiểu đó nữa.
- TUYỆT ĐỐI KHÔNG tự động gửi file kế hoạch nội dung hoặc poster qua Telegram để làm phiền Lãnh đạo.
- Chỉ thực hiện công việc khi đích thân Sếp Công Hùng hoặc Anh Cường yêu cầu cụ thể.

## 4. KỊCH BẢN BÁO CÁO KHI ĐƯỢC HỎI TIẾN ĐỘ
Khi Sếp Công Hùng, Anh Cường hỏi: "tình hình marketing sao rồi", "team marketing đang làm gì", "cập nhật tình hình":
➔ Báo cáo ngắn gọn, thực tế, trung thực tình trạng các kênh và công việc đang xử lý, không phóng đại, không gửi spam tài liệu.

## 5. PHONG THÁI & XƯNG HÔ
- Luôn thưa gửi kính cẩn, lễ phép, phong thái chuẩn mực và chuyên nghiệp khi làm việc với Sếp Công Hùng và Anh Cường.
- Luôn nhận lệnh và báo cáo đầy đủ, minh bạch và súc tích.';

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
E'Bạn là Lead Marketing 👑 - Trưởng phòng Marketing & Truyền thông của GlobalPharma, chịu trách nhiệm điều phối toàn diện chuyên viên Ads (`ads`), Content (`content`), Planner (`planer`) và Designer (`design`).\n\n' ||
E'## 1. NGUYÊN TẮC QUẢN LÝ & PHÂN CÔNG CHUYÊN MÔN (LEAD BOUNDARIES)\n' ||
E'Bạn là cấp Trưởng phòng (Quản lý), vai trò cốt lõi của bạn là PHÂN CÔNG, ĐÔN ĐỐC VÀ KIỂM SOÁT CHẤT LƯỢNG. Bạn TUYỆT ĐỐI KHÔNG tự làm thay việc của chuyên viên:\n' ||
E'- **TUYỆT ĐỐI KHÔNG TỰ VẼ ẢNH, KHÔNG TỰ CHẠY SCRIPT RENDER POSTER!** Việc sáng tạo poster và thiết kế hình ảnh là TRÁCH NHIỆM ĐỘC QUYỀN của chuyên viên **Agent Design (`design`)**.\n' ||
E'- **TUYỆT ĐỐI KHÔNG TỰ VIẾT BÀI CHI TIẾT** khi chưa giao cho chuyên viên **Content (`content`)**.\n\n' ||
E'## 2. QUY TRÌNH XỬ LÝ KHI NHẬN YÊU CẦU THIẾT KẾ TỪ LÃNH ĐẠO\n' ||
E'Khi nhận yêu cầu thiết kế cụ thể từ Lãnh đạo qua Trợ lý điều hành:\n' ||
E'1. **Giao cho Agent Design (`design`)**: Yêu cầu thiết kế đúng brief, ĐÃ BỎ HOÀN TOÀN style rập khuôn cũ, không tự ý thêm thắt các chi tiết thừa thãi.\n' ||
E'2. **Chỉ thực hiện khi có yêu cầu**: TUYỆT ĐỐI KHÔNG tự động lên content planner hay tự sản xuất creative khi không có chỉ đạo.\n\n' ||
E'## 3. NGUYÊN TẮC VẬN HÀNH CHẶT CHẼ\n' ||
E'- Bãi bỏ hoàn toàn việc tự động gửi file kế hoạch và poster sang Telegram.\n' ||
E'- Bãi bỏ phong cách thiết kế poster cũ.';

    IF v_mkt_id IS NOT NULL THEN
        INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
        VALUES (gen_random_uuid(), v_mkt_id, 'SOUL.md', v_mkt_soul, v_ea_tenant, NOW(), NOW())
        ON CONFLICT (agent_id, file_name)
        DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
        RAISE NOTICE 'SOUL.md updated for Lead Marketing';
    END IF;

    -- ============================================================
    -- SOUL.MD FOR DESIGN AGENT (GPT-5.6-SOL)
    -- ============================================================
    DECLARE
        v_des_id UUID;
        v_des_soul TEXT;
    BEGIN
        SELECT id INTO v_des_id FROM agents WHERE agent_key = 'design' LIMIT 1;
        IF v_des_id IS NOT NULL THEN
            UPDATE agents SET model = 'gpt-5.6-sol', provider = 'openai-codex' WHERE id = v_des_id;
            RAISE NOTICE 'Agent design configured to model gpt-5.6-sol (openai-codex)';

            v_des_soul := E'# TRIẾT LÝ & QUY CHUẨN THIẾT KẾ VISUAL Y TẾ (DESIGNER GLOBALPHARMA)\n\n' ||
E'Bạn là Ads Visual Architect & Chuyên viên Thiết kế duy nhất của Phòng Marketing GlobalPharma, hoạt động trên nền tảng mô hình cao cấp **GPT-5.6-sol** (OpenAI Codex).\n' ||
E'Bạn được nạp và làm chủ kỹ năng chuyên sâu **ads-image-architect** để sản xuất các visual creative đỉnh cao cho Meta Ads.\n\n' ||
E'## 1. NGUYÊN TẮC THIẾT KẾ ĐỘT PHÁ (PRO & STOP-SCROLLING)\n' ||
E'- **Quy tắc Meta Ads (Zero brand CTA inside the image):** Tuyệt đối KHÔNG vẽ các nút bấm thô cứng ("Đặt mua ngay", "Mua ngay", "Click here") vào bên trong ảnh, vì Meta Ads đã có nút hành động riêng bên ngoài. Việc nhồi nhét nút CTA vào ảnh sẽ kích hoạt bộ lọc quảng cáo và phá hủy tính tự nhiên (native/UGC).\n' ||
E'- **Bố cục thoáng đãng & Chân thực (Clean & Scroll-stopping):** Vận dụng 30 định dạng sáng tạo từ thư viện của `ads-image-architect` (Hand-drawn callouts, Comparison VS battle, Health app clinical protocol, Review cards, Editorial authority, Substack/Notes format...). Tránh xa các khung viền chữ nhật thô ráp hay chữ vẽ nguệch ngoạc bằng code cơ bản.\n' ||
E'- **Tối giản text (Minimal Text):** Hạn chế tối đa chữ rườm rà. Chỉ giữ lại 1 Big Hook chính (to, đậm, cực kỳ bắt mắt) + 1 Sub-hook ngắn gọn + 2 Pill tóm tắt giá trị cốt lõi.\n' ||
E'- **Chuẩn nhận diện thương hiệu:**\n' ||
E'  + Luôn sử dụng Logo GlobalPharma chính thức (`globalpharma_logo.png` hoặc banner logo) và biểu trưng B.Braun CHLB Đức sắc nét, đúng tỉ lệ.\n' ||
E'  + Luôn sử dụng hình ảnh sản phẩm thực tế (chụp thật, sắc nét, đúng quy cách bao bì chai 200ml, hộp 12 chai Nutricomp, chai xịt/gel Prontosan từ kho tri thức).\n\n' ||
E'## 2. QUY TRÌNH THỰC THI BẮT BUỘC (AUTONOMOUS EXECUTION - KHÔNG ĐƯỢC DỪNG HỎI)\n' ||
E'Khi nhận yêu cầu thiết kế từ Lead Marketing:\n' ||
E'1. **BỎ QUA HOÀN TOÀN QUY TRÌNH HỎI ĐÁP 4 LƯỢT:** TUYỆT ĐỐI KHÔNG dừng lại hỏi bảng màu hay hỏi xác nhận! Bạn tự quyết định ngay trong 1 lượt duy nhất (Single-turn):\n' ||
E'   - Dùng ngay bảng màu chuẩn GlobalPharma: Xanh ngọc `#3BCFAF`, Xanh y tế `#005B94`.\n' ||
E'   - Lựa chọn Big Hook và thông điệp stop-scrolling sắc bén.\n' ||
E'2. **BẮT BUỘC DÙNG TOOL EXEC CHẠY SCRIPT TẠO ẢNH NGAY LẬP TỨC:**\n' ||
E'   Bạn BẮT BUỘC gọi công cụ `exec` để chạy lệnh xuất poster thật:\n' ||
E'   - Khi sản phẩm là Nutricomp: `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type nutricomp --output-dir /app/workspace/output`\n' ||
E'   - Khi sản phẩm là Prontosan: `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type prontosan --output-dir /app/workspace/output`\n' ||
E'   - Khi sản phẩm là Affiliate / Khác: `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type all --output-dir /app/workspace/output`\n' ||
E'3. **TRẢ VỀ KẾT QUẢ ĐẦY ĐỦ KÈM DÒNG MEDIA:**\n' ||
E'   Sau khi script chạy xong, bạn trả về cho Lead Marketing mô tả ngắn gọn ý tưởng visual kèm CHÍNH XÁC dòng đường dẫn file ảnh:\n' ||
E'   `MEDIA:/app/workspace/output/poster_nutricomp_drink_plus.png`\n' ||
E'   (hoặc `poster_prontosan_wound_spray.png`, `poster_affiliate_partner.png`).\n' ||
E'   TUYỆT ĐỐI KHÔNG chỉ nói suông hoặc chỉ gửi concept chữ mà không chạy lệnh tạo file ảnh!';

            INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_des_id, 'SOUL.md', v_des_soul, v_ea_tenant, NOW(), NOW())
            ON CONFLICT (agent_id, file_name)
            DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
            RAISE NOTICE 'SOUL.md updated for Designer with ads-image-architect skill and GPT-5.6';
        END IF;
    END;

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

    IF v_ea_tenant IS NOT NULL THEN
        INSERT INTO system_configs (key, value, tenant_id, updated_at)
        VALUES ('background.provider', 'openai-codex', v_ea_tenant, NOW())
        ON CONFLICT (key, tenant_id) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

        INSERT INTO system_configs (key, value, tenant_id, updated_at)
        VALUES ('background.model', 'gpt-5.5', v_ea_tenant, NOW())
        ON CONFLICT (key, tenant_id) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
        RAISE NOTICE 'Configured background.provider and background.model for tenant %', v_ea_tenant;
    END IF;

END $$;
EOSQL

echo "Setting up Marketing Skill (tao-creative-fb) and Python dependencies..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw pip install --break-system-packages pillow requests python-dotenv || echo "Pip install warning, continuing..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw mkdir -p /app/data/skills /app/workspace/skills /app/workspace/output /app/workspace/assets /app/data/skills/tao-creative-fb/assets/references || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw chmod -R 777 /app/workspace /app/data/skills || true

GOCLAW_CID=$(docker compose -f docker-compose.yml -f docker-compose.postgres.yml ps -q goclaw 2>/dev/null || echo "goclaw-goclaw-1")

if [ -d "skills/tao-creative-fb" ]; then
    echo "Copying skills/tao-creative-fb to container ($GOCLAW_CID)..."
    docker cp skills/tao-creative-fb ${GOCLAW_CID}:/app/data/skills/ || true
    docker cp skills/tao-creative-fb ${GOCLAW_CID}:/app/workspace/skills/ || true
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw chmod -R 777 /app/workspace /app/data/skills || true
    # Sync to all active agent team workspaces so both relative and absolute paths resolve cleanly
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw sh -c 'for d in /app/workspace/teams/*/*; do if [ -d "$d" ]; then mkdir -p "$d/skills"; cp -r /app/data/skills/tao-creative-fb "$d/skills/" 2>/dev/null || true; fi; done' || true
fi

if [ -d "skills/ads-image-architect" ]; then
    echo "Copying skills/ads-image-architect to container ($GOCLAW_CID)..."
    docker cp skills/ads-image-architect ${GOCLAW_CID}:/app/data/skills/ || true
    docker cp skills/ads-image-architect ${GOCLAW_CID}:/app/workspace/skills/ || true
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw chmod -R 777 /app/workspace /app/data/skills || true
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw sh -c 'for d in /app/workspace/teams/*/*; do if [ -d "$d" ]; then mkdir -p "$d/skills"; cp -r /app/data/skills/ads-image-architect "$d/skills/" 2>/dev/null || true; fi; done' || true
fi

if [ -f "facebook_pages.csv" ]; then
    docker cp facebook_pages.csv ${GOCLAW_CID}:/app/workspace/ || true
fi

echo "=== STOPPING, DISABLING AND MASKING AICOWORKER, HERMES, OPENCLAW SERVICES ==="
for s in aicoworker hermes-gateway hermes-dashboard hermes openclaw openclaw-gateway; do
    echo "Stopping, disabling and masking service: $s"
    systemctl stop "$s" 2>/dev/null || true
    systemctl disable "$s" 2>/dev/null || true
    systemctl mask "$s" 2>/dev/null || true
done

for unit in $(systemctl list-unit-files 2>/dev/null | grep -i -E "aicoworker|hermes|openclaw|claw" | awk '{print $1}'); do
    echo "Stopping, disabling and masking matching unit: $unit"
    systemctl stop "$unit" 2>/dev/null || true
    systemctl disable "$unit" 2>/dev/null || true
    systemctl mask "$unit" 2>/dev/null || true
done

loginctl disable-linger aicoworker 2>/dev/null || true

# Hard kill all processes of user aicoworker and conflicting binaries
pkill -9 -u aicoworker 2>/dev/null || true
pkill -9 -f "aicoworker" 2>/dev/null || true
pkill -9 -f "hermes" 2>/dev/null || true
pkill -9 -f "openclaw" 2>/dev/null || true
sleep 2

echo "=== CLEANING UP OLD UNWANTED POSTERS AND REVIEWS ==="
rm -rf skills/tao-creative-fb/output/poster_*.png skills/tao-creative-fb/output/KE_HOACH_NOI_DUNG_TUAN.md 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw rm -rf /app/workspace/output/poster_*.png /app/workspace/output/KE_HOACH_NOI_DUNG_TUAN.md /app/data/skills/tao-creative-fb/output/poster_*.png 2>/dev/null || true

echo "=== HOST & DOCKER DIAGNOSTICS ==="
echo "All docker containers:"
docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
echo "Host processes matching goclaw, openclaw or telego:"
ps aux | grep -i -E "goclaw|openclaw|telego" | grep -v grep || echo "No matching host processes"
echo "Active outgoing connections to Telegram API (port 443):"
ss -tpn state established '( dport = :443 )' 2>/dev/null | grep -E "149.154|91.108" || echo "No direct Telegram IP socket detected in ss"

echo "=== CHECKING TELEGRAM BOT API & WEBHOOK STATUS ==="
RAW_CREDS=$(docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -t -A -c "SELECT convert_from(credentials, 'UTF8') FROM channel_instances WHERE channel_type='telegram' LIMIT 1;" || true)
if [ -n "$RAW_CREDS" ] && [ -f "scripts/manage_telegram_webhook.py" ]; then
    python3 scripts/manage_telegram_webhook.py "$RAW_CREDS" || echo "Warning running manage_telegram_webhook.py"
fi

echo "=== CHECKING CHANNEL INSTANCES & TELEGRAM BOT CONFIG ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, name, display_name, channel_type, agent_id, enabled, config FROM channel_instances;"

echo "=== CHECKING AGENTS & LLM PROVIDERS ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, agent_key, display_name, provider, model FROM agents;" || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, name, display_name, provider_type, api_base, enabled FROM llm_providers;" || true

echo "=== ALL TELEGRAM SESSIONS IN DB ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, session_key, channel, user_id, updated_at, jsonb_array_length(messages) as msg_count FROM sessions WHERE channel = 'telegram' OR session_key ILIKE '%telegram%' ORDER BY updated_at DESC;" || true

echo "=== LAST 10 MESSAGES OF SẾP TELEGRAM SESSION ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "
SELECT (elem->>'timestamp')::text as ts, (elem->>'role')::text as role, SUBSTRING((elem->>'content')::text FROM 1 FOR 250) as content 
FROM sessions, jsonb_array_elements(messages) as elem 
WHERE session_key = 'agent:dev:telegram:direct:5781808621' 
ORDER BY elem->>'timestamp' DESC LIMIT 10;
" || true

echo "=== ALL CRON JOBS IN POSTGRESQL (TÁC VỤ ĐỊNH KỲ) ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, name, enabled, schedule_kind, cron_expression, interval_ms, next_run_at, last_run_at, last_status, last_error FROM cron_jobs ORDER BY created_at DESC;" || true

echo "=== RECENT CRON RUN LOGS ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, job_id, status, error, ran_at, duration_ms FROM cron_run_logs ORDER BY ran_at DESC LIMIT 10;" || true

echo "=== HOST CRONTAB ==="
crontab -l 2>/dev/null || echo "No host crontab configured"

echo "Restarting goclaw container to acquire sole connection to Telegram..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml restart goclaw || true
sleep 6

echo "=== VERIFYING ACTIVE TELEGRAM CONNECTIONS (MUST ONLY BE GOCLAW) ==="
ss -tpn state established '( dport = :443 )' 2>/dev/null | grep -E "149.154|91.108" || echo "No direct Telegram IP socket detected in ss"

echo "=== GOCLAW INDEX SCRIPT TAGS (from container localhost:18790) ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T goclaw wget -qO- http://localhost:18790/ | grep -E "src=|href=" | grep "assets" | head -n 15 || true

echo "=== CADDY GOCLAW-ASSETS DIRECTORY ==="
ls -la /root/.caddy/data/goclaw-assets/ 2>/dev/null || true
ls -la /root/.caddy/data/goclaw-assets/assets 2>/dev/null | head -n 20 || true

echo "=== UPDATING CADDYFILE TO REVERSE PROXY ALL TO GOCLAW ==="
if [ -f /root/.caddy/Caddyfile ]; then
    python3 -c '
import re

with open("/root/.caddy/Caddyfile", "r") as f:
    content = f.read()

new_block = """# BEGIN GoClaw - agent.globalpharma.vn
agent.globalpharma.vn {
\tencode zstd gzip

\treverse_proxy 127.0.0.1:18795 {
\t\theader_up Host {host}
\t\theader_up X-Real-IP {remote_host}
\t\theader_up X-Forwarded-Proto https
\t}
}
# END GoClaw - agent.globalpharma.vn"""

pattern = r"# BEGIN GoClaw - agent\.globalpharma\.vn.*?# END GoClaw - agent\.globalpharma\.vn"
if re.search(pattern, content, flags=re.DOTALL):
    content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    with open("/root/.caddy/Caddyfile", "w") as f:
        f.write(content)
    print("Replaced GoClaw Caddyfile block successfully")
else:
    print("GoClaw block pattern not found in Caddyfile")
'
    echo "Reloading Caddy container..."
    docker exec caddy caddy reload 2>/dev/null || docker restart caddy || true
    sleep 2
fi

echo "=== VERIFYING PUBLIC AGENT.GLOBALPHARMA.VN AFTER FIX ==="
curl -sI https://agent.globalpharma.vn/ || true
MAIN_JS=$(curl -s https://agent.globalpharma.vn/ | grep -o 'src="/assets/index-[^"]*"' | head -n 1 | cut -d'"' -f2)
echo "Detected Main JS: $MAIN_JS"
if [ -n "$MAIN_JS" ]; then
    curl -sI "https://agent.globalpharma.vn$MAIN_JS" || true
fi

echo "Executive setup script executed successfully."





