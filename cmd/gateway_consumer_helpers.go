package cmd

import (
	"context"
	"fmt"
	"mime"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/google/uuid"

	"github.com/nextlevelbuilder/goclaw/internal/agent"
	"github.com/nextlevelbuilder/goclaw/internal/bus"
	"github.com/nextlevelbuilder/goclaw/internal/channels"
	"github.com/nextlevelbuilder/goclaw/internal/config"
	"github.com/nextlevelbuilder/goclaw/internal/sessions"
	"github.com/nextlevelbuilder/goclaw/internal/store"
	"github.com/nextlevelbuilder/goclaw/internal/tools"
)

// resolveAgentRoute determines which agent should handle a message
// based on config bindings. Priority: peer → channel → default.
// Matching TS resolve-route.ts binding resolution.
func resolveAgentRoute(cfg *config.Config, channel, chatID, peerKind string) string {
	for _, binding := range cfg.Bindings {
		if bindingMatchesInbound(binding, channel, chatID, peerKind) {
			return config.NormalizeAgentID(binding.AgentID)
		}
	}

	return cfg.ResolveDefaultAgentID()
}

type defaultAgentGetter interface {
	GetDefault(ctx context.Context) (*store.AgentData, error)
}

func resolveAgentRouteForInbound(ctx context.Context, cfg *config.Config, agentStore defaultAgentGetter, channel, chatID, peerKind string) string {
	if cfg == nil {
		return config.DefaultAgentID
	}
	for _, binding := range cfg.Bindings {
		if bindingMatchesInbound(binding, channel, chatID, peerKind) {
			return config.NormalizeAgentID(binding.AgentID)
		}
	}
	if agentStore != nil {
		if ag, err := agentStore.GetDefault(ctx); err == nil && ag != nil && ag.AgentKey != "" {
			return ag.AgentKey
		}
	}
	return cfg.ResolveDefaultAgentID()
}

func bindingMatchesInbound(binding config.AgentBinding, channel, chatID, peerKind string) bool {
	match := binding.Match
	if match.Channel != channel {
		return false
	}

	// Peer-level match (most specific)
	if match.Peer != nil {
		return match.Peer.Kind == peerKind && match.Peer.ID == chatID
	}

	// Channel-level match (least specific, no peer constraint)
	return true
}

func inboundMessageTenantContext(ctx context.Context, msg bus.InboundMessage) context.Context {
	if ctx == nil {
		ctx = context.Background()
	}
	if msg.TenantID != uuid.Nil {
		return store.WithTenantID(ctx, msg.TenantID)
	}
	return store.WithTenantID(ctx, store.MasterTenantID)
}

// overrideSessionKeyFromLocalKey extracts topic/thread ID from the composite
// local_key and returns the correct session key for forum topics or DM threads.
// If localKey is empty or has no suffix, the original sessionKey is returned unchanged.
func overrideSessionKeyFromLocalKey(sessionKey, localKey, agentID, channel, chatID, peerKind string) string {
	if localKey == "" {
		return sessionKey
	}
	if idx := strings.Index(localKey, ":topic:"); idx > 0 && peerKind == string(sessions.PeerGroup) {
		var topicID int
		fmt.Sscanf(localKey[idx+7:], "%d", &topicID)
		if topicID > 0 {
			return sessions.BuildGroupTopicSessionKey(agentID, channel, chatID, topicID)
		}
	} else if idx := strings.Index(localKey, ":thread:"); idx > 0 && peerKind == string(sessions.PeerDirect) {
		var threadID int
		fmt.Sscanf(localKey[idx+8:], "%d", &threadID)
		if threadID > 0 {
			return sessions.BuildDMThreadSessionKey(agentID, channel, chatID, threadID)
		}
	}
	return sessionKey
}

// extractSessionMetadata builds a metadata map from channel InboundMessage metadata.
// Used to persist friendly names (display_name, username, chat_title) into sessions
// and user profiles so the web UI can show human-readable labels.
func extractSessionMetadata(msg bus.InboundMessage, peerKind string) map[string]string {
	meta := make(map[string]string)

	// Display name: prefer first_name (Telegram), fall back to display_name (Discord)
	if v := msg.Metadata["first_name"]; v != "" {
		meta["display_name"] = v
	} else if v := msg.Metadata["display_name"]; v != "" {
		meta["display_name"] = v
	}

	if v := msg.Metadata[tools.MetaUsername]; v != "" {
		meta[tools.MetaUsername] = v
	}
	if peerKind != "" {
		meta["peer_kind"] = peerKind
	}
	if v := msg.Metadata[tools.MetaChatTitle]; v != "" {
		meta[tools.MetaChatTitle] = v
	}

	if len(meta) == 0 {
		return nil
	}
	return meta
}

// resolveGroupDisplayTitle fills presentation context for internally
// re-ingressed group messages that no longer carry inbound chat metadata.
// It leaves routing identifiers untouched and silently falls back when a
// channel cannot resolve a platform-specific display title.
func resolveGroupDisplayTitle(ctx context.Context, mgr *channels.Manager, channel, chatID, peerKind, title string) string {
	if title != "" || peerKind != string(sessions.PeerGroup) || mgr == nil || channel == "" || chatID == "" {
		return title
	}
	resolved, err := mgr.ResolveGroupDisplayTitle(ctx, channel, chatID)
	if err != nil {
		return title
	}
	return resolved
}

func resolveInboundChatTitle(ctx context.Context, mgr *channels.Manager, msg bus.InboundMessage, peerKind string) string {
	title := msg.Metadata[tools.MetaChatTitle]
	if !bus.IsInternalSender(msg.SenderID) {
		return title
	}
	return resolveGroupDisplayTitle(ctx, mgr, msg.Channel, msg.ChatID, peerKind, title)
}

// buildPancakeSessionLabel returns "Pancake:{senderName}:{pageName}" with non-empty parts only.
func buildPancakeSessionLabel(senderName, pageName string) string {
	label := "Pancake"
	if senderName != "" {
		label += ":" + senderName
	}
	if pageName != "" {
		label += ":" + pageName
	}
	return label
}

// buildAnnounceOutMeta builds outbound metadata for announce messages so that
// Send() can route replies to the correct forum topic or DM thread.
func buildAnnounceOutMeta(localKey string) map[string]string {
	if localKey == "" {
		return nil
	}
	meta := map[string]string{"local_key": localKey}
	if idx := strings.Index(localKey, ":topic:"); idx > 0 {
		meta[tools.MetaMessageThreadID] = localKey[idx+7:]
	} else if idx := strings.Index(localKey, ":thread:"); idx > 0 {
		meta[tools.MetaMessageThreadID] = localKey[idx+8:]
	}
	return meta
}

// mediaToMarkdown converts media results to markdown image/link syntax using the
// /v1/files/ HTTP endpoint. Used for WS channel where outbound media attachments
// are not supported (no channel handler). Returns empty string if no media.
// Uses absolute file paths with the /v1/files endpoint (auth-token protected).
// Generates relative URLs (/v1/files/...) so they work regardless of the server's
// external hostname — the browser resolves them from the current origin.
func mediaToMarkdown(media []agent.MediaResult, cfg *config.Config) string {
	if len(media) == 0 {
		return ""
	}

	var parts []string
	for _, mr := range media {
		cleanPath := filepath.Clean(mr.Path)
		// Strip leading "/" so URL path is /v1/files/app/.goclaw/...
		urlPath := strings.TrimPrefix(cleanPath, "/")
		if urlPath == "" {
			continue
		}
		// Store clean path only — no auth tokens in persisted session messages.
		// Frontend adds auth (Bearer header or ?ft= signed token) at render time.
		// Guard: if path is already a /v1/ URL (e.g. from mutated media), don't double-prefix.
		var fileURL string
		if strings.HasPrefix(urlPath, "v1/files/") || strings.HasPrefix(urlPath, "v1/media/") {
			fileURL = "/" + strings.SplitN(urlPath, "?", 2)[0] // strip any existing query params
		} else {
			fileURL = "/v1/files/" + urlPath
		}
		if strings.HasPrefix(mr.ContentType, "image/") {
			parts = append(parts, fmt.Sprintf("![image](%s)", fileURL))
		} else {
			parts = append(parts, fmt.Sprintf("[%s](%s)", filepath.Base(mr.Path), fileURL))
		}
	}
	if len(parts) == 0 {
		return ""
	}
	return "\n\n" + strings.Join(parts, "\n")
}

// mediaToMarkdownFromPaths is like mediaToMarkdown but accepts raw file paths
// ([]string from bus.InboundMessage.Media) instead of []agent.MediaResult.
func mediaToMarkdownFromPaths(files []bus.MediaFile, cfg *config.Config) string {
	if len(files) == 0 {
		return ""
	}
	media := make([]agent.MediaResult, 0, len(files))
	for _, f := range files {
		ct := f.MimeType
		if ct == "" {
			ct = mime.TypeByExtension(filepath.Ext(f.Path))
		}
		if ct == "" {
			ct = "application/octet-stream"
		}
		media = append(media, agent.MediaResult{
			Path:        f.Path,
			ContentType: ct,
		})
	}
	return mediaToMarkdown(media, cfg)
}

// resolveChannelType returns the platform type for a channel instance name.
// Returns empty string if channelMgr is nil or channel name is empty.
func resolveChannelType(channelMgr *channels.Manager, name string) string {
	if channelMgr == nil || name == "" {
		return ""
	}
	return channelMgr.ChannelTypeForName(name)
}

// resolveSenderName extracts the sender display name from channel metadata.
// Checks "sender_name" (Feishu), "first_name" (Telegram), "user_name" (WhatsApp).
// Sanitizes to prevent prompt injection via newlines/control chars.
func resolveSenderName(msg bus.InboundMessage) string {
	for _, key := range []string{"sender_name", "first_name", "user_name", "push_name", "display_name"} {
		if name := msg.Metadata[key]; name != "" {
			clean := strings.NewReplacer("\n", " ", "\r", " ", "\t", " ").Replace(strings.TrimSpace(name))
			if len([]rune(clean)) > 100 {
				clean = string([]rune(clean)[:100])
			}
			return clean
		}
	}
	return ""
}

// autoAttachCreativeMedia checks if an outbound message represents a creative/social post
// without attached media. If so, it looks up corresponding product posters on disk
// and automatically attaches them to the outbound message so the user receives both caption and image.
func autoAttachCreativeMedia(outMsg *bus.OutboundMessage) {
	if outMsg == nil || len(outMsg.Media) > 0 || outMsg.Content == "" {
		return
	}

	contentLower := strings.ToLower(outMsg.Content)
	isCreativeFlow := strings.Contains(contentLower, "caption") ||
		strings.Contains(contentLower, "poster") ||
		strings.Contains(contentLower, "bài viết") ||
		strings.Contains(contentLower, "bài page") ||
		strings.Contains(contentLower, "ý tưởng") ||
		strings.Contains(contentLower, "nutricomp") ||
		strings.Contains(contentLower, "prontosan") ||
		strings.Contains(contentLower, "globalpharma")

	if !isCreativeFlow {
		return
	}

	// Candidate file search directories
	searchDirs := []string{
		"/app/workspace/output",
		"/app/data/skills/tao-creative-fb/output",
		"skills/tao-creative-fb/output",
		"/app/skills/tao-creative-fb/output",
		"output",
	}

	// Calculate weighted scores for each product to prevent false positives
	// (e.g. Vietnamese "cẩn thận" or "thận trọng" falsely triggering Renal).
	var plusScore, renalScore, prontosanScore, comboScore int

	// Contextual idea selection boost: When user selects Idea 2 ("chọn 2", "ý tưởng 2"), it corresponds to Nutricomp Drink Plus.
	if strings.Contains(contentLower, "ý tưởng 2") || strings.Contains(contentLower, "ý số 2") || strings.Contains(contentLower, "chọn 2") {
		plusScore += 20
	} else if strings.Contains(contentLower, "ý tưởng 1") || strings.Contains(contentLower, "ý số 1") || strings.Contains(contentLower, "chọn 1") {
		renalScore += 20
	} else if strings.Contains(contentLower, "ý tưởng 3") || strings.Contains(contentLower, "ý số 3") || strings.Contains(contentLower, "chọn 3") {
		prontosanScore += 20
	}

	// Nutricomp Drink Plus keywords
	plusKeywords := []struct {
		kw     string
		weight int
	}{
		{"nutricomp plus", 15},
		{"drink plus", 15},
		{"nutricomp® drink plus", 15},
		{"plus", 8},
		{"sau phẫu thuật", 10},
		{"sau mổ", 10},
		{"suy kiệt", 10},
		{"300 kcal", 10},
		{"1.5 kcal", 10},
		{"bồi bổ", 6},
		{"hồi phục thể trạng", 8},
		{"cao năng lượng", 8},
		{"ăn kém", 6},
		{"nhanh no", 6},
	}
	for _, pk := range plusKeywords {
		if strings.Contains(contentLower, pk.kw) {
			plusScore += pk.weight
		}
	}

	// Prontosan keywords
	prontosanKeywords := []struct {
		kw     string
		weight int
	}{
		{"prontosan", 15},
		{"vết thương", 10},
		{"biofilm", 12},
		{"loét", 8},
		{"vết trầy", 8},
		{"vết xước", 8},
		{"màng sinh học", 10},
		{"làm sạch vết thương", 12},
		{"rửa vết thương", 12},
		{"chai xịt", 8},
		{"xịt vết thương", 10},
		{"vô trùng", 6},
		{"lành thương", 8},
	}
	for _, pk := range prontosanKeywords {
		if strings.Contains(contentLower, pk.kw) {
			prontosanScore += pk.weight
		}
	}

	// Nutricomp Drink Renal keywords (strip "cẩn thận" and "thận trọng" to prevent false triggers)
	cleanRenalContent := strings.ReplaceAll(contentLower, "cẩn thận", "")
	cleanRenalContent = strings.ReplaceAll(cleanRenalContent, "thận trọng", "")
	renalKeywords := []struct {
		kw     string
		weight int
	}{
		{"nutricomp renal", 15},
		{"drink renal", 15},
		{"nutricomp® drink renal", 15},
		{"renal", 10},
		{"suy thận", 12},
		{"chạy thận", 12},
		{"lọc máu", 12},
		{"bệnh thận", 10},
		{"bệnh nhân thận", 10},
		{"chức năng thận", 10},
		{"cầu thận", 10},
		{"400 kcal", 10},
		{"2.0 kcal", 10},
		{"urê huyết", 8},
		{"kali", 6},
		{"phospho", 6},
		{"thận", 4},
	}
	for _, rk := range renalKeywords {
		if strings.Contains(cleanRenalContent, rk.kw) {
			renalScore += rk.weight
		}
	}

	// Combo keywords
	comboKeywords := []struct {
		kw     string
		weight int
	}{
		{"combo 12", 15},
		{"1.296.000", 15},
		{"108.000", 10},
		{"thùng 12 chai", 12},
		{"12 chai", 10},
		{"hộp quà", 8},
		{"combo", 6},
	}
	for _, ck := range comboKeywords {
		if strings.Contains(contentLower, ck.kw) {
			comboScore += ck.weight
		}
	}

	var targetType string
	var productCandidates []string
	maxScore := 0

	if plusScore > maxScore {
		maxScore = plusScore
		targetType = "plus"
		productCandidates = []string{
			"poster_nutricomp_drink_plus.png",
			"poster_nutricomp_plus_placement.png",
			"poster_plus_auto.png",
		}
	}
	if renalScore > maxScore {
		maxScore = renalScore
		targetType = "renal"
		productCandidates = []string{
			"poster_nutricomp_renal.png",
			"poster_nutricomp_renal_placement.png",
			"organic_post_renal.png",
		}
	}
	if prontosanScore > maxScore {
		maxScore = prontosanScore
		targetType = "prontosan"
		productCandidates = []string{
			"poster_prontosan_wound_spray.png",
			"poster_prontosan_clinical.jpg",
		}
	}
	if comboScore > maxScore {
		maxScore = comboScore
		targetType = "combo"
		productCandidates = []string{
			"poster_nutricomp_combo12.png",
		}
	}

	if len(productCandidates) == 0 {
		return
	}

	// 1. Check if the message contains explicit Headline / Subline markers.
	// If so, dynamically generate a tailor-made poster with the exact text!
	var headline, subline string
	lines := strings.Split(outMsg.Content, "\n")
	for _, l := range lines {
		trimmed := strings.TrimSpace(l)
		lower := strings.ToLower(trimmed)
		if strings.HasPrefix(lower, "• headline:") || strings.HasPrefix(lower, "headline:") || strings.HasPrefix(lower, "- headline:") || strings.HasPrefix(lower, "* headline:") {
			parts := strings.SplitN(trimmed, ":", 2)
			if len(parts) == 2 {
				headline = strings.TrimSpace(parts[1])
			}
		} else if strings.HasPrefix(lower, "• subline:") || strings.HasPrefix(lower, "subline:") || strings.HasPrefix(lower, "- subline:") || strings.HasPrefix(lower, "* subline:") {
			parts := strings.SplitN(trimmed, ":", 2)
			if len(parts) == 2 {
				subline = strings.TrimSpace(parts[1])
			}
		}
	}

	// Also check if first non-empty line after Caption: is a bold headline or hook
	if headline == "" {
		for i, l := range lines {
			trimmed := strings.TrimSpace(l)
			if strings.EqualFold(trimmed, "caption:") || strings.EqualFold(trimmed, "caption đề xuất:") {
				for j := i + 1; j < len(lines); j++ {
					candidate := strings.TrimSpace(lines[j])
					if candidate != "" && len(candidate) < 100 && !strings.HasPrefix(candidate, "*") {
						headline = candidate
						break
					}
				}
				break
			}
		}
	}

	var foundPath string

	// If we have a detected product and a headline, invoke render_poster.py dynamically
	if targetType != "" && headline != "" {
		renderScriptCandidates := []string{
			"/app/data/skills/tao-creative-fb/scripts/render_poster.py",
			"/app/workspace/skills/tao-creative-fb/scripts/render_poster.py",
			"skills/tao-creative-fb/scripts/render_poster.py",
		}
		var scriptPath string
		for _, sp := range renderScriptCandidates {
			if info, err := os.Stat(sp); err == nil && !info.IsDir() {
				scriptPath = sp
				break
			}
		}

		if scriptPath != "" {
			outDir := "/app/workspace/output"
			if info, err := os.Stat(outDir); err != nil || !info.IsDir() {
				outDir = "skills/tao-creative-fb/output"
			}
			customOutName := fmt.Sprintf("creative_tailored_%s_%d.png", targetType, time.Now().UnixNano()%100000)
			customOutPath := filepath.Join(outDir, customOutName)

			cmdArgs := []string{scriptPath, "--type", targetType, "--headline", headline, "--output", customOutPath}
			if subline != "" {
				cmdArgs = append(cmdArgs, "--subline", subline)
			}

			// Try running with python3 or python
			pyCmd := exec.Command("python3", cmdArgs...)
			if err := pyCmd.Run(); err != nil {
				pyCmd = exec.Command("python", cmdArgs...)
				_ = pyCmd.Run()
			}

			if info, err := os.Stat(customOutPath); err == nil && !info.IsDir() && info.Size() > 0 {
				foundPath = customOutPath
			}
		}
	}

	// 2. Fallback to existing pre-rendered master posters if dynamic rendering wasn't triggered
	if foundPath == "" {
		for _, dir := range searchDirs {
			for _, name := range productCandidates {
				cand := filepath.Join(dir, name)
				if info, err := os.Stat(cand); err == nil && !info.IsDir() && info.Size() > 0 {
					foundPath = cand
					break
				}
			}
			if foundPath != "" {
				break
			}
		}
	}

	if foundPath != "" {
		outMsg.Media = append(outMsg.Media, bus.MediaAttachment{
			URL:         foundPath,
			ContentType: "image/png",
		})
		// Clean up textual "Gợi ý poster" bullet points from message content
		// since real visual poster is now attached directly.
		if idx := strings.Index(outMsg.Content, "Gợi ý poster:"); idx != -1 {
			outMsg.Content = strings.TrimSpace(outMsg.Content[:idx])
		} else if idx := strings.Index(outMsg.Content, "Gợi ý visual:"); idx != -1 {
			outMsg.Content = strings.TrimSpace(outMsg.Content[:idx])
		}
	}
}
