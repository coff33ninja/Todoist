import sqlite3

def process_natural_language_query(query_text, get_db):
    """
    Process natural language queries for the inventory system.
    
    Based on keywords in the query_text, this function handles queries
    about items/inventory, repairs, budget/cost or components.
    
    Args:
        query_text (str): The natural language query.
        get_db (function): A function returning a SQLite connection with a custom row factory.
    
    Returns:
        str: A response string with the query results or a message if nothing was found.
    """
    query_lower = query_text.lower().strip()
    response = ""
    
    try:
        # Check for query intent based on keywords
        
        # Query about items/inventory:
        if "item" in query_lower or "inventory" in query_lower:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
            items = cursor.fetchall()
            
            if items:
                response = "There are {} items in inventory. ".format(len(items))
                # List names of first few items
                item_names = [item.get("name", "unknown") for item in items[:5]]
                response += "Some items are: " + ", ".join(item_names) + "."
            else:
                response = "No items are found in the inventory."
        
        # Query about repairs:
        elif "repair" in query_lower:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""SELECT r.*, i.name as item_name
                              FROM repairs r 
                              JOIN items i ON r.item_id = i.id 
                              ORDER BY repair_date DESC""")
            repairs = cursor.fetchall()
            if repairs:
                response = "There are {} repair records. ".format(len(repairs))
                # Compose a summary for a few repairs
                repair_details = []
                for rep in repairs[:5]:
                    date = rep.get("repair_date", "unknown date")
                    item = rep.get("item_name", "unknown item")
                    repair_details.append(f"{item} on {date}")
                response += "Recent repairs: " + "; ".join(repair_details) + "."
            else:
                response = "No repair records were found."
        
        # Query about budget or overall cost:
        elif "budget" in query_lower or "cost" in query_lower:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budget WHERE id=1")
            budget = cursor.fetchone()
            if budget:
                amount = budget.get("amount", 0)
                period = budget.get("period", "unspecified")
                response = f"The current budget is set at ${amount} for the {period} period."
            else:
                response = "The budget has not been set up yet."
        
        # Query about components:
        elif "component" in query_lower:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""SELECT c.*, i.name as item_name 
                              FROM components c 
                              JOIN items i ON c.item_id = i.id 
                              ORDER BY priority DESC, created_at DESC""")
            components = cursor.fetchall()
            if components:
                response = "There are {} components required. ".format(len(components))
                comp_details = []
                for comp in components[:5]:
                    cname = comp.get("name", "unknown")
                    item = comp.get("item_name", "unknown item")
                    comp_details.append(f"{cname} for {item}")
                response += "Some components are: " + "; ".join(comp_details) + "."
            else:
                response = "No components were found."
        
        else:
            response = ("I'm sorry, I didn't understand your query. "
                        "Please ask about items, repairs, budget, or components.")
    
    except Exception as error:
        response = f"An error occurred while processing your query: {error}"
    
    return response