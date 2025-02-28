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

@app.route("/api/received_item", methods=["POST"])
def handle_received_item():
    """Handle conversations about items (received, bought, found, etc.)."""
    try:
        data = request.get_json()
        if not data or "statement" not in data:
            return jsonify({"error": "Missing statement in request"}), 400

        statement = data["statement"].lower()
        
        # Analyze the statement to determine the type of transaction
        acquisition_patterns = {
            "got": "received",
            "received": "received",
            "gave me": "received",
            "given": "received",
            "bought": "purchased",
            "purchased": "purchased",
            "found": "found",
            "borrowed": "borrowed",
            "rented": "rented",
            "inherited": "inherited",
            "traded": "traded",
            "made": "made",
            "won": "won",
            "gave away": "disposed",
            "donated": "disposed",
            "threw away": "disposed",
            "lost": "lost"
        }

        transaction_type = None
        for pattern, type_ in acquisition_patterns.items():
            if pattern in statement:
                transaction_type = type_
                break

        if not transaction_type:
            return jsonify({
                "error": "Could not understand the type of transaction",
                "valid_formats": [
                    "I just got/received a [item]",
                    "I bought/purchased a [item]",
                    "I found a [item]",
                    "I borrowed/rented a [item]",
                    "I inherited/traded/made/won a [item]",
                    "I gave away/donated/lost a [item]"
                ]
            }), 400

        # Extract item name
        item_name = None
        for pattern in acquisition_patterns.keys():
            if pattern in statement:
                parts = statement.split(pattern)
                if len(parts) > 1:
                    item_name = parts[1].strip().strip('a').strip()
                    break

        if not item_name:
            return jsonify({"error": "Could not identify the item name"}), 400

        # Initialize conversation flow based on transaction type
        conversation_flow = {
            "received": [
                "from_whom",
                "condition",
                "value",
                "location",
                "usage",
                "maintenance",
                "notes"
            ],
            "purchased": [
                "where_purchased",
                "price",
                "warranty",
                "condition",
                "location",
                "usage",
                "maintenance",
                "notes"
            ],
            "found": [
                "where_found",
                "condition",
                "ownership_verification",
                "location",
                "notes"
            ],
            "borrowed": [
                "from_whom",
                "duration",
                "condition",
                "location",
                "return_date",
                "notes"
            ],
            "rented": [
                "from_where",
                "cost",
                "duration",
                "condition",
                "location",
                "return_date",
                "notes"
            ],
            "inherited": [
                "from_whom",
                "condition",
                "value",
                "documentation",
                "location",
                "notes"
            ],
            "traded": [
                "with_whom",
                "traded_for",
                "condition",
                "value",
                "location",
                "notes"
            ],
            "made": [
                "materials_used",
                "cost",
                "time_spent",
                "location",
                "notes"
            ],
            "won": [
                "where_won",
                "contest_details",
                "value",
                "condition",
                "location",
                "notes"
            ],
            "disposed": [
                "disposal_method",
                "reason",
                "to_whom",
                "value",
                "condition",
                "notes"
            ],
            "lost": [
                "last_seen",
                "circumstances",
                "value",
                "condition",
                "notes"
            ]
        }

        # Get the question flow for this transaction type
        questions = conversation_flow.get(transaction_type, [])
        
        # Question templates
        question_templates = {
            "from_whom": "Who gave you the {}?",
            "where_purchased": "Where did you purchase the {}?",
            "price": "How much did the {} cost?",
            "warranty": "Does the {} come with a warranty? (yes/no)",
            "condition": "What condition is the {} in? (new/like new/very good/good/fair/poor/broken)",
            "value": "What's the approximate value of the {}?",
            "location": "Where are you storing the {}?",
            "usage": "Where will you primarily use the {}?",
            "maintenance": "Does the {} require any regular maintenance? (yes/no)",
            "where_found": "Where did you find the {}?",
            "ownership_verification": "Have you verified if the {} belongs to someone? (yes/no)",
            "duration": "How long will you have the {}?",
            "return_date": "When do you need to return the {}?",
            "from_where": "Where did you rent the {} from?",
            "cost": "How much are you paying for the {}?",
            "documentation": "Do you have any documentation for the {}? (yes/no)",
            "with_whom": "Who did you trade with to get the {}?",
            "traded_for": "What did you trade to get the {}?",
            "materials_used": "What materials did you use to make the {}?",
            "time_spent": "How long did it take to make the {}?",
            "where_won": "Where did you win the {}?",
            "contest_details": "What contest or event did you win the {} in?",
            "disposal_method": "How did you dispose of the {}?",
            "reason": "Why did you dispose of the {}?",
            "to_whom": "Who did you give the {} to?",
            "last_seen": "When did you last see the {}?",
            "circumstances": "What were the circumstances when you lost the {}?",
            "notes": "Any additional notes about the {}?"
        }

        return jsonify({
            "status": "success",
            "next_question": question_templates[questions[0]].format(item_name),
            "conversation_state": {
                "item_name": item_name,
                "transaction_type": transaction_type,
                "questions": questions,
                "current_question_index": 0,
                "answers": {}
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/received_item/continue", methods=["POST"])
def continue_received_item_conversation():
    """Continue the conversation about an item."""
    try:
        data = request.get_json()
        if not data or "conversation_state" not in data or "answer" not in data:
            return jsonify({"error": "Missing required data"}), 400

        state = data["conversation_state"]
        answer = data["answer"]
        
        # Store the answer
        current_question = state["questions"][state["current_question_index"]]
        state["answers"][current_question] = answer
        
        # Move to next question
        state["current_question_index"] += 1
        
        # Check if we have more questions
        if state["current_question_index"] < len(state["questions"]):
            # Get next question
            next_question = state["questions"][state["current_question_index"]]
            question_templates = {
                "from_whom": "Who gave you the {}?",
                "where_purchased": "Where did you purchase the {}?",
                "price": "How much did the {} cost?",
                "warranty": "Does the {} come with a warranty? (yes/no)",
                "condition": "What condition is the {} in? (new/like new/very good/good/fair/poor/broken)",
                "value": "What's the approximate value of the {}?",
                "location": "Where are you storing the {}?",
                "usage": "Where will you primarily use the {}?",
                "maintenance": "Does the {} require any regular maintenance? (yes/no)",
                "where_found": "Where did you find the {}?",
                "ownership_verification": "Have you verified if the {} belongs to someone? (yes/no)",
                "duration": "How long will you have the {}?",
                "return_date": "When do you need to return the {}?",
                "from_where": "Where did you rent the {} from?",
                "cost": "How much are you paying for the {}?",
                "documentation": "Do you have any documentation for the {}? (yes/no)",
                "with_whom": "Who did you trade with to get the {}?",
                "traded_for": "What did you trade to get the {}?",
                "materials_used": "What materials did you use to make the {}?",
                "time_spent": "How long did it take to make the {}?",
                "where_won": "Where did you win the {}?",
                "contest_details": "What contest or event did you win the {} in?",
                "disposal_method": "How did you dispose of the {}?",
                "reason": "Why did you dispose of the {}?",
                "to_whom": "Who did you give the {} to?",
                "last_seen": "When did you last see the {}?",
                "circumstances": "What were the circumstances when you lost the {}?",
                "notes": "Any additional notes about the {}?"
            }
            return jsonify({
                "status": "success",
                "next_question": question_templates[next_question].format(state["item_name"]),
                "conversation_state": state
            })
        
        # No more questions, save to database
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Begin transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Handle different transaction types
            if state["transaction_type"] in ["received", "purchased", "found", "borrowed", "rented", "inherited", "traded", "made", "won"]:
                # Add item to inventory
                cursor.execute('''
                    INSERT INTO items (
                        name, quantity, price, location, condition,
                        acquisition_type, acquisition_date, storage_location,
                        usage_location, notes, warranty_info
                    ) VALUES (?, 1, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
                ''', (
                    state["item_name"],
                    float(state["answers"].get("price", 0)) if state["answers"].get("price", "0").replace(".", "").isdigit() else 0,
                    state["answers"]["location"],
                    state["answers"].get("condition", "Unknown"),
                    state["transaction_type"],
                    state["answers"]["location"],
                    state["answers"].get("usage", state["answers"]["location"]),
                    state["answers"].get("notes", ""),
                    state["answers"].get("warranty", "No warranty information")
                ))
                
                item_id = cursor.lastrowid
                
                # Add to item history
                cursor.execute('''
                    INSERT INTO item_history (
                        item_id, action_type, from_whom, to_whom,
                        new_location, condition_change, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id,
                    state["transaction_type"],
                    state["answers"].get("from_whom", ""),
                    state["answers"].get("to_whom", ""),
                    state["answers"]["location"],
                    state["answers"].get("condition", "Unknown"),
                    state["answers"].get("notes", "")
                ))

                # Add maintenance record if maintenance is required
                if state["answers"].get("maintenance", "").lower() == "yes":
                    cursor.execute('''
                        INSERT INTO maintenance_records (
                            item_id, maintenance_type, notes
                        ) VALUES (?, 'Regular maintenance required', ?)
                    ''', (
                        item_id,
                        "Initial maintenance record created during item registration"
                    ))

            elif state["transaction_type"] in ["disposed", "lost"]:
                # Update existing item as disposed/lost
                cursor.execute('''
                    UPDATE items 
                    SET disposal_date = CURRENT_TIMESTAMP,
                        disposal_method = ?,
                        notes = ?
                    WHERE name = ? 
                    AND disposal_date IS NULL
                ''', (
                    state["transaction_type"],
                    f"Status: {state['transaction_type'].upper()}. " + state["answers"].get("notes", ""),
                    state["item_name"]
                ))

                # Add to item history
                cursor.execute('''
                    INSERT INTO item_history (
                        item_id, action_type, to_whom,
                        condition_change, notes
                    ) VALUES (
                        (SELECT id FROM items WHERE name = ? ORDER BY id DESC LIMIT 1),
                        ?, ?, ?, ?
                    )
                ''', (
                    state["item_name"],
                    state["transaction_type"],
                    state["answers"].get("to_whom", ""),
                    state["answers"].get("condition", "Unknown"),
                    state["answers"].get("notes", "")
                ))

            conn.commit()
            
            return jsonify({
                "status": "completed",
                "message": f"Thanks! I've recorded all the information about the {state['item_name']}.",
                "recorded_data": {
                    "item_name": state["item_name"],
                    "transaction_type": state["transaction_type"],
                    "answers": state["answers"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            })

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
