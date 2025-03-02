from ..database_handler import DatabaseHandler

class PurchaseHistoryHandler:
    def __init__(self, db_path: str):
        """Initialize the PurchaseHistoryHandler with the database path."""
        self.database_handler = DatabaseHandler(db_path)

    def handle(self, filters):
        """Handle the purchase_history intent with the provided filters."""
        # Example logic to retrieve purchase history
        query = "SELECT * FROM purchases WHERE user_id = ?"
        params = []

        if 'user_id' in filters:
            params.append(filters['user_id'])
        else:
            return {"error": "User ID filter is required."}

        history = self.database_handler.execute_query(query, params)
        return {"history": history}
