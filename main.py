from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime
from inventory_manager import InventoryManager
from receipt_processor import ReceiptProcessor
from task_manager import TaskManager
from budget_tracker import BudgetTracker
from nlu_processor import process_natural_language_query

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
inventory = InventoryManager()
receipt_processor = ReceiptProcessor()
task_manager = TaskManager()
budget_tracker = BudgetTracker()

# Configure upload folder
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
@app.route("/api/trades", methods=["GET"])
def get_trades():
    try:
        trades = inventory.get_trades()
        return jsonify(trades)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search", methods=["GET"])
def search_items():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Search query is required"}), 400

    try:
        items = inventory.search_items(query)
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/items", methods=["GET"])
def get_items():
    try:
        items = inventory.get_items()
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/items", methods=["POST"])
def add_item():
    data = request.get_json()
    required_fields = ["name"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        item_id = inventory.add_item(
            name=data["name"],
            description=data.get("description"),
            quantity=data.get("quantity", 1),
            acquisition_type=data.get("acquisition_type", "purchase"),
            source_details=data.get("source_details"),
            price=data.get("price"),
            purchase_date=data.get("purchase_date"),
            warranty_expiry=data.get("warranty_expiry"),
            location=data.get("location"),
            condition=data.get("condition", "new"),
            notes=data.get("notes"),
        )

        # If this is a trade, record the trade details
        if data.get("acquisition_type") == "trade" and data.get("traded_item"):
            inventory.add_trade(
                item_id=item_id,
                traded_item=data["traded_item"],
                traded_item_value=data.get("traded_item_value"),
                trade_partner=data.get("trade_partner"),
                notes=data.get("trade_notes"),
            )

        return jsonify({"message": "Item added successfully", "id": item_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/repairs", methods=["POST"])
def add_repair():
    data = request.get_json()
    required_fields = ["item_id", "description"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Add the repair record
        repair_id = task_manager.add_repair(
            item_id=data["item_id"],
            description=data["description"],
            repair_date=data.get("repair_date"),
            cost=data.get("cost"),
            next_due_date=data.get("next_due_date"),
            status=data.get("status", "scheduled"),
        )

        # If components are specified, add them
        if "components" in data and isinstance(data["components"], list):
            for component in data["components"]:
                task_manager.add_component(
                    repair_id=repair_id,
                    name=component["name"],
                    quantity=component.get("quantity", 1),
                    estimated_cost=component.get("estimated_cost"),
                    priority=component.get("priority", "medium"),
                    status=component.get("status", "needed"),
                )

        return (
            jsonify(
                {"message": "Repair record added successfully", "repair_id": repair_id}
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/repairs", methods=["GET"])
def get_repairs():
    try:
        repairs = task_manager.get_repairs()
        return jsonify(repairs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/budget", methods=["GET"])
def get_budget():
    try:
        budget = budget_tracker.get_budget()
        if not budget:
            return jsonify({"error": "Budget not set"}), 404

        # Get current period spending
        total_spent = budget_tracker.calculate_total_spent()
        available = budget_tracker.calculate_available_budget()

        return jsonify(
            {"budget": budget, "total_spent": total_spent, "available": available}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/budget", methods=["POST"])
def update_budget():
    data = request.get_json()
    if "amount" not in data:
        return jsonify({"error": "Amount is required"}), 400

    try:
        budget_tracker.update_budget(
            amount=data["amount"],
            period=data.get("period", "monthly"),
            notes=data.get("notes"),
        )
        return jsonify({"message": "Budget updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/components", methods=["POST"])
def add_component():
    data = request.get_json()
    required_fields = ["item_id", "name", "quantity_needed"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        task_manager.add_component(
            item_id=data["item_id"],
            name=data["name"],
            quantity_needed=data["quantity_needed"],
            estimated_cost=data.get("estimated_cost"),
            priority=data.get("priority", "medium"),
            status=data.get("status", "needed"),
        )
        return jsonify({"message": "Component added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/components", methods=["GET"])
def get_components():
    try:
        components = task_manager.get_components()
        return jsonify(components)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    query_text = data.get("query", "")
    if not query_text:
        return jsonify({"error": "No query provided"}), 400

    try:
        response = process_natural_language_query(query_text, get_db())
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        parsed_data = receipt_processor.parse_receipt(file_path)

        # Add items to inventory
        for item in parsed_data["items"]:
            inventory.add_item(
                name=item["name"],
                purchase_date=parsed_data["date"],
                price=item["price"],
                acquisition_type="purchase",
            )

        return (
            jsonify(
                {
                    "message": "Receipt processed and items added to inventory",
                    "data": parsed_data,
                }
            ),
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
