import sqlite3
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import torch


class NLUProcessor:
    def __init__(self, model_path='ai_models/nlu_model.pkl'):
        # Initialize patterns for basic matching
        self.patterns = {
            'search': [
                r'show\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?'
                r'(?:items?|products?|things?)(?:\s+in\s+(.+))?',
                r'what\s+(?:items?|products?|things?)'
                r'(?:\s+do\s+I\s+have)?(?:\s+in\s+(.+))?',
                r'list\s+(?:all\s+)?(?:items?|products?|things?)'
                r'(?:\s+in\s+(.+))?'
            ],
            'count': [
                r'how\s+many\s+(?:items?|products?|things?)'
                r'(?:\s+do\s+I\s+have)?(?:\s+in\s+(.+))?',
                r'count\s+(?:all\s+)?(?:items?|products?|things?)'
                r'(?:\s+in\s+(.+))?'
            ],
            'value': [
                r'what\s+is\s+the\s+(?:total\s+)?value\s+of\s+(?:my\s+)?'
                r'(?:inventory|items?|products?|things?)(?:\s+in\s+(.+))?',
                r'how\s+much\s+(?:is|are)\s+(?:my\s+)?(?:inventory|items?'
                r'|products?|things?)(?:\s+worth)?(?:\s+in\s+(.+))?'
            ],
            'price_range': [
                r'what\s+(?:items?|products?|things?)\s+cost\s+(?:more|less)'
                r'\s+than\s+(\d+(?:\.\d{2})?)',
                r'show\s+(?:me\s+)?(?:items?|products?|things?)\s+(?:that\s+)?'
                r'cost\s+(?:more|less)\s+than\s+(\d+(?:\.\d{2})?)'
            ]
        }

        # Initialize ML model
        self.model_path = model_path
        self.model, self.tokenizer = self._load_or_create_model()
        self.context = None

    def _load_or_create_model(self):
        """Load or create the transformer model"""
        model_name = "distilbert-base-uncased"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=4  # 4 intents: search, count, value, price_range
        )
        return model, tokenizer

    def process_natural_language_query(self, query, get_db):
        """Process a natural language query using the transformer model"""
        if not query:
            return {"error": "Empty query"}

        # Tokenize and predict
        inputs = self.tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits

        # Get predicted intent
        probabilities = softmax(logits, dim=1)
        predicted_label = int(torch.argmax(probabilities, dim=1).item())

        # Map label to intent
        intents = ["search", "count", "value", "price_range"]
        predicted_intent = intents[predicted_label]

        # Handle intent
        if predicted_intent == "search":
            return self._handle_search(get_db().cursor(), None)
        elif predicted_intent == "count":
            return self._handle_count(get_db().cursor(), None)
        elif predicted_intent == "value":
            return self._handle_value(get_db().cursor(), None)
        elif predicted_intent == "price_range":
            return self._handle_price_range(get_db().cursor(), None)
        else:
            return {"message": "I'm not sure how to handle that request."}

    def _handle_search(self, cursor, match):
        """Handle search queries"""
        location = match.group(1) if match and match.groups() else None

        if location:
            cursor.execute('''
                SELECT * FROM items
                WHERE location LIKE ?
                ORDER BY name
            ''', (f'%{location}%',))
        else:
            cursor.execute('SELECT * FROM items ORDER BY name')

        items = []
        for row in cursor.fetchall():
            items.append(dict(row))

        if not items:
            return {"message": "No items found"}

        return {"items": items}

    def _handle_count(self, cursor, match):
        """Handle count queries"""
        location = match.group(1) if match and match.groups() else None

        if location:
            cursor.execute('''
                SELECT COUNT(*) as count FROM items
                WHERE location LIKE ?
            ''', (f'%{location}%',))
        else:
            cursor.execute('SELECT COUNT(*) as count FROM items')

        result = cursor.fetchone()
        count = result['count'] if isinstance(result, sqlite3.Row) else result[0]

        location_str = f" in {location}" if location else ""
        return {"message": f"You have {count} items{location_str}."}

    def _handle_value(self, cursor, match):
        """Handle value queries"""
        location = match.group(1) if match and match.groups() else None

        if location:
            cursor.execute('''
                SELECT SUM(price * quantity) as total FROM items
                WHERE location LIKE ? AND price IS NOT NULL
            ''', (f'%{location}%',))
        else:
            cursor.execute('''
                SELECT SUM(price * quantity) as total FROM items
                WHERE price IS NOT NULL
            ''')

        result = cursor.fetchone()
        total = result['total'] if isinstance(result, sqlite3.Row) else result[0]
        total = total or 0

        location_str = f" in {location}" if location else ""
        return {
            "message": f"The total value of items{location_str} is ${total:.2f}"
        }

    def _handle_price_range(self, cursor, match):
        """Handle price range queries"""
        comparison = 'more' if match and 'more' in match.group(0) else 'less'
        price = float(match.group(1)) if match else 0

        if comparison == 'more':
            cursor.execute('''
                SELECT * FROM items
                WHERE price > ?
                ORDER by price DESC
            ''', (price,))
        else:
            cursor.execute('''
                SELECT * FROM items
                WHERE price < ?
                ORDER by price
            ''', (price,))

        items = []
        for row in cursor.fetchall():
            items.append(dict(row))

        if not items:
            return {
                "message": f"No items found {comparison} than ${price:.2f}"
            }

        return {"items": items}

    def set_context(self, context):
        """Set conversation context"""
        self.context = context

    def get_context(self):
        """Get current conversation context"""
        return self.context
