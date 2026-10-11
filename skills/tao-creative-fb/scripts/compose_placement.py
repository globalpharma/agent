#!/usr/bin/env python3
"""
Commercial Product Placement Script - GlobalPharma
Places real official B.Braun product packaging and GlobalPharma logo onto
photorealistic lifestyle/studio backgrounds with realistic contact and cast shadows.
"""

import os
import argparse
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

def create_placement(
    bg_path: str = None,
    product_type: str = "renal",
    output_path: str = "skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png",
    ref_dir: str = "skills/tao-creative-fb/assets/references"
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    p_lower = str(product_type).lower()

    # Automatic background resolution if not supplied or missing
    if not bg_path or bg_path == "auto" or not os.path.exists(bg_path):
        candidate_bgs = []
        if "prontosan" in p_lower:
            candidate_bgs = [os.path.join(ref_dir, "bg_prontosan_clinical.jpg")]
        elif "plus" in p_lower:
            candidate_bgs = [os.path.join(ref_dir, "bg_lifestyle_dining.jpg"), os.path.join(ref_dir, "bg_luxury_teal_podium.jpg")]
        else:
            candidate_bgs = [os.path.join(ref_dir, "bg_luxury_teal_podium.jpg"), os.path.join(ref_dir, "bg_lifestyle_dining.jpg")]

        bg_path = None
        for b in candidate_bgs:
            if os.path.exists(b):
                bg_path = b
                break

        if not bg_path:
            # Create high quality solid medical canvas
            bg = Image.new('RGBA', (1080, 1080), (15, 30, 40, 255))
        else:
            bg = Image.open(bg_path).convert('RGBA')
    else:
        bg = Image.open(bg_path).convert('RGBA')

    canvas_w, canvas_h = bg.size

    # 1. Select Product Reference
    if "prontosan" in p_lower:
        prod_file = os.path.join(ref_dir, "cut_prontosan_bottle.png")
        prod_w = int(canvas_w * 0.28)
        pos_x = int(canvas_w * 0.55)
        pos_y = int(canvas_h * 0.42)
    elif "combo" in p_lower:
        prod_file = os.path.join(ref_dir, "cut_nutricomp_box.png")
        prod_w = int(canvas_w * 0.45)
        pos_x = int(canvas_w * 0.45)
        pos_y = int(canvas_h * 0.49)
    elif "plus" in p_lower:
        plus_bottle = os.path.join(ref_dir, "cut_nutricomp_plus_bottle.png")
        if os.path.exists(plus_bottle):
            prod_file = plus_bottle
            prod_w = int(canvas_w * 0.36)
            pos_x = int(canvas_w * 0.55)
            pos_y = int(canvas_h * 0.38)
        else:
            prod_file = os.path.join(ref_dir, "real_nutricomp_drink_plus_vanilla.jpg")
            prod_w = int(canvas_w * 0.36)
            pos_x = int(canvas_w * 0.55)
            pos_y = int(canvas_h * 0.38)
    else:  # default: Nutricomp Renal 200ml single bottle
        single_bottle = os.path.join(ref_dir, "cut_nutricomp_single_bottle.png")
        if os.path.exists(single_bottle):
            prod_file = single_bottle
            prod_w = int(canvas_w * 0.38)
            pos_x = int(canvas_w * 0.55)
            pos_y = int(canvas_h * 0.38)
        else:
            prod_file = os.path.join(ref_dir, "cut_nutricomp_box.png")
            prod_w = int(canvas_w * 0.45)
            pos_x = int(canvas_w * 0.45)
            pos_y = int(canvas_h * 0.49)

    if not os.path.exists(prod_file):
        raise FileNotFoundError(f"Product reference not found: {prod_file}")

    prod = Image.open(prod_file).convert('RGBA')
    logo_file = os.path.join(ref_dir, "real_logo_globalpharma_master.png")
    if not os.path.exists(logo_file):
        logo_file = os.path.join(ref_dir, "real_logo_globalpharma_banner.png")
    logo = Image.open(logo_file).convert('RGBA') if os.path.exists(logo_file) else None

    # Scale product
    prod_h = int(prod.height * (prod_w / prod.width))
    prod_scaled = prod.resize((prod_w, prod_h), Image.Resampling.LANCZOS)

    # Warmth & Lighting Adjustment
    r, g, b, a = prod_scaled.split()
    rgb = Image.merge('RGB', (r, g, b))
    enhancer_b = ImageEnhance.Brightness(rgb)
    rgb = enhancer_b.enhance(1.02)
    r2, g2, b2 = rgb.split()
    prod_warm = Image.merge('RGBA', (r2, g2, b2, a))

    # Realistic Shadows (Cast + Contact)
    shadow_layer = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))

    # Cast shadow
    alpha_mask = prod_scaled.split()[-1]
    shadow_shape = Image.new('RGBA', prod_scaled.size, (45, 30, 18, 90))
    shadow_shape.putalpha(alpha_mask)
    cast_w = int(prod_w * 1.02)
    cast_h = int(prod_h * 0.30)
    cast_shadow = shadow_shape.resize((cast_w, cast_h), Image.Resampling.BILINEAR)
    cast_shadow = cast_shadow.filter(ImageFilter.GaussianBlur(16))
    shadow_layer.paste(cast_shadow, (pos_x + 20, pos_y + prod_h - 38), cast_shadow)

    # Tight Contact shadow
    contact_w = int(prod_w * 0.88)
    contact_h = 16
    contact_shadow = Image.new('RGBA', (contact_w, contact_h), (35, 22, 12, 150))
    contact_mask = Image.new('L', (contact_w, contact_h), 0)
    draw = ImageDraw.Draw(contact_mask)
    draw.ellipse([0, 0, contact_w, contact_h], fill=190)
    contact_shadow.putalpha(contact_mask)
    contact_shadow = contact_shadow.filter(ImageFilter.GaussianBlur(5))
    shadow_layer.paste(contact_shadow, (pos_x + 28, pos_y + prod_h - 10), contact_shadow)

    # Composite layers
    composed = Image.alpha_composite(bg, shadow_layer)
    composed.paste(prod_warm, (pos_x, pos_y), prod_warm)

    # Logo Placement (Top Left, elegant subtle white glow)
    if logo:
        logo_w = int(canvas_w * 0.16)
        logo_h = int(logo.height * (logo_w / logo.width))
        logo_scaled = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        logo_alpha = logo_scaled.split()[-1]
        logo_glow = Image.new('RGBA', logo_scaled.size, (255, 255, 255, 130))
        logo_glow.putalpha(logo_alpha)
        logo_glow = logo_glow.filter(ImageFilter.GaussianBlur(3))

        logo_pos_x = int(canvas_w * 0.05)
        logo_pos_y = int(canvas_h * 0.045)
        composed.paste(logo_glow, (logo_pos_x, logo_pos_y), logo_glow)
        composed.paste(logo_scaled, (logo_pos_x, logo_pos_y), logo_scaled)

    composed.convert('RGB').save(output_path, quality=95)
    print(f"MEDIA:{os.path.abspath(output_path)}")
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compose real product placement onto lifestyle/studio background")
    parser.add_argument("--bg", default="auto", help="Path to lifestyle background image (default: auto)")
    parser.add_argument("--product", default="renal", choices=["renal", "nutricomp", "plus", "combo", "prontosan"])
    parser.add_argument("--output", default="skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png")
    parser.add_argument("--ref-dir", default="skills/tao-creative-fb/assets/references")
    args = parser.parse_args()

    create_placement(args.bg, args.product, args.output, args.ref_dir)
