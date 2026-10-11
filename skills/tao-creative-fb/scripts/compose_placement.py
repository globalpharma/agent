#!/usr/bin/env python3
"""
Commercial Product Placement Script - GlobalPharma
Places real official B.Braun product packaging and GlobalPharma brand header onto
photorealistic lifestyle/studio backgrounds with realistic contact and cast shadows.
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

def find_ref_dir(given_dir: str = None) -> str:
    candidates = []
    if given_dir:
        candidates.append(given_dir)
    script_dir = Path(__file__).resolve().parent
    candidates.extend([
        str(script_dir.parent / "assets" / "references"),
        "/app/data/skills/tao-creative-fb/assets/references",
        "/app/workspace/skills/tao-creative-fb/assets/references",
        "skills/tao-creative-fb/assets/references",
    ])
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    return given_dir or "skills/tao-creative-fb/assets/references"

def create_placement(
    bg_path: str = None,
    product_type: str = "renal",
    output_path: str = "skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png",
    ref_dir: str = None
):
    ref_dir = find_ref_dir(ref_dir)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    p_lower = str(product_type).lower()

    # Automatic background resolution if not supplied or missing
    if not bg_path or bg_path == "auto" or not os.path.exists(bg_path):
        candidate_bgs = []
        if "prontosan" in p_lower:
            candidate_bgs = [os.path.join(ref_dir, "bg_prontosan_clinical.jpg")]
        elif "plus" in p_lower:
            candidate_bgs = [os.path.join(ref_dir, "bg_lifestyle_dining.jpg"), os.path.join(ref_dir, "bg_luxury_teal_podium.jpg")]
        else:
            candidate_bgs = [os.path.join(ref_dir, "bg_lifestyle_dining.jpg"), os.path.join(ref_dir, "bg_luxury_teal_podium.jpg")]

        bg_path = None
        for b in candidate_bgs:
            if os.path.exists(b):
                bg_path = b
                break

        if not bg_path:
            bg = Image.new('RGBA', (1024, 1024), (245, 243, 238, 255))
        else:
            bg = Image.open(bg_path).convert('RGBA')
    else:
        bg = Image.open(bg_path).convert('RGBA')

    canvas_w, canvas_h = bg.size

    # 1. Select Product Reference
    if "prontosan" in p_lower:
        prod_file = os.path.join(ref_dir, "cut_prontosan_bottle.png")
        prod_h = int(canvas_h * 0.44)
        prod_w = int(prod_h * 0.58)
        pos_x = int(canvas_w * 0.54)
        pos_y = int(canvas_h * 0.44)
    elif "combo" in p_lower or "box" in p_lower:
        prod_file = os.path.join(ref_dir, "cut_nutricomp_box.png")
        prod_w = int(canvas_w * 0.48)
        prod = Image.open(prod_file).convert('RGBA')
        prod_h = int(prod.height * (prod_w / prod.width))
        pos_x = int(canvas_w * 0.46)
        pos_y = int(canvas_h * 0.48)
    elif "plus" in p_lower:
        plus_bottle = os.path.join(ref_dir, "cut_nutricomp_plus_bottle.png")
        prod_file = plus_bottle if os.path.exists(plus_bottle) else os.path.join(ref_dir, "real_nutricomp_drink_plus_strawberry.jpg")
        prod = Image.open(prod_file).convert('RGBA')
        prod_h = int(canvas_h * 0.46)
        prod_w = int(prod.width * (prod_h / prod.height))
        pos_x = int(canvas_w * 0.52)
        pos_y = int(canvas_h * 0.42)
    else:  # default: Nutricomp Renal 200ml single bottle
        renal_bottle = os.path.join(ref_dir, "cut_nutricomp_renal_bottle.png")
        if not os.path.exists(renal_bottle):
            renal_bottle = os.path.join(ref_dir, "cut_nutricomp_single_bottle.png")
        prod_file = renal_bottle
        prod = Image.open(prod_file).convert('RGBA')
        prod_h = int(canvas_h * 0.46)
        prod_w = int(prod.width * (prod_h / prod.height))
        pos_x = int(canvas_w * 0.52)
        pos_y = int(canvas_h * 0.42)

    if not os.path.exists(prod_file):
        raise FileNotFoundError(f"Product reference not found: {prod_file}")

    if 'prod' not in locals():
        prod = Image.open(prod_file).convert('RGBA')

    prod_scaled = prod.resize((prod_w, prod_h), Image.Resampling.LANCZOS)

    # Warmth & Lighting Matching
    r, g, b, a = prod_scaled.split()
    rgb = Image.merge('RGB', (r, g, b))
    rgb = ImageEnhance.Color(rgb).enhance(1.04)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.01)
    r2, g2, b2 = rgb.split()
    prod_warm = Image.merge('RGBA', (r2, g2, b2, a))

    # Realistic 3-Layer Shadow Architecture
    shadow_layer = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    # Layer 1: Soft directional table shadow (window light from left-front casting to right)
    cast_w = int(prod_w * 1.3)
    cast_h = int(prod_h * 0.22)
    cast_layer = Image.new('RGBA', (cast_w, cast_h), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(cast_layer)
    cdraw.ellipse([0, 0, cast_w, cast_h], fill=(45, 28, 16, 70))
    cast_layer = cast_layer.filter(ImageFilter.GaussianBlur(14))
    shadow_layer.paste(cast_layer, (pos_x + int(prod_w * 0.15), pos_y + prod_h - int(cast_h * 0.65)), cast_layer)

    # Layer 2: Medium ambient occlusion shadow under the base
    mid_w = int(prod_w * 0.88)
    mid_h = int(prod_h * 0.08)
    mid_layer = Image.new('RGBA', (mid_w, mid_h), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(mid_layer)
    mdraw.ellipse([0, 0, mid_w, mid_h], fill=(35, 20, 10, 140))
    mid_layer = mid_layer.filter(ImageFilter.GaussianBlur(6))
    shadow_layer.paste(mid_layer, (pos_x + int(prod_w * 0.08), pos_y + prod_h - int(mid_h * 0.70)), mid_layer)

    # Layer 3: Direct contact crease line (grounding the bottle firmly on the wood)
    con_w = int(prod_w * 0.76)
    con_h = int(prod_h * 0.04)
    con_layer = Image.new('RGBA', (con_w, con_h), (0, 0, 0, 0))
    ImageDraw.Draw(con_layer).ellipse([0, 0, con_w, con_h], fill=(25, 12, 6, 210))
    con_layer = con_layer.filter(ImageFilter.GaussianBlur(2))
    shadow_layer.paste(con_layer, (pos_x + int(prod_w * 0.13), pos_y + prod_h - int(con_h * 0.75)), con_layer)

    # Composite product onto background
    composed = Image.alpha_composite(bg, shadow_layer)
    composed.paste(prod_warm, (pos_x, pos_y), prod_warm)

    # 2. Official Brand Header Badge (GlobalPharma + German Flag Roundel)
    header_file = os.path.join(ref_dir, "brand_header_master.png")
    if os.path.exists(header_file):
        header = Image.open(header_file).convert('RGBA')
        hdr_w = int(canvas_w * 0.36)
        hdr_h = int(header.height * (hdr_w / header.width))
        header_scaled = header.resize((hdr_w, hdr_h), Image.Resampling.LANCZOS)

        pad_x = 16
        pad_y = 10
        pill_w = hdr_w + pad_x * 2
        pill_h = hdr_h + pad_y * 2
        pill_x = int(canvas_w * 0.04)
        pill_y = int(canvas_h * 0.04)

        # Frosted glass card with clean rounded border
        pill = Image.new('RGBA', (pill_w, pill_h), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(pill)
        pdraw.rounded_rectangle([0, 0, pill_w, pill_h], radius=16, fill=(255, 255, 255, 240), outline=(230, 238, 242, 220), width=1)

        # Subtle card shadow
        pill_shadow = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(pill_shadow)
        sdraw.rounded_rectangle([pill_x + 2, pill_y + 4, pill_x + pill_w + 2, pill_y + pill_h + 4], radius=16, fill=(0, 0, 0, 40))
        pill_shadow = pill_shadow.filter(ImageFilter.GaussianBlur(8))

        composed = Image.alpha_composite(composed, pill_shadow)
        composed.paste(pill, (pill_x, pill_y), pill)
        composed.paste(header_scaled, (pill_x + pad_x, pill_y + pad_y), header_scaled)

    composed.convert('RGB').save(output_path, quality=95)
    print(f"MEDIA:{os.path.abspath(output_path)}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compose real product placement onto lifestyle/studio background")
    parser.add_argument("--bg", default="auto", help="Path to lifestyle background image (default: auto)")
    parser.add_argument("--product", default="renal", choices=["renal", "nutricomp", "plus", "combo", "prontosan"])
    parser.add_argument("--output", default="skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png")
    parser.add_argument("--ref-dir", default=None)
    args = parser.parse_args()

    create_placement(args.bg, args.product, args.output, args.ref_dir)
