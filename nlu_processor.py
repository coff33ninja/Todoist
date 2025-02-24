import sqlite3
import re
from datetime import datetime

class NLUProcessor:
    def __init__(self):
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

    def process_natural_language_query(self, query, get_db):
        """Process a natural language query and return relevant information"""
        if not query:
            return {"error": "Empty query"}

        query = query.lower().strip()

        try:
            # Get database connection
            conn = get_db()
            cursor = conn.cursor()

            # Try to match query patterns
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

    def _handle_search(self, cursor, match):
        """Handle search queries"""
        location = match.group(1) if match.groups() else None

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
        location = match.group(1) if match.groups() else None

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
        location = match.group(1) if match.groups() else None

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
        comparison = 'more' if 'more' in match.group(0) else 'less'
        price = float(match.group(1))

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
