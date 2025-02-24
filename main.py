from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from ocr_processor import ReceiptProcessor
from nlu_processor import process_natural_language_query

# Configure upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
CORS(app)

# Database setup
DATABASE = "inventory.db"


def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = dict_factory
    return conn


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER DEFAULT 1,
                purchase_date TEXT,
                price REAL,
                warranty_expiry TEXT,
                acquisition_type TEXT CHECK(acquisition_type IN ('purchase', 'trade', 'gift')),
                location TEXT,
                condition TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                transaction_type TEXT CHECK(transaction_type IN ('purchase', 'trade', 'gift')),
                amount REAL,
                source TEXT,
                date TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                repair_date TEXT,
                description TEXT,
                cost REAL,
                next_due_date TEXT,
                status TEXT CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY,
                amount REAL,
                period TEXT,  -- 'monthly', 'yearly', etc.
                last_updated TEXT,
                notes TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                name TEXT NOT NULL,
                quantity_needed INTEGER,
                estimated_cost REAL,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
                status TEXT CHECK(status IN ('needed', 'ordered', 'received')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES items(id)
            )
        """
        )
        conn.commit()


# API Routes


@app.route("/api/items", methods=["GET"])
def get_items():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
        items = cursor.fetchall()
        return jsonify(items)


@app.route("/api/items", methods=["POST"])
def add_item():
    data = request.get_json()
    required_fields = ["name", "quantity"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO items (
                name, description, quantity, purchase_date, price,
                warranty_expiry, acquisition_type, location, condition, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                data["name"],
                data.get("description"),
                data["quantity"],
                data.get("purchase_date"),
                data.get("price"),
                data.get("warranty_expiry"),
                data.get("acquisition_type", "purchase"),
                data.get("location"),
                data.get("condition"),
                data.get("notes"),
            ),
        )
        item_id = cursor.lastrowid

        # Add transaction record if it's a purchase
        if data.get("price") is not None:
            cursor.execute(
                """
                INSERT INTO transactions (
                    item_id, transaction_type, amount, source, date, details
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    item_id,
                    data.get("acquisition_type", "purchase"),
                    data.get("price"),
                    data.get("source"),
                    data.get("purchase_date", datetime.now().strftime("%Y-%m-%d")),
                    data.get("notes"),
                ),
            )
        conn.commit()
        return jsonify({"message": "Item added successfully", "id": item_id}), 201


@app.route("/api/repairs", methods=["POST"])
def add_repair():
    data = request.get_json()
    required_fields = ["item_id", "repair_date", "description"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO repairs (
                item_id, repair_date, description, cost,
                next_due_date, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                data["item_id"],
                data["repair_date"],
                data["description"],
                data.get("cost"),
                data.get("next_due_date"),
                data.get("status", "scheduled"),
            ),
        )
        conn.commit()
        return jsonify({"message": "Repair record added successfully"}), 201


@app.route("/api/repairs", methods=["GET"])
def get_repairs():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT r.*, i.name as item_name 
            FROM repairs r 
            JOIN items i ON r.item_id = i.id 
            ORDER BY repair_date DESC
        """
        )
        repairs = cursor.fetchall()
        return jsonify(repairs)


@app.route("/api/budget", methods=["GET"])
def get_budget():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget WHERE id=1")
        budget = cursor.fetchone()
        if not budget:
            return jsonify({"error": "Budget not set"}), 404
        return jsonify(budget)


@app.route("/api/budget", methods=["POST"])
def update_budget():
    data = request.get_json()
    if "amount" not in data:
        return jsonify({"error": "Amount is required"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO budget (
                id, amount, period, last_updated, notes
            )
            VALUES (1, ?, ?, CURRENT_TIMESTAMP, ?)
        """,
            (data["amount"], data.get("period", "monthly"), data.get("notes")),
        )
        conn.commit()
        return jsonify({"message": "Budget updated successfully"}), 200


@app.route("/api/components", methods=["POST"])
def add_component():
    data = request.get_json()
    required_fields = ["item_id", "name", "quantity_needed"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO components (
                item_id, name, quantity_needed, estimated_cost,
                priority, status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                data["item_id"],
                data["name"],
                data["quantity_needed"],
                data.get("estimated_cost"),
                data.get("priority", "medium"),
                data.get("status", "needed"),
            ),
        )
        conn.commit()
        return jsonify({"message": "Component added successfully"}), 201


@app.route("/api/components", methods=["GET"])
def get_components():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, i.name as item_name 
            FROM components c 
            JOIN items i ON c.item_id = i.id 
            ORDER BY priority DESC, created_at DESC
        """
        )
        components = cursor.fetchall()
        return jsonify(components)


@app.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    query_text = data.get("query", "")
    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    response = process_natural_language_query(query_text, get_db())
    return jsonify({"response": response})


@app.route("/api/receipts/upload", methods=["POST"])
def upload_receipt():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Process the receipt
        processor = ReceiptProcessor()
        extracted_text = processor.extract_text(file_path)
        if not extracted_text:
            return jsonify({"error": "Failed to process receipt"}), 500

        parsed_data = processor.parse_receipt(extracted_text)
        if not parsed_data:
            return jsonify({"error": "Failed to parse receipt"}), 500

        return (
            jsonify({"message": "Receipt processed successfully", "data": parsed_data}),
            200,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/receipts/<filename>", methods=["GET"])
def get_receipt(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
