# init_db.py
import sqlite3

# Connect to the database file (it will be created if it doesn't exist)
conn = sqlite3.connect('database.db')
print("Database created or opened successfully.")

# Create the table
conn.execute('''
CREATE TABLE conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL
);
''')
print("Table created successfully.")

# Close the connection
conn.close()