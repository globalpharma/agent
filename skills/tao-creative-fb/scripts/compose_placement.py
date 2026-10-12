#!/usr/bin/env python3
"""
Commercial Product Placement & Master Template Compositor - GlobalPharma
Places real official B.Braun product packaging and GlobalPharma logo onto
photorealistic AI lifestyle/studio backgrounds with realistic contact shadows,
or renders dynamic headlines when running standalone.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# Resolve references directory across local and container paths
candidate_refs = [
    SKILL_DIR / "assets" / "references",
    Path("/app/data/skills/tao-creative-fb/assets/references"),
    Path("/app/workspace/skills/tao-creative-fb/assets/references"),
    SKILL_DIR.parent.parent / "skills" / "tao-creative-fb" / "assets" / "references",
]
REFS_DIR = SKILL_DIR / "assets" / "references"
for c in candidate_refs:
    if c.exists():
        REFS_DIR = c
        break

sys.path.insert(0, str(SCRIPT_DIR))
try:
    from render_poster import (
        render_pro_nutricomp_renal,
        render_pro_nutricomp_plus,
        render_pro_prontosan,
        render_pro_nutricomp_combo,
    )
    HAS_RENDERER = True
except Exception:
    HAS_RENDERER = False


def create_placement(
    bg_path: str = None,
    product_type: str = "renal",
    output_path: str = None,
    ref_dir: str = None,
    headline: str = None,
    subline: str = None,
):
    p_lower = str(product_type).lower()
    if not output_path or output_path.endswith("poster_nutricomp_renal_placement.png"):
        output_dir = Path("/app/workspace/output") if Path("/app/workspace").exists() else (SKILL_DIR / "output")
        output_path = str(output_dir / f"creative_placed_{p_lower}_{int(time.time()*1000)}.png")

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    r_dir = Path(ref_dir) if ref_dir and Path(ref_dir).exists() else REFS_DIR

    # Case 1: Real AI image provided as background -> Do True Optical Product Placement
    if bg_path and bg_path != "auto" and os.path.exists(bg_path):
        try:
            bg = Image.open(bg_path).convert('RGBA')
            canvas_w, canvas_h = bg.size

            # Select authentic bottle cut
            if "prontosan" in p_lower:
                prod_candidates = ["cut_prontosan_bottle.png"]
                target_scale = 0.44
                pos_x_ratio = 0.65
                pos_y_ratio = 0.48
            elif "plus" in p_lower:
                prod_candidates = ["cut_nutricomp_plus_bottle.png", "crop_nutricomp_bottle.png"]
                target_scale = 0.46
                pos_x_ratio = 0.65
                pos_y_ratio = 0.46
            elif "combo" in p_lower or "box" in p_lower:
                prod_candidates = ["cut_nutricomp_box.png", "real_nutricomp_combo12_giftbox.png"]
                target_scale = 0.48
                pos_x_ratio = 0.45
                pos_y_ratio = 0.46
            else: # renal
                prod_candidates = ["cut_nutricomp_renal_bottle.png", "cut_nutricomp_single_bottle.png"]
                target_scale = 0.46
                pos_x_ratio = 0.65
                pos_y_ratio = 0.46

            prod_file = None
            for cand in prod_candidates:
                p_cand = r_dir / cand
                if p_cand.exists():
                    prod_file = str(p_cand)
                    break

            if prod_file and os.path.exists(prod_file):
                prod = Image.open(prod_file).convert('RGBA')
                prod_h = int(canvas_h * target_scale)
                prod_w = int(prod.width * (prod_h / prod.height))
                prod_scaled = prod.resize((prod_w, prod_h), Image.Resampling.LANCZOS)

                pos_x = int(canvas_w * pos_x_ratio)
                pos_y = int(canvas_h * pos_y_ratio)

                # Keep bottle within canvas boundaries
                if pos_x + prod_w > canvas_w - 20:
                    pos_x = canvas_w - prod_w - 20
                if pos_y + prod_h > canvas_h - 20:
                    pos_y = canvas_h - prod_h - 20

                # Cast + contact shadows
                shadow = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
                sdraw = ImageDraw.Draw(shadow)
                sdraw.ellipse(
                    [pos_x - int(prod_w * 0.1), pos_y + prod_h - int(prod_h * 0.1),
                     pos_x + prod_w + int(prod_w * 0.1), pos_y + prod_h + int(prod_h * 0.05)],
                    fill=(0, 0, 0, 120)
                )
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))

                composed = Image.alpha_composite(bg, shadow)
                composed.paste(prod_scaled, (pos_x, pos_y), prod_scaled)
            else:
                composed = bg

            # Add Official Brand Header Badge (Top-Left)
            header_cand = r_dir / "brand_header_master.png"
            if not header_cand.exists():
                header_cand = r_dir / "real_logo_globalpharma_master.png"

            if header_cand.exists():
                header = Image.open(str(header_cand)).convert('RGBA')
                hdr_w = int(canvas_w * 0.38)
                hdr_h = int(header.height * (hdr_w / header.width))
                header_scaled = header.resize((hdr_w, hdr_h), Image.Resampling.LANCZOS)

                pad_x = 16
                pad_y = 10
                pill_w = hdr_w + pad_x * 2
                pill_h = hdr_h + pad_y * 2
                pill_x = int(canvas_w * 0.04)
                pill_y = int(canvas_h * 0.04)

                pill = Image.new('RGBA', (pill_w, pill_h), (0, 0, 0, 0))
                pdraw = ImageDraw.Draw(pill)
                pdraw.rounded_rectangle(
                    [0, 0, pill_w, pill_h],
                    radius=16,
                    fill=(255, 255, 255, 235),
                    outline=(220, 230, 235, 200),
                    width=1
                )

                composed.paste(pill, (pill_x, pill_y), pill)
                composed.paste(header_scaled, (pill_x + pad_x, pill_y + pad_y), header_scaled)

            composed.convert('RGB').save(out_p, quality=95)
            print(f"MEDIA:{os.path.abspath(out_p)}")
            return str(out_p)
        except Exception as e:
            print(f"[WARN] Optical placement on AI background failed: {e}, falling back to renderer")

    # Case 2: Standalone or no background -> Use dynamic headline poster
    if HAS_RENDERER:
        if "prontosan" in p_lower:
            render_pro_prontosan(headline=headline, subline=subline, output_path=out_p)
        elif "plus" in p_lower:
            render_pro_nutricomp_plus(headline=headline, subline=subline, output_path=out_p)
        elif "combo" in p_lower or "box" in p_lower:
            render_pro_nutricomp_combo(headline=headline, subline=subline, output_path=out_p)
        else:
            render_pro_nutricomp_renal(headline=headline, subline=subline, output_path=out_p)
    else:
        print(f"[ERROR] Renderer not available and no background provided")

    print(f"MEDIA:{os.path.abspath(out_p)}")
    return str(out_p)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GlobalPharma Master Reference Placement")
    parser.add_argument("--bg", type=str, default="auto", help="Path to background image")
    parser.add_argument("--product", type=str, default="renal", help="Product type: renal | plus | combo | prontosan")
    parser.add_argument("--headline", type=str, default=None, help="Optional headline override")
    parser.add_argument("--subline", type=str, default=None, help="Optional subline override")
    parser.add_argument("--output", type=str, default="skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png")
    parser.add_argument("--ref-dir", type=str, default=None)
    args, _ = parser.parse_known_args()

    create_placement(
        bg_path=args.bg,
        product_type=args.product,
        output_path=args.output,
        ref_dir=args.ref_dir,
        headline=args.headline,
        subline=args.subline,
    )
