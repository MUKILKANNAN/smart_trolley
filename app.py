from flask import Flask, render_template, request, jsonify, send_file
from fpdf import FPDF
import barcode
from barcode.writer import ImageWriter
import os
import ollama

app = Flask(__name__)

# 1. Product Database
products_db = {
    "1001": {"name": "Dairy Milk", "price": 40},
    "1002": {"name": "Coca Cola", "price": 50},
    "1003": {"name": "Maggi Noodles", "price": 20},
    "1004": {"name": "Lay's Chips", "price": 10}
}

cart = {}

def create_barcodes():
    path = 'static/barcodes'
    if not os.path.exists(path): os.makedirs(path)
    for code in products_db:
        BAR = barcode.get_barcode_class('code128')
        img_bar = BAR(code, writer=ImageWriter())
        img_bar.save(f"{path}/{code}")

create_barcodes()

@app.route('/')
def index():
    global cart
    cart = {} 
    return render_template('index.html', products=products_db)

@app.route('/payment_page')
def payment_page():
    total = sum(item['price'] * item['qty'] for item in cart.values())
    return render_template('payment.html', total=total)

# tinydolphin base panna Smart Search Prediction
@app.route('/ai_search', methods=['POST'])
def ai_search():
    text = request.json.get('text').lower()
    product_names = [v['name'] for v in products_db.values()]
    
    # Flipkart Logic: Direct starting letter match first
    quick_match = [name for name in product_names if name.lower().startswith(text)]
    if quick_match:
        return jsonify({"suggestion": quick_match[0]})

    # AI Prediction using tinydolphin
    prompt = f"Product list: {', '.join(product_names)}. User is typing: '{text}'. Predict the correct product. Output ONLY the name."
    try:
        response = ollama.generate(model='tinydolphin', prompt=prompt)
        prediction = response['response'].strip()
        for name in product_names:
            if name.lower() in prediction.lower():
                return jsonify({"suggestion": name})
    except:
        pass
    return jsonify({"suggestion": ""})

@app.route('/add_item', methods=['POST'])
def add_item():
    code = request.json.get('code')
    found_code = None
    for k, v in products_db.items():
        if k == code or v['name'].lower() == code.lower():
            found_code = k
            break
            
    if found_code:
        if found_code in cart:
            cart[found_code]['qty'] += 1
        else:
            cart[found_code] = {"name": products_db[found_code]['name'], "price": products_db[found_code]['price'], "qty": 1}
        return jsonify({"success": True, "cart": cart, "total": sum(item['price'] * item['qty'] for item in cart.values())})
    return jsonify({"success": False})

@app.route('/update_qty', methods=['POST'])
def update_qty():
    code, action = request.json.get('code'), request.json.get('action')
    if code in cart:
        if action == 'plus': cart[code]['qty'] += 1
        elif action == 'minus':
            cart[code]['qty'] -= 1
            if cart[code]['qty'] <= 0: del cart[code]
    return jsonify({"success": True, "cart": cart, "total": sum(item['price'] * item['qty'] for item in cart.values())})

@app.route('/pay', methods=['POST'])
def pay():
    data = request.json
    if (data.get('num') == "43215678" and data.get('pin') == "1122") or \
       (data.get('upi') == "user@okbank") or (data.get('bank') == "admin123"):
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/get_bill')
def get_bill():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18); pdf.cell(200, 10, txt="SMART TROLLEY RECEIPT", ln=True, align='C')
    pdf.set_font("Arial", size=12); pdf.ln(10)
    total = 0
    for code, item in cart.items():
        line_total = item['price'] * item['qty']
        pdf.cell(80, 10, txt=f"{item['name']} (x{item['qty']})")
        pdf.cell(110, 10, txt=f"Rs.{line_total}", ln=True, align='R')
        total += line_total
    pdf.ln(5); pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, txt=f"GRAND TOTAL: Rs.{total}", ln=True, align='R')
    pdf.output("invoice.pdf")
    return send_file("invoice.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)