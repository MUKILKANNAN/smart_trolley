from flask import Flask, render_template, request, jsonify, send_file, session
from fpdf import FPDF
import barcode
from barcode.writer import ImageWriter
import os
import ollama

app = Flask(__name__)
app.secret_key = 'smart_trolley_secret'

# 1. Product Database
products_db = {
    "1001": {"name": "Dairy Milk", "price": 40, "category": "chocolate"},
    "1002": {"name": "Coca Cola", "price": 50, "category": "soda"},
    "1003": {"name": "Maggi Noodles", "price": 20, "category": "noodles"},
    "1004": {"name": "Lay's Chips", "price": 10, "category": "snacks"}
}

# 2. Barcode to CSV item mapping
barcode_to_csv_item = {
    "1001": "chocolate",
    "1002": "soda",
    "1003": "whole milk",
    "1004": "butter"
}

cart = {}

# 3. Create barcodes
def create_barcodes():
    path = 'static/barcodes'
    if not os.path.exists(path): 
        os.makedirs(path)
    for code in products_db:
        BAR = barcode.get_barcode_class('code128')
        img_bar = BAR(code, writer=ImageWriter())
        img_bar.save(f"{path}/{code}")

create_barcodes()

# 4. Routes

@app.route('/')
def index():
    global cart
    
    # Check if coming from payment success reset
    if request.args.get('reset') == 'true':
        cart = {}  # Clear the cart
    
    return render_template('index.html', products=products_db)

@app.route('/payment_page')
def payment_page():
    total = sum(item['price'] * item['qty'] for item in cart.values())
    return render_template('payment.html', total=total)



# 5. Barcode Scanning
@app.route('/scan_barcode', methods=['POST'])
def scan_barcode():
    code = request.json.get('code')
    
    if code not in products_db:
        return jsonify({"success": False})
    
    # Add to cart
    if code in cart:
        cart[code]['qty'] += 1
    else:
        cart[code] = {
            "name": products_db[code]['name'],
            "price": products_db[code]['price'],
            "qty": 1
        }
    
    # Get recommendations
    csv_item = barcode_to_csv_item.get(code, "")
    recommendations = get_recommendations(csv_item)
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    
    return jsonify({
        "success": True,
        "product": products_db[code]['name'],
        "cart": cart,
        "total": total,
        "recommendations": recommendations
    })

# 6. Get recommendations from groceries.csv
def get_recommendations(item_name):
    """Get recommendations based on groceries.csv patterns"""
    item_name = item_name.lower()
    
    # Simple recommendation logic based on product categories
    recommendations = []
    
    # Map items to categories and recommend similar
    item_categories = {
        "chocolate": ["Dairy Milk - ₹40", "Coca Cola - ₹50"],
        "soda": ["Coca Cola - ₹50", "Lay's Chips - ₹10"],
        "whole milk": ["Dairy Milk - ₹40", "Maggi Noodles - ₹20"],
        "butter": ["Lay's Chips - ₹10", "Dairy Milk - ₹40"],
        "milk": ["Dairy Milk - ₹40", "Maggi Noodles - ₹20"],
        "noodles": ["Maggi Noodles - ₹20", "Lay's Chips - ₹10"],
        "chips": ["Lay's Chips - ₹10", "Coca Cola - ₹50"]
    }
    
    # Check for matches
    for key in item_categories:
        if key in item_name:
            recommendations = item_categories[key]
            break
    
    # Fallback: recommend all other products
    if not recommendations:
        current_product = None
        for product in products_db.values():
            if item_name in product['name'].lower():
                current_product = product
                break
        
        if current_product:
            for code, product in products_db.items():
                if product['name'] != current_product['name']:
                    recommendations.append(f"{product['name']} - ₹{product['price']}")
    
    return recommendations[:3]  # Return top 3 recommendations

# 7. Ollama Next-Word Prediction (SIMPLIFIED VERSION)
@app.route('/ollama_predict', methods=['POST'])
def ollama_predict():
    """Simple Ollama prediction - No external CSV dependency"""
    try:
        data = request.json
        text = data.get('text', '').strip().lower()
        
        if len(text) < 1:
            return jsonify({"prediction": ""})
        
        # Product list for matching
        product_names = [p['name'] for p in products_db.values()]
        
        # First: Direct letter matching (most reliable)
        for product_name in product_names:
            if product_name.lower().startswith(text):
                return jsonify({"prediction": product_name})
        
        # Second: Partial word matching
        for product_name in product_names:
            for word in product_name.lower().split():
                if text in word:
                    return jsonify({"prediction": product_name})
        
        # Third: Try Ollama if available
        try:
            prompt = f"Products: {', '.join(product_names)}. User typed: '{text}'. What product are they trying to type? Return ONLY the product name."
            response = ollama.generate(model='tinydolphin', prompt=prompt)
            prediction = response['response'].strip()
            
            # Validate prediction matches a real product
            for product_name in product_names:
                if product_name.lower() in prediction.lower():
                    return jsonify({"prediction": product_name})
        except:
            pass  # Ollama not available or failed
        
        return jsonify({"prediction": ""})
        
    except Exception as e:
        print(f"Ollama predict error: {e}")
        return jsonify({"prediction": ""})

# 8. AI Search (existing - keep for compatibility)
@app.route('/ai_search', methods=['POST'])
def ai_search():
    text = request.json.get('text').lower()
    product_names = [v['name'] for v in products_db.values()]
    
    # Direct match
    quick_match = [name for name in product_names if name.lower().startswith(text)]
    if quick_match:
        return jsonify({"suggestion": quick_match[0]})

    # AI Prediction
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

# 9. Manual item addition
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
            cart[found_code] = {
                "name": products_db[found_code]['name'],
                "price": products_db[found_code]['price'],
                "qty": 1
            }
        
        # Get recommendations
        csv_item = barcode_to_csv_item.get(found_code, "")
        recommendations = get_recommendations(csv_item)
        
        total = sum(item['price'] * item['qty'] for item in cart.values())
        
        return jsonify({
            "success": True, 
            "cart": cart, 
            "total": total,
            "recommendations": recommendations
        })
    return jsonify({"success": False})

# 10. Update quantity
@app.route('/update_qty', methods=['POST'])
def update_qty():
    code = request.json.get('code')
    action = request.json.get('action')
    
    if code in cart:
        if action == 'plus':
            cart[code]['qty'] += 1
        elif action == 'minus':
            cart[code]['qty'] -= 1
            if cart[code]['qty'] <= 0:
                del cart[code]
    
    total = sum(item['price'] * item['qty'] for item in cart.values())
    return jsonify({
        "success": True, 
        "cart": cart, 
        "total": total
    })

# 11. Get cart
@app.route('/get_cart', methods=['GET'])
def get_cart():
    total = sum(item['price'] * item['qty'] for item in cart.values())
    return jsonify({
        "success": True,
        "cart": cart,
        "total": total
    })

# 12. Payment
@app.route('/pay', methods=['POST'])
def pay():
    data = request.json
    if (data.get('num') == "43215678" and data.get('pin') == "1122") or \
       (data.get('upi') == "user@okbank") or (data.get('bank') == "admin123"):
        return jsonify({"success": True})
    return jsonify({"success": False})

# 13. Bill generation
@app.route('/get_bill')
def get_bill():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 10, txt="SMART TROLLEY RECEIPT", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    
    total = 0
    for code, item in cart.items():
        line_total = item['price'] * item['qty']
        pdf.cell(80, 10, txt=f"{item['name']} (x{item['qty']})")
        pdf.cell(110, 10, txt=f"₹{line_total}", ln=True, align='R')
        total += line_total
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt=f"GRAND TOTAL: ₹{total}", ln=True, align='R')
    
    pdf.output("invoice.pdf")
    return send_file("invoice.pdf", as_attachment=True)

# if __name__ == '__main__':
#     app.run(debug=True)


# Change this:
# app.run(debug=True)

# To this (host='0.0.0.0' allows other devices to connect):
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)