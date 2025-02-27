import re
import os
import sqlite3
import spacy
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from torch.nn.functional import softmax
import torch


class NLUProcessor:
    def __init__(self, model_path="ai_models/nlu_model", db_path="inventory.db"):
        """Initialize the NLUProcessor with model and database connections."""
        # Define supported intents as a class attribute for easy modification
        self.intents = [
            "search",
            "count",
            "value",
            "price_range",
            "repair",
            "purchase_history",
        ]

        # Regular expression patterns for intent detection
        self.patterns = {
            "search": [
                r"show\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:items?|products?|things?)(?:\s+in\s+(.+))?"
            ],
            "count": [r"how\s+many\s+(?:items?|products?|things?)(?:\s+in\s+(.+))?"],
            "value": [
                r"what\s+is\s+the\s+(?:total\s+)?value\s+of\s+(?:my\s+)?(?:inventory|items?|products?|things?)(?:\s+in\s+(.+))?"
            ],
            "price_range": [
                r"what\s+(?:items?|products?|things?)\s+cost\s+(?:more|less)\s+than\s+(\d+(?:\.\d{2})?)"
            ],
            "repair": [
                r"(?:list|what|show)\s+(?:all\s+)?(?:items?|products?|things?)\s+(?:that\s+)?(?:need|due\s+for)\s+(?:to\s+be\s+)?(?:repair|fixed)"
            ],
            "purchase_history": [
                r"what\s+(?:did\s+I\s+buy|items?\s+(?:I\s+bought))\s+(last\s+\w+|\w+\s+ago|on\s+sale)"
            ],
        }

        self.model_path = model_path
        self.db_conn = sqlite3.connect(db_path)  # Internal database connection
        self.model, self.tokenizer = self._load_or_create_model()
        self.trained = False
        self.context = None  # For multi-turn conversation support
        self.nlp = spacy.load("en_core_web_sm")  # Load spaCy for advanced NLP

    def _load_or_create_model(self):
        """Load an existing model or create a new one if it doesn't exist."""
        model_name = "distilbert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        try:
            if os.path.exists(self.model_path) and os.path.exists(
                os.path.join(self.model_path, "config.json")
            ):
                model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_path
                )
            else:
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name, num_labels=len(self.intents)
                )
        except Exception as e:
            print(f"Error loading model: {e}")
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name, num_labels=len(self.intents)
            )
        return model, tokenizer

    def train_model(
        self, train_dataset, eval_dataset=None, epochs=3, batch_size=16, output_dir=None
    ):
        """
        Train the NLU model.

        Args:
            train_dataset: A transformers Dataset with 'text' (query) and 'label' (intent index) columns.
            eval_dataset: Optional evaluation dataset for validation during training.
            epochs: Number of training epochs (default: 3).
            batch_size: Batch size for training and evaluation (default: 16).
            output_dir: Directory to save the trained model (default: self.model_path).
        """
        training_args = TrainingArguments(
            output_dir=output_dir or self.model_path,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            evaluation_strategy="epoch" if eval_dataset else "no",
            save_steps=10_000,
            save_total_limit=2,
            logging_dir="./logs",
        )
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
        )
        trainer.train()
        trainer.save_model(output_dir or self.model_path)
        self.trained = True

    def extract_filters(self, query):
        """Extract filters from the query using spaCy and regex."""
        filters = {}
        doc = self.nlp(query)
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Location
                filters["location"] = ent.text
            elif ent.label_ == "MONEY":  # Price
                filters["price"] = ent.text

        # Regex-based filter extraction
        m = re.search(r"in\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["location"] = m.group(1).strip()
        m = re.search(r"category\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["category"] = m.group(1).strip()
        m = re.search(r"tag[s]?\s+([\w\s,]+)", query, re.IGNORECASE)
        if m:
            filters["tags"] = m.group(1).strip()
        m = re.search(r"purchased\s+on\s+([\d/-]+)", query, re.IGNORECASE)
        if m:
            filters["purchase_date"] = m.group(1).strip()
        if re.search(r"\b(gifts?|free)\b", query, re.IGNORECASE):
            filters["is_gift"] = True
        m = re.search(r"stored\s+in\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["storage_location"] = m.group(1).strip()
        m = re.search(r"used\s+in\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["usage_location"] = m.group(1).strip()
        m = re.search(
            r"cost\s+(more|less)\s+than\s+(\d+(?:\.\d{2})?)", query, re.IGNORECASE
        )
        if m:
            filters["comparison"] = m.group(1)
            filters["price"] = m.group(2)
        m = re.search(r"last\s+(\w+)", query, re.IGNORECASE)
        if m:
            filters["time_period"] = m.group(1)
        return filters

    def process_natural_language_query(self, query):
        """Process a natural language query and return the result."""
        if not query:
            return {"error": "Empty query"}

        cursor = self.db_conn.cursor()
        inputs = self.tokenizer(
            query, return_tensors="pt", truncation=True, padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        probabilities = softmax(logits, dim=1)
        predicted_label = int(torch.argmax(probabilities, dim=1).item())
        predicted_intent = self.intents[predicted_label]

        # Use context for multi-turn conversations
        if self.context and "previous_filters" in self.context:
            filters = self.context["previous_filters"]
            filters.update(self.extract_filters(query))
        else:
            filters = self.extract_filters(query)

        # Intent handlers
        handlers = {
            "search": self.handle_search,
            "count": self._handle_count,
            "value": self._handle_value,
            "price_range": self._handle_price_range,
            "repair": self._handle_repair,
            "purchase_history": self._handle_purchase_history,
            None: lambda cursor, filters: {
                "message": "I’m not sure how to handle that."
            },
        }

        handler = handlers.get(predicted_intent, handlers[None])
        result = handler(cursor, filters)
        self.set_context({"previous_filters": filters})  # Update context
        return result

    def handle_search(self, cursor, filters):
        """Handle search intent."""
        sql = "SELECT * FROM items WHERE 1=1"
        params = []
        if "location" in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if "category" in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if "tags" in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        if "purchase_date" in filters:
            sql += " AND purchase_date = ?"
            params.append(filters["purchase_date"])
        sql += " ORDER BY name"
        try:
            cursor.execute(sql, params)
            items = [dict(row) for row in cursor.fetchall()]
            return {"items": items} if items else {"message": "No items found."}
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def _handle_count(self, cursor, filters):
        """Handle count intent."""
        sql = "SELECT COUNT(*) as count FROM items WHERE 1=1"
        params = []
        if "location" in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if "category" in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if "tags" in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        try:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            count = result["count"] if result else 0
            return {"message": f"You have {count} matching items."}
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def _handle_value(self, cursor, filters):
        """Handle value intent."""
        sql = "SELECT SUM(price * quantity) as total FROM items WHERE price IS NOT NULL"
        params = []
        if "location" in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if "category" in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if "tags" in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        try:
            cursor.execute(sql, params)
            result = cursor.fetchone()
            total = result["total"] if result and result["total"] is not None else 0
            return {"message": f"The total value is ${total:.2f}"}
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def _handle_price_range(self, cursor, filters):
        """Handle price_range intent."""
        comparison = filters.get("comparison", "more")
        try:
            price = float(filters.get("price", 0))
        except ValueError:
            price = 0
        sql = f"SELECT * FROM items WHERE price {'>' if comparison == 'more' else '<'} ? ORDER BY price {'DESC' if comparison == 'more' else 'ASC'}"
        try:
            cursor.execute(sql, (price,))
            items = [dict(row) for row in cursor.fetchall()]
            return (
                {"items": items}
                if items
                else {"message": f"No items found {comparison} than ${price:.2f}"}
            )
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def _handle_repair(self, cursor, filters):
        """Handle repair intent."""
        sql = "SELECT * FROM items WHERE needs_repair = 1"
        params = []
        if "location" in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        try:
            cursor.execute(sql, params)
            items = [dict(row) for row in cursor.fetchall()]
            return (
                {"items": items}
                if items
                else {"message": "No items needing repair found."}
            )
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def _handle_purchase_history(self, cursor, filters):
        """Handle purchase_history intent."""
        sql = "SELECT * FROM items WHERE purchase_date IS NOT NULL"
        params = []
        if "time_period" in filters:
            sql += " AND purchase_date LIKE ?"
            params.append(f"%{filters['time_period']}%")
        sql += " ORDER BY purchase_date DESC"
        try:
            cursor.execute(sql, params)
            items = [dict(row) for row in cursor.fetchall()]
            return (
                {"items": items} if items else {"message": "No purchase history found."}
            )
        except sqlite3.Error as e:
            return {"error": f"Database error: {e}"}

    def set_context(self, context):
        """Set the context for multi-turn conversations."""
        self.context = context

    def get_context(self):
        """Get the current context."""
        return self.context
