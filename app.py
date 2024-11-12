import uuid
from flask import Flask, request, jsonify
from datetime import datetime
import math
import re

app = Flask(__name__)

# In-memory store for receipts
receipts = {}

# Utility function to validate receipt input using regex
def validate_receipt(receipt):
    # Validate retailer name
    if not re.match(r'^[\w\s\-\&]+$', receipt['retailer']):
        return False, "Invalid retailer name format."
    
    # Validate purchase date (YYYY-MM-DD format)
    try:
        datetime.strptime(receipt['purchaseDate'], "%Y-%m-%d")
    except ValueError:
        return False, "Invalid purchase date format."
    
    # Validate purchase time (24-hour format HH:MM)
    try:
        datetime.strptime(receipt['purchaseTime'], "%H:%M")
    except ValueError:
        return False, "Invalid purchase time format."
    
    # Validate total amount (must be in the format XX.XX)
    if not re.match(r'^\d+\.\d{2}$', receipt['total']):
        return False, "Invalid total format."
    
    # Validate items
    for item in receipt['items']:
        # Validate item description
        if not re.match(r'^[\w\s\-]+$', item['shortDescription']):
            return False, f"Invalid item description: {item['shortDescription']}"
        
        # Validate item price
        if not re.match(r'^\d+\.\d{2}$', item['price']):
            return False, f"Invalid item price: {item['price']}"
    
    return True, ""

# Utility function to calculate points
def calculate_points(receipt):
    points = 0

    # Rule 1: Points for retailer name length
    points += len([char for char in receipt['retailer'] if char.isalnum()])

    # Rule 2: Points for round dollar amount
    if float(receipt['total']).is_integer():
        points += 50

    # Rule 3: Points for total being a multiple of 0.25
    if float(receipt['total']) % 0.25 == 0:
        points += 25

    # Rule 4: Points for number of items (every two items = 5 points)
    points += (len(receipt['items']) // 2) * 5

    # Rule 5: Item description length and price calculation
    for item in receipt['items']:
        if len(item['shortDescription'].strip()) % 3 == 0:
            price = math.ceil(float(item['price']) * 0.2)
            points += price

    # Rule 6: Points for odd day of purchase date
    purchase_day = int(receipt['purchaseDate'].split('-')[2])
    if purchase_day % 2 != 0:
        points += 6

    # Rule 7: Points for purchase time between 2:00 PM and 4:00 PM
    purchase_time = datetime.strptime(receipt['purchaseTime'], '%H:%M')
    if datetime.strptime('14:00', '%H:%M') <= purchase_time < datetime.strptime('16:00', '%H:%M'):
        points += 10

    return points

# Endpoint: Process Receipts
@app.route('/receipts/process', methods=['POST'])
def process_receipt():
    data = request.get_json()
    
    # Validate receipt data
    is_valid, error_message = validate_receipt(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400
    
    # Generate unique ID for the receipt
    receipt_id = str(uuid.uuid4())
    
    # Save the receipt in memory
    receipts[receipt_id] = data
    
    return jsonify({"id": receipt_id}), 200

# Endpoint: Get Points
@app.route('/receipts/<receipt_id>/points', methods=['GET'])
def get_points(receipt_id):
    if receipt_id not in receipts:
        return jsonify({"error": "No receipt found for that id"}), 404

    receipt = receipts[receipt_id]
    points = calculate_points(receipt)
    
    return jsonify({"points": points}), 200

if __name__ == '__main__':
    app.run(debug=True)
