from ..database_handler import DatabaseHandler

class SearchHandler:
    def __init__(self, db_path: str):
        """Initialize the SearchHandler with the database path."""
        self.database_handler = DatabaseHandler(db_path)

    def handle(self, filters):
        """Handle the search intent with the provided filters."""
        # Example logic to query the database based on filters
        query = "SELECT * FROM items WHERE 1=1"
        params = []

        if 'category' in filters:
            query += " AND category = ?"
            params.append(filters['category'])
        if 'price_min' in filters:
            query += " AND price >= ?"
            params.append(filters['price_min'])
        if 'price_max' in filters:
            query += " AND price <= ?"
            params.append(filters['price_max'])

        results = self.database_handler.execute_query(query, params)
        return {"results": results}
