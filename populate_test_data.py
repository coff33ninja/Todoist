import sqlite3

def populate_test_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert test items
    cursor.executemany("""
        INSERT INTO items (name, description, quantity, purchase_date, price)
        VALUES (?, ?, ?, ?, ?)
    """, [
        ("Test Item 1", "First test item", 5, "2023-01-01", 100.0),
        ("Test Item 2", "Second test item", 3, "2023-02-01", 150.0)
    ])

    # Insert test repairs
    cursor.executemany("""
        INSERT INTO repairs (item_id, repair_date, description, cost)
        VALUES (?, ?, ?, ?)
    """, [
        (1, "2023-01-15", "First repair", 50.0),
        (2, "2023-02-15", "Second repair", 75.0)
    ])

    # Insert test budget
    cursor.execute("""
        INSERT INTO budget (amount, period)
        VALUES (?, ?)
    """, (1000.0, "monthly"))

    # Insert test components
    cursor.executemany("""
        INSERT INTO components (item_id, name, quantity_needed)
        VALUES (?, ?, ?)
    """, [
        (1, "Component 1", 2),
        (2, "Component 2", 3)
    ])

    conn.commit()
    conn.close()

if __name__ == "__main__":
    populate_test_data("inventory.db")
