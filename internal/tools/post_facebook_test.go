package tools

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestPostFacebookTool_Interface(t *testing.T) {
	// Compile-time assertion
	var _ Tool = (*PostFacebookTool)(nil)
}

func TestDetectFacebookProduct(t *testing.T) {
	tests := []struct {
		caption  string
		expected string
	}{
		{
			caption:  "Biofilm là gì? Prontosan làm sạch vết thương hở và ngăn ngừa nhiễm trùng",
			expected: "prontosan",
		},
		{
			caption:  "Dinh dưỡng chuyên biệt cho bệnh nhân suy thận mạn lọc máu với Nutricomp Renal",
			expected: "nutricomp",
		},
		{
			caption:  "Hồi phục sau phẫu thuật, bổ sung dinh dưỡng cao năng lượng 300 kcal Drink Plus",
			expected: "nutricomp",
		},
		{
			caption:  "Cơ hội hợp tác affiliate dược sĩ, mô hình kinh doanh một người solopreneur",
			expected: "affiliate",
		},
		{
			caption:  "Chào buổi sáng mọi người",
			expected: "all",
		},
	}

	for _, tc := range tests {
		actual := detectFacebookProduct(tc.caption)
		if actual != tc.expected {
			t.Errorf("detectFacebookProduct(%q) = %q, want %q", tc.caption, actual, tc.expected)
		}
	}
}

func TestFilterFacebookPages(t *testing.T) {
	samplePages := []FacebookPageConfig{
		{ID: "1", Name: "Affiliate Page", ProductGroup: "affiliate", Enabled: true},
		{ID: "2", Name: "Prontosan Spray Page", ProductGroup: "prontosan", Enabled: true},
		{ID: "3", Name: "Chăm sóc vết thương Prontosan", ProductGroup: "prontosan", Enabled: true},
		{ID: "4", Name: "Nutricomp Drink Plus Page", ProductGroup: "nutricomp", Enabled: true},
		{ID: "5", Name: "Nutricomp Renal Page", ProductGroup: "nutricomp", Enabled: true},
		{ID: "6", Name: "Sức Khỏe Cho Mọi Nhà", ProductGroup: "all", Enabled: true},
		{ID: "7", Name: "Disabled Page", ProductGroup: "prontosan", Enabled: false},
	}

	// 1. Prontosan filter should include prontosan + all, exclude affiliate and disabled
	prontosanFiltered := filterFacebookPages(samplePages, "prontosan", nil)
	if len(prontosanFiltered) != 3 {
		t.Fatalf("filterFacebookPages(prontosan) returned %d pages, want 3", len(prontosanFiltered))
	}
	for _, p := range prontosanFiltered {
		if p.ProductGroup == "affiliate" || p.ID == "7" {
			t.Errorf("unexpected page in prontosanFiltered: %+v", p)
		}
	}

	// 2. Nutricomp filter should include nutricomp + all, exclude affiliate
	nutricompFiltered := filterFacebookPages(samplePages, "nutricomp", nil)
	if len(nutricompFiltered) != 3 {
		t.Fatalf("filterFacebookPages(nutricomp) returned %d pages, want 3", len(nutricompFiltered))
	}
	for _, p := range nutricompFiltered {
		if p.ProductGroup == "affiliate" {
			t.Errorf("unexpected affiliate page in nutricompFiltered: %+v", p)
		}
	}

	// 3. Target IDs filter
	specificFiltered := filterFacebookPages(samplePages, "prontosan", []string{"2"})
	if len(specificFiltered) != 1 || specificFiltered[0].ID != "2" {
		t.Errorf("filterFacebookPages with specific ID returned %+v, want 1 page with ID 2", specificFiltered)
	}
}

func TestPostFacebookTool_DryRun(t *testing.T) {
	tmpDir := t.TempDir()
	imgPath := filepath.Join(tmpDir, "test_poster.png")
	if err := os.WriteFile(imgPath, []byte("fake image data"), 0644); err != nil {
		t.Fatalf("failed to create fake image: %v", err)
	}

	tool := NewPostFacebookTool(tmpDir)

	// Dry run with auto product
	res := tool.Execute(context.Background(), map[string]any{
		"image":   imgPath,
		"caption": "Biofilm vết thương Prontosan",
		"dry_run": true,
	})

	if res.IsError {
		t.Fatalf("Execute(dry_run) returned error: %s", res.ForLLM)
	}

	if res.ForUser == "" {
		t.Errorf("expected non-empty ForUser report in dry run")
	}
}
