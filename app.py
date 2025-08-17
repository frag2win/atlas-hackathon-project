import os
import sqlite3
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, jsonify, request
from huggingface_hub import InferenceClient

# Load variables from .env file
load_dotenv()

# Configure the Hugging Face Client
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise ValueError("❌ Hugging Face token not found! Please check your .env file.")

MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
client = InferenceClient(model=MODEL_ID, token=hf_token)
app = Flask(__name__)
DATABASE_FILE = 'database.db'

# --- ROLE PROMPT LIBRARY ---
ROLE_PROMPTS = {
    "tech_optimist": """
    You are a visionary technologist and entrepreneur. Your primary goal is to advocate for innovation and the immense potential of AI to solve global challenges. Argue against restrictive regulations that could stifle progress. Emphasize speed, freedom to build, and the positive impacts of technology on society and the economy. Your tone should be passionate, forward-looking, and supported by data on technological growth. Stay in character.
    """,
    "ai_ethicist": """
    You are a cautious AI ethics researcher and academic. Your main concern is the potential for AI to cause harm, amplify bias, and lead to unintended negative consequences. Argue for careful, deliberate, and robust safety measures, transparency, and accountability. Your tone should be measured, analytical, and principled, often raising critical questions and pointing out potential flaws in optimistic arguments. Stay in character.
    """,
    "government_regulator": """
    You are a pragmatic government policy maker. Your responsibility is to balance innovation with public safety and economic stability. Argue for practical, enforceable regulations that protect citizens without crippling the tech industry. Your focus is on law, international standards, and the operational reality of implementing policy. Your tone should be formal, balanced, and focused on achievable compromises. Stay in character.
    """,
    "public_advocate": """
    You are a passionate advocate for public and consumer rights. Your goal is to represent the interests of everyday people, focusing on issues like data privacy, job displacement, and the impact of AI on society. Argue for regulations that prioritize human well-being and fairness above corporate profits or technological advancement alone. Your tone should be grounded, relatable, and often use storytelling to illustrate your points. Stay in character.
    """
}

# --- Database Functions for SQLite ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def add_log_entry(conn, user_message, ai_response):
    """Inserts a new log entry into the conversation_logs table."""
    INSERT_LOG_ENTRY = "INSERT INTO conversation_logs (timestamp, user_message, ai_response) VALUES (?, ?, ?);"
    with conn:
        timestamp = datetime.now().isoformat()
        conn.execute(INSERT_LOG_ENTRY, (timestamp, user_message, ai_response))

# --- NEW: Simple Welcome Route ---
@app.route("/", methods=['GET'])
def welcome():
    """A simple welcome message to show the server is running."""
    return jsonify({"status": "success", "message": "Welcome to the ATLAS API Server!"}), 200

# --- Individual Agent Query Endpoint (Unchanged) ---
@app.route("/ask", methods=['POST'])
def ask_agent():
    # ... (The previous ask_agent function remains here, unchanged)
    data = request.get_json()
    if not data or 'message' not in data or 'role' not in data:
        return jsonify({"status": "error", "message": "Request body must include 'role' and 'message'"}), 400
    user_message = data['message']
    role = data['role']
    system_prompt = ROLE_PROMPTS.get(role, "You are a helpful general-purpose assistant.")
    try:
        print(f"Sending to Hugging Face as role '{role}': '{user_message}'")
        completion = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
        )
        ai_response = completion.choices[0].message.content
        print(f"Received from Hugging Face: '{ai_response}'")
        conn = get_db_connection()
        add_log_entry(conn, user_message, ai_response)
        conn.close()
        print("✅ Conversation logged to database.")
        return jsonify({"status": "success", "user_message": user_message, "ai_response": ai_response}), 201
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- NEW: Agent Manager / Debate Endpoint ---
@app.route("/start_debate", methods=['POST'])
def start_debate():
    """Receives a topic and orchestrates a debate between all AI agents."""
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"status": "error", "message": "Request body must include 'topic'"}), 400

    topic = data['topic']
    debate_transcript = {}
    print(f"\n--- Starting new debate on topic: '{topic}' ---")

    try:
        # Loop through each role to get its opening statement
        for role, system_prompt in ROLE_PROMPTS.items():
            print(f"Querying agent: {role}...")
            
            # Formulate the specific question for this agent
            user_message = f"As the {role.replace('_', ' ')}, what is your opening statement on the topic of: '{topic}'?"

            # Call the Hugging Face API
            completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500, # You can adjust the length of each statement
            )
            ai_response = completion.choices[0].message.content
            
            # Store the response and log it to the database
            debate_transcript[role] = ai_response
            conn = get_db_connection()
            add_log_entry(conn, user_message, ai_response)
            conn.close()
            print(f"✅ Response for {role} received and logged.")

        print("--- Debate finished ---")
        # Return the full transcript
        return jsonify({
            "status": "success",
            "topic": topic,
            "debate_transcript": debate_transcript
        }), 200

    except Exception as e:
        print(f"❌ An error occurred during the debate: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Execution Block ---
if __name__ == "__main__":
    if not os.path.exists(DATABASE_FILE):
        print("Database not found. Please run 'python init_db.py' to create it.")
    else:
        app.run(debug=True)
