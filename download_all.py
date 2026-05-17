#!/usr/bin/env python3
"""
Download product images for ミニ四駆・ミニカー・バイク inventory.
Uses Yahoo! Shopping search to find real product images.
"""
import os, json, time, sys, re, urllib.request, urllib.parse, ssl

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DATA_DIR, 'data')
IMG_DIR = os.path.join(DATA_DIR, 'images')
PROGRESS_FILE = os.path.join(DATA_DIR, 'download_progress.json')

os.makedirs(IMG_DIR, exist_ok=True)
ctx = ssl._create_unverified_context()

def load_products():
    with open(os.path.join(DATA_DIR, 'products.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def save_progress(idx, total, saved, failed):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'idx': idx, 'total': total, 'saved': saved, 'failed': failed, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}, f, ensure_ascii=False)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return None

def search_yahoo_img(query, maker=''):
    """Search Yahoo! Shopping and return first image URL."""
    q = f'{maker} {query}'.strip()
    encoded_q = urllib.parse.quote(q)
    url = f'https://shopping.yahoo.co.jp/search?p={encoded_q}&image_size=300'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        img_pattern = re.compile(r'item-shopping\.c\.yimg\.jp/i/j/([A-Za-z0-9_]+)\?resolution=\d+')
        matches = img_pattern.findall(html)
        seen = set()
        for m in matches:
            if m not in seen:
                seen.add(m)
                return f'https://item-shopping.c.yimg.jp/i/j/{m}?resolution=2x'
        return None
    except Exception:
        return None

def download_img(url, path):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://shopping.yahoo.co.jp/',
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read()
        with open(path, 'wb') as f:
            f.write(data)
        return len(data)
    except:
        return None

def main():
    products = load_products()
    total = len(products)
    print(f'Total products: {total}')

    progress = load_progress()
    start_idx = progress['idx'] if progress else 0
    saved = progress.get('saved', 0) if progress else 0
    failed = progress.get('failed', 0) if progress else 0

    if start_idx > 0:
        print(f'Resuming from index {start_idx} (saved: {saved}, failed: {failed})')

    SAVE_INTERVAL = 25

    for i in range(start_idx, total):
        p = products[i]
        jan = p['jan']
        maker = p.get('maker', '')
        name = p.get('name', '')
        img_path = os.path.join(IMG_DIR, f'{jan}.jpg')

        if os.path.exists(img_path) and os.path.getsize(img_path) > 5000:
            print(f'[{i+1}/{total}] ✓ {jan} (exists)')
            saved += 1
            save_progress(i + 1, total, saved, failed)
            continue

        img_url = search_yahoo_img(name, maker)
        if img_url:
            result = download_img(img_url, img_path)
            if result and result > 5000:
                print(f'[{i+1}/{total}] ✓ {jan} ({result}b) [{saved+1} saved]')
                saved += 1
                save_progress(i + 1, total, saved, failed)
                time.sleep(0.4)
                continue

        print(f'[{i+1}/{total}] ✗ {jan} no image')
        failed += 1
        save_progress(i + 1, total, saved, failed)

        if (i + 1) % SAVE_INTERVAL == 0:
            print(f'--- Progress: {i+1}/{total}, saved={saved}, failed={failed} ---')

        time.sleep(0.5)

    print(f'\nDone! {saved} saved, {failed} failed / {total} total')
    try:
        os.remove(PROGRESS_FILE)
    except:
        pass

if __name__ == '__main__':
    main()