#!/usr/bin/env python3
"""
Simple product image generator using Pillow.
Creates placeholder images with product name when real images aren't available.
Run as: python3 generate_placeholders.py

This creates simple but informative placeholder images.
"""
import os
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
PRODUCTS_FILE = DATA_DIR / "products.json"
FONT_PATH = "/System/Library/Fonts/HiraginoSans-W6.ttc"

IMAGES_DIR.mkdir(exist_ok=True)

# ── Color palette for different categories ────────────────────────────────────
CATEGORY_COLORS = {
    "カード": (37, 99, 235),    # Blue - card games
    "サプライ": (34, 197, 94),   # Green - supplies
}

# Fallback font - use system default
def get_font(size=20):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
        except:
            return ImageFont.load_default()

def make_placeholder(product, size=(300, 300)):
    """Create a simple placeholder image for a product."""
    category = product.get("sheet", "カード")
    bg_color = CATEGORY_COLORS.get(category, (100, 100, 100))
    
    # Create image
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add category label at top
    font_sm = get_font(14)
    font_md = get_font(20)
    font_lg = get_font(28)
    
    # Category badge
    badge_text = "カード" if category == "カード" else "サプライ"
    badge_w, badge_h = draw.textsize(badge_text, font=font_sm) if hasattr(draw, 'textsize') else (60, 20)
    draw.rectangle([10, 10, 10 + badge_w + 12, 10 + badge_h + 8], fill=(255, 255, 255))
    draw.text((16, 12), badge_text, fill=bg_color, font=font_sm)
    
    # Product name (Japanese text, wrap if too long)
    name = product.get("name", "")[:30]
    
    # Split into lines
    chars_per_line = 12
    lines = []
    current_line = ""
    for char in name:
        current_line += char
        if len(current_line) >= chars_per_line:
            lines.append(current_line)
            current_line = ""
    if current_line:
        lines.append(current_line)
    
    # Draw product name centered
    y_start = 100
    line_height = 32
    for i, line in enumerate(lines[:4]):
        y = y_start + i * line_height
        # Get text size
        try:
            tw, th = draw.textsize(line, font=font_md)
        except:
            tw = len(line) * 16
            th = 20
        x = (size[0] - tw) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font_md)
    
    # JAN code at bottom
    jan = product.get("jan", "")
    font_jan = get_font(12)
    try:
        jw, jh = draw.textsize(jan, font=font_jan)
    except:
        jw, jh = len(jan) * 8, 12
    draw.text(((size[0] - jw) // 2, size[1] - 30), jan, fill=(200, 200, 200), font=font_jan)
    
    return img

def generate_all():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)
    
    print(f"Generating placeholders for {len(products)} products...")
    
    for i, p in enumerate(products):
        jan = p.get("jan", "")
        name = p.get("name", "")[:15]
        safe_name = "".join(c for c in name if c.isalnum() or c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        filename = f"{jan}_{safe_name[:15]}.jpg"
        filepath = IMAGES_DIR / filename
        
        if p.get("image_url") and Path(BASE_DIR / "static" / p["image_url"].lstrip("/")).exists():
            print(f"[{i+1}/{len(products)}] Skip {jan} - already exists")
            continue
        
        img = make_placeholder(p)
        img.save(filepath, "JPEG", quality=85)
        
        rel_path = f"/static/images/{filename}"
        p["image_url"] = rel_path
        
        print(f"[{i+1}/{len(products)}] Created: {filename}")
    
    # Save updated products
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\nDone! All {len(products)} products have images.")

if __name__ == "__main__":
    generate_all()