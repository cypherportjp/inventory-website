"""
Flask app for ミニ四駆・ミニカー・バイク 在庫注文システム.
"""
import os, json, csv, uuid, io
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file, send_from_directory

app = Flask(__name__)
app.secret_key = 'miniq-inventory-secret-2026'
app.config['JSON_AS_ASCII'] = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ORDERS_FILE = os.path.join(DATA_DIR, 'orders.json')
ADMIN_PASSWORD = 'toyohaya'  # change this for production
TAX_RATE = 0.10  # 消費税 10%

# 掛率設定（maker: rate 0.0-1.0）例: 68% なら 0.68
DISCOUNT_RATES = {
    'ﾀﾐﾔ': 0.68,
}

def load_products():
    with open(os.path.join(DATA_DIR, 'products.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

carts = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/products')
def get_products():
    products = load_products()
    for p in products:
        rate = DISCOUNT_RATES.get(p.get('maker', ''), 1.0)
        p['discount_rate'] = rate  # 0.0-1.0
        p['list_price'] = p['price']  # 定価
        p['price'] = round(p['price'] * rate)  # 下代
    return jsonify(products)

@app.route('/api/session/new', methods=['POST'])
def new_session():
    sid = str(uuid.uuid4())[:8]
    carts[sid] = []
    return jsonify({'session_id': sid})

@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = request.json
    sid = data.get('session_id')
    product = data.get('product')
    qty = int(data.get('qty', 1))
    if not sid or sid not in carts:
        return jsonify({'error': 'Invalid session'}), 400
    cart = carts[sid]
    for item in cart:
        if item['jan'] == product['jan']:
            item['qty'] += qty
            return jsonify(cart)
    cart.append({
        'jan': product['jan'],
        'name': product['name'],
        'maker': product['maker'],
        'list_price': product.get('list_price', product['price']),
        'discount_rate': product.get('discount_rate', 1.0),
        'price': product['price'],
        'qty': qty,
        'code': product.get('code', ''),
        'image_url': product.get('image_url') or '',
    })
    return jsonify(cart)

@app.route('/api/cart', methods=['GET'])
def cart_get():
    sid = request.args.get('session_id')
    return jsonify(carts.get(sid, []))

@app.route('/api/cart/clear', methods=['POST'])
def cart_clear():
    data = request.json
    sid = data.get('session_id')
    if sid and sid in carts:
        carts[sid] = []
    return jsonify({'ok': True})

@app.route('/api/order/complete', methods=['POST'])
def order_complete():
    """Submit order: save to orders.json and return order ID."""
    data = request.json
    sid = data.get('session_id')
    client_name = data.get('client_name', '').strip() or 'ゲスト'
    if not sid or sid not in carts or not carts[sid]:
        return jsonify({'error': 'Empty cart'}), 400

    products = load_products()
    jan_map = {p['jan']: p for p in products}

    order = {
        'id': str(uuid.uuid4())[:8].upper(),
        'session_id': sid,
        'client_name': client_name,
        'submitted_at': datetime.now().isoformat(sep=' ', timespec='seconds'),
        'items': [],
        'subtotal': 0,
        'tax': 0,
        'total': 0,
    }

    subtotal = 0
    for item in carts[sid]:
        sub = item['price'] * item['qty']
        subtotal += sub
        order['items'].append({
            'jan': item['jan'],
            'maker': item['maker'],
            'code': item.get('code', ''),
            'name': item['name'],
            'list_price': item.get('list_price', item['price']),
            'discount_rate': item.get('discount_rate', 1.0),
            'price': item['price'],
            'qty': item['qty'],
            'subtotal': sub,
        })
    order['subtotal'] = subtotal
    order['tax'] = round(subtotal * TAX_RATE)
    order['total'] = subtotal + order['tax']

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    # Clear the cart
    carts[sid] = []

    return jsonify({'order_id': order['id'], 'order': order})

@app.route('/api/order/by-session', methods=['GET'])
def orders_by_session():
    """Get all orders for a session ID (via cookie)."""
    sid = request.args.get('session_id', '')
    orders = load_orders()
    session_orders = [o for o in orders if o['session_id'] == sid]
    return jsonify(session_orders)

@app.route('/api/admin/orders')
def admin_get_orders():
    """Get all orders (password protected via query param)."""
    pw = request.args.get('password', '')
    if pw != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(load_orders())

@app.route('/api/admin/export/<order_id>')
def admin_export_order(order_id):
    """Export a specific order as CSV."""
    pw = request.args.get('password', '')
    if pw != ADMIN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    orders = load_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(['JANコード', 'メーカー', '品番', '商品名', '定価', '掛率', '下代', '注文数', '単位', '小計'])
    for item in order['items']:
        rate_pct = f"{item.get('discount_rate', 1.0)*100:.0f}%"
        w.writerow([
            item['jan'],
            item['maker'],
            item['code'],
            item['name'],
            item.get('list_price', item['price']),
            rate_pct,
            item['price'],
            item['qty'],
            '個',
            item['subtotal'],
        ])
    w.writerow([])
    w.writerow(['合計', '', '', '', '', '', '', '', '', order['subtotal']])
    w.writerow(['消費税(10%)', '', '', '', '', '', '', '', '', order['tax']])
    w.writerow(['総計', '', '', '', '', '', '', '', '', order['total']])
    output.seek(0)
    fname = f"order_{order_id}_{order['submitted_at'][:10].replace('-','')}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=fname
    )

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(DATA_DIR, 'images/' + filename)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)