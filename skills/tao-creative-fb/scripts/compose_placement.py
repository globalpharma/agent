#!/usr/bin/env python3
"""
Commercial Product Placement & Master Template Compositor - GlobalPharma
Ensures 100% adherence to approved Master Reference Templates for Renal, Plus, and Prontosan.
"""

import os
import sys
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render_poster import (
    render_pro_nutricomp_renal,
    render_pro_nutricomp_plus,
    render_pro_prontosan,
    render_pro_nutricomp_combo,
)


def create_placement(
    bg_path: str = None,
    product_type: str = "renal",
    output_path: str = "skills/tao-creative-fb/output/poster_nutricomp_renal_placement.png",
    ref_dir: str = None,
    headline: str = None,
    subline: str = None,
):
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    p_lower = str(product_type).lower()

    if "prontosan" in p_lower:
        render_pro_prontosan(headline=headline, subline=subline, output_path=out_p)
    elif "plus" in p_lower:
        render_pro_nutricomp_plus(headline=headline, subline=subline, output_path=out_p)
    elif "combo" in p_lower or "box" in p_lower:
        render_pro_nutricomp_combo(headline=headline, subline=subline, output_path=out_p)
    else:
        render_pro_nutricomp_renal(headline=headline, subline=subline, output_path=out_p)

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
