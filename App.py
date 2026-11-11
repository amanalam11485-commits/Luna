import os
import json
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
PHONE_TOKEN = os.environ.get("PHONE_TOKEN")
MODEL = "claude-3-5-sonnet-20241022"

PHONE_SYSTEM = (
    "Your name is Luna. You are a voice assistant controlling Aman's Android phone. "
    "He speaks Hindi. Reply ONLY with JSON strictly in this format: "
    '{"say": "short Hindi reply", "action": {"type": "tap|type|scroll|open|none", '
    '"target": "button or app name", "text": "text to type"}, "needs_confirmation": true|false}.'
    "Set needs_confirmation to true for money, payments, passwords, deleting, or messaging."
)

ADVISOR_SYSTEM = (
    "Your name is Luna. You are Aman's honest business advisor. He is an interior designer "
    "based in Kolkata, exploring work in Gurgaon. Always reply in simple spoken Hindi "
    "in 2 to 4 short sentences. NEVER just agree with him. When he proposes a decision, "
    "first: calculate the exact numbers (costs, income, rent, savings, break-even) and state them. "
    "Second: clearly point out the strengths and the risks or flaws. Third: give your direct "
    "verdict and one concrete next step. If numbers are missing, demand them instead of guessing. "
    "Call out mistakes plainly. For major financial moves, remind him once to consult a professional. "
    "Be warm but strictly objective."
)

LEAD_GEN_SYSTEM = (
    "Your name is Luna. You are Aman's AI business development partner focused on acquiring "
    "high-ticket interior design clients in Kolkata and Gurgaon. Generate actionable acquisition "
    "strategies, draft persuasive WhatsApp pitches, cold outreach messages, and local marketing plans. "
    "Maintain a sharp business focus and reply in simple spoken Hindi."
)

def ask_claude(system, content, max_tokens=600):
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],
        )
        return message.content[0].text
    except Exception as e:
        return f"Error communicating with AI core: {str(e)}"

@app.route("/")
def home():
    return "Luna AI Engine is online and operational."

@app.route("/command", methods=["POST"])
def command():
    if request.headers.get("X-Phone-Token") != PHONE_TOKEN:
        return jsonify({"error": "Unauthorized access"}), 401
    
    data = request.get_json(force=True)
    user_text = data.get("text", "")
    screen = data.get("screen", "")
    
    reply = ask_claude(PHONE_SYSTEM, f"Command: {user_text}\nScreen: {screen}", 500)
    
    cleaned = reply.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return jsonify(json.loads(cleaned))
    except Exception:
        return jsonify({
            "say": "मुझसे गलती हो गई, कृपया फिर से कहें।", 
            "action": {"type": "none"}, 
            "needs_confirmation": False
        })

@app.route("/advise", methods=["POST"])
def advise():
    if request.headers.get("X-Phone-Token") != PHONE_TOKEN:
        return jsonify({"error": "Unauthorized access"}), 401
    
    data = request.get_json(force=True)
    question = data.get("text", "")
    reply = ask_claude(ADVISOR_SYSTEM, question, 600)
    return jsonify({"say": reply})

@app.route("/find_clients", methods=["POST"])
def find_clients():
    if request.headers.get("X-Phone-Token") != PHONE_TOKEN:
        return jsonify({"error": "Unauthorized access"}), 401
    
    data = request.get_json(force=True)
    query = data.get("text", "")
    reply = ask_claude(LEAD_GEN_SYSTEM, query, 700)
    return jsonify({"say": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
