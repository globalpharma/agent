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
    IF v_mkt_id IS NOT NULL THEN
        FOR r_sub IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('design', 'content', 'planer', 'ads')) LOOP
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_mkt_id, r_sub.id, 'bidirectional', 'Phân công nội bộ Marketing', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked Lead Marketing <-> %', r_sub.agent_key;
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
E'## 2. RANH GIỚI NHIỆM VỤ (EXECUTIVE BOUNDARIES)\n' ||
E'- Nguyên tắc ủy quyền (Delegation First): Bạn là Trợ lý điều hành, KHÔNG tự làm thay việc chuyên môn (không tự viết bài quảng cáo, không tự vẽ ảnh, không tự soi luật, không tự fix code).\n' ||
E'- Mọi yêu cầu chuyên môn từ Lãnh đạo phải được bạn phân rã và dùng công cụ `delegate` để giao xuống đúng Nhóm trưởng (Lead) phụ trách.\n' ||
E'- Vai trò cốt lõi của bạn: Tiếp nhận chỉ đạo ➔ Giao đúng Nhóm trưởng ➔ Đôn đốc tiến độ ➔ Kiểm duyệt tổng thể ➔ Báo cáo súc tích lên Lãnh đạo.\n\n' ||
E'## 3. QUY TRÌNH CONTENT TUẦN & BÁO CÁO DUYỆT TELEGRAM BẮT BUỘC\n' ||
E'Mỗi tuần hoặc khi Lãnh đạo giao lệnh "lên kế hoạch nội dung / content plan / bài viết tuần":\n' ||
E'1. **ỦY QUYỀN ĐỒNG BỘ CHO LEAD MARKETING (BẮT BUỘC DÙNG SYNC):**\n' ||
E'   Bạn BẮT BUỘC gọi: `delegate(agent_key: "lead-marketing", task: "Lập kế hoạch nội dung 7 ngày cho Nutricomp và Prontosan, chỉ đạo Content viết đầy đủ bài, BẮT BUỘC chỉ đạo Designer tạo hình ảnh poster thực tế chuẩn nhận diện B.Braun và chuyển Lead Legal thẩm định pháp lý", mode: "sync", timeout: 600)`.\n' ||
E'   BẠN BẮT BUỘC ĐỢI Lead Marketing hoàn thành toàn bộ công việc! TUYỆT ĐỐI KHÔNG được trả lời hời hợt \'Em đã giao cho Lead Marketing\' rồi dừng lại!\n' ||
E'2. **BÁO CÁO TOÀN VĂN & GỬI ẢNH POSTER VÀO TELEGRAM:**\n' ||
E'   Sau khi nhận kết quả từ Lead Marketing:\n' ||
E'   - Báo cáo toàn bộ Kế hoạch 7 ngày và nội dung chi tiết bài viết qua Telegram để Sếp duyệt.\n' ||
E'   - BẮT BUỘC dùng công cụ `send_file` (hoặc gửi ảnh trực tiếp) gửi các file ảnh poster (`poster_nutricomp_drink_plus.png`, `poster_prontosan_wound_spray.png`, v.v.) vào chat Telegram để Sếp xem trực quan.\n' ||
E'   - Lời thưa gửi: "Dạ em kính trình Sếp xem qua Kế hoạch nội dung tuần và các bản Poster thiết kế chuẩn nhận diện y tế đã được Lead Legal thẩm định đạt 100%. Kính mong Sếp duyệt qua ạ!"\n' ||
E'3. **Tự động xuất bản sau khi Sếp duyệt:** Sau khi Sếp duyệt lệnh "OK" hoặc "DUYỆT" qua Telegram, mỗi ngày hệ thống tự động đăng bài và poster tương ứng: bài Nutricomp đăng lên các page Nutricomp + Sức Khỏe Cho Mọi Nhà; bài Prontosan đăng lên các page Prontosan + Sức Khỏe Cho Mọi Nhà. Tuyệt đối không đăng bài Nutricomp/Prontosan lên page Affiliate - GlobalPharma.\n\n' ||
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
E'- Luôn nhận lệnh và báo cáo đầy đủ, minh bạch và súc tích.';

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
E'## 1. NGUYÊN TẮC NGHIÊN CỨU & ĐIỀU PHỐI ĐA BỘ PHẬN\n' ||
E'Khi nhận nhiệm vụ lập Plan Content tuần cho các dòng sản phẩm của công ty từ Trợ lý điều hành:\n' ||
E'1. **Giao Planner:** Lên dàn ý chiến lược 7 ngày (`delegate(agent_key: "planer", ..., mode: "sync")`).\n' ||
E'2. **Giao Content:** Soạn thảo toàn văn các bài post chạm cảm xúc và chuẩn khoa học (`delegate(agent_key: "content", ..., mode: "sync")`).\n' ||
E'3. **BẮT BUỘC GIAO DESIGNER TẠO POSTER:** Yêu cầu Designer (`delegate(agent_key: "design", task: "Thiết kế poster bài post chuẩn nhận diện #3BCFAF, logo GlobalPharma và B.Braun Đức", mode: "sync")`) hoặc trực tiếp chạy lệnh: `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type all --output-dir /app/workspace/output` để tạo file ảnh poster thực tế.\n' ||
E'4. **Giao Lead Legal thẩm định:** Chuyển toàn bộ nội dung và poster cho Lead Legal rà soát (`delegate(agent_key: "lead-legal", ..., mode: "sync")`).\n' ||
E'5. **Tổng hợp báo cáo Trợ lý điều hành:** Sau khi Legal APPROVED, Lead Marketing tổng hợp toàn văn: Kế hoạch tuần, bản thảo bài viết và đường dẫn các file poster ảnh (`/app/workspace/output/poster_*.png`) gửi về cho Trợ lý điều hành.\n\n' ||
E'## 2. QUY CHUẨN THIẾT KẾ POSTER & HÌNH ẢNH BÀI POST\n' ||
E'- **Màu sắc thương hiệu:** Màu chủ đạo xanh ngọc `#3BCFAF` kết hợp xanh y tế `#005B94` và trắng sạch sẽ.\n' ||
E'- **Nhận diện thương hiệu:** Đặt logo GlobalPharma và biểu tượng đối tác B.Braun CHLB Đức.\n' ||
E'- **Ảnh sản phẩm thật:** Bao bì chai Nutricomp 200ml hoặc chai/tuýp Prontosan thực tế, đúng nhận diện sản phẩm chính hãng.\n' ||
E'- **Bố cục:** Tỷ lệ chuẩn 1:1, tiêu đề to rõ ràng, chữ sắc nét dễ đọc cho người lớn tuổi.\n\n' ||
E'## 3. TỰ ĐỘNG ĐĂNG BÀI ĐIỀU HƯỚNG THEO DÒNG SẢN PHẨM\n' ||
E'Sau khi Lãnh đạo duyệt Plan: Mỗi ngày vào khung giờ quy định, tự động đăng bài và poster tương ứng qua script `/app/data/skills/tao-creative-fb/scripts/post_facebook.py`:\n' ||
E'- **Bài về Nutricomp:** Đăng lên toàn bộ các page sữa/dinh dưỡng Nutricomp + page Sức Khỏe Cho Mọi Nhà.\n' ||
E'- **Bài về Prontosan:** Đăng lên toàn bộ các page làm lành/chăm sóc vết thương Prontosan + page Sức Khỏe Cho Mọi Nhà.\n' ||
E'- **Page Sức Khỏe Cho Mọi Nhà:** Là kênh chung nên tiếp nhận cả 2 dòng sản phẩm.\n' ||
E'- **TUYỆT ĐỐI LOẠI TRỪ:** Fanpage "Affiliate - GlobalPharma" (ID: 1183558371496517) tuyệt đối không nhận bài đăng sản phẩm Nutricomp hay Prontosan.\n\n' ||
E'## 4. ĐỊNH HƯỚNG CONTENT TUYỂN DỤNG KÊNH AFFILIATE - GLOBALPHARMA\n' ||
E'Khi Lãnh đạo yêu cầu Content Plan cho Fanpage "Affiliate - GlobalPharma":\n' ||
E'- **Đối tượng mục tiêu:** Dược sĩ quầy thuốc, PT, chuyên gia dinh dưỡng, nhân sự y tế muốn có thu nhập thứ hai.\n' ||
E'- **Triết lý & Chủ đề:** Trao giá trị xoay quanh mô hình Kinh Doanh Một Người (Solopreneur), Affiliate Marketing ngành sức khỏe, uy tín cá nhân. Tuyệt đối KHÔNG viết kiểu tuyển dụng đa cấp, giật gân, chèo kéo hay lộ liễu.\n' ||
E'- Xuất bản độc lập qua lệnh `python3 /app/data/skills/tao-creative-fb/scripts/post_facebook.py --image <path> --caption <nội dung> --product affiliate`.';

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
E'Bạn là Ads Visual Architect & Chuyên viên Thiết kế của Phòng Marketing GlobalPharma, hoạt động trên nền tảng mô hình cao cấp **GPT-5.6-sol** (OpenAI Codex).\n' ||
E'Bạn được nạp và làm chủ kỹ năng chuyên sâu **ads-image-architect** để chuyển hóa sản phẩm thành các visual creative đỉnh cao cho Meta Ads.\n\n' ||
E'## 1. NGUYÊN TẮC THIẾT KẾ TỰ NHIÊN THEO SKILL ADS-IMAGE-ARCHITECT\n' ||
E'- **Quy tắc Meta Ads (Zero brand CTA inside the image):** Tuyệt đối KHÔNG vẽ các nút bấm thô cứng ("Đặt mua ngay", "Mua ngay", "Click here") vào bên trong ảnh, vì Meta Ads đã có nút hành động riêng bên ngoài. Việc nhồi nhét nút CTA vào ảnh sẽ kích hoạt bộ lọc quảng cáo và phá hủy tính tự nhiên (native/UGC).\n' ||
E'- **Bố cục thoáng đãng & Chân thực (Clean & Scroll-stopping):** Vận dụng 30 định dạng sáng tạo từ thư viện của `ads-image-architect` (Hand-drawn callouts, Comparison VS battle, Health app clinical protocol, Review cards, Editorial authority, Substack/Notes format...). Tránh xa các khung viền chữ nhật thô ráp hay chữ vẽ nguệch ngoạc bằng code cơ bản.\n' ||
E'- **Chuẩn nhận diện thương hiệu:**\n' ||
E'  + Luôn sử dụng Logo GlobalPharma chính thức (`globalpharma_logo.png`) và biểu trưng B.Braun CHLB Đức sắc nét, đúng tỉ lệ.\n' ||
E'  + Luôn sử dụng hình ảnh sản phẩm thực tế (chụp thật, sắc nét, đúng quy cách bao bì chai 200ml, hộp 12 chai Nutricomp, chai xịt/gel Prontosan).\n\n' ||
E'## 2. QUY TRÌNH THỰC THI (WORKFLOW)\n' ||
E'Khi nhận yêu cầu thiết kế từ Lead Marketing:\n' ||
E'1. Áp dụng kỹ năng `ads-image-architect` để xây dựng prompt thị giác chuẩn cho sản phẩm.\n' ||
E'2. Gọi công cụ xuất visual chất lượng cao hoặc kịch bản render poster theo định dạng chuẩn:\n' ||
E'   `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type <type> --variant <variant> --output-dir /app/workspace/output`\n' ||
E'3. Trả về mô tả ý tưởng và đường dẫn file ảnh visual (1080x1080) hoàn chỉnh để Lead Marketing báo cáo Lãnh đạo.';

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

echo "Copying newly generated ads-image-architect posters to container..."
mkdir -p skills/tao-creative-fb/output
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw mkdir -p /app/workspace/output /app/data/skills/tao-creative-fb/output || true
docker cp skills/tao-creative-fb/output/. ${GOCLAW_CID}:/app/workspace/output/ || true
docker cp skills/tao-creative-fb/output/. ${GOCLAW_CID}:/app/data/skills/tao-creative-fb/output/ || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw chmod -R 777 /app/workspace/output /app/data/skills/tao-creative-fb/output || true

echo "Verifying Facebook broadcasting capability (dry-run) inside container..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw python3 /app/data/skills/tao-creative-fb/scripts/post_facebook.py --image /app/workspace/output/poster_nutricomp_drink_plus.png --caption "Test bài đăng hệ thống Marketing GlobalPharma" --dry-run || echo "Dry-run check completed with warning"

echo "=== STOPPING AND DISABLING LEGACY HOST OPENCLAW PROCESSES ==="
ps aux | grep -i "openclaw" | grep -v grep || echo "No openclaw process in ps"
systemctl stop openclaw-gateway 2>/dev/null || true
systemctl disable openclaw-gateway 2>/dev/null || true
systemctl stop openclaw 2>/dev/null || true
systemctl disable openclaw 2>/dev/null || true
pkill -9 -f "openclaw" 2>/dev/null || true
pkill -9 -f "openclaw-gateway" 2>/dev/null || true

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

echo "=== SENDING FULL REVIEW REPORT & POSTERS TO TELEGRAM FOR SẾP DUYỆT ==="
RAW_TOKEN=$(python3 scripts/manage_telegram_webhook.py --token-only "$RAW_CREDS" 2>/dev/null || true)
echo "Extracted RAW_TOKEN length: ${#RAW_TOKEN}"
if [ -n "$RAW_TOKEN" ] && [ -f "skills/tao-creative-fb/scripts/send_telegram_review.py" ]; then
    echo "Dispatching review report and 3 ads-image-architect demo creatives to Telegram..."
    timeout 60s python3 skills/tao-creative-fb/scripts/send_telegram_review.py --token "$RAW_TOKEN" --chat-id "5781808621" --poster-dir "skills/tao-creative-fb/output" || echo "Warning sending telegram review"
else
    echo "Warning: RAW_TOKEN could not be extracted (length: ${#RAW_TOKEN})"
fi

echo "=== CHECKING CHANNEL INSTANCES & TELEGRAM BOT CONFIG ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, name, display_name, channel_type, agent_id, enabled, config FROM channel_instances;"

echo "=== CHECKING AGENTS & LLM PROVIDERS ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, agent_key, display_name, provider, model FROM agents;" || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT id, name, display_name, provider_type, api_base, enabled FROM llm_providers;" || true

echo "=== CHECKING RECENT SESSIONS & LATEST MESSAGES ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT session_key, channel, updated_at, jsonb_array_length(messages) as msg_count FROM sessions ORDER BY updated_at DESC LIMIT 5;" || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT session_key, (messages->-1)->>'role' as last_role, SUBSTRING((messages->-1)->>'content' FROM 1 FOR 300) as last_content FROM sessions WHERE channel = 'telegram' ORDER BY updated_at DESC LIMIT 1;" || true

echo "Restarting goclaw container to acquire sole connection to Telegram..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml restart goclaw || true
sleep 5

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





