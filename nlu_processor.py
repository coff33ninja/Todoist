from datetime import datetime, timedelta
import re
import logging
from typing import Dict, Any, Callable

class NLUProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def process_natural_language_query(self, query_text: str, get_db: Callable) -> Dict[str, Any]:
        """
        Process natural language queries for the inventory system.
        """
        query_lower = query_text.lower().strip()

        try:
            conn = get_db()
            cursor = conn.cursor()

            # Time-related patterns
            time_patterns = {
                "last month": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "last week": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "yesterday": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "today": datetime.now().strftime("%Y-%m-%d")
            }

            # Check for time-specific queries
            time_frame = None
            for pattern, date in time_patterns.items():
                if pattern in query_lower:
                    time_frame = date
                    break

            # Query about items by acquisition type
            if "traded" in query_lower or "trade" in query_lower:
                cursor.execute("""
                    SELECT i.*, t.traded_item, t.traded_item_value, t.trade_partner
                    FROM items i
                    JOIN trades t ON i.id = t.item_id
                    WHERE i.acquisition_type = 'trade'
                    ORDER BY i.created_at DESC
                """)
                items = cursor.fetchall()
                return {
                    "type": "trades",
                    "count": len(items),
                    "items": items
                }

            # Query about purchases in a time frame
            elif "buy" in query_lower or "bought" in query_lower or "purchase" in query_lower:
                query = """
                    SELECT * FROM items
                    WHERE acquisition_type = 'purchase'
                """
                if time_frame:
                    query += " AND purchase_date >= ?"
                    cursor.execute(query, (time_frame,))
                else:
                    cursor.execute(query)
                items = cursor.fetchall()
                return {
                    "type": "purchases",
                    "count": len(items),
                    "items": items
                }

            # Query about repairs
            elif "repair" in query_lower or "fix" in query_lower or "list all repairs" in query_lower:
                status_patterns = {
                    "scheduled": "scheduled" in query_lower,
                    "in progress": "progress" in query_lower,
                    "completed": "completed" in query_lower or "done" in query_lower,
                    "pending": "pending" in query_lower or "need" in query_lower
                }

                status = next((k for k, v in status_patterns.items() if v), None)

                query = """
                    SELECT r.*, i.name as item_name
                    FROM repairs r
                    LEFT JOIN items i ON r.item_id = i.id
                """
                if status:
                    query += " WHERE r.status = ?"
                    cursor.execute(query, (status,))
                else:
                    cursor.execute(query)
                
                repairs = cursor.fetchall()
                return {
                    "type": "repairs",
                    "count": len(repairs),
                    "repairs": repairs
                }

            # Query about components
            elif "component" in query_lower or "part" in query_lower:
                status = None
                if "needed" in query_lower:
                    status = "needed"
                elif "ordered" in query_lower:
                    status = "ordered"
                elif "received" in query_lower:
                    status = "received"

                query = """
                    SELECT c.*, i.name as item_name
                    FROM components c
                    JOIN items i ON c.item_id = i.id
                """
                if status:
                    query += " WHERE c.status = ?"
                    cursor.execute(query, (status,))
                else:
                    cursor.execute(query)
                components = cursor.fetchall()
                return {
                    "type": "components",
                    "count": len(components),
                    "components": components
                }

            # Query about budget
            elif any(phrase in query_lower for phrase in ["budget", "show me the budget", "money", "spent"]):
                cursor.execute("SELECT id, amount, period FROM budget")
                budgets = cursor.fetchall()

                if not budgets:
                    return {
                        "type": "budget",
                        "message": "No budget has been set"
                    }

                budget = budgets[0]

                # Calculate spending
                cursor.execute("SELECT COALESCE(SUM(price), 0) as total FROM items WHERE acquisition_type = 'purchase'")
                total_spent = cursor.fetchone()["total"]

                return {
                    "type": "budget",
                    "budget": budget,
                    "total_spent": total_spent,
                    "remaining": budget["amount"] - total_spent
                }

            # General item search
            else:
                # Extract potential search terms
                words = re.findall(r'\w+', query_lower)
                search_terms = [w for w in words if len(w) > 2 and w not in
                              ['the', 'and', 'for', 'that', 'what', 'where', 'when', 'how']]

                # If the query doesn't match any specific patterns
                if not any(word in query_lower for word in ["item", "repair", "budget", "component", "part"]):
                    return {
                        "type": "error",
                        "message": "I'm not sure what you're asking about. Try asking about items, "
                                "repairs, budget, or components."
                    }

                # Default to returning all items
                cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
                items = cursor.fetchall()
                return {
                    "type": "search",
                    "count": len(items),
                    "items": items
                }

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "type": "error",
                "message": f"An error occurred while processing your query: {str(e)}"
            }

# For backward compatibility with tests
def process_natural_language_query(query_text: str, get_db: Callable) -> Dict[str, Any]:
    processor = NLUProcessor()
    return processor.process_natural_language_query(query_text, get_db)