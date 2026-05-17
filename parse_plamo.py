import openpyxl, json, os, urllib.request, ssl

# Parse Excel
path = '/Users/housemouse/inventory-website/プラモデル・鉄道模型在庫リスト260416 (2).xlsx'
wb = openpyxl.load_workbook(path, data_only=True)
ws = wb['在庫リスト']

products = []
for i, row in enumerate(ws.iter_rows(min_row=3, values_only=True)):
    maker = row[0]
    price = row[1]
    jan = str(row[2]) if row[2] else ''
    name = row[3]
    stock = row[4]
    unit = row[6]
    if not name:
        continue
    products.append({
        'id': i-2,
        'maker': str(maker) if maker else '',
        'price': int(price) if price else 0,
        'jan': jan,
        'name': str(name),
        'stock': str(stock) if stock else '',
        'unit': str(unit) if unit else '個',
    })

print(f'Total: {len(products)} products')
with open('./data/products.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
print('Saved data/products.json')

# First 10 for image test
with open('./data/products_first10.json', 'w', encoding='utf-8') as f:
    json.dump(products[:10], f, ensure_ascii=False, indent=2)
print('Saved first 10 for image test')