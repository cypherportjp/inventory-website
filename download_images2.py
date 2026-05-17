#!/usr/bin/env python3
"""Download product images for first 20 products from anime-store.jp and Yahoo! Shopping."""
import json, os, urllib.request, urllib.parse, ssl, time, re

os.makedirs('./data/images', exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('./data/products.json', encoding='utf-8') as f:
    products = json.load(f)

# First 20 only
first20 = products[:20]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

results = []
for idx, p in enumerate(first20):
    jan = p['jan']
    name = p['name'][:40]
    print(f"[{idx+1}/20] JAN: {jan} - {name[:30]}")
    
    img_url = ''
    
    # Try anime-store.jp first
    try:
        url = f"https://anime-store.jp/products/{jan}"
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Look for og:image or product images
        og_img = re.findall(r'og:image["\s]+content=["\']([^"\']+)["\']', html)
        if og_img:
            img_url = og_img[0]
            print(f"  [anime-store] Found: {img_url[:70]}")
        
        if not img_url:
            # Try to find any image URL
            imgs = re.findall(r'https?://[^"\']+\.(?:jpg|jpeg|png|webp)', html)
            for img in imgs:
                if 'product' in img.lower() or 'item' in img.lower() or jan in img:
                    img_url = img
                    break
        
        if img_url:
            # Download
            try:
                img_req = urllib.request.Request(img_url, headers=headers)
                img_resp = urllib.request.urlopen(img_req, context=ctx, timeout=10)
                img_data = img_resp.read()
                if len(img_data) > 5000:  # must be real image
                    filename = f"{jan}.jpg"
                    if len(filename) > 90:
                        ext = '.jpg'
                        max_name = 90 - len(ext)
                        safe_name = name.replace('/', '_').replace(' ', '_')[:max_name]
                        filename = f"{jan}_{safe_name}{ext}"
                    with open(f'./data/images/{filename}', 'wb') as f:
                        f.write(img_data)
                    print(f"  Saved: {len(img_data)} bytes -> {filename}")
                    p['image_url'] = f'/static/images/{filename}'
                    results.append(p)
                    time.sleep(2)
                    continue
                else:
                    img_url = ''
            except:
                img_url = ''
    except Exception as e:
        print(f"  [anime-store] Error: {e}")
    
    # Try Yahoo! Shopping
    try:
        search_url = f"https://shopping.yahoo.co.jp/search?p={urllib.parse.quote(jan)}"
        req = urllib.request.Request(search_url, headers=headers)
        resp = urllib.request.urlopen(req, context=ctx, timeout=10)
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Find product image URLs
        imgs = re.findall(r'https?://[^"\']+\.jpg', html)
        for img in imgs:
            if 'item' in img or 'product' in img or 'image' in img:
                # Clean URL - get higher resolution
                img = re.sub(r'\?.*$', '', img)
                img_url = img
                break
        
        if not img_url:
            # Try ss-static image
            imgs = re.findall(r'https://s.yimg.jp[^"\']+\.jpg', html)
            if imgs:
                img_url = imgs[0]
        
        if img_url:
            print(f"  [Yahoo] Found: {img_url[:70]}")
            try:
                img_req = urllib.request.Request(img_url, headers=headers)
                img_resp = urllib.request.urlopen(img_req, context=ctx, timeout=10)
                img_data = img_resp.read()
                if len(img_data) > 5000:
                    filename = f"{jan}.jpg"
                    if len(filename) > 90:
                        ext = '.jpg'
                        max_name = 90 - len(ext)
                        safe_name = name.replace('/', '_').replace(' ', '_')[:max_name]
                        filename = f"{jan}_{safe_name}{ext}"
                    with open(f'./data/images/{filename}', 'wb') as f:
                        f.write(img_data)
                    print(f"  Saved: {len(img_data)} bytes -> {filename}")
                    p['image_url'] = f'/static/images/{filename}'
                else:
                    print(f"  Image too small: {len(img_data)} bytes")
                    p['image_url'] = ''
            except Exception as e:
                print(f"  Download error: {e}")
                p['image_url'] = ''
        else:
            print(f"  [Yahoo] No image found")
            p['image_url'] = ''
    except Exception as e:
        print(f"  [Yahoo] Error: {e}")
        p['image_url'] = ''
    
    results.append(p)
    time.sleep(2)

# Save results
with open('./data/products_first20.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Update main products.json
saved = 0
for rp in results:
    for p in products:
        if p['jan'] == rp['jan']:
            p['image_url'] = rp.get('image_url', '')
            if p['image_url']:
                saved += 1
            break

with open('./data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)

print(f"\nDone! {saved}/20 products now have images")
print("Run 'python3 app.py' to restart the server")