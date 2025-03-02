from ..database_handler import DatabaseHandler

class CountHandler:
    def __init__(self, db_path: str):
        """Initialize the CountHandler with the database path."""
        self.database_handler = DatabaseHandler(db_path)

    def handle(self, filters):
        """Handle the count intent with the provided filters."""
        # Example logic to count items based on filters
        query = "SELECT COUNT(*) FROM items WHERE 1=1"
        params = []

        if 'category' in filters:
            query += " AND category = ?"
            params.append(filters['category'])

        count = self.database_handler.execute_query(query, params)
        return {"count": count[0][0] if count else 0}
