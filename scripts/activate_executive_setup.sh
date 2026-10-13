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
    v_openai_key TEXT;
BEGIN
    v_openai_key := convert_from(decode('c2stcHJvai1BUmNvWHRJc25ucGdaRndwOXdfUXpucXBGRXVOYnBBaGdtb3VIY2RweVB5X21KOWxtc3NEbEQxQm5mMkhmNTQ0S1BXdmJ5SmF4elQzQmxia0ZKOXpzR3c2bHFnSGNLOTFkLUlfTUx6UmZ6NUQ0UTJ4ZEZWNmJDUXBwMnZmS0ZSb1lsbWEwajBUclI4VnA2OVZOUzB1Q0RCWmROQUE=', 'base64'), 'UTF-8');
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
E'  + Khi Lãnh đạo yêu cầu "tạo content", "tạo bài đăng", "gen bài Page", "creative ads", "chọn ý tưởng 1/2/3" (hoặc chỉ nhắn "1", "2", "3", "chọn 2"), hoặc gọi skill `tao-creative-fb`:\n' ||
E'    BẮT BUỘC ĐỐI CHIẾU CHÍNH XÁC VỚI Ý TƯỞNG ĐÃ ĐỀ XUẤT ĐỂ XÁC ĐỊNH ĐÚNG 100% SẢN PHẨM:\n' ||
E'    - Nếu chọn Ý TƯỞNG 2 (hoặc chủ đề phục hồi sau phẫu thuật, sau mổ, suy kiệt, dinh dưỡng cao năng lượng 300 kcal, ăn kém):\n' ||
E'      👉 SẢN PHẨM BẮT BUỘC LÀ NUTRICOMP DRINK PLUS! TUYỆT ĐỐI KHÔNG VIẾT VỀ PRONTOSAN HAY RENAL!\n' ||
E'    - Nếu chọn Ý TƯỞNG 1 (hoặc chủ đề dinh dưỡng thận, lọc máu, chạy thận, suy thận mạn, kiểm soát đạm, 400 kcal):\n' ||
E'      👉 SẢN PHẨM BẮT BUỘC LÀ NUTRICOMP DRINK RENAL!\n' ||
E'    - Nếu chọn Ý TƯỞNG 3 (hoặc chủ đề rửa vết thương, vết loét, phá màng biofilm, sát trùng ngoài da):\n' ||
E'      👉 SẢN PHẨM BẮT BUỘC LÀ PRONTOSAN SPRAY!\n' ||
E'    - Nếu chọn combo 12 chai / hộp quà: SẢN PHẨM LÀ COMBO 12 CHAI.\n' ||
E'    🚫 QUY TẮC CỐT LÕI (TUYỆT ĐỐI KHÔNG TÁI SỬ DỤNG ẢNH CỦA LƯỢT TRƯỚC TRONG LỊCH SỬ CHAT):\n' ||
E'    - MỖI LẦN Sếp yêu cầu tạo bài đăng/poster là một ấn phẩm MỚI ĐỘC BẢN 100%.\n' ||
E'    - TUYỆT ĐỐI KHÔNG BAO GIỜ copy, lấy lại hoặc ghi lại đường dẫn ảnh (MEDIA:...) đã xuất hiện ở các câu trả lời hoặc tool result trước trong lịch sử cuộc trò chuyện!\n' ||
E'    - BẮT BUỘC PHẢI THỰC SỰ GỌI TOOL để sinh file ảnh mới toanh cho lượt này:\n' ||
E'      + Cách 1 (Khuyên dùng): Gọi công cụ `create_image(prompt: "...")` để vẽ bối cảnh nhiếp ảnh mới toanh theo góc nhìn của bài viết (hệ thống sẽ tự động ghép chai sản phẩm chính hãng và logo GlobalPharma lên bức ảnh đó).\n' ||
E'      + Cách 2: Gọi công cụ `exec` chạy render poster mới với đúng tiêu đề của bài viết: `render_poster --type [plus|renal|prontosan|combo] --headline "<tiêu đề bài viết>"`.\n' ||
E'    - Nghiêm cấm mọi hành vi không gọi tool mà tự ý chép lại đường dẫn ảnh cũ của lượt trước!\n' ||
E'  + Khi Lãnh đạo yêu cầu "đăng bài", "đăng lên page", "đăng fanpage", "publish facebook", "đăng 9 page" (cho Prontosan, Nutricomp, v.v.):\n' ||
E'    🚫 TUYỆT ĐỐI KHÔNG BÁO THIẾU TOKEN HAY THIẾU QUYỀN PUBLISH! HỆ THỐNG ĐÃ CÓ SẴN 100% TOKEN & DANH SÁCH 17 FANPAGE (BAO GỒM FANPAGE CHÍNH CÔNG TY `https://www.facebook.com/globalpharmavn` - ID: `321910945365410` - `Globalpharmavn - Sức Khỏe Cho Mọi Nhà`)!\n' ||
E'    File token đã lưu sẵn tại `pages.json` và `facebook_pages.csv` ngay trong workspace.\n' ||
E'    Bạn gọi NGAY công cụ: `post_facebook(image: "<đường_dẫn_ảnh>", caption: "<nội_dung_caption>", product: "prontosan" [hoặc "nutricomp" / "all"])`.\n' ||
E'    Hoặc gọi công cụ `exec` chạy lệnh: `post_facebook --image "<đường_dẫn_ảnh>" --caption "<nội_dung_caption>" --product [prontosan|nutricomp|all] (hoặc python3 /app/workspace/skills/tao-creative-fb/scripts/post_facebook.py ..., lưu ý KHÔNG gọi /app/data/)`.\n' ||
E'    Hệ thống sẽ tự động lọc đúng danh sách 9 Fanpage mục tiêu (9 Fanpage Prontosan nếu là Prontosan; 9 Fanpage Nutricomp nếu là Nutricomp Renal/Plus; CẢ 2 NHÓM ĐỀU LUÔN BAO GỒM FANPAGE CHÍNH CÔNG TY `https://www.facebook.com/globalpharmavn`), đăng thật qua Facebook Graph API kèm độ trễ 2s chống spam, và trả về bảng mã Post ID để bạn báo cáo ngay cho Sếp!\n' ||
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
E'- Bãi bỏ phong cách thiết kế poster cũ.\n\n' ||
E'## 4. QUY TRÌNH ĐĂNG BÀI LÊN MẠNG LƯỚI FANPAGE (KHI LÃNH ĐẠO RA LỆNH ĐĂNG)\n' ||
E'Hệ thống ĐÃ LƯU SẴN 100% token của toàn bộ 17 Fanpage (bao gồm Fanpage chính công ty `https://www.facebook.com/globalpharmavn` - ID: `321910945365410` - `Globalpharmavn - Sức Khỏe Cho Mọi Nhà`) tại `pages.json` và `facebook_pages.csv` ngay trong workspace.\n' ||
E'Khi nhận lệnh đăng bài lên Fanpage, gọi ngay công cụ `post_facebook` hoặc lệnh `exec: post_facebook --image "<ảnh>" --caption "<caption>" --product [prontosan|nutricomp|all] (hoặc python3 /app/workspace/skills/tao-creative-fb/scripts/post_facebook.py ..., lưu ý KHÔNG gọi /app/data/)`.\n' ||
E'Hệ thống tự động đăng lên đúng 9 Fanpage của từng nhóm (bao gồm Fanpage chính công ty `https://www.facebook.com/globalpharmavn`) qua Graph API và xuất bảng mã Post ID để báo cáo cho Sếp. TUYỆT ĐỐI KHÔNG BÁO THIẾU QUYỀN HAY THIẾU TOKEN!';

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
E'- **NGUYÊN TẮC BẮT BUỘC: KHÔNG TÁI SỬ DỤNG ẢNH MẪU - LUÔN TẠO POSTER / ẢNH MỚI 100%:**\n' ||
E'  + Toàn bộ các ảnh tham chiếu (`style_nutricomp_renal_master.jpg`, `poster_nutricomp_renal.png`, `poster_nutricomp_drink_plus.png`, `poster_prontosan_wound_spray.png`, `master_poster_*.png`) CHỈ LÀ TÀI LIỆU HƯỚNG DẪN VỀ BỐ CỤC VÀ STYLE THẨM MỸ!\n' ||
E'  + 🚫 TUYỆT ĐỐI CẤM gửi lại các file ảnh mẫu tĩnh cũ! Mỗi bài viết BẮT BUỘC phải sinh một bức ảnh/poster mới hoàn toàn độc bản!\n' ||
E'  + BẮT BUỘC dùng 1 trong 2 cách sau để xuất ảnh mới:\n' ||
E'    * Cách 1 (Sáng tạo bối cảnh đời thực mới qua AI - KHUYÊN DÙNG): Gọi công cụ `create_image(prompt: "...")` để vẽ bối cảnh nhiếp ảnh mới toanh theo góc nhìn của bài viết (phòng ăn gia đình ấm cúng, người sau mổ phục hồi thể trạng, người cao tuổi an tâm, v.v.), hệ thống sẽ tự động ghép chai sản phẩm chính hãng và logo GlobalPharma lên bức ảnh đó.\n' ||
E'    * Cách 2 (Render poster mới với tiêu đề bài viết): Gọi công cụ `exec` chạy: `render_poster --type [plus|renal|prontosan|combo] --headline "<tiêu đề bài viết>" --subline "<tóm tắt thông điệp>" --output /app/workspace/output/creative_<time>.png` để sinh ra file poster mới mang đúng tiêu đề của bài viết!\n' ||
E'- **TRẢ VỀ KẾT QUẢ CHO SẾP:** Báo cáo ngắn gọn ý nghĩa thiết kế và BẮT BUỘC kết thúc bằng dòng `MEDIA:<đường_dẫn_ảnh_mới>` để giao diện hiển thị trực tiếp!';

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
E'  + KHI ĐƯỢC YÊU CẦU FULL BÀI / CREATIVE HOẶC GỌI SKILL TAO-CREATIVE-FB (CẢ ẢNH VÀ CAPTION): BẮT BUỘC gọi công cụ render poster hoặc delegate cho Agent Design để xuất ảnh mới mang đúng tiêu đề (`render_poster --type [plus|renal|combo|prontosan] --headline "<tiêu đề>" --subline "<tóm tắt>" --output /app/workspace/output/creative_<time>.png (hoặc python3 /app/workspace/skills/tao-creative-fb/scripts/render_poster.py ..., lưu ý KHÔNG gọi /app/data/)`), không bao giờ chỉ trả về mỗi bài viết.\n' ||
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

    -- 4. CONFIGURE CHATGPT PLUS POOL ACROSS ALL 3 ACCOUNTS (openai-codex, chatgpthnkt, lequyenopenai-codex)
    -- Đảm bảo alias 'hnkt' trỏ đến 'chatgpthnkt' (hoặc ngược lại) để agent gọi trực tiếp tên nào cũng chạy
    INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
    SELECT gen_random_uuid(), 'hnkt', 'ChatGPT Plus HNKT (Alias)', provider_type, api_key, api_base, tenant_id, enabled, settings, NOW(), NOW()
    FROM llm_providers
    WHERE name = 'chatgpthnkt' AND NOT EXISTS (SELECT 1 FROM llm_providers WHERE name = 'hnkt');

    INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
    SELECT gen_random_uuid(), 'chatgpthnkt', 'ChatGPT Plus HNKT', provider_type, api_key, api_base, tenant_id, enabled, settings, NOW(), NOW()
    FROM llm_providers
    WHERE name = 'hnkt' AND NOT EXISTS (SELECT 1 FROM llm_providers WHERE name = 'chatgpthnkt');

    -- Tự động liên kết chéo tất cả tài khoản ChatGPT OAuth trong DB vào codex_pool
    -- Khi 1 tài khoản hết hạn/quota/auth fail, hệ thống tự failover/round-robin sang các tài khoản còn lại
    DECLARE
        r_lp RECORD;
        v_pool_members text[];
    BEGIN
        FOR r_lp IN SELECT name FROM llm_providers WHERE provider_type = 'chatgpt_oauth' LOOP
            SELECT array_agg(name) INTO v_pool_members
            FROM llm_providers
            WHERE provider_type = 'chatgpt_oauth' AND name != r_lp.name;

            IF v_pool_members IS NOT NULL AND array_length(v_pool_members, 1) > 0 THEN
                UPDATE llm_providers
                SET settings = jsonb_set(
                    COALESCE(settings, '{}'::jsonb),
                    '{codex_pool}',
                    jsonb_build_object(
                        'strategy', 'round_robin',
                        'extra_provider_names', to_jsonb(v_pool_members)
                    )
                ),
                updated_at = NOW()
                WHERE name = r_lp.name;
                RAISE NOTICE 'Configured codex_pool on provider % with backups: %', r_lp.name, v_pool_members;
            END IF;
        END LOOP;
    END;

    -- 5. CONFIGURE OFFICIAL OPENAI PROVIDER (API KEY)
    -- Cho phép agent gọi trực tiếp provider "openai" (gpt-4o, dall-e-3, v.v.)
    INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'openai',
        'OpenAI Official (API Key)',
        'openai_compat',
        v_openai_key,
        'https://api.openai.com/v1',
        v_ea_tenant,
        true,
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (tenant_id, name) DO UPDATE SET
        api_key = EXCLUDED.api_key,
        api_base = 'https://api.openai.com/v1',
        provider_type = 'openai_compat',
        display_name = 'OpenAI Official (API Key)',
        enabled = true,
        updated_at = NOW();

    INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'openai-api',
        'OpenAI API (Alias)',
        'openai_compat',
        v_openai_key,
        'https://api.openai.com/v1',
        v_ea_tenant,
        true,
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (tenant_id, name) DO UPDATE SET
        api_key = EXCLUDED.api_key,
        api_base = 'https://api.openai.com/v1',
        provider_type = 'openai_compat',
        display_name = 'OpenAI API (Alias)',
        enabled = true,
        updated_at = NOW();

    IF v_ea_tenant != '0193a5b0-7000-7000-8000-000000000001'::uuid THEN
        INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'openai',
            'OpenAI Official (API Key)',
            'openai_compat',
            v_openai_key,
            'https://api.openai.com/v1',
            '0193a5b0-7000-7000-8000-000000000001'::uuid,
            true,
            '{}'::jsonb,
            NOW(),
            NOW()
        )
        ON CONFLICT (tenant_id, name) DO UPDATE SET
            api_key = EXCLUDED.api_key,
            api_base = 'https://api.openai.com/v1',
            provider_type = 'openai_compat',
            display_name = 'OpenAI Official (API Key)',
            enabled = true,
            updated_at = NOW();

        INSERT INTO llm_providers (id, name, display_name, provider_type, api_key, api_base, tenant_id, enabled, settings, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'openai-api',
            'OpenAI API (Alias)',
            'openai_compat',
            v_openai_key,
            'https://api.openai.com/v1',
            '0193a5b0-7000-7000-8000-000000000001'::uuid,
            true,
            '{}'::jsonb,
            NOW(),
            NOW()
        )
        ON CONFLICT (tenant_id, name) DO UPDATE SET
            api_key = EXCLUDED.api_key,
            api_base = 'https://api.openai.com/v1',
            provider_type = 'openai_compat',
            display_name = 'OpenAI API (Alias)',
            enabled = true,
            updated_at = NOW();
    END IF;
    RAISE NOTICE 'Configured official OpenAI provider (API Key) for tenant % and master', v_ea_tenant;

    -- Configure create_image builtin tool
    -- Chuỗi ưu tiên: Thử openai-codex (được router pool hỗ trợ toàn bộ các tài khoản Plus),
    -- sau đó thử trực tiếp chatgpthnkt, hnkt, lequyenopenai-codex,
    -- rồi thử tiếp OpenAI Official (DALL-E 3), cuối cùng mới tới Gemini studioaigg
    INSERT INTO builtin_tools (name, display_name, description, category, enabled, settings, requires, metadata, created_at, updated_at)
    VALUES (
        'create_image',
        'Create Image',
        'Generate images from text descriptions using AI',
        'media',
        true,
        '{"providers":[{"provider":"openai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"chatgpthnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"hnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"lequyenopenai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"openai","model":"dall-e-3","enabled":true},{"provider":"studioaigg","model":"gemini-2.5-flash-image","enabled":true}]}'::jsonb,
        '{}'::text[],
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (name) DO UPDATE SET 
        enabled = true,
        settings = '{"providers":[{"provider":"openai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"chatgpthnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"hnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"lequyenopenai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"openai","model":"dall-e-3","enabled":true},{"provider":"studioaigg","model":"gemini-2.5-flash-image","enabled":true}]}'::jsonb,
        updated_at = NOW();

    UPDATE builtin_tools 
    SET settings = '{"providers":[{"provider":"openai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"chatgpthnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"hnkt","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"lequyenopenai-codex","model":"gpt-5.5","params":{"image_model":"gpt-image-2.5-flare"},"enabled":true},{"provider":"openai","model":"dall-e-3","enabled":true},{"provider":"studioaigg","model":"gemini-2.5-flash-image","enabled":true}]}'::jsonb
    WHERE name = 'create_image';
    RAISE NOTICE 'Configured builtin_tools settings for create_image with full ChatGPT Plus account pool fallback and OpenAI DALL-E 3 backup';

    -- Configure post_facebook builtin tool
    INSERT INTO builtin_tools (name, display_name, description, category, enabled, settings, requires, metadata, created_at, updated_at)
    VALUES (
        'post_facebook',
        'Post Facebook Fanpages',
        'Publish images and captions to GlobalPharma Facebook Fanpages via Graph API using stored access tokens',
        'social',
        true,
        '{}'::jsonb,
        '{}'::text[],
        '{}'::jsonb,
        NOW(),
        NOW()
    )
    ON CONFLICT (name) DO UPDATE SET enabled = true, updated_at = NOW();
    RAISE NOTICE 'Registered builtin tool post_facebook';

    -- Ensure marketing and executive agents can freely use create_image, post_facebook, exec, and bash tools
    UPDATE agents SET tools_config = '{}' WHERE status = 'active';

    -- Pin tao-creative-fb skill for all active agents so they always have full skill instructions inline
    UPDATE agents SET other_config = jsonb_set(COALESCE(other_config, '{}'::jsonb), '{pinned_skills}', '["tao-creative-fb"]'::jsonb) WHERE status = 'active';
    RAISE NOTICE 'Pinned tao-creative-fb skill for all active agents';

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
        REAL_OPENAI_KEY=$(echo "c2stcHJvai1BUmNvWHRJc25ucGdaRndwOXdfUXpucXBGRXVOYnBBaGdtb3VIY2RweVB5X21KOWxtc3NEbEQxQm5mMkhmNTQ0S1BXdmJ5SmF4elQzQmxia0ZKOXpzR3c2bHFnSGNLOTFkLUlfTUx6UmZ6NUQ0UTJ4ZEZWNmJDUXBwMnZmS0ZSb1lsbWEwajBUclI4VnA2OVZOUzB1Q0RCWmROQUE=" | base64 -d)
        echo "OPENAI_API_KEY=\"$REAL_OPENAI_KEY\"" > /app/data/skills/tao-creative-fb/.env
        echo "OPENAI_IMAGE_MODEL=\"dall-e-3\"" >> /app/data/skills/tao-creative-fb/.env
        cp /app/data/skills/tao-creative-fb/.env /app/skills/tao-creative-fb/.env 2>/dev/null || true
        cp /app/data/skills/tao-creative-fb/.env /app/workspace/skills/tao-creative-fb/.env 2>/dev/null || true
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
    docker cp facebook_pages.csv ${GOCLAW_CID}:/app/data/ || true
    docker cp facebook_pages.csv ${GOCLAW_CID}:/app/ || true
fi

if [ -f "skills/tao-creative-fb/pages.json" ]; then
    docker cp skills/tao-creative-fb/pages.json ${GOCLAW_CID}:/app/workspace/ || true
    docker cp skills/tao-creative-fb/pages.json ${GOCLAW_CID}:/app/data/ || true
    docker cp skills/tao-creative-fb/pages.json ${GOCLAW_CID}:/app/data/skills/tao-creative-fb/ || true
    docker cp skills/tao-creative-fb/pages.json ${GOCLAW_CID}:/app/skills/tao-creative-fb/ || true
fi

# Sync facebook_pages.csv and pages.json to all agent and team workspaces + symlink post_facebook CLI
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw sh -c '
    ln -sf /app/data/skills/tao-creative-fb/scripts/post_facebook.py /usr/local/bin/post_facebook 2>/dev/null || true
    chmod +x /app/data/skills/tao-creative-fb/scripts/post_facebook.py 2>/dev/null || true
    ln -sf /app/data/skills/tao-creative-fb/scripts/render_poster.py /usr/local/bin/render_poster 2>/dev/null || true
    chmod +x /app/data/skills/tao-creative-fb/scripts/render_poster.py 2>/dev/null || true
    ln -sf /app/data/skills/tao-creative-fb/scripts/compose_placement.py /usr/local/bin/compose_placement 2>/dev/null || true
    chmod +x /app/data/skills/tao-creative-fb/scripts/compose_placement.py 2>/dev/null || true
    chmod -R +x /app/workspace/skills/tao-creative-fb/scripts/ /app/data/skills/tao-creative-fb/scripts/ 2>/dev/null || true
    for d in /app/workspace/teams/*/* /app/workspace/agents/*; do
        if [ -d "$d" ]; then
            cp -f /app/workspace/facebook_pages.csv "$d/facebook_pages.csv" 2>/dev/null || true
            cp -f /app/data/skills/tao-creative-fb/pages.json "$d/pages.json" 2>/dev/null || true
        fi
    done
' || true

echo "Updating cron_jobs to automatically deliver to Telegram (5781808621)..."
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -e PGPASSWORD="$PG_PASS" postgres psql -U "$PG_USER" -d "$PG_DB" << 'EOSQL'
UPDATE cron_jobs
SET deliver = true,
    deliver_channel = 'telegram',
    deliver_to = '5781808621'
WHERE deliver = false OR deliver_channel = '' OR deliver_to = '' OR deliver_to = 'striverle' OR deliver_to = '@striverle';

-- Delete conflicting old cron job
DELETE FROM cron_jobs WHERE name = 'fanpage-content';

-- Preserve active Telegram conversation history
-- UPDATE sessions SET messages = '[]'::jsonb, updated_at = NOW() WHERE session_key LIKE '%5781808621%';

-- 3 TÁC VỤ ĐỊNH KỲ BUỔI SÁNG (NUTRICOMP DRINK PLUS 9H00, RENAL 9H10, PRONTOSAN 9H20)
DO $$
DECLARE
    v_target_agent UUID;
    v_tenant UUID;
    v_owner VARCHAR;
BEGIN
    -- Tìm Agent thực thi (ưu tiên Trợ lý điều hành hoặc Lead Marketing)
    SELECT id, tenant_id, owner_id INTO v_target_agent, v_tenant, v_owner
    FROM agents
    WHERE (display_name ILIKE '%Trợ lý điều hành%' OR display_name ILIKE '%Trợ lý%' OR agent_key ILIKE '%tro-ly%' OR agent_key ILIKE '%assistant%')
      AND status = 'active'
    ORDER BY created_at ASC
    LIMIT 1;

    IF v_target_agent IS NULL THEN
        SELECT id, tenant_id, owner_id INTO v_target_agent, v_tenant, v_owner
        FROM agents
        WHERE status = 'active'
        ORDER BY is_default DESC, created_at ASC
        LIMIT 1;
    END IF;

    IF v_target_agent IS NOT NULL AND v_tenant IS NOT NULL THEN
        -- Task 1: 9h00 sáng - Nutricomp Drink Plus
        INSERT INTO cron_jobs (
            id, tenant_id, agent_id, user_id, name, enabled, schedule_kind, cron_expression, timezone,
            payload, stateless, deliver, deliver_channel, deliver_to, wake_heartbeat, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            v_tenant,
            v_target_agent,
            v_owner,
            'daily-morning-nutricomp-plus-0900',
            true,
            'cron',
            '0 9 * * *',
            'Asia/Ho_Chi_Minh',
            jsonb_build_object(
                'kind', 'agent_turn',
                'message', 'Đã đến lịch định kỳ 9h00 sáng. Hãy thực hiện nhiệm vụ:
1. Đọc kiến thức và tài liệu sản phẩm Nutricomp Drink Plus trong Brain / Skills.
2. Chọn ngẫu nhiên 1 góc độ sáng tạo (angle) thật ấn tượng, khác biệt và sâu sắc về mặt lâm sàng/dinh dưỡng (ví dụ: phục hồi sau mổ, người suy kiệt, ung thư cần năng lượng cao 300 kcal/chai, bổ sung EPA chống suy mòn, tiện dụng dễ uống).
3. Viết 1 bài đăng Facebook chuẩn y khoa và truyền cảm hứng (độ dài 80-150 từ, có hashtag #Nutricomp #NutricompDrinkPlus #Globalpharma #DinhDuongYHoc).
4. BẮT BUỘC THỰC SỰ GỌI CÔNG CỤ TẠO ẢNH MỚI TRONG LƯỢT NÀY (TUYỆT ĐỐI KHÔNG BỊA ĐƯỜNG DẪN ẢNH VÀ KHÔNG GỬI LẠI ẢNH CŨ):
   - Bạn BẮT BUỘC phải gọi công cụ trong lượt này để tạo ảnh thật:
     + Cách 1 (Khuyên dùng): Dùng công cụ create_image(prompt: "...") để sinh ảnh bối cảnh mới độc bản cho bài viết (hệ thống sẽ tự động ghép chai Nutricomp Drink Plus nắp cam và logo GlobalPharma lên ảnh).
     + Cách 2: Dùng công cụ exec chạy: render_poster --type plus --headline "<tiêu đề ngắn bài viết>" --subline "Bổ sung dinh dưỡng cao năng lượng 300Kcal/200ml"
   - Sau khi công cụ hoàn tất và trả về file ảnh thành phẩm, bạn mới kết thúc bài trả lời bằng dòng: MEDIA:<đường_dẫn_ảnh_vừa_tạo> để hệ thống tự động gửi ảnh poster trực tiếp vào Telegram cùng bài viết cho Sếp duyệt.
5. Gửi toàn bộ nội dung bài viết + ảnh poster vào Telegram này để Sếp duyệt. Nhắc rõ danh sách 9 Fanpage (8 Fanpage Nutricomp + Fanpage chính công ty GlobalPharma) sẽ đăng khi Sếp bấm duyệt/xác nhận:
   - https://www.facebook.com/globalpharmavn/ (Fanpage chính công ty: Globalpharmavn - Sức Khỏe Cho Mọi Nhà - ID: 321910945365410)
   - https://www.facebook.com/nutricomp.globalpharma/
   - https://www.facebook.com/suadinhduongyhocduc/
   - https://www.facebook.com/dinhduongducnutricomp/
   - https://www.facebook.com/nutricomplus/
   - https://www.facebook.com/nutricomprenal/
   - https://www.facebook.com/dinhduongphuchoinangluong/
   - https://www.facebook.com/suadinhduongyhocduc.nutricomp/
   - https://www.facebook.com/suckhoechomoinhacom/
(Lưu ý: Chỉ đăng lên 9 page trên — luôn bao gồm Fanpage chính công ty https://www.facebook.com/globalpharmavn/ — khi Sếp duyệt lệnh đăng qua tool post_facebook với product="nutricomp").'
            ),
            false,
            true,
            'telegram',
            '5781808621',
            false,
            NOW(),
            NOW()
        )
        ON CONFLICT (agent_id, tenant_id, name)
        DO UPDATE SET
            cron_expression = EXCLUDED.cron_expression,
            timezone = EXCLUDED.timezone,
            enabled = true,
            deliver = true,
            deliver_channel = 'telegram',
            deliver_to = '5781808621',
            payload = EXCLUDED.payload,
            updated_at = NOW();

        -- Task 2: 9h10 sáng - Nutricomp Drink Renal
        INSERT INTO cron_jobs (
            id, tenant_id, agent_id, user_id, name, enabled, schedule_kind, cron_expression, timezone,
            payload, stateless, deliver, deliver_channel, deliver_to, wake_heartbeat, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            v_tenant,
            v_target_agent,
            v_owner,
            'daily-morning-nutricomp-renal-0910',
            true,
            'cron',
            '10 9 * * *',
            'Asia/Ho_Chi_Minh',
            jsonb_build_object(
                'kind', 'agent_turn',
                'message', 'Đã đến lịch định kỳ 9h10 sáng. Hãy thực hiện nhiệm vụ:
1. Đọc kiến thức và tài liệu sản phẩm Nutricomp Drink Renal trong Brain / Skills.
2. Chọn ngẫu nhiên 1 góc độ sáng tạo (angle) thật ấn tượng, khác biệt và chuyên sâu y khoa cho bệnh nhân suy thận (ví dụ: công thức giảm protein, kiểm soát nghiêm ngặt Kali - Natri - Photpho, bảo tồn chức năng thận, năng lượng chuẩn xác 2.0 kcal/ml, hương vani thơm ngon).
3. Viết 1 bài đăng Facebook chuẩn y khoa, tận tâm (độ dài 80-150 từ, có hashtag #Nutricomp #NutricompDrinkRenal #DinhDuongBenhNhanThan #Globalpharma).
4. BẮT BUỘC THỰC SỰ GỌI CÔNG CỤ TẠO ẢNH MỚI TRONG LƯỢT NÀY (TUYỆT ĐỐI KHÔNG BỊA ĐƯỜNG DẪN ẢNH VÀ KHÔNG GỬI LẠI ẢNH CŨ):
   - Bạn BẮT BUỘC phải gọi công cụ trong lượt này để tạo ảnh thật:
     + Cách 1 (Khuyên dùng): Dùng công cụ create_image(prompt: "...") để sinh ảnh bối cảnh mới độc bản cho bài viết (hệ thống sẽ tự động ghép chai Nutricomp Drink Renal nắp tím và logo GlobalPharma lên ảnh).
     + Cách 2: Dùng công cụ exec chạy: render_poster --type renal --headline "<tiêu đề ngắn bài viết>" --subline "Dinh dưỡng chuyên biệt kiểm soát điện giải"
   - Sau khi công cụ hoàn tất và trả về file ảnh thành phẩm, bạn mới kết thúc bài trả lời bằng dòng: MEDIA:<đường_dẫn_ảnh_vừa_tạo> để hệ thống tự động gửi ảnh poster trực tiếp vào Telegram cùng bài viết cho Sếp duyệt.
5. Gửi toàn bộ nội dung bài viết + ảnh poster vào Telegram này để Sếp duyệt. Nhắc rõ danh sách 9 Fanpage (8 Fanpage Nutricomp + Fanpage chính công ty GlobalPharma) sẽ đăng khi Sếp bấm duyệt/xác nhận:
   - https://www.facebook.com/globalpharmavn/ (Fanpage chính công ty: Globalpharmavn - Sức Khỏe Cho Mọi Nhà - ID: 321910945365410)
   - https://www.facebook.com/nutricomp.globalpharma/
   - https://www.facebook.com/suadinhduongyhocduc/
   - https://www.facebook.com/dinhduongducnutricomp/
   - https://www.facebook.com/nutricomplus/
   - https://www.facebook.com/nutricomprenal/
   - https://www.facebook.com/dinhduongphuchoinangluong/
   - https://www.facebook.com/suadinhduongyhocduc.nutricomp/
   - https://www.facebook.com/suckhoechomoinhacom/
(Lưu ý: Chỉ đăng lên 9 page trên — luôn bao gồm Fanpage chính công ty https://www.facebook.com/globalpharmavn/ — khi Sếp duyệt lệnh đăng qua tool post_facebook với product="nutricomp").'
            ),
            false,
            true,
            'telegram',
            '5781808621',
            false,
            NOW(),
            NOW()
        )
        ON CONFLICT (agent_id, tenant_id, name)
        DO UPDATE SET
            cron_expression = EXCLUDED.cron_expression,
            timezone = EXCLUDED.timezone,
            enabled = true,
            deliver = true,
            deliver_channel = 'telegram',
            deliver_to = '5781808621',
            payload = EXCLUDED.payload,
            updated_at = NOW();

        -- Task 3: 9h20 sáng - Prontosan
        INSERT INTO cron_jobs (
            id, tenant_id, agent_id, user_id, name, enabled, schedule_kind, cron_expression, timezone,
            payload, stateless, deliver, deliver_channel, deliver_to, wake_heartbeat, created_at, updated_at
        ) VALUES (
            gen_random_uuid(),
            v_tenant,
            v_target_agent,
            v_owner,
            'daily-morning-prontosan-0920',
            true,
            'cron',
            '20 9 * * *',
            'Asia/Ho_Chi_Minh',
            jsonb_build_object(
                'kind', 'agent_turn',
                'message', 'Đã đến lịch định kỳ 9h20 sáng. Hãy thực hiện nhiệm vụ:
1. Đọc kiến thức và tài liệu giải pháp Prontosan (B. Braun / Đức) trong Brain / Skills.
2. Chọn ngẫu nhiên 1 góc độ sáng tạo (angle) thật ấn tượng, khác biệt và thuyết phục về chăm sóc vết thương (ví dụ: phá vỡ màng Biofilm cứng đầu, ngăn ngừa nhiễm trùng tái phát, làm sạch vết thương không đau xót, bộ đôi dung dịch rửa + gel kháng khuẩn, vết loét tiểu đường/tì đè).
3. Viết 1 bài đăng Facebook chuẩn chuyên môn y tế (độ dài 80-150 từ, có hashtag #Prontosan #BBraun #PhaVoBiofilm #ChamSocVetThuong #Globalpharma).
4. BẮT BUỘC THỰC SỰ GỌI CÔNG CỤ TẠO ẢNH MỚI TRONG LƯỢT NÀY (TUYỆT ĐỐI KHÔNG BỊA ĐƯỜNG DẪN ẢNH VÀ KHÔNG GỬI LẠI ẢNH CŨ):
   - Bạn BẮT BUỘC phải gọi công cụ trong lượt này để tạo ảnh thật:
     + Cách 1 (Khuyên dùng): Dùng công cụ create_image(prompt: "...") để sinh ảnh bối cảnh mới độc bản cho bài viết (hệ thống sẽ tự động ghép chai xịt Prontosan và logo GlobalPharma lên ảnh).
     + Cách 2: Dùng công cụ exec chạy: render_poster --type prontosan --headline "<tiêu đề ngắn bài viết>" --subline "Làm sạch  •  Rửa  •  Dưỡng ẩm"
   - Sau khi công cụ hoàn tất và trả về file ảnh thành phẩm, bạn mới kết thúc bài trả lời bằng dòng: MEDIA:<đường_dẫn_ảnh_vừa_tạo> để hệ thống tự động gửi ảnh poster trực tiếp vào Telegram cùng bài viết cho Sếp duyệt.
5. Gửi toàn bộ nội dung bài viết + ảnh poster vào Telegram này để Sếp duyệt. Nhắc rõ danh sách 9 Fanpage (8 Fanpage Prontosan + Fanpage chính công ty GlobalPharma) sẽ đăng khi Sếp bấm duyệt/xác nhận:
   - https://www.facebook.com/globalpharmavn/ (Fanpage chính công ty: Globalpharmavn - Sức Khỏe Cho Mọi Nhà - ID: 321910945365410)
   - https://www.facebook.com/prontosan.globalpharma/
   - https://www.facebook.com/giaiphapnhanhlanhvetthuong
   - https://www.facebook.com/giaiphapchamsocvetthuong
   - https://www.facebook.com/prontosanchamsocvetthuong/
   - https://www.facebook.com/chamsocvetthuongprontosan/
   - https://www.facebook.com/prontosanspray/
   - https://www.facebook.com/prontosanspraylamlanhvetthuong/
   - https://www.facebook.com/suckhoechomoinhacom/
(Lưu ý: Tuyệt đối chỉ đăng vào 9 page trên — luôn bao gồm Fanpage chính công ty https://www.facebook.com/globalpharmavn/ — không lẫn sang page Nutricomp. Chỉ đăng khi Sếp duyệt lệnh qua tool post_facebook với product="prontosan").'
            ),
            false,
            true,
            'telegram',
            '5781808621',
            false,
            NOW(),
            NOW()
        )
        ON CONFLICT (agent_id, tenant_id, name)
        DO UPDATE SET
            cron_expression = EXCLUDED.cron_expression,
            timezone = EXCLUDED.timezone,
            enabled = true,
            deliver = true,
            deliver_channel = 'telegram',
            deliver_to = '5781808621',
            payload = EXCLUDED.payload,
            updated_at = NOW();

        RAISE NOTICE 'Successfully configured 3 morning cron tasks (09h00, 09h10, 09h20) for agent %', v_target_agent;
    END IF;
END $$;
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

echo "=== CLEANING UP OBSOLETE STATIC POSTER MOCKUPS & ENFORCING PERMISSIONS ==="
rm -f skills/tao-creative-fb/output/KE_HOACH_NOI_DUNG_TUAN.md skills/tao-creative-fb/output/poster_*.png skills/tao-creative-fb/output/poster_*.jpg 2>/dev/null || true
docker compose -f docker-compose.yml -f docker-compose.postgres.yml exec -T -u 0 goclaw sh -c '
    rm -f /app/workspace/output/KE_HOACH_NOI_DUNG_TUAN.md /app/workspace/output/poster_*.png /app/workspace/output/poster_*.jpg /app/data/skills/tao-creative-fb/output/poster_*.png /app/data/skills/tao-creative-fb/output/poster_*.jpg 2>/dev/null || true
    mkdir -p /app/workspace/output /app/data/skills/tao-creative-fb/output
    chmod -R 777 /app/workspace /app/data /app/skills
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





