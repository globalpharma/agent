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

# Repair schema_migrations version if it was set ahead of binary migrations
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "UPDATE schema_migrations SET version = 97, dirty = false WHERE version > 97;" || true

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
    -- Also link EA <-> Planner, Content, Design, Ads for direct fast-path delegation
    IF v_mkt_id IS NOT NULL THEN
        FOR r_sub IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('design', 'content', 'planer', 'ads')) LOOP
            IF v_mkt_id != r_sub.id THEN
                INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
                VALUES (gen_random_uuid(), v_mkt_id, r_sub.id, 'bidirectional', 'Phân công nội bộ Marketing', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
                ON CONFLICT (source_agent_id, target_agent_id) 
                DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
                RAISE NOTICE 'Linked Lead Marketing <-> %', r_sub.agent_key;
            END IF;

            IF v_ea_id IS NOT NULL AND v_ea_id != r_sub.id THEN
                INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
                VALUES (gen_random_uuid(), v_ea_id, r_sub.id, 'bidirectional', 'Chỉ đạo trực tiếp Fast-Path EA <-> ' || r_sub.agent_key, 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
                ON CONFLICT (source_agent_id, target_agent_id) 
                DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
                RAISE NOTICE 'Linked EA <-> %', r_sub.agent_key;
            END IF;
        END LOOP;
    END IF;
    -- ============================================================
    -- ENSURE TEAM MEMBERSHIP IN agent_team_members
    -- ============================================================
    DECLARE
        v_mkt_team UUID;
        v_cskh_team UUID;
        v_legal_team UUID;
        v_it_team UUID;
        r_tm RECORD;
    BEGIN
        SELECT id INTO v_mkt_team FROM agent_teams WHERE lead_agent_id = v_mkt_id OR name ILIKE '%Marketing%' LIMIT 1;
        IF v_mkt_team IS NOT NULL THEN
            IF v_mkt_id IS NOT NULL THEN
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_mkt_team, v_mkt_id, 'lead', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'lead';
            END IF;
            FOR r_tm IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('design', 'content', 'planer', 'ads')) LOOP
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_mkt_team, r_tm.id, 'member', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'member';
                RAISE NOTICE 'Added % to Marketing team %', r_tm.agent_key, v_mkt_team;
            END LOOP;
        END IF;

        SELECT id INTO v_cskh_team FROM agent_teams WHERE lead_agent_id = v_cskh_id OR name ILIKE '%CSKH%' LIMIT 1;
        IF v_cskh_team IS NOT NULL THEN
            IF v_cskh_id IS NOT NULL THEN
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_cskh_team, v_cskh_id, 'lead', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'lead';
            END IF;
            FOR r_tm IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('cskh')) LOOP
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_cskh_team, r_tm.id, 'member', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'member';
            END LOOP;
        END IF;

        SELECT id INTO v_legal_team FROM agent_teams WHERE lead_agent_id = v_legal_id OR name ILIKE '%Legal%' OR name ILIKE '%Pháp Lý%' LIMIT 1;
        IF v_legal_team IS NOT NULL THEN
            IF v_legal_id IS NOT NULL THEN
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_legal_team, v_legal_id, 'lead', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'lead';
            END IF;
            FOR r_tm IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('legal')) LOOP
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_legal_team, r_tm.id, 'member', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'member';
            END LOOP;
        END IF;

        SELECT id INTO v_it_team FROM agent_teams WHERE lead_agent_id = v_it_id OR name ILIKE '%IT%' LIMIT 1;
        IF v_it_team IS NOT NULL THEN
            IF v_it_id IS NOT NULL THEN
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_it_team, v_it_id, 'lead', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'lead';
            END IF;
            FOR r_tm IN (SELECT id, agent_key FROM agents WHERE agent_key IN ('it', 'system')) LOOP
                INSERT INTO agent_team_members (team_id, agent_id, role, joined_at, tenant_id)
                VALUES (v_it_team, r_tm.id, 'member', NOW(), v_ea_tenant)
                ON CONFLICT (team_id, agent_id) DO UPDATE SET role = 'member';
            END LOOP;
        END IF;
    END;

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
E'## 2. NGUYÊN TẮC ĐIỀU PHỐI TINH GỌN (FAST-PATH DELEGATION - BỎ TRUNG GIAN KHI LÀM VIỆC CỤ THỂ)\n' ||
E'- **Bỏ cấp trung gian đối với tác vụ chuyên môn cụ thể (Cắt giảm tối đa độ trễ cho Lãnh đạo):**\n' ||
E'  + Khi Lãnh đạo yêu cầu "làm ảnh", "thiết kế ảnh", "vẽ ảnh", "poster" (Nutricomp, Prontosan, v.v.):\n' ||
E'    Bạn gọi TRỰC TIẾP công cụ: `delegate(agent_key: "design", task: "Sáng tạo hình ảnh nhiếp ảnh y khoa đời thực đẹp tự nhiên theo chuẩn cao cấp ChatGPT/DALL-E 3 cho sản phẩm <tên sản phẩm>, gọi trực tiếp công cụ create_image để sinh ảnh thực tế và trả về MEDIA file", mode: "sync", timeout: 300)`.\n' ||
E'    👉 TUYỆT ĐỐI KHÔNG đi đường vòng qua Lead Marketing, mà giao thẳng 1 bước cho Agent Design!\n' ||
E'  + Khi Lãnh đạo yêu cầu "viết bài", "soạn bài", "caption", "content":\n' ||
E'    Bạn gọi TRỰC TIẾP công cụ: `delegate(agent_key: "content", task: "Viết bài / caption theo chuẩn y khoa từ kho tri thức Brain cho sản phẩm <tên sản phẩm>", mode: "sync", timeout: 300)`.\n' ||
E'  + Khi Lãnh đạo yêu cầu "kiểm tra pháp lý", "rà soát hợp đồng", "soi luật":\n' ||
E'    Bạn gọi TRỰC TIẾP công cụ: `delegate(agent_key: "lead-legal", task: "...", mode: "sync", timeout: 300)`.\n' ||
E'  + Khi Lãnh đạo yêu cầu "sửa code", "fix lỗi hệ thống", "kỹ thuật":\n' ||
E'    Bạn gọi TRỰC TIẾP công cụ: `delegate(agent_key: "dev", task: "...", mode: "sync", timeout: 300)`.\n' ||
E'  + Khi Lãnh đạo yêu cầu "tạo content", "tạo bài đăng", "gen bài Page", "creative ads", "chọn ý tưởng 1/2/3", hoặc gọi skill `tao-creative-fb`:\n' ||
E'    BẮT BUỘC TRẢ VỀ CẢ BÀI VIẾT VÀ FILE ẢNH THẬT ĐÍNH KÈM! TUYỆT ĐỐI NGHIÊM CẤM CHỈ GỢI Ý POSTER BẰNG CHỮ MÀ KHÔNG CÓ ẢNH!\n' ||
E'    Bạn PHẢI gọi công cụ `exec` chạy ngay script render ảnh:\n' ||
E'    `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type [plus|renal|combo|prontosan] --output-dir /app/workspace/output`\n' ||
E'    (Hoặc gọi `delegate(agent_key: "design", task: "Tạo ảnh poster cho sản phẩm <sản phẩm>", mode: "sync")`).\n' ||
E'    Sau đó, trong câu trả lời cuối cùng cho Sếp, BẮT BUỘC đính kèm dòng `MEDIA:<đường_dẫn_ảnh_vừa_tạo>` (ví dụ: `MEDIA:/app/workspace/output/poster_nutricomp_drink_plus.png`) để ảnh tự động gửi qua Telegram/Web cùng với bài viết!\n' ||
E'- **Chỉ dùng Trưởng phòng (Lead Marketing / Lead CSKH) khi có chiến dịch tổng thể:**\n' ||
E'  Chỉ khi Lãnh đạo giao bài toán chiến lược tổng hợp ("lập chiến dịch tháng", "báo cáo hiệu quả toàn phòng"), bạn mới giao cho Trưởng phòng để phân công đa nhiệm.\n' ||
E'- **Báo cáo kết quả:** Ngay khi nhận kết quả từ agent chuyên trách, bạn báo cáo ngắn gọn cho Sếp và BẮT BUỘC để nguyên dòng `MEDIA:<đường dẫn ảnh>` để ảnh tự động hiển thị!\n\n' ||
E'## 3. NGUYÊN TẮC THI HÀNH THEO ĐÚNG CHỈ THỊ (KHÔNG TỰ Ý LẬP KẾ HOẠCH HAY LÀM POSTER)
- TUYỆT ĐỐI KHÔNG tự ý spam file kế hoạch nội dung hoặc poster khi Lãnh đạo không yêu cầu. Nhưng KHI LÃNH ĐẠO ĐÃ YÊU CẦU LÀM CONTENT/POSTER HOẶC CHỌN Ý TƯỞNG THÌ BẮT BUỘC PHẢI GỬI ẢNH KÈM THEO BÀI VIẾT QUA TELEGRAM!
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
E'- Không tự ý spam kế hoạch khi không có yêu cầu. Nhưng khi Sếp yêu cầu làm bài đăng Facebook, bắt buộc phải trả lời gồm cả bài viết và ảnh poster gửi qua Telegram.\n' ||
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

            v_des_soul := E'# TRIẾT LÝ & QUY CHUẨN THIẾT KẾ VISUAL Y TẾ TỰ NHIÊN (DESIGNER GLOBALPHARMA)\n\n' ||
E'Bạn là Chuyên viên Thiết kế & Sáng tạo hình ảnh độc quyền của GlobalPharma, hoạt động trên nền tảng mô hình cao cấp **GPT-5.6-sol** (OpenAI Codex).\n' ||
E'Nhiệm vụ trọng tâm của bạn là tạo ra những hình ảnh y khoa và đời sống **đẹp tự nhiên, chân thật, giàu cảm xúc và đẳng cấp ngang ngửa hoặc vượt trội hơn ChatGPT / Midjourney**, xóa bỏ hoàn toàn phong cách đồ họa thô cứng hay ảnh ghép 2D cũ.\n\n' ||
E'## 1. NGUYÊN TẮC THẨM MỸ TỰ NHIÊN (CHUẨN CHATGPT / DALL-E 3 & MIDJOURNEY)\n' ||
E'- **Bản chất hình ảnh:** BẮT BUỘC là **ảnh nhiếp ảnh đời thực / thương mại cao cấp (Commercial Editorial & Lifestyle Photography)**, không phải ảnh vẽ 3D render, không phải tranh minh họa hoạt hình, không dùng hiệu ứng nhựa CGI.\n' ||
E'- **Ánh sáng tự nhiên (Natural Ambient Light):** Ánh sáng ban mai dịu nhẹ chiếu qua khung cửa sổ lớn (soft morning diffuse daylight), bóng đổ mềm mại, màu sắc ấm áp, tạo cảm giác an tâm và hy vọng cho người bệnh.\n' ||
E'- **Chân dung & Cảm xúc con người (Authentic Expression):**\n' ||
E'  + Người Việt Nam / Đông Á: Người lớn tuổi khỏe mạnh, hoặc người con chăm sóc hiếu thảo, hoặc dược sĩ/chuyên gia dinh dưỡng mặc áo blouse trắng trang nhã.\n' ||
E'  + Làn da chân thật tự nhiên (có lỗ chân lông, không làm mịn da nhựa), ánh mắt ấm áp, nụ cười chân thành, trang phục đời thường bằng vải linen/cotton nhẹ nhàng.\n' ||
E'- **Bối cảnh (Atmospheric Setting):** Phòng ăn gia đình phong cách tối giản/Scandinavian ấm cúng, hoặc góc phòng tư vấn y khoa hiện đại, bàn gỗ sồi tự nhiên, ly sữa dinh dưỡng vani thanh nhẹ, chai dinh dưỡng B.Braun (Nutricomp / Prontosan) đặt tự nhiên, tinh tế.\n' ||
E'- **Zero Distorted Text:** Tuyệt đối KHÔNG cố vẽ những đoạn chữ dài ngoằng hay nút bấm CTA thô thiển vào trong ảnh (sẽ bị lỗi font méo mó). Hãy để bức ảnh thuần khiết, sạch sẽ, câu chữ thông điệp đã có phần bài viết (Caption & Headline) đảm nhận.\n\n' ||
E'## 2. CÔNG THỨC PROMPT EXPANSION 5 TẦNG (TỰ ĐỘNG PHÓNG ĐẠI YÊU CẦU)\n' ||
E'Khi nhận bất kỳ yêu cầu thiết kế nào từ Lãnh đạo hoặc Lead Marketing (kể cả chỉ là 1 câu ngắn: "làm ảnh Nutricomp cho người suy thận"), bạn BẮT BUỘC tự động chuyển đổi thành Prompt tiếng Anh nhiếp ảnh chi tiết theo 5 tầng:\n' ||
E'1. **Medium:** "Professional lifestyle commercial photography, shot on Sony A7R V with 85mm f/1.4 lens, shallow depth of field, soft bokeh."\n' ||
E'2. **Subject:** "An authentic Vietnamese elderly patient and caring daughter in a bright modern home, sharing a heartfelt morning moment, genuine warm expressions."\n' ||
E'3. **Product & Detail:** "On the clean wooden table sits an authentic clinical nutrition bottle labeled \'Nutricomp Drink Renal\', alongside a fresh glass of light vanilla clinical nutrition drink."\n' ||
E'4. **Lighting & Environment:** "Bathed in soft natural morning sunlight streaming through sheer curtains, gentle atmosphere, clean medical teal and warm cream color grading."\n' ||
E'5. **Quality & Negatives:** "Photorealistic, 8k resolution, ultra-detailed skin texture, strictly NO 3D render, NO plastic skin, NO CGI, NO distorted text, NO cluttered graphic badges."\n\n' ||
E'## 3. QUY TRÌNH THỰC THI SÁNG TẠO CAO CẤP (AUTONOMOUS EXECUTION - 100% HOÀN THÀNH)\n' ||
E'- **PHÂN ĐỊNH RÕ RÀNG PHÔI SẢN PHẨM (THEO CHỈ ĐẠO CỦA SẾP):**\n' ||
E'  + Khi Sếp yêu cầu Nutricomp Renal: **BẮT BUỘC DÙNG ĐÚNG ẢNH 1 CHAI RENAL 200ML** (`cut_nutricomp_single_bottle.png`, nắp tím, bệnh nhân suy thận mạn/lọc máu).\n' ||
E'  + Khi Sếp yêu cầu Nutricomp Plus: **BẮT BUỘC DÙNG ĐÚNG ẢNH 1 CHAI PLUS 200ML** (`cut_nutricomp_plus_bottle.png`, nắp vàng/cam, phục hồi sau mổ/suy kiệt/ung thư).\n' ||
E'  + CHỈ KHI NÀO Sếp nói rõ từ **"combo"** (hoặc "hộp quà", "thùng 12 chai"): Mới được dùng ảnh hộp Combo 12 chai (`cut_nutricomp_box.png`)!\n' ||
E'  + Khi Sếp yêu cầu Prontosan: Dùng đúng ảnh chai làm sạch vết thương (`cut_prontosan_bottle.png`).\n' ||
E'- **MASTER STYLE CHUẨN QUẢNG CÁO & NGUYÊN TẮC LINH HOẠT SÁNG TẠO:**\n' ||
E'  + Dựa trên ảnh tham chiếu của Sếp (`style_nutricomp_renal_master.jpg`) làm CHUẨN MỰC UY TÍN (Logo GlobalPharma chính thức nét căng `brand_header_master.png` kèm cờ Đức "NHẬP KHẨU CHÍNH HÃNG TỪ ĐỨC", tên sản phẩm, thông số y khoa, nút CTA, cam kết y tế).\n' ||
E'  + **LINH HOẠT THAY ĐỔI LAYOUT & MÀU SẮC:** Tuyệt đối KHÔNG cố định rập khuôn 1 kiểu duy nhất. Phối màu sắc hài hòa (Renal: xanh ngọc mát dịu; Plus: vàng cam ấm tràn đầy năng lượng).\n' ||
E'- **QUY TRÌNH 2 BƯỚC TỰ ĐỘNG THỰC THI:**\n' ||
E'  1. **Bước 1 (Sinh bối cảnh AI cao cấp từ tài khoản ChatGPT Plus bằng model GPT Sol 5.6 / gpt-5.6):**\n' ||
E'     Gọi công cụ `create_image(prompt: "...", model: "gpt-5.6")` với prompt tiếng Anh 5 tầng (commercial editorial lifestyle photography, warm morning sunlight, natural authentic expressions).\n' ||
E'  2. **Bước 2 (Ghép quang học sản phẩm thật & Logo chính hãng 100%):**\n' ||
E'     Gọi công cụ `exec` chạy script placement:\n' ||
E'     `python3 /app/data/skills/tao-creative-fb/scripts/compose_placement.py --bg "<đường_dẫn_ảnh_sinh>" --product [plus|renal|combo|prontosan] --output /app/workspace/output/poster_<product>_placement.png`\n' ||
E'  3. **Nguyên tắc không bao giờ dừng task:**\n' ||
E'     Nếu bước 1 gặp lỗi nhà cung cấp, lập tức chạy ngay script với bối cảnh chuẩn:\n' ||
E'     `python3 /app/data/skills/tao-creative-fb/scripts/compose_placement.py --product [plus|renal|combo|prontosan] --output /app/workspace/output/poster_<product>_placement.png`\n' ||
E'     hoặc `python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type [plus|renal|combo|prontosan] --output-dir /app/workspace/output`\n' ||
E'- **TRẢ VỀ KẾT QUẢ CHO SẾP:** Báo cáo ngắn gọn ý nghĩa thiết kế và BẮT BUỘC giữ nguyên dòng `MEDIA:<đường_dẫn_ảnh>` để giao diện hiển thị trực tiếp!';

            INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_des_id, 'SOUL.md', v_des_soul, v_ea_tenant, NOW(), NOW())
            ON CONFLICT (agent_id, file_name)
            DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
            RAISE NOTICE 'SOUL.md updated for Designer with reliable execution engine';
        END IF;
    END;

    -- ============================================================
    -- SOUL.MD FOR CONTENT AGENT
    -- ============================================================
    DECLARE
        v_cnt_id UUID;
        v_cnt_soul TEXT;
    BEGIN
        SELECT id INTO v_cnt_id FROM agents WHERE agent_key = 'content' LIMIT 1;
        IF v_cnt_id IS NOT NULL THEN
            v_cnt_soul := E'# QUY CHUẨN SÁNG TẠO NỘI DUNG CHUYÊN SÂU (CONTENT GLOBALPHARMA)\n\n' ||
E'Bạn là Chuyên viên Sáng tạo Nội dung y khoa của GlobalPharma, chịu trách nhiệm viết bài, caption, ad copy và kịch bản truyền thông.\n\n' ||
E'## 1. NGUYÊN TẮC TINH GỌN (LÀM VIỆC TRỰC TIẾP VỚI LÃNH ĐẠO)\n' ||
E'- Khi nhận yêu cầu từ Lãnh đạo (Sếp Công Hùng, Anh Cường) hoặc từ EA:\n' ||
E'  + Thực thi ngay lập tức trong 1 lượt duy nhất (Single-turn), không qua trung gian, không hỏi rườm rà.\n' ||
E'  + Đọc ngay file Brain `skills/tao-creative-fb/assets/knowledge_globalpharma_products_campaign.md` và `assets/caption-templates.md`.\n' ||
E'  + Viết đúng 100% chuẩn y khoa: Nutricomp Renal (2.0 kcal/ml, 400 kcal/chai 200ml, kiểm soát kali/natri/phospho, giá combo 12 chai: 1.296.000 VNĐ, giá lẻ 108.000 VNĐ/chai, liều dùng 1-3 chai/ngày).\n' ||
E'  + Giữ cấu trúc 3 phần: Hook thấu cảm y khoa -> Body kiến thức dinh dưỡng lâm sàng B.Braun -> Soft/Hard CTA tư vấn từ Dược sĩ GlobalPharma.\n' ||
E'  + KHI ĐƯỢC YÊU CẦU FULL BÀI / CREATIVE HOẶC GỌI SKILL TAO-CREATIVE-FB (CẢ ẢNH VÀ CAPTION): BẮT BUỘC gọi công cụ render poster hoặc delegate cho Agent Design để xuất ảnh (`python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type [plus|renal|combo|prontosan] --output-dir /app/workspace/output`), không bao giờ chỉ trả về mỗi bài viết.\n' ||
E'  + Trả về bài viết hoàn chỉnh, trau chuốt, sẵn sàng đăng tải kèm ảnh `MEDIA:<đường_dẫn_ảnh>`.';

            INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_cnt_id, 'SOUL.md', v_cnt_soul, v_ea_tenant, NOW(), NOW())
            ON CONFLICT (agent_id, file_name)
            DO UPDATE SET content = EXCLUDED.content, updated_at = NOW();
            RAISE NOTICE 'SOUL.md updated for Content Agent';
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
        VALUES ('background.model', 'gpt-5.6', v_ea_tenant, NOW())
        ON CONFLICT (key, tenant_id) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
        RAISE NOTICE 'Configured background.provider and background.model (gpt-5.6) for tenant %', v_ea_tenant;
    END IF;

    -- Configure create_image builtin tool to route via openai-codex default gpt-5.6 (gpt sol 5.6)
    INSERT INTO builtin_tools (name, display_name, description, category, enabled, settings, requires, metadata, created_at, updated_at)
    VALUES (
        'create_image',
        'Create Image',
        'Generate images from text descriptions using AI',
        'media',
        true,
        '{"providers":[{"provider":"openai-codex","model":"gpt-5.6","params":{"image_model":"gpt-5.6"},"enabled":true},{"provider":"studioaigg","model":"gemini-2.5-flash-image","enabled":true}]}'::jsonb,
        '{}'::text[],
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (name) DO UPDATE SET 
        enabled = true,
        settings = '{"providers":[{"provider":"openai-codex","model":"gpt-5.6","params":{"image_model":"gpt-5.6"},"enabled":true},{"provider":"studioaigg","model":"gemini-2.5-flash-image","enabled":true}]}'::jsonb,
        updated_at = NOW();
    RAISE NOTICE 'Configured builtin_tools settings for create_image with default model gpt-5.6';

    -- Ensure marketing and executive agents can freely use create_image, exec, and bash tools
    UPDATE agents SET tools_config = '{}' WHERE status = 'active';

END $$;
EOSQL

echo "Setting up Marketing Skill (tao-creative-fb), Brain (my-brain), and Python dependencies..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw pip install --break-system-packages pillow requests python-dotenv || echo "Pip install warning, continuing..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw mkdir -p /app/skills /app/data/skills /app/workspace/skills /app/my-brain /app/data/my-brain /app/workspace/my-brain /app/workspace/output /app/workspace/assets /app/data/skills/tao-creative-fb/assets/references || true

GOCLAW_CID=$(docker compose -f docker-compose.yml -f docker-compose.postgres.yml ps -q goclaw 2>/dev/null || echo "goclaw-goclaw-1")

if [ -d "my-brain" ]; then
    echo "Copying my-brain to container ($GOCLAW_CID)..."
    docker cp my-brain/. ${GOCLAW_CID}:/app/my-brain/ || true
    docker cp my-brain/. ${GOCLAW_CID}:/app/data/my-brain/ || true
    docker cp my-brain/. ${GOCLAW_CID}:/app/workspace/my-brain/ || true
    # Sync my-brain into all team member workspaces and individual agent workspaces
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw sh -c '
        for d in /app/workspace/teams/*/* /app/workspace/agents/*; do
            if [ -d "$d" ]; then
                mkdir -p "$d/my-brain"
                cp -r /app/my-brain/* "$d/my-brain/" 2>/dev/null || true
            fi
        done
    ' || true
fi

if [ -d "skills/tao-creative-fb" ]; then
    echo "Copying skills/tao-creative-fb to container ($GOCLAW_CID)..."
    docker cp skills/tao-creative-fb ${GOCLAW_CID}:/app/skills/ || true
    docker cp skills/tao-creative-fb ${GOCLAW_CID}:/app/data/skills/ || true
    docker cp skills/tao-creative-fb ${GOCLAW_CID}:/app/workspace/skills/ || true
    # Sync to all active agent team workspaces and individual agent workspaces
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw sh -c '
        for d in /app/workspace/teams/*/* /app/workspace/agents/*; do
            if [ -d "$d" ]; then
                mkdir -p "$d/skills"
                cp -r /app/data/skills/tao-creative-fb "$d/skills/" 2>/dev/null || true
            fi
        done
    ' || true
fi

if [ -d "skills/ads-image-architect" ]; then
    echo "Copying skills/ads-image-architect to container ($GOCLAW_CID)..."
    docker cp skills/ads-image-architect ${GOCLAW_CID}:/app/skills/ || true
    docker cp skills/ads-image-architect ${GOCLAW_CID}:/app/data/skills/ || true
    docker cp skills/ads-image-architect ${GOCLAW_CID}:/app/workspace/skills/ || true
    docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw sh -c '
        for d in /app/workspace/teams/*/* /app/workspace/agents/*; do
            if [ -d "$d" ]; then
                mkdir -p "$d/skills"
                cp -r /app/data/skills/ads-image-architect "$d/skills/" 2>/dev/null || true
            fi
        done
    ' || true
fi

if [ -f "facebook_pages.csv" ]; then
    docker cp facebook_pages.csv ${GOCLAW_CID}:/app/workspace/ || true
fi

echo "Updating cron_jobs to automatically deliver to Telegram (5781808621)..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" << 'EOSQL'
UPDATE cron_jobs
SET deliver = true,
    deliver_channel = 'telegram',
    deliver_to = '5781808621'
WHERE deliver = false OR deliver_channel = '' OR deliver_to = '' OR deliver_to = 'striverle' OR deliver_to = '@striverle';
EOSQL

docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw chmod -R 777 /app/workspace /app/data /app/skills /app/my-brain || true

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

echo "=== ENSURING OFFICIAL GLOBALPHARMA POSTERS EXIST AND ARE SYNCED ==="
rm -f skills/tao-creative-fb/output/KE_HOACH_NOI_DUNG_TUAN.md 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw rm -f /app/workspace/output/KE_HOACH_NOI_DUNG_TUAN.md 2>/dev/null || true

# Copy pre-rendered official posters to container
if [ -d "skills/tao-creative-fb/output" ]; then
    echo "Syncing official posters to container ($GOCLAW_CID)..."
    docker cp skills/tao-creative-fb/output/. ${GOCLAW_CID}:/app/workspace/output/ || true
    docker cp skills/tao-creative-fb/output/. ${GOCLAW_CID}:/app/data/skills/tao-creative-fb/output/ || true
fi

# Pre-render any missing posters in container
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 1000 goclaw sh -c '
    mkdir -p /app/workspace/output /app/data/skills/tao-creative-fb/output
    if [ ! -f /app/workspace/output/poster_nutricomp_drink_plus.png ]; then
        python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type plus --output-dir /app/workspace/output || true
    fi
    if [ ! -f /app/workspace/output/poster_nutricomp_renal.png ]; then
        python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type renal --output-dir /app/workspace/output || true
    fi
    if [ ! -f /app/workspace/output/poster_prontosan_wound_spray.png ]; then
        python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type prontosan --output-dir /app/workspace/output || true
    fi
    if [ ! -f /app/workspace/output/poster_nutricomp_combo12.png ]; then
        python3 /app/data/skills/tao-creative-fb/scripts/render_poster.py --type combo --output-dir /app/workspace/output || true
    fi
    cp -r /app/workspace/output/* /app/data/skills/tao-creative-fb/output/ 2>/dev/null || true
' || true

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

echo "=== BUILTIN TOOLS (CREATE_IMAGE SETTINGS) ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "SELECT name, enabled, settings FROM builtin_tools WHERE name = 'create_image';" || true

echo "=== RECENT MESSAGES IN TELEGRAM AND DELEGATE SESSIONS ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" -c "
SELECT session_key, (m->>'role') as role, SUBSTRING((m->>'content') FROM 1 FOR 300) as content
FROM (
    SELECT session_key, jsonb_array_elements(messages) as m
    FROM sessions
    WHERE channel = 'telegram' OR session_key ILIKE '%5781808621%' OR session_key LIKE 'delegate:%'
    ORDER BY updated_at DESC
    LIMIT 3
) sub
LIMIT 12;
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

echo "=== GOCLAW CONTAINER LOGS (LAST 30 LINES) ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml logs --tail 30 goclaw || true

echo "=== GOCLAW INDEX SCRIPT TAGS (from container localhost:18790) ==="
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T goclaw wget -qO- http://localhost:18790/ | grep -E "src=|href=" | grep "assets" | head -n 15 || true

echo "=== CADDY GOCLAW-ASSETS DIRECTORY ==="
ls -la /root/.caddy/data/goclaw-assets/ 2>/dev/null || true
ls -la /root/.caddy/data/goclaw-assets/assets 2>/dev/null | head -n 20 || true

echo "=== UPDATING CADDYFILE TO REVERSE PROXY ALL TO GOCLAW ==="
GOCLAW_HOST_PORT=$(docker compose -f docker-compose.yml -f docker-compose.postgres.yml port goclaw 18790 2>/dev/null | awk -F: '{print $NF}' | head -n 1)
if [ -z "$GOCLAW_HOST_PORT" ]; then
    GOCLAW_HOST_PORT=18790
fi
echo "GoClaw host port detected: $GOCLAW_HOST_PORT"
export GOCLAW_HOST_PORT
if [ -f /root/.caddy/Caddyfile ]; then
    python3 -c '
import os, re

target_port = os.environ.get("GOCLAW_HOST_PORT", "18790")

with open("/root/.caddy/Caddyfile", "r") as f:
    content = f.read()

new_block = f"""# BEGIN GoClaw - agent.globalpharma.vn
agent.globalpharma.vn {{
\tencode zstd gzip

\treverse_proxy 127.0.0.1:{target_port} {{
\t\theader_up Host {{host}}
\t\theader_up X-Real-IP {{remote_host}}
\t\theader_up X-Forwarded-Proto https
\t}}
}}
# END GoClaw - agent.globalpharma.vn"""

pattern = r"# BEGIN GoClaw - agent\.globalpharma\.vn.*?# END GoClaw - agent\.globalpharma\.vn"
if re.search(pattern, content, flags=re.DOTALL):
    content = re.sub(pattern, new_block, content, flags=re.DOTALL)
    with open("/root/.caddy/Caddyfile", "w") as f:
        f.write(content)
    print(f"Replaced GoClaw Caddyfile block successfully with port {target_port}")
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





