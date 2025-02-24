import sqlite3
import re
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

class NLUProcessor:
    def __init__(self, model_path='ai_models/nlu_model.pkl'):
        # Initialize patterns for basic matching
        self.patterns = {
            'search': [
                r'show\s+(?:me\s+)?(?:all\s+)?(?:the\s+)?(?:items?|products?|things?)(?:\s+in\s+(.+))?',
                r'what\s+(?:items?|products?|things?)(?:\s+do\s+I\s+have)?(?:\s+in\s+(.+))?',
                r'list\s+(?:all\s+)?(?:items?|products?|things?)(?:\s+in\s+(.+))?'
            ],
            'count': [
                r'how\s+many\s+(?:items?|products?|things?)(?:\s+do\s+I\s+have)?(?:\s+in\s+(.+))?',
                r'count\s+(?:all\s+)?(?:items?|products?|things?)(?:\s+in\s+(.+))?'
            ],
            'value': [
                r'what\s+is\s+the\s+(?:total\s+)?value\s+of\s+(?:my\s+)?(?:inventory|items?|products?|things?)(?:\s+in\s+(.+))?',
                r'how\s+much\s+(?:is|are)\s+(?:my\s+)?(?:inventory|items?|products?|things?)(?:\s+worth)?(?:\s+in\s+(.+))?'
            ],
            'price_range': [
                r'what\s+(?:items?|products?|things?)\s+cost\s+(?:more|less)\s+than\s+(\d+(?:\.\d{2})?)',
                r'show\s+(?:me\s+)?(?:items?|products?|things?)\s+(?:that\s+)?cost\s+(?:more|less)\s+than\s+(\d+(?:\.\d{2})?)'
            ]
        }

        # Initialize ML model
        self.model_path = model_path
        self.model = self._load_or_create_model()
        self.context = None

    def _load_or_create_model(self):
        """Load or create the ML model"""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        else:
            # Create new model pipeline
            model = Pipeline([
                ('tfidf', TfidfVectorizer()),
                ('clf', LogisticRegression())
            ])
            return model

    def train_model(self, X, y):
        """Train the ML model with new data"""
        self.model.fit(X, y)
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def process_natural_language_query(self, query, get_db):
        """Process a natural language query using both pattern matching and ML"""
        if not query:
            return {"error": "Empty query"}

        query = query.lower().strip()

        # First try pattern matching
        pattern_result = self._try_pattern_matching(query, get_db)
        if pattern_result.get('items') or pattern_result.get('message'):
            return pattern_result

        # Fall back to ML model
        return self._handle_with_ml(query, get_db)

    def _try_pattern_matching(self, query, get_db):
        """Try to match query patterns"""
        try:
            conn = get_db()
            cursor = conn.cursor()

            for intent, patterns in self.patterns.items():
                for pattern in patterns:
                    match = re.match(pattern, query)
                    if match:
                        if intent == 'search':
                            return self._handle_search(cursor, match)
                        elif intent == 'count':
                            return self._handle_count(cursor, match)
                        elif intent == 'value':
                            return self._handle_value(cursor, match)
                        elif intent == 'price_range':
                            return self._handle_price_range(cursor, match)

            return {"message": "I don't understand that query. Try asking about items, their count, or value."}

        except Exception as e:
            return {"error": str(e)}

    def _handle_with_ml(self, query, get_db):
        """Handle query using machine learning"""
        try:
            # Predict intent using ML model
            predicted_intent = self.model.predict([query])[0]

            # Handle based on predicted intent
            if predicted_intent == 'search':
                return self._handle_search(get_db().cursor(), None)
            elif predicted_intent == 'count':
                return self._handle_count(get_db().cursor(), None)
            elif predicted_intent == 'value':
                return self._handle_value(get_db().cursor(), None)
            elif predicted_intent == 'price_range':
                return self._handle_price_range(get_db().cursor(), None)
            else:
                return {"message": "I'm not sure how to handle that request."}

        except Exception as e:
            return {"error": str(e)}

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
        return {"message": f"The total value of items{location_str} is ${total:.2f}"}

    def _handle_price_range(self, cursor, match):
        """Handle price range queries"""
        comparison = 'more' if match and 'more' in match.group(0) else 'less'
        price = float(match.group(1)) if match else 0

        if comparison == 'more':
            cursor.execute('''
                SELECT * FROM items
                WHERE price > ?
                ORDER BY price DESC
            ''', (price,))
        else:
            cursor.execute('''
                SELECT * FROM items
                WHERE price < ?
                ORDER BY price
            ''', (price,))

        items = []
        for row in cursor.fetchall():
            items.append(dict(row))

        if not items:
            return {"message": f"No items found {comparison} than ${price:.2f}"}

        return {"items": items}

    def set_context(self, context):
        """Set conversation context"""
        self.context = context

    def get_context(self):
        """Get current conversation context"""
        return self.context
