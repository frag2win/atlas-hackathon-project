import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from werkzeug.exceptions import BadRequest

# Load variables from .env file
load_dotenv()

# --- Configurations ---
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
    raise ValueError("❌ No Hugging Face API keys (HF_TOKEN_1, etc.) found in .env file!")

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

# --- Simple In-Memory Cache ---
DEBATE_CACHE = {}
CACHE_EXPIRATION_MINUTES = 60

# --- ROLE PROMPTS ---
ROLE_PROMPTS = {
    "tech_optimist": "You are a visionary technologist. Argue for AI’s potential...",
    "ai_ethicist": "You are a cautious AI ethics researcher. Argue for safety...",
    "bias_auditor": "You are an impartial Bias Auditor. Analyze debate bias...",
    "moderator": "You are a skilled debate moderator. Provide a balanced summary...",
    "osint_analyst": (
        "You are a world-class Open-Source Intelligence (OSINT) analyst. "
        "Present your findings in the first person. Your report must be structured "
        "with the following four sections: "
        "1. 'Sources I Have Analyzed', "
        "2. 'Author and Publication Credibility Assessment', "
        "3. 'Legitimacy of the Information', "
        "4. 'Final Conclusion'."
    ),
    "generic_agent": "You are a helpful AI assistant."
}

# --- Helper Functions ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def add_log_entry(conn, user_message, ai_response):
    INSERT_LOG_ENTRY = "INSERT INTO conversation_logs (timestamp, user_message, ai_response) VALUES (?, ?, ?);"
    with conn:
        timestamp = datetime.now().isoformat()
        conn.execute(INSERT_LOG_ENTRY, (timestamp, user_message, ai_response))

def call_ai_agent(model_id, system_prompt, user_message, max_tokens=1024):
    """
    Calls the Hugging Face API using a pool of tokens with fallback logic.
    Handles different response formats safely.
    """
    for i, token in enumerate(hf_tokens):
        print(f"Attempting to call AI with token #{i + 1}...")
        try:
            client = InferenceClient(model=model_id, token=token)
            completion = client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
            )

            # 🔎 Debug print
            print("🔍 Raw completion object:", completion)

            # Handle OpenAI-style dict
            if hasattr(completion, "choices") and completion.choices:
                choice = completion.choices[0]
                if isinstance(choice, dict) and "message" in choice:
                    return choice["message"].get("content", "")
                if hasattr(choice, "message"):
                    return choice.message.get("content", "")

            # Handle HuggingFace text style
            if hasattr(completion, "generated_text"):
                return completion.generated_text

            return str(completion)

        except HfHubHTTPError as e:
            if e.response.status_code in [402, 429]:
                print(f"⚠️ Token #{i + 1} failed: {e}. Trying next token.")
                continue
            else:
                raise e
    raise Exception("All available API tokens have failed.")

def get_article_content(topic: str) -> str:
    """Fetches and reads articles, with a fallback to headlines."""
    if not news_api_key or not jina_api_key:
        print("⚠️ OSINT keys not found. Disabling evidence gathering.")
        return "OSINT evidence gathering is disabled due to missing API keys."
        
    print(f"Fetching and reading articles for topic: {topic}")
    try:
        news_url = (f"https://newsapi.org/v2/everything?q={topic}&sortBy=relevancy&pageSize=3&apiKey={news_api_key}")
        news_response = requests.get(news_url)
        news_response.raise_for_status()
        articles = news_response.json().get("articles", [])
        if not articles: 
            return "No relevant articles found."

        full_text, headlines = "", ""
        for article in articles:
            headlines += f"- Headline: '{article['title']}' (Source: {article['source']['name']})\n"
            url = article['url']
            reader_url = f"https://r.jina.ai/{url}"
            headers = {"Authorization": f"Bearer {jina_api_key}"}
            try:
                content_response = requests.get(reader_url, headers=headers, timeout=20)
                if content_response.ok:
                    soup = BeautifulSoup(content_response.text, 'html.parser')
                    full_text += (
                        f"--- ARTICLE START ---\n"
                        f"SOURCE: {article['source']['name']}\n"
                        f"HEADLINE: {article['title']}\n"
                        f"AUTHOR: {article.get('author', 'Not specified')}\n\n"
                        f"CONTENT:\n{soup.get_text()}\n"
                        f"--- ARTICLE END ---\n\n"
                    )
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not read URL {url}: {e}")
        
        if not full_text:
            print("⚠️ Web Reader failed. Falling back to using headlines only.")
            return f"Here is a summary of recent news headlines:\n{headlines}"
            
        return full_text
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not fetch news headlines: {e}")
        return "Could not retrieve any news articles."

def get_json_from_request():
    try:
        return request.get_json(force=True)
    except BadRequest:
        raw_data = request.get_data(as_text=True)
        print(f"🚨 FAILED TO PARSE JSON. RAW REQUEST DATA:\n---\n{raw_data}\n---")
        return None

# --- API Endpoints ---
@app.route("/", methods=['GET'])
def welcome():
    return jsonify({"status": "success", "message": "Welcome to the ATLAS API Server!"}), 200

@app.route("/analyze_topic", methods=['POST'])
def analyze_topic():
    data = get_json_from_request()
    if not data or 'topic' not in data:
        return jsonify({"status": "error", "message": "Request body must be valid JSON and include 'topic'"}), 400

    topic = data['topic']
    model_key = data.get("model", DEFAULT_MODEL)
    model_id = SUPPORTED_MODELS.get(model_key)
    if not model_id:
        return jsonify({"status": "error", "message": f"Model '{model_key}' not supported."}), 400

    try:
        article_text = get_article_content(topic)
        system_prompt = ROLE_PROMPTS["osint_analyst"]
        user_message = f"Here is the topic for analysis: '{topic}'.\n\nHere are the source articles I have retrieved:\n{article_text}"
        report = call_ai_agent(model_id, system_prompt, user_message)
        
        with get_db_connection() as conn:
            add_log_entry(conn, f"OSINT Analysis on: {topic}", report)

        return jsonify({"status": "success", "osint_report": report}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/run_debate", methods=['POST'])
def run_debate():
    data = get_json_from_request()
    if not data or 'topic' not in data:
        return jsonify({"status": "error", "message": "Request body must be valid JSON and include 'topic'"}), 400

    topic = data['topic']
    model_key = data.get("model", DEFAULT_MODEL)
    model_id = SUPPORTED_MODELS.get(model_key)
    if not model_id:
        return jsonify({"status": "error", "message": f"Model '{model_key}' not supported."}), 400

    cache_key = f"{topic}_{model_key}"
    if cache_key in DEBATE_CACHE:
        cached_data = DEBATE_CACHE[cache_key]
        if datetime.now() < cached_data['timestamp'] + timedelta(minutes=CACHE_EXPIRATION_MINUTES):
            print(f"✅ Returning cached result for topic: '{topic}'")
            return jsonify(cached_data['response'])

    try:
        article_text = get_article_content(topic)
        
        debate_transcript = {}
        debaters = {"tech_optimist": ROLE_PROMPTS["tech_optimist"], "ai_ethicist": ROLE_PROMPTS["ai_ethicist"]}
        for role, system_prompt in debaters.items():
            user_message = (f"Here is the content of relevant articles:\n{article_text}\n\n"
                            f"Based on this evidence and your role as the {role.replace('_', ' ')}, "
                            f"what is your opening statement on the topic of: '{topic}'?")
            ai_response = call_ai_agent(model_id, system_prompt, user_message)
            debate_transcript[role] = ai_response
        
        transcript_for_audit = f"Debate Topic: '{topic}'.\n\n"
        for role, statement in debate_transcript.items():
            transcript_for_audit += f"--- STATEMENT FROM: {role.replace('_', ' ').title()} ---\n{statement}\n\n"
        audit_report = call_ai_agent(model_id, ROLE_PROMPTS["bias_auditor"], transcript_for_audit)

        text_for_moderator = (f"DEBATE TRANSCRIPT:\n{transcript_for_audit}\n\nBIAS AUDIT REPORT:\n{audit_report}")
        final_synthesis = call_ai_agent(model_id, ROLE_PROMPTS["moderator"], text_for_moderator)
        
        response_data = {
            "status": "success",
            "debate_transcript": debate_transcript,
            "audit_report": audit_report,
            "final_synthesis": final_synthesis
        }
        DEBATE_CACHE[cache_key] = {"timestamp": datetime.now(), "response": response_data}
        print(f"✅ Stored new result in cache for topic: '{topic}'")

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Main Execution Block ---
if __name__ == "__main__":
    if not os.path.exists(DATABASE_FILE):
        print("Database not found. Please run 'python init_db.py' to create it.")
    else:
        app.run(debug=True, port=5000)
