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

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize NLU processor
nlu_processor = NLUProcessor(model_path="ai_models/nlu_model.pkl")

# Ensure the uploads directory exists
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(uploads_dir, exist_ok=True)

# Ensure the db directory exists
db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
os.makedirs(db_dir, exist_ok=True)

def get_db():
    """Get database connection with row factory."""
    db_path = os.path.join(db_dir, 'inventory.db')
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
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

@app.route('/api/upload_receipt', methods=['POST'])
def upload_receipt():
    try:
        print("Received upload_receipt request")
        if 'file' not in request.files:
            print("No file part in request")
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("No selected file")
            return jsonify({"error": "No selected file"}), 400

        # Create a timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get the file extension
        _, ext = os.path.splitext(file.filename)
        
        # Create a new filename with timestamp
        new_filename = f"receipt_{timestamp}{ext}"
        
        # Save the file to uploads directory
        upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', new_filename)
        print(f"Saving file to: {upload_path}")
        file.save(upload_path)

        # Read the file content
        with open(upload_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File content:\n{content}")

        # Initialize receipt processor
        receipt_processor = ReceiptProcessor()
        
        # Process the receipt
        result = receipt_processor.parse_receipt(content)
        print(f"Parsing result: {result}")
        
        if result is None:
            return jsonify({"error": "Failed to parse receipt data"}), 400

        # Add file path to result
        result["file_path"] = new_filename

        return jsonify(result)

    except Exception as e:
        print(f"Error processing receipt: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
            app.run(debug=True, port=5000)
