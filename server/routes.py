from flask import request, jsonify
from server import app

from system.food_manager import add_orders

@app.route('/query', methods=['POST'])
def pquery():

    orders = request.json.get('orders')

    return jsonify(add_orders(orders))
