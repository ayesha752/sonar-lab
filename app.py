import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)
DB_PASSWORD = os.environ.get("DB_PASSWORD")


@app.route("/user")
def get_user():
    name = request.args.get("name", "")
    conn = sqlite3.connect("app.db")
    rows = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
    conn.close()
    return str(rows)


if __name__ == "__main__":
    app.run()
