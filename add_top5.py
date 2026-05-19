#!/usr/bin/env python3
"""Add 5 products from Excel to inventory, with images, at the top of the list."""
import json, os, urllib.request, urllib.parse, ssl, time, re, openpyxl

os.makedirs('./data/images', exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── 1. Load existing products ──────────────────────────────────────────────
with open('data/products.json', encoding='utf-8') as f:
    existing = json.load(f)

print(f"Loaded {len(existing)} existing products, highest id={max(p['id'] for p in existing)}")

# ── 2. Read first 5 rows from Excel ────────────────────────────────────────
wb = openpyxl.load_workbook('data/ミニ四駆・ミニカーバイク他完成品 在庫リスト0515.xlsx')
ws = wb.active

new_rows = []
for row in ws.iter_rows(min_row=6, max_row=10, values_only=True):
    mfr, jan, sku, name, ct, box_, price, stock, order_qty, unit = row
    # Normalize maker name
    if mfr == 'ﾀﾐﾔ':
        mfr_norm = 'ﾀﾐﾔ'
    else:
        mfr_norm = mfr
    new_rows.append({
        'maker': mfr_norm,
        'jan': str(jan),
        'code': str(sku) if sku else '',
        'name': name or '',
        'ct': ct,
        'box': box_,
        'price': int(price) if price else 0,
        'stock': stock or '○',
        'order_qty': str(order_qty) if order_qty else '',
        'unit': unit or '個',
    })

print("\nNew products to add:")
for r in new_rows:
    print(f"  [{r['maker']}] {r['jan']} {r['name']} ¥{r['price']}")

# ── 3. Download images from Tamiya website ────────────────────────────────
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://www.tamiya.com/',
}

# Tamiya product page pattern
ITEM_BASE = 94000  # base item number from tamiya URL pattern
# item numbers from excel: 1, 2, 3, 4, 5 → need actual item numbers
# Let's use the actual item page on tamiya.com using search

def download_image(url, jan, max_retries=2):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, context=ctx, timeout=20)
            img_data = resp.read()
            filepath = f'./data/images/{jan}.jpg'
            with open(filepath, 'wb') as f:
                f.write(img_data)
            print(f"  ✓ Downloaded {jan} ({len(img_data)} bytes)")
            return f'/static/images/{jan}.jpg'
        except Exception as e:
            print(f"  ✗ Failed {url[:60]} — {e}")
            time.sleep(2)
    return ''

# Tamiya URLs for the specific products (from search results above)
tamiya_urls = {
    '4950344031504': 'https://www.tamiya.com/japan/products/95555/index.html',  # 2mm aluminum lock nut purple
    '4950344031511': 'https://www.tamiya.com/japan/products/95555/index.html',  # orange same page
    '4950344032891': 'https://www.tamiya.com/japan/products/95439/index.html',  # gumblaster XTO
    '4950344032907': 'https://www.tamiya.com/japan/products/95512/index.html',  # broken gigant black premium
    '4950344032914': 'https://www.tamiya.com/japan/products/95435/index.html',  # HG maintenance base
}

# Try to get actual image from Tamiya product page
def extract_tamiya_image(product_url, jan):
    try:
        req = urllib.request.Request(product_url, headers=headers)
        resp = urllib.request.urlopen(req, context=ctx, timeout=20)
        html = resp.read().decode('utf-8', errors='ignore')
        # Look for main product image
        matches = re.findall(r'https://tamiya\.com[^\s"]+\.(jpg|JPG|png|PNG)', html)
        if not matches:
            # Try og:image
            matches = re.findall(r'og:image["\s]+content="([^"]+)"', html)
        if not matches:
            # Try any large image
            matches = re.findall(r'https://[^\s"]+/(products|images)[^\s"]+\.(jpg|JPG)', html)
        if matches:
            return download_image(matches[0], jan)
    except Exception as e:
        print(f"  Failed to extract from {product_url}: {e}")
    return ''

print("\nDownloading images...")
for r in new_rows:
    url = tamiya_urls.get(r['jan'], '')
    if url:
        img = extract_tamiya_image(url, r['jan'])
        r['image_url'] = img
    else:
        r['image_url'] = ''
    time.sleep(1)

# ── 4. Reassign IDs: new products get 1-5, existing shift to 6+ ─────────────
new_products = []
for i, r in enumerate(new_rows, start=1):
    new_products.append({
        'id': i,
        **r,
    })

for p in existing:
    p['id'] += 5

# ── 5. Merge and save ──────────────────────────────────────────────────────
all_products = new_products + existing
with open('data/products.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

print(f"\nDone! Wrote {len(all_products)} products.")
print("New products at top:")
for p in new_products:
    print(f"  id={p['id']} [{p['maker']}] {p['jan']} {p['name']} img={p['image_url']}")