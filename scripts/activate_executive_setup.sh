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
    v_soul_content TEXT;
    v_extra_soul TEXT;
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

    -- Insert/Update Agent Links from EA to each lead
    IF v_ea_id IS NOT NULL THEN
        -- Lead Marketing
        IF v_mkt_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_mkt_id, 'bidirectional', 'Ủy quyền nhiệm vụ Marketing, bài viết truyền thông, quảng cáo Fanpage', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA -> Lead Marketing';
        END IF;

        -- Lead CSKH
        IF v_cskh_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_cskh_id, 'bidirectional', 'Ủy quyền xử lý CSKH, tư vấn khách hàng, phản hồi dịch vụ', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA -> Lead CSKH';
        END IF;

        -- Lead Legal
        IF v_legal_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_legal_id, 'bidirectional', 'Ủy quyền kiểm duyệt pháp lý, thẩm định tuân thủ y tế/dược phẩm', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA -> Lead Legal';
        END IF;

        -- Lead IT
        IF v_it_id IS NOT NULL THEN
            INSERT INTO agent_links (id, source_agent_id, target_agent_id, direction, description, status, created_by, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, v_it_id, 'bidirectional', 'Ủy quyền xử lý kỹ thuật, giải pháp AI, công nghệ, GoClaw', 'active', COALESCE(v_ea_owner, 'admin'), v_ea_tenant, NOW(), NOW())
            ON CONFLICT (source_agent_id, target_agent_id) 
            DO UPDATE SET status = 'active', direction = 'bidirectional', description = EXCLUDED.description, updated_at = NOW();
            RAISE NOTICE 'Linked EA -> Lead IT';
        END IF;

        -- Update SOUL.md in agent_context_files
        v_extra_soul := E'\n\n# BẢN QUY CHẾ ĐIỀU HÀNH & PHỐI HỢP LIÊN PHÒNG BAN (GLOBALPHARMA)\n\n' ||
E'Bạn là GP - Trợ lý điều hành cấp cao (Chief of Staff) của Ban Lãnh đạo GlobalPharma, trực tiếp hỗ trợ Sếp Công Hùng và Anh Cường.\n\n' ||
E'## 1. CƠ CẤU 4 PHÒNG BAN CHUYÊN MÔN (4 TEAM AI)\n' ||
E'Hệ thống vận hành của công ty gồm 4 phòng ban chính thức trên GoClaw. Khi Lãnh đạo hỏi về danh sách phòng ban hay cơ cấu công ty, KHÔNG tự suy đoán các phòng ban lý thuyết, mà BẮT BUỘC báo cáo chính xác 4 phòng ban sau:\n\n' ||
E'1. **Phòng CSKH (Chăm sóc khách hàng)**: Trưởng phòng Lead CSKH 👑 (điều phối chất lượng dịch vụ, xử lý cảnh báo, phàn nàn).\n' ||
E'2. **Phòng Marketing (Truyền thông & Tiếp thị)**: Trưởng phòng Lead Marketing 👑 (phân rã mục tiêu, giao việc, kiểm soát tiến độ và chất lượng cho Ads, Content, Design).\n' ||
E'3. **Phòng Pháp Lý**: Trưởng phòng Lead Legal 👑 (rà soát tuân thủ pháp lý y tế, dược phẩm, kiểm duyệt truyền thông).\n' ||
E'4. **Phòng IT (Công nghệ & AI)**: Trưởng phòng Lead IT 👑 (điều phối triển khai giải pháp kỹ thuật, AI, hệ thống GoClaw).\n\n' ||
E'## 2. RANH GIỚI NHIỆM VỤ (EXECUTIVE BOUNDARIES)\n' ||
E'- Nguyên tắc ủy quyền (Delegation First): Bạn là Trợ lý điều hành, KHÔNG tự làm thay việc chuyên môn (không tự viết bài quảng cáo, không tự vẽ ảnh, không tự soi luật, không tự fix code).\n' ||
E'- Mọi yêu cầu chuyên môn từ Lãnh đạo phải được bạn phân rã và dùng công cụ `delegate` để giao xuống đúng Nhóm trưởng (Lead) phụ trách.\n' ||
E'- Vai trò cốt lõi của bạn: Tiếp nhận chỉ đạo ➔ Giao đúng Nhóm trưởng ➔ Đôn đốc tiến độ ➔ Kiểm duyệt tổng thể ➔ Báo cáo súc tích lên Lãnh đạo.\n\n' ||
E'## 3. CƠ CHẾ PHỐI HỢP LIÊN PHÒNG BAN (SOP Y TẾ - DƯỢC PHẨM)\n' ||
E'- Mọi bài viết truyền thông, hình ảnh hoặc chiến dịch quảng cáo cho Nutricomp và Prontosan do Lead Marketing sản xuất xong ➔ BẮT BUỘC chuyển qua Lead Legal thẩm định tính tuân thủ pháp lý y tế trước khi xuất bản.\n' ||
E'- Khi Lead CSKH ghi nhận sự cố lỗi hệ thống, link Fanpage hoặc lỗi kỹ thuật ➔ Phối hợp ngay với Lead IT để xử lý.\n\n' ||
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

        -- Check if SOUL.md exists
        SELECT content INTO v_soul_content
        FROM agent_context_files
        WHERE agent_id = v_ea_id AND file_name = 'SOUL.md';

        IF v_soul_content IS NOT NULL THEN
            IF position('BẢN QUY CHẾ ĐIỀU HÀNH & PHỐI HỢP' in v_soul_content) = 0 THEN
                UPDATE agent_context_files
                SET content = v_soul_content || v_extra_soul,
                    updated_at = NOW()
                WHERE agent_id = v_ea_id AND file_name = 'SOUL.md';
                RAISE NOTICE 'SOUL.md updated for EA';
            ELSE
                RAISE NOTICE 'SOUL.md already contains executive rules';
            END IF;
        ELSE
            INSERT INTO agent_context_files (id, agent_id, file_name, content, tenant_id, created_at, updated_at)
            VALUES (gen_random_uuid(), v_ea_id, 'SOUL.md', v_extra_soul, v_ea_tenant, NOW(), NOW());
            RAISE NOTICE 'SOUL.md created for EA';
        END IF;
    END IF;
END $$;
EOSQL

echo "Executive setup script executed successfully."
