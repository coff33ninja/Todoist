import sqlite3

def check_receipts():
    """Check the contents of the purchases and purchase_items tables."""
    conn = sqlite3.connect("db/inventory.db")
    cursor = conn.cursor()

    # Check if purchases table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchases'")
    if cursor.fetchone() is None:
        print("Purchases table does not exist.")
    else:
        # Fetch purchases
        cursor.execute("SELECT * FROM purchases")
        purchases = cursor.fetchall()

        print("Purchases:")
        for purchase in purchases:
            print(purchase)

    # Check if purchase_items table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='purchase_items'")
    if cursor.fetchone() is None:
        print("Purchase Items table does not exist.")
    else:
        # Fetch purchase items
        cursor.execute("SELECT * FROM purchase_items")
        purchase_items = cursor.fetchall()

        print("\nPurchase Items:")
        for item in purchase_items:
            print(item)

    conn.close()

if __name__ == "__main__":
    check_receipts()
