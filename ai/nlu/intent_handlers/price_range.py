from ..database_handler import DatabaseHandler

class PriceRangeHandler:
    def __init__(self, db_path: str):
        """Initialize the PriceRangeHandler with the database path."""
        self.database_handler = DatabaseHandler(db_path)

    def handle(self, filters):
        """Handle the price_range intent with the provided filters."""
        # Example logic to retrieve items within a specified price range
        query = "SELECT * FROM items WHERE price BETWEEN ? AND ?"
        params = []

        if 'price_min' in filters and 'price_max' in filters:
            params.append(filters['price_min'])
            params.append(filters['price_max'])
        else:
            return {"error": "Price range filters are required."}

        results = self.database_handler.execute_query(query, params)
        return {"results": results}
