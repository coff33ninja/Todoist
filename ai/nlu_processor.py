import re
import sqlite3
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.nn.functional import softmax
import torch

class NLUProcessor:
    def __init__(self, model_path='ai_models/nlu_model.pkl'):
        # Basic patterns still exist (they can be extended later)
        self.patterns = {
            'search': [
                r'show\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:items?|products?|things?)(?:\s+in\s+(.+))?'
            ],
            'count': [
                r'how\s+many\s+(?:items?|products?|things?)(?:\s+in\s+(.+))?'
            ],
            'value': [
                r'what\s+is\s+the\s+(?:total\s+)?value\s+of\s+(?:my\s+)?(?:inventory|items?|products?|things?)(?:\s+in\s+(.+))?'
            ],
            'price_range': [
                r'what\s+(?:items?|products?|things?)\s+cost\s+(?:more|less)\s+than\s+(\d+(?:\.\d{2})?)'
            ]
        }

        self.model_path = model_path
        self.model, self.tokenizer = self._load_or_create_model()
        self.trained = False
        self.context = None

    def _load_or_create_model(self):
        model_name = "distilbert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=4  # intents: search, count, value, price_range
        )
        return model, tokenizer

    def train_model(self, train_dataset):
        training_args = TrainingArguments(
            output_dir='./results',
            num_train_epochs=3,
            per_device_train_batch_size=16,
            save_steps=10_000,
            save_total_limit=2,
            logging_dir='./logs',
        )
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
        )
        trainer.train()

    def extract_filters(self, query):
        """Extract simple filters from the query based on key words."""
        filters = {}
        # Look for location using "in ..."
        m = re.search(r'in\s+([\w\s]+)', query, re.IGNORECASE)
        if m:
            filters['location'] = m.group(1).strip()
        m = re.search(r'category\s+([\w\s]+)', query, re.IGNORECASE)
        if m:
            filters['category'] = m.group(1).strip()
        m = re.search(r'tag[s]?\s+([\w\s,]+)', query, re.IGNORECASE)
        if m:
            filters['tags'] = m.group(1).strip()
        m = re.search(r'purchased\s+on\s+([\d/-]+)', query, re.IGNORECASE)
        if m:
            filters['purchase_date'] = m.group(1).strip()
        # Add gift filter
        if re.search(r'\b(gifts?|free)\b', query, re.IGNORECASE):
            filters['is_gift'] = True
        # Add storage/usage location filters
        m = re.search(r'stored\s+in\s+([\w\s]+)', query, re.IGNORECASE)
        if m:
            filters['storage_location'] = m.group(1).strip()
        m = re.search(r'used\s+in\s+([\w\s]+)', query, re.IGNORECASE)
        if m:
            filters['usage_location'] = m.group(1).strip()
        return filters

    def _handle_search(self, cursor, filters):
        """Build a SQL query using any filters provided."""
        sql = "SELECT * FROM items WHERE 1=1"
        params = []
        if 'location' in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if 'category' in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if 'tags' in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        if 'purchase_date' in filters:
            sql += " AND purchase_date = ?"
            params.append(filters['purchase_date'])
        if 'is_gift' in filters:
            sql += " AND is_gift = 1"
        if 'storage_location' in filters:
            sql += " AND storage_location LIKE ?"
            params.append(f"%{filters['storage_location']}%")
        if 'usage_location' in filters:
            sql += " AND usage_location LIKE ?"
            params.append(f"%{filters['usage_location']}%")
        sql += " ORDER BY name"

    def process_natural_language_query(self, query, get_db):
        if not query:
            return {"error": "Empty query"}

        # Predict using the transformer model
        inputs = self.tokenizer(query, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits

        probabilities = softmax(logits, dim=1)
        predicted_label = int(torch.argmax(probabilities, dim=1).item())
        intents = ["search", "count", "value", "price_range"]
        predicted_intent = intents[predicted_label]

        # Extract extra filters from the query text
        filters = self.extract_filters(query)

        db_cursor = get_db().cursor()

        if predicted_intent == "search":
            return self._handle_search(db_cursor, filters)
        elif predicted_intent == "count":
            return self._handle_count(db_cursor, filters)
        elif predicted_intent == "value":
            return self._handle_value(db_cursor, filters)
        elif predicted_intent == "price_range":
            return self._handle_price_range(db_cursor, filters)
        else:
            return {"message": "I'm not sure how to handle that request."}

    def _handle_search(self, cursor, filters):
        """Build a SQL query using any filters provided."""
        sql = "SELECT * FROM items WHERE 1=1"
        params = []
        if 'location' in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if 'category' in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if 'tags' in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        if 'purchase_date' in filters:
            sql += " AND purchase_date = ?"
            params.append(filters['purchase_date'])
        sql += " ORDER BY name"

        cursor.execute(sql, params)
        items = [dict(row) for row in cursor.fetchall()]
        if not items:
            return {"message": "No items found matching your query."}
        return {"items": items}

    def _handle_count(self, cursor, filters):
        sql = "SELECT COUNT(*) as count FROM items WHERE 1=1"
        params = []
        if 'location' in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if 'category' in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if 'tags' in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        if 'purchase_date' in filters:
            sql += " AND purchase_date = ?"
            params.append(filters['purchase_date'])
        cursor.execute(sql, params)
        result = cursor.fetchone()
        count = result['count'] if result else 0
        return {"message": f"You have {count} matching items."}

    def _handle_value(self, cursor, filters):
        sql = "SELECT SUM(price * quantity) as total FROM items WHERE price IS NOT NULL"
        params = []
        if 'location' in filters:
            sql += " AND location LIKE ?"
            params.append(f"%{filters['location']}%")
        if 'category' in filters:
            sql += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        if 'tags' in filters:
            sql += " AND tags LIKE ?"
            params.append(f"%{filters['tags']}%")
        if 'purchase_date' in filters:
            sql += " AND purchase_date = ?"
            params.append(filters['purchase_date'])
        cursor.execute(sql, params)
        result = cursor.fetchone()
        total = result['total'] if result and result['total'] is not None else 0
        return {"message": f"The total value is ${total:.2f}"}

    def _handle_price_range(self, cursor, filters):
        # For price range, assume filters contains numeric value in 'price' key from regex
        # (This example can be extended as needed.)
        comparison = 'more' if filters.get('comparison') == 'more' else 'less'
        try:
            price = float(filters.get('price', 0))
        except Exception:
            price = 0
        if comparison == 'more':
            cursor.execute("SELECT * FROM items WHERE price > ? ORDER BY price DESC", (price,))
        else:
            cursor.execute("SELECT * FROM items WHERE price < ? ORDER BY price", (price,))
        items = [dict(row) for row in cursor.fetchall()]
        if not items:
            return {"message": f"No items found {comparison} than ${price:.2f}"}
        return {"items": items}

    def set_context(self, context):
        self.context = context

    def get_context(self):
        return self.context