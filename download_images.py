#!/usr/bin/env python3
"""Download product images from Amazon for the first 20 products."""
import json, os, urllib.request, urllib.parse, ssl, time, re

os.makedirs('./data/images', exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Load first 20 products
with open('./data/products.json', encoding='utf-8') as f:
    all_products = json.load(f)

products = all_products[:20]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.amazon.co.jp/',
}

results = []
for idx, p in enumerate(products):
    jan = p['jan']
    name = p['name'][:40].replace('/', ' ').replace('　', ' ')
    query = f"{jan} {name}".strip()
    print(f"[{idx+1}/20] Search: {query[:60]}")
    
    search_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(jan)}"
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Extract image URLs from Amazon search results
        img_urls = re.findall(r'https://m\.media-amazon\.com/images/I/[a-zA-Z0-9]+._AC_UL\d+_\.jpg', html)
        img_urls = list(dict.fromkeys(img_urls))
        
        if img_urls:
            img_url = img_urls[0]
            print(f"  Found: {img_url[:70]}")
            
            img_req = urllib.request.Request(img_url, headers=headers)
            img_resp = urllib.request.urlopen(img_req, context=ctx, timeout=15)
            img_data = img_resp.read()
            
            filename = f"{jan}.jpg"
            if len(filename) > 90:
                ext = '.jpg'
                max_name = 90 - len(ext)
                safe_name = name[:max_name].replace(' ', '_').replace('/', '_')
                filename = f"{jan}_{safe_name}{ext}"
            
            filepath = f'./data/images/{filename}'
            with open(filepath, 'wb') as f:
                f.write(img_data)
            print(f"  Saved: {len(img_data)} bytes -> {filename}")
            p['image_url'] = f'/static/images/{filename}'
        else:
            print(f"  No image found")
            p['image_url'] = ''
            
    except Exception as e:
        print(f"  Error: {e}")
        p['image_url'] = ''
    
    results.append(p)
    time.sleep(3)

# Save to products_first20.json
with open('./data/products_first20.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Also update main products.json to mark image_url for first 20
for i, rp in enumerate(results):
    all_products[i]['image_url'] = rp.get('image_url', '')

with open('./data/products.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

print(f'\nDone! Saved 20 images to data/images/')