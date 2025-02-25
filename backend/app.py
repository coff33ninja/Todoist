#!/usr/bin/env python
"""
Flask backend for serving the NLU model and processing queries.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import sys
from datetime import datetime

# Ensure repository path is accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ai.nlu_processor import NLUProcessor
from ai.ocr_processor import ReceiptProcessor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize NLU processor
nlu_processor = NLUProcessor(model_path="ai_models/nlu_model.pkl")

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect("db/inventory.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/query", methods=["POST"])
def process_query():
    """Process natural language queries."""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Missing query in request"}), 400

        query = data["query"]
        result = nlu_processor.process_natural_language_query(query, get_db)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Get list of predefined categories."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"categories": categories})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/items", methods=["POST"])
def add_item():
    """Add a new item to the inventory."""
    try:
        data = request.get_json()
        required_fields = ["name", "quantity", "price", "location"]

        # Validate required fields
        if not all(field in data for field in required_fields):
            return (
                jsonify(
                    {
                        "error": f"Missing required fields. Please provide: {', '.join(required_fields)}"
                    }
                ),
                400,
            )

        # Validate data types
        try:
            quantity = int(data["quantity"])
            price = float(data["price"]) if not data.get("is_gift", False) else 0
            if quantity <= 0 or price < 0:
                raise ValueError
        except ValueError:
            return (
                jsonify(
                    {
                        "error": "Invalid quantity or price. Quantity must be positive integer, price must be non-negative number."
                    }
                ),
                400,
            )

        conn = get_db()
        cursor = conn.cursor()

        # Validate category if provided
        if data.get("category"):
            cursor.execute(
                "SELECT 1 FROM categories WHERE name = ?", (data["category"],)
            )
            if not cursor.fetchone():
                return jsonify({"error": f"Invalid category: {data['category']}"}), 400

        cursor.execute(
            """
        INSERT INTO items (
            name, quantity, price, location, description,
            category, tags, purchase_date, is_gift,
            storage_location, usage_location
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                quantity,
                price,
                data["location"],
                data.get("description", ""),
                data.get("category", ""),
                data.get("tags", ""),
                data.get("purchase_date", ""),
                data.get("is_gift", False),
                data.get("storage_location", ""),
                data.get("usage_location", ""),
            ),
        )

        item_id = cursor.lastrowid
        conn.commit()

        # Fetch the inserted item
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        item = dict(cursor.fetchone())

        conn.close()

        return jsonify({"message": "Item added successfully", "item": item})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item from the inventory."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM items WHERE id = ?", (item_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Item not found"}), 404

        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Item deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/locations", methods=["GET"])
def get_locations():
    """Get list of existing locations for autocomplete."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT location FROM items WHERE location IS NOT NULL')
        locations = [row[0] for row in cursor.fetchall()]
        conn.close()
        return jsonify({"locations": locations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

@app.route("/api/upload_receipt", methods=["POST"])
def upload_receipt():
    """Upload a receipt and extract text using OCR."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Save the file to the uploads directory
        uploads_dir = 'uploads'
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, file.filename)
        file.save(file_path)

        # Process the receipt
        receipt_processor = ReceiptProcessor()
        if file.filename.endswith('.txt'):
            # Read text file directly
            extracted_text = file.read().decode('utf-8')
        else:
            # Process using OCR
            extracted_text = receipt_processor.extract_text(file_path)

        if extracted_text is None:
            return jsonify({"error": "Failed to extract text from receipt"}), 500

        print(f"Extracted Text: {extracted_text}")  # Debug statement
        parsed_data = receipt_processor.parse_receipt(extracted_text)

        if parsed_data is None:
            return jsonify({"error": "Failed to parse receipt data"}), 500

        # Log the parsed data into the database
        conn = get_db()
        cursor = conn.cursor()

        # Insert store name and date into the purchases table
        cursor.execute(
            """
            INSERT INTO purchases (store_name, purchase_date, total)
            VALUES (?, ?, ?)
            """,
            (parsed_data["store_name"], parsed_data["date"], parsed_data["total"]),
        )
        purchase_id = cursor.lastrowid

        # Insert items into the purchase_items table
        for item in parsed_data["items"]:
            cursor.execute(
                """
                INSERT INTO purchase_items (purchase_id, description, quantity, price, acquisition_type)
                VALUES (?, ?, ?, ?, ?)
                """,
                (purchase_id, item["description"], item["quantity"], item["price"], item["acquisition_type"]),
            )

        conn.commit()
        conn.close()

        return jsonify({"message": "Receipt processed successfully", "parsed_data": parsed_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
            
if __name__ == "__main__":
            app.run(debug=True, port=5000)
