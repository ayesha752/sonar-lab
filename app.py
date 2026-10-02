import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# Read secret from environment variables instead of hardcoding
DB_PASSWORD = os.environ.get("DB_PASSWORD", "default_secure_value")

@app.route("/user")
def get_user():
    name = request.args.get("name")
    
    # Use context manager to safely open and close connection
    with sqlite3.connect("app.db") as conn:
        # Use parameterized queries to prevent SQL Injection
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
        
    return str(rows)

if __name__ == "__main__":
    # Disable debug mode for production security
    app.run(debug=False)
