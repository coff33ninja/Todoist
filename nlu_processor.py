from datetime import datetime, timedelta
import re

def process_natural_language_query(query_text, get_db):
    """
    Process natural language queries for the inventory system.
    
    Examples:
    - "What items did I buy last month?"
    - "Show me all traded items"
    - "What repairs are scheduled?"
    - "How much budget is left?"
    - "What components do I need to buy?"
    
    Args:
        query_text (str): The natural language query
        get_db (callable): Function that returns a database connection
    
    Returns:
        dict: Response with query results
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
        elif "repair" in query_lower or "fix" in query_lower:
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
                JOIN items i ON r.item_id = i.id
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
                SELECT c.*, r.description as repair_description
                FROM components c
                JOIN repairs r ON c.repair_id = r.id
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
        elif "budget" in query_lower or "money" in query_lower or "spent" in query_lower:
            cursor.execute("SELECT * FROM budget WHERE id = 1")
            budget = cursor.fetchone()
            
            if not budget:
                return {
                    "type": "budget",
                    "message": "No budget has been set"
                }
            
            # Calculate spending
            cursor.execute("SELECT SUM(price) FROM items WHERE acquisition_type = 'purchase'")
            total_spent = cursor.fetchone()[0] or 0
            
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
            
            if search_terms:
                placeholders = ' OR '.join(['name LIKE ? OR description LIKE ? OR notes LIKE ?' 
                                          for _ in search_terms])
                params = []
                for term in search_terms:
                    params.extend([f'%{term}%'] * 3)
                
                cursor.execute(f"""
                    SELECT * FROM items 
                    WHERE {placeholders}
                    ORDER BY created_at DESC
                """, params)
                items = cursor.fetchall()
                return {
                    "type": "search",
                    "count": len(items),
                    "items": items
                }
            
            # If no specific query is recognized
            return {
                "type": "error",
                "message": "I'm not sure what you're asking about. Try asking about items, "
                          "repairs, budget, or components."
            }
            
    except Exception as e:
        return {
            "type": "error",
            "message": f"An error occurred while processing your query: {str(e)}"
        }