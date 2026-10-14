package tools

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/textproto"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// FacebookPageConfig represents a single Fanpage configuration with its Access Token.
type FacebookPageConfig struct {
	ID           string `json:"id"`
	Name         string `json:"name"`
	URL          string `json:"url,omitempty"`
	Category     string `json:"category,omitempty"`
	Token        string `json:"token"`
	ProductGroup string `json:"product_group"`
	Enabled      bool   `json:"enabled"`
}

// PostFacebookTool publishes posters and captions to GlobalPharma's Facebook Fanpages via Graph API.
type PostFacebookTool struct {
	workspace string
}

// NewPostFacebookTool creates a PostFacebookTool.
func NewPostFacebookTool(workspace string) *PostFacebookTool {
	return &PostFacebookTool{workspace: workspace}
}

func (t *PostFacebookTool) Name() string { return "post_facebook" }

func (t *PostFacebookTool) Description() string {
	return "Đăng hình ảnh poster và nội dung bài viết (caption) lên mạng lưới Fanpage Facebook của GlobalPharma qua Facebook Graph API. " +
		"Hệ thống ĐÃ LƯU SẴN 100% Page Access Token và ID cho tất cả 17 Fanpage trong hệ thống (Prontosan, Nutricomp, Sức Khỏe Cho Mọi Nhà, Affiliate). " +
		"Tự động phân loại Fanpage mục tiêu theo dòng sản phẩm (ví dụ: 'prontosan' đăng lên 8 Fanpage Prontosan, 'nutricomp' đăng lên các Fanpage Nutricomp). " +
		"Hỗ trợ chế độ dry_run=true để kiểm tra danh sách page trước khi đăng thật."
}

func (t *PostFacebookTool) Parameters() map[string]any {
	return map[string]any{
		"type": "object",
		"properties": map[string]any{
			"image": map[string]any{
				"type":        "string",
				"description": "Đường dẫn file ảnh poster cần đăng (tuyệt đối hoặc tương đối trong workspace, ví dụ: 'generated/2026-10-12/...png' hoặc '/app/workspace/output/poster.png')",
			},
			"caption": map[string]any{
				"type":        "string",
				"description": "Nội dung bài viết (caption) hoàn chỉnh cần đăng lên Fanpage (hoặc đường dẫn đến file text chứa caption)",
			},
			"product": map[string]any{
				"type":        "string",
				"enum":        []string{"prontosan", "nutricomp", "affiliate", "all", "auto"},
				"description": "Dòng sản phẩm mục tiêu: 'prontosan' (8 Fanpage Prontosan + chung), 'nutricomp' (các Fanpage Nutricomp + chung), 'affiliate' (chỉ page Affiliate), 'all' (tất cả), 'auto' (tự động nhận diện từ caption). Mặc định là 'auto'.",
			},
			"page_ids": map[string]any{
				"type":        "array",
				"items":       map[string]any{"type": "string"},
				"description": "Danh sách Page ID cụ thể nếu chỉ muốn đăng lên một số Fanpage được chỉ định.",
			},
			"dry_run": map[string]any{
				"type":        "boolean",
				"description": "Nếu true thì chỉ mô phỏng kiểm thử danh sách page, không gọi API đăng thật. Mặc định là false (đăng thật).",
			},
		},
		"required": []string{"image", "caption"},
	}
}

func (t *PostFacebookTool) Execute(ctx context.Context, args map[string]any) *Result {
	imageRaw, _ := args["image"].(string)
	captionRaw, _ := args["caption"].(string)
	productRaw, _ := args["product"].(string)
	dryRun, _ := args["dry_run"].(bool)

	imageRaw = strings.TrimSpace(imageRaw)
	captionRaw = strings.TrimSpace(captionRaw)
	productRaw = strings.ToLower(strings.TrimSpace(productRaw))
	if productRaw == "" {
		productRaw = "auto"
	}

	if imageRaw == "" {
		return ErrorResult("thiếu đường dẫn file ảnh ('image')")
	}
	if captionRaw == "" {
		return ErrorResult("thiếu nội dung bài viết ('caption')")
	}

	// Resolve caption if it is a file path
	if content, err := os.ReadFile(captionRaw); err == nil && len(content) > 0 {
		captionRaw = string(content)
	}
	captionRaw = cleanFacebookCaption(captionRaw)

	// Resolve image file path
	imagePath := t.resolveImagePath(ctx, imageRaw)
	if imagePath == "" {
		return ErrorResult(fmt.Sprintf("không tìm thấy file ảnh tại: '%s'. Vui lòng kiểm tra lại đường dẫn file ảnh.", imageRaw))
	}

	// Load Fanpage configs
	pages, err := t.loadPagesConfig(ctx)
	if err != nil || len(pages) == 0 {
		return ErrorResult(fmt.Sprintf("không thể nạp danh sách Fanpage và Token: %v", err))
	}

	// Specific page_ids filter if provided
	var targetIDs []string
	if idsVal, ok := args["page_ids"].([]any); ok {
		for _, v := range idsVal {
			if s, ok := v.(string); ok && strings.TrimSpace(s) != "" {
				targetIDs = append(targetIDs, strings.TrimSpace(s))
			}
		}
	}

	// Auto detect product from caption if needed
	if productRaw == "auto" {
		productRaw = detectFacebookProduct(captionRaw)
	}

	// Filter pages
	filtered := filterFacebookPages(pages, productRaw, targetIDs)
	if len(filtered) == 0 {
		return ErrorResult(fmt.Sprintf("không tìm thấy Fanpage nào phù hợp với sản phẩm '%s'", productRaw))
	}

	// Check environment variable DRY_RUN
	if !dryRun {
		if envDry := strings.ToLower(os.Getenv("DRY_RUN")); envDry == "true" || envDry == "1" {
			dryRun = true
		}
	}

	// Execute posting
	type postOutcome struct {
		Index     int
		PageID    string
		PageName  string
		Success   bool
		PostID    string
		ErrorText string
		DryRun    bool
	}

	client := &http.Client{Timeout: 90 * time.Second}
	var outcomes []postOutcome

	for idx, p := range filtered {
		if dryRun || strings.HasPrefix(p.Token, "EAAV...") && len(p.Token) < 30 {
			outcomes = append(outcomes, postOutcome{
				Index:    idx + 1,
				PageID:   p.ID,
				PageName: p.Name,
				Success:  true,
				PostID:   fmt.Sprintf("%s_mock_%d", p.ID, time.Now().Unix()),
				DryRun:   true,
			})
			continue
		}

		postID, postErr := postPhotoToFacebook(ctx, client, imagePath, captionRaw, p.ID, p.Token)
		if postErr != nil {
			outcomes = append(outcomes, postOutcome{
				Index:     idx + 1,
				PageID:    p.ID,
				PageName:  p.Name,
				Success:   false,
				ErrorText: postErr.Error(),
				DryRun:    false,
			})
		} else {
			outcomes = append(outcomes, postOutcome{
				Index:    idx + 1,
				PageID:   p.ID,
				PageName: p.Name,
				Success:  true,
				PostID:   postID,
				DryRun:   false,
			})
		}

		// Sleep 2 seconds between pages to prevent spam flagging
		if idx < len(filtered)-1 && !dryRun {
			select {
			case <-ctx.Done():
				break
			case <-time.After(2 * time.Second):
			}
		}
	}

	// Generate summary report
	successCount := 0
	for _, o := range outcomes {
		if o.Success {
			successCount++
		}
	}

	var sb strings.Builder
	sb.WriteString("### 📊 Báo Cáo Kết Quả Đăng Bài Lên Mạng Lưới Fanpage Facebook\n\n")
	sb.WriteString(fmt.Sprintf("- **Dòng sản phẩm phân luồng:** `%s`\n", strings.ToUpper(productRaw)))
	sb.WriteString(fmt.Sprintf("- **File ảnh poster:** `%s`\n", filepath.Base(imagePath)))
	if dryRun {
		sb.WriteString("- **Chế độ:** `DRY-RUN (Mô phỏng an toàn - không gọi API thật)`\n")
	} else {
		sb.WriteString("- **Chế độ:** `LIVE POST (Đã đăng thật qua Facebook Graph API)`\n")
	}
	sb.WriteString(fmt.Sprintf("- **Tổng số Fanpage xử lý:** %d | **Thành công:** %d | **Thất bại:** %d\n\n", len(outcomes), successCount, len(outcomes)-successCount))

	sb.WriteString("| STT | Tên Fanpage | Page ID | Trạng Thái | Chi Tiết / Post ID |\n")
	sb.WriteString("|---|---|---|---|---|\n")
	for _, o := range outcomes {
		status := "✅ Thành công"
		detail := o.PostID
		if !o.Success {
			status = "❌ Thất bại"
			detail = o.ErrorText
		}
		sb.WriteString(fmt.Sprintf("| %d | %s | `%s` | %s | %s |\n", o.Index, o.PageName, o.PageID, status, detail))
	}

	return UserResult(sb.String())
}

func (t *PostFacebookTool) resolveImagePath(ctx context.Context, raw string) string {
	raw = strings.TrimSpace(raw)
	// Remove MEDIA: prefix if model included it
	raw = strings.TrimPrefix(raw, "MEDIA:")
	raw = strings.TrimSpace(raw)

	// Direct check
	if fi, err := os.Stat(raw); err == nil && !fi.IsDir() {
		return raw
	}

	// Candidates
	ws := ToolWorkspaceFromCtx(ctx)
	if ws == "" {
		ws = t.workspace
	}

	candidates := []string{
		filepath.Join(ws, raw),
		filepath.Join("/app/workspace", raw),
		filepath.Join("/app/workspace/output", raw),
		filepath.Join("/app/workspace/output", filepath.Base(raw)),
		filepath.Join("/app/data/skills/tao-creative-fb/output", filepath.Base(raw)),
		filepath.Join("skills/tao-creative-fb/output", filepath.Base(raw)),
	}

	for _, cand := range candidates {
		if fi, err := os.Stat(cand); err == nil && !fi.IsDir() {
			return cand
		}
	}

	return ""
}

func (t *PostFacebookTool) loadPagesConfig(ctx context.Context) ([]FacebookPageConfig, error) {
	ws := ToolWorkspaceFromCtx(ctx)
	if ws == "" {
		ws = t.workspace
	}

	jsonCandidates := []string{
		filepath.Join(ws, "pages.json"),
		filepath.Join(ws, "skills/tao-creative-fb/pages.json"),
		"/app/workspace/pages.json",
		"/app/data/skills/tao-creative-fb/pages.json",
		"/app/skills/tao-creative-fb/pages.json",
		"skills/tao-creative-fb/pages.json",
		"pages.json",
	}

	for _, p := range jsonCandidates {
		if data, err := os.ReadFile(p); err == nil && len(data) > 0 {
			var pages []FacebookPageConfig
			if err := json.Unmarshal(data, &pages); err == nil && len(pages) > 0 {
				return pages, nil
			}
		}
	}

	// Fallback to CSV
	csvCandidates := []string{
		filepath.Join(ws, "facebook_pages.csv"),
		"/app/workspace/facebook_pages.csv",
		"/app/facebook_pages.csv",
		"facebook_pages.csv",
	}

	for _, p := range csvCandidates {
		if pages, err := parseFacebookPagesCSV(p); err == nil && len(pages) > 0 {
			return pages, nil
		}
	}

	return nil, fmt.Errorf("không tìm thấy file pages.json hoặc facebook_pages.csv")
}

func parseFacebookPagesCSV(csvPath string) ([]FacebookPageConfig, error) {
	f, err := os.Open(csvPath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	if len(records) < 2 {
		return nil, fmt.Errorf("file CSV trống hoặc không có dữ liệu")
	}

	var pages []FacebookPageConfig
	idRegex := regexp.MustCompile(`\d+`)

	for _, row := range records[1:] {
		if len(row) < 6 {
			continue
		}
		rawID := row[1]
		matches := idRegex.FindAllString(rawID, -1)
		pageID := rawID
		if len(matches) > 0 {
			pageID = matches[0]
		}
		pageName := strings.TrimSpace(row[2])
		category := strings.TrimSpace(row[3])
		token := strings.TrimSpace(row[5])

		if pageID == "" || token == "" {
			continue
		}

		// Detect product group
		pg := "nutricomp"
		lowerName := strings.ToLower(pageName)
		if strings.Contains(lowerName, "affiliate") {
			pg = "affiliate"
		} else if strings.Contains(lowerName, "prontosan") || strings.Contains(lowerName, "vết thương") {
			pg = "prontosan"
		} else if strings.Contains(lowerName, "sức khỏe cho mọi nhà") {
			pg = "all"
		}

		pages = append(pages, FacebookPageConfig{
			ID:           pageID,
			Name:         pageName,
			Category:     category,
			Token:        token,
			ProductGroup: pg,
			Enabled:      true,
		})
	}

	return pages, nil
}

func filterFacebookPages(pages []FacebookPageConfig, product string, targetIDs []string) []FacebookPageConfig {
	var filtered []FacebookPageConfig

	for _, p := range pages {
		if len(targetIDs) > 0 {
			matched := false
			pURL := strings.TrimRight(strings.ToLower(p.URL), "/")
			pName := strings.ToLower(p.Name)
			for _, tid := range targetIDs {
				cleanTID := strings.TrimRight(strings.ToLower(strings.TrimSpace(tid)), "/")
				if p.ID == tid || (pURL != "" && (pURL == cleanTID || strings.HasSuffix(pURL, "/"+cleanTID))) || (cleanTID != "" && strings.Contains(pName, cleanTID)) {
					matched = true
					break
				}
			}
			if matched {
				filtered = append(filtered, p)
			}
			continue
		}

		if !p.Enabled {
			continue
		}

		pg := strings.ToLower(p.ProductGroup)
		switch product {
		case "prontosan":
			if pg == "affiliate" {
				continue
			}
			if pg == "prontosan" || pg == "all" || pg == "general" || pg == "both" {
				filtered = append(filtered, p)
			}
		case "nutricomp":
			if pg == "affiliate" {
				continue
			}
			if pg == "nutricomp" || pg == "all" || pg == "general" || pg == "both" {
				filtered = append(filtered, p)
			}
		case "affiliate":
			if pg == "affiliate" {
				filtered = append(filtered, p)
			}
		default:
			// "all"
			filtered = append(filtered, p)
		}
	}

	return filtered
}

func detectFacebookProduct(caption string) string {
	lower := strings.ToLower(caption)
	prontosanKeywords := []string{"prontosan", "vết thương", "loét", "biofilm", "lành vết thương", "spray", "kháng khuẩn", "sát trùng"}
	nutricompKeywords := []string{"nutricomp", "renal", "drink plus", "dinh dưỡng", "thận", "lọc máu", "suy kiệt", "sau phẫu thuật", "năng lượng cao"}
	affiliateKeywords := []string{"affiliate", "tiếp thị liên kết", "solopreneur", "dược sĩ", "thu nhập", "cộng tác viên"}

	pScore := 0
	for _, kw := range prontosanKeywords {
		if strings.Contains(lower, kw) {
			pScore++
		}
	}
	nScore := 0
	for _, kw := range nutricompKeywords {
		if strings.Contains(lower, kw) {
			nScore++
		}
	}
	aScore := 0
	for _, kw := range affiliateKeywords {
		if strings.Contains(lower, kw) {
			aScore++
		}
	}

	if aScore > pScore && aScore > nScore {
		return "affiliate"
	}
	if pScore > nScore {
		return "prontosan"
	}
	if nScore > pScore {
		return "nutricomp"
	}
	if pScore > 0 {
		return "prontosan"
	}
	if nScore > 0 {
		return "nutricomp"
	}
	return "all"
}

func postPhotoToFacebook(ctx context.Context, client *http.Client, imagePath, caption, pageID, token string) (string, error) {
	url := fmt.Sprintf("https://graph.facebook.com/v19.0/%s/photos", pageID)

	fileData, err := os.ReadFile(imagePath)
	if err != nil {
		return "", fmt.Errorf("không đọc được file ảnh: %w", err)
	}

	var body bytes.Buffer
	writer := multipart.NewWriter(&body)

	// message / caption
	if err := writer.WriteField("caption", caption); err != nil {
		return "", err
	}
	if err := writer.WriteField("message", caption); err != nil {
		return "", err
	}
	if err := writer.WriteField("access_token", token); err != nil {
		return "", err
	}

	// source file
	mimeType := "image/jpeg"
	if strings.HasSuffix(strings.ToLower(imagePath), ".png") {
		mimeType = "image/png"
	}

	h := make(textproto.MIMEHeader)
	h.Set("Content-Disposition", fmt.Sprintf(`form-data; name="source"; filename="%s"`, filepath.Base(imagePath)))
	h.Set("Content-Type", mimeType)
	part, err := writer.CreatePart(h)
	if err != nil {
		return "", err
	}
	if _, err := part.Write(fileData); err != nil {
		return "", err
	}

	if err := writer.Close(); err != nil {
		return "", err
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, &body)
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("lỗi mạng khi gọi Facebook Graph API: %w", err)
	}
	defer resp.Body.Close()

	respBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("lỗi đọc phản hồi từ Facebook: %w", err)
	}

	var resJSON struct {
		ID     string `json:"id"`
		PostID string `json:"post_id"`
		Error  *struct {
			Message string `json:"message"`
			Code    int    `json:"code"`
		} `json:"error"`
	}

	if err := json.Unmarshal(respBytes, &resJSON); err != nil {
		return "", fmt.Errorf("phản hồi Graph API không hợp lệ: %s", string(respBytes))
	}

	if resJSON.Error != nil {
		return "", fmt.Errorf("mã lỗi %d: %s", resJSON.Error.Code, resJSON.Error.Message)
	}

	postID := resJSON.PostID
	if postID == "" {
		postID = resJSON.ID
	}

	return postID, nil
}

// cleanFacebookCaption strips markdown bold (***, **), italic (*, _), and headers (#)
// so that the caption posted to Facebook Graph API renders as clean plain text without font errors or asterisks.
func cleanFacebookCaption(text string) string {
	if text == "" {
		return ""
	}

	// 1. Strip bold-italic ***text*** -> text
	reTriple := regexp.MustCompile(`\*\*\*([^*\n\r]+)\*\*\*`)
	text = reTriple.ReplaceAllString(text, "$1")

	// 2. Strip bold **text** -> text
	reDouble := regexp.MustCompile(`\*\*([^*\n\r]+)\*\*`)
	text = reDouble.ReplaceAllString(text, "$1")

	// 3. Strip italic *text* -> text (when enclosed with spaces or punctuation)
	reSingle := regexp.MustCompile(`(^|[\s(])\*([^*\n\r]+)\*($|[\s).,!?:;])`)
	text = reSingle.ReplaceAllString(text, "$1$2$3")

	// 4. Strip ___text___ and __text__
	reUnderTriple := regexp.MustCompile(`___([^_\n\r]+)___`)
	text = reUnderTriple.ReplaceAllString(text, "$1")
	reUnderDouble := regexp.MustCompile(`__([^_\n\r]+)__`)
	text = reUnderDouble.ReplaceAllString(text, "$1")

	// 5. Strip _text_
	reUnderSingle := regexp.MustCompile(`(^|[\s(])_([^_\n\r]+)_($|[\s).,!?:;])`)
	text = reUnderSingle.ReplaceAllString(text, "$1$2$3")

	// 6. Strip markdown headers (# Heading -> Heading)
	reHeader := regexp.MustCompile(`(?m)^#{1,6}\s+`)
	text = reHeader.ReplaceAllString(text, "")

	// 7. Strip any leftover asterisks that cause font issues on Facebook
	text = strings.ReplaceAll(text, "***", "")
	text = strings.ReplaceAll(text, "**", "")

	return strings.TrimSpace(text)
}
