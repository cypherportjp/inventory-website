#!/usr/bin/env python3
"""
Product image scraper.
Searches by JAN code and product name, downloads images to local folder.
Run as: python3 scraper.py [--limit N] [--resume]

Images will be saved to: data/images/
"""
import os
import json
import time
import requests
from urllib.parse import quote
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
PRODUCTS_FILE = DATA_DIR / "products.json"

IMAGES_DIR.mkdir(exist_ok=True)

# ── Config ───────────────────────────────────────────────────────────────────
SEARCH_ENGINE = "duckduckgo"   # "duckduckgo" or "google"
IMAGE_ENGINE  = "jina"         # jina.ai based extraction (free, no key needed)
REQUEST_DELAY  = 2.0             # seconds between requests (be polite!)
MAX_RETRIES   = 2
# ─────────────────────────────────────────────────────────────────────────────

def load_products():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

def search_jan(jan_code, product_name):
    """Search for image URL by JAN code. Returns first result URL or None."""
    query = f"{jan_code} {product_name[:20]}"
    url = f"https://duckduckgo.com/?q={quote(query)}&ia=images"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        # Look for image URLs in the response
        # DuckDuckGo HTML response contains image links in JSON
        import re
        # Find image URLs from the page
        matches = re.findall(r'"image":"(https://[^"]+)"', resp.text)
        if matches:
            return matches[0]
    except Exception as e:
        print(f"  Search error: {e}")
    
    return None

def jina_extract(url):
    """Use jina.ai to extract the main image from a web page."""
    try:
        api_url = f"https://r.jina.ai/{quote(url, safe='')}"
        resp = requests.get(api_url, timeout=15, headers={"Accept": "text/plain"})
        if resp.status_code == 200:
            text = resp.text
            # Look for image URLs in the extracted text
            import re
            img_matches = re.findall(r'https?://[^"\s]+\.(?:jpg|jpeg|png|webp)[^"\s]*', text, re.IGNORECASE)
            if img_matches:
                return img_matches[0]
    except Exception as e:
        print(f"  Jina extract error: {e}")
    return None

def download_image(url, save_path):
    """Download an image to save_path. Returns True on success."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15, stream=True)
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "image" not in content_type and "jpeg" not in content_type:
                # Try to detect from URL
                pass
            with open(save_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print(f"  Download error: {e}")
    return False

def make_safe_filename(jan, name):
    """Create a safe filename from JAN + product name."""
    name_part = "".join(c for c in name[:15] if c.isalnum() or c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    return f"{jan}_{name_part[:15]}"

def scrape_all(limit=None, resume=False):
    products = load_products()
    total = len(products)
    start_index = 0
    
    if resume:
        # Find first product without an image
        for i, p in enumerate(products):
            if not p.get("image_url"):
                start_index = i
                break
        else:
            print("All products already have images.")
            return
    
    count = 0
    for i in range(start_index, total):
        p = products[i]
        
        if limit and count >= limit:
            break
        
        if p.get("image_url"):
            print(f"[{i+1}/{total}] Skip {p['jan']} - already has image")
            continue
        
        jan = p["jan"]
        name = p["name"]
        
        print(f"[{i+1}/{total}] Searching: {jan} - {name[:30]}...")
        
        image_url = search_jan(jan, name)
        
        if image_url:
            print(f"  Found URL: {image_url[:80]}")
            save_name = make_safe_filename(jan, name) + ".jpg"
            save_path = IMAGES_DIR / save_name
            
            if download_image(image_url, save_path):
                rel_path = f"/static/images/{save_name}"
                p["image_url"] = rel_path
                print(f"  Saved: {rel_path}")
                count += 1
            else:
                print(f"  Failed to download")
                p["image_url"] = ""
        else:
            print(f"  No image found")
            p["image_url"] = ""
        
        # Save progress after each item
        save_products(products)
        time.sleep(REQUEST_DELAY)
    
    print(f"\nDone! Downloaded {count} images.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scrape product images")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of products to process")
    parser.add_argument("--resume", action="store_true", help="Resume from first product without image")
    args = parser.parse_args()
    
    scrape_all(limit=args.limit, resume=args.resume)