import os
import sqlite3

def get_user_data(username: str):
    # Safe parameterized query
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM users WHERE name = ?", (username,)).fetchall()
    return rows

if __name__ == "__main__":
    db_pass = os.environ.get("DB_PASSWORD", "default_value")
    print(get_user_data("test_user"))
