import sqlite3

def list_tables(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print("Tables in database:")
        for table in tables:
            print(f"- {table[0]}")
            # Print columns for each table
            columns = cursor.execute(f"PRAGMA table_info({table[0]})").fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
    except Exception as e:
        print(f"Error inspecting database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    list_tables("inventory.db")
