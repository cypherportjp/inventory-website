#!/usr/bin/env python3
"""Scrape product images for first 10 items using Bing Image Search."""
import json, os, urllib.request, urllib.parse, ssl, time, re

os.makedirs('./data/images', exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with open('./data/products_first10.json', encoding='utf-8') as f:
    products = json.load(f)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

results = []
for idx, p in enumerate(products):
    jan = p['jan']
    name = p['name'][:30]
    maker = p['maker']
    
    # Build search query: use product name + maker
    query = f"{maker} {name}".strip()
    print(f"[{idx+1}/10] Searching: {query}")
    
    url = f'https://www.bing.com/images/search?q={urllib.parse.quote(query)}&first=0'
    
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        html = resp.read().decode('utf-8', errors='ignore')
        
        # Extract image URLs from Bing response
        # Look for "murl":"..." pattern
        urls = re.findall(r'murl"\s*:\s*"([^"]+)"', html)
        
        if not urls:
            # Try another pattern
            urls = re.findall(r'"murl"\s*:\s*"([^"]+)"', html)
        
        if urls:
            img_url = urls[0]
            print(f"  Found: {img_url[:80]}")
            
            # Download image
            try:
                img_req = urllib.request.Request(img_url, headers=headers)
                img_resp = urllib.request.urlopen(img_req, context=ctx, timeout=15)
                img_data = img_resp.read()
                
                # Save with JAN code
                filename = f"{jan}.jpg"
                # truncate if too long
                if len(filename) > 90:
                    ext = '.jpg'
                    max_name = 90 - len(ext)
                    filename = jan + '_' + name[:max_name].replace('/','_').replace(' ','_') + ext
                
                filepath = f'./data/images/{filename}'
                with open(filepath, 'wb') as f:
                    f.write(img_data)
                print(f"  Saved: {filepath} ({len(img_data)} bytes)")
                p['image_url'] = f'/static/images/{filename}'
            except Exception as e:
                print(f"  Download failed: {e}")
                p['image_url'] = ''
        else:
            print(f"  No images found")
            p['image_url'] = ''
            
    except Exception as e:
        print(f"  Search failed: {e}")
        p['image_url'] = ''
    
    results.append(p)
    time.sleep(2)  # be nice to Bing

# Save updated products with image URLs
with open('./data/products_first10.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\nDone! Updated products with image URLs.')