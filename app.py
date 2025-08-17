import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, jsonify, request

# Load variables from .env file
load_dotenv()

# --- Create the Flask App ---
app = Flask(__name__)

# --- Database Functions ---

def get_db_connection():
    """Establishes a connection to the database."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return conn

def add_log_entry(conn, user_message, ai_response):
    """Inserts a new log entry."""
    INSERT_LOG_ENTRY = "INSERT INTO conversation_logs (timestamp, user_message, ai_response) VALUES (%s, %s, %s);"
    with conn.cursor() as cur:
        timestamp = datetime.now()
        cur.execute(INSERT_LOG_ENTRY, (timestamp, user_message, ai_response))
    conn.commit()

def get_all_logs(conn):
    """Fetches all log entries from the database."""
    with conn.cursor() as cur:
        cur.execute("SELECT id, timestamp, user_message, ai_response FROM conversation_logs ORDER BY timestamp DESC;")
        # Fetch all rows from the query
        logs_raw = cur.fetchall()
        # Get column names from the cursor description
        column_names = [desc[0] for desc in cur.description]
        # Format the data as a list of dictionaries for easy JSON conversion
        logs_formatted = []
        for log in logs_raw:
            logs_formatted.append(dict(zip(column_names, log)))
        return logs_formatted

# --- API Endpoints / Routes ---

@app.route("/add_log", methods=['POST'])
def add_log_route():
    """API endpoint to add a new log."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"status": "error", "message": "Missing 'message' in request body"}), 400
    
    user_message = data['message']
    conn = None
    try:
        conn = get_db_connection()
        ai_response_placeholder = "This is a placeholder AI response."
        add_log_entry(conn, user_message, ai_response_placeholder)
        return jsonify({"status": "success", "message": "Log added!", "your_message": user_message}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route("/get_logs", methods=['GET'])
def get_logs_route():
    """API endpoint to retrieve all logs."""
    conn = None
    try:
        conn = get_db_connection()
        all_logs = get_all_logs(conn)
        return jsonify(all_logs), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

# --- Main Execution Block ---

if __name__ == "__main__":
    app.run(debug=True)