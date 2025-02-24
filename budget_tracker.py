from inventory_manager import InventoryManager

class BudgetTracker:
    def __init__(self, db_path='inventory.db'):
        self.inventory = InventoryManager(db_path)

    def calculate_total_spent(self):
        cursor = self.inventory.conn.cursor()
        cursor.execute('SELECT SUM(purchase_price) FROM items')
        total = cursor.fetchone()[0]
        return total if total else 0.0

    def calculate_available_budget(self, total_budget):
        total_spent = self.calculate_total_spent()
        return total_budget - total_spent

    def get_purchase_history(self):
        cursor = self.inventory.conn.cursor()
        cursor.execute('''
            SELECT name, purchase_price, purchase_date 
            FROM items 
            WHERE purchase_price IS NOT NULL
            ORDER BY purchase_date DESC
        ''')
        return cursor.fetchall()
