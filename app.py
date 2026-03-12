from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Kairenz Slack Bot Running"

@app.route("/slack/events", methods=["POST"])
def slack_events():

    data = request.json

    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
