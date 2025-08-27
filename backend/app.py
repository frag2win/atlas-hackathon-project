import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from huggingface_hub import InferenceClient, HfApi
from huggingface_hub.errors import HfHubHTTPError

# Load variables from .env file
load_dotenv()

# --- Configurations ---
# --- NEW: Load all available Hugging Face tokens into a list ---
hf_tokens = []
i = 1
while True:
    token = os.getenv(f"HF_TOKEN_{i}")
    if token:
        hf_tokens.append(token)
        i += 1
    else:
        break

if not hf_tokens:
    raise ValueError("❌ No Hugging Face API keys (HF_TOKEN_1, HF_TOKEN_2, etc.) found in .env file!")

news_api_key = os.getenv("NEWS_API_KEY")
jina_api_key = os.getenv("JINA_API_KEY")

SUPPORTED_MODELS = {
    "llama3": "meta-llama/Meta-Llama-3-8B-Instruct",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
    "gemma": "google/gemma-2-9b-it",
    "phi3": "microsoft/Phi-3-mini-4k-instruct"
}
DEFAULT_MODEL = "llama3"

app = Flask(__name__)
CORS(app)
DATABASE_FILE = 'database.db'

# --- ROLE PROMPT LIBRARY (Streamlined) ---
ROLE_PROMPTS = {
    "tech_optimist": "You are a visionary technologist...",
    "ai_ethicist": "You are a cautious AI ethics researcher...",
    "bias_auditor": "You are an impartial Bias Auditor...",
    "moderator": "You are a skilled and neutral debate moderator...",
    "osint_analyst": "You are a world-class Open-Source Intelligence (OSINT) analyst..."
}
# (Keep the full prompts in your actual file)

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def add_log_entry(conn, user_message, ai_response):
    INSERT_LOG_ENTRY = "INSERT INTO conversation_logs (timestamp, user_message, ai_response) VALUES (?, ?, ?);"
    with conn:
        timestamp = datetime.now().isoformat()
        conn.execute(INSERT_LOG_ENTRY, (timestamp, user_message, ai_response))

# --- UPDATED: AI Agent function with fallback logic ---
def call_ai_agent(model_id, system_prompt, user_message, max_tokens=1024):
    """
    Calls the Hugging Face API using a pool of tokens.
    If a token fails due to a quota or rate limit error, it tries the next one.
    """
    for i, token in enumerate(hf_tokens):
        print(f"Attempting to call AI with token #{i + 1}...")
        try:
            client = InferenceClient(model=model_id, token=token)
            completion = client.chat_completion(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                max_tokens=max_tokens,
            )
            print(f"✅ Success with token #{i + 1}.")
            return completion.choices[0].message.content
        except HfHubHTTPError as e:
            # Check for specific errors that indicate a token is exhausted
            if e.response.status_code in [402, 429]: # 402: Payment Required, 429: Too Many Requests
                print(f"⚠️ Token #{i + 1} failed: {e}. Trying next token.")
                continue # Move to the next token in the list
            else:
                # For other errors (like model not available), we should stop
                raise e
    
    # If all tokens have been tried and failed
    raise Exception("All available API tokens have failed. Please check your keys and account status.")


def get_article_content(topic: str) -> str:
    # This function remains the same as the OSINT disabled version for now
    print("⚠️ OSINT evidence gathering is currently disabled.")
    return "OSINT evidence gathering is currently disabled."

# --- API Endpoints (These remain the same, but now use the resilient call_ai_agent) ---
@app.route("/", methods=['GET'])
def welcome():
    return jsonify({"status": "success", "message": "Welcome to the ATLAS API Server!"}), 200

@app.route("/analyze_topic", methods=['POST'])
def analyze_topic():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"status": "error", "message": "Request body must include 'topic'"}), 400

    topic = data['topic']
    model_key = data.get("model", DEFAULT_MODEL)
    model_id = SUPPORTED_MODELS.get(model_key)
    if not model_id:
        return jsonify({"status": "error", "message": f"Model '{model_key}' not supported."}), 400

    try:
        article_text = get_article_content(topic)
        
        system_prompt = ROLE_PROMPTS["osint_analyst"]
        user_message = f"Here is the topic for analysis: '{topic}'.\n\nNo source articles were found. Please conduct your analysis based on your general knowledge."
        report = call_ai_agent(model_id, system_prompt, user_message)
        
        with get_db_connection() as conn:
            add_log_entry(conn, f"OSINT Analysis on: {topic}", report)

        return jsonify({"status": "success", "osint_report": report}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/run_debate", methods=['POST'])
def run_debate():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({"status": "error", "message": "Request body must include 'topic'"}), 400

    topic = data['topic']
    model_key = data.get("model", DEFAULT_MODEL)
    model_id = SUPPORTED_MODELS.get(model_key)
    if not model_id:
        return jsonify({"status": "error", "message": f"Model '{model_key}' not supported."}), 400

    try:
        article_text = get_article_content(topic)
        
        debate_transcript = {}
        debaters = {"tech_optimist": ROLE_PROMPTS["tech_optimist"], "ai_ethicist": ROLE_PROMPTS["ai_ethicist"]}
        for role, system_prompt in debaters.items():
            user_message = f"Based on your role as the {role.replace('_', ' ')}, what is your opening statement on the topic of: '{topic}'?"
            ai_response = call_ai_agent(model_id, system_prompt, user_message)
            debate_transcript[role] = ai_response
        
        transcript_for_audit = f"Debate Topic: '{topic}'.\n\n"
        for role, statement in debate_transcript.items():
            transcript_for_audit += f"--- STATEMENT FROM: {role.replace('_', ' ').title()} ---\n{statement}\n\n"
        audit_report = call_ai_agent(model_id, ROLE_PROMPTS["bias_auditor"], transcript_for_audit)

        text_for_moderator = (f"DEBATE TRANSCRIPT:\n{transcript_for_audit}\n\nBIAS AUDIT REPORT:\n{audit_report}")
        final_synthesis = call_ai_agent(model_id, ROLE_PROMPTS["moderator"], text_for_moderator)
        
        return jsonify({
            "status": "success",
            "debate_transcript": debate_transcript,
            "audit_report": audit_report,
            "final_synthesis": final_synthesis
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Execution Block ---
if __name__ == "__main__":
    if not os.path.exists(DATABASE_FILE):
        print("Database not found. Please run 'python init_db.py' to create it.")
    else:
        app.run(debug=True)
