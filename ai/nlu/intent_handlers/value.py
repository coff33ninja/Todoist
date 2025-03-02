from ..database_handler import DatabaseHandler

class ValueHandler:
    def __init__(self, db_path: str):
        """Initialize the ValueHandler with the database path."""
        self.database_handler = DatabaseHandler(db_path)

    def handle(self, filters):
        """Handle the value intent with the provided filters."""
        # Example logic to retrieve specific values based on filters
        query = "SELECT value FROM items WHERE 1=1"
        params = []

        if 'item_id' in filters:
            query += " AND id = ?"
            params.append(filters['item_id'])

        values = self.database_handler.execute_query(query, params)
        return {"values": values}
