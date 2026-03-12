from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Kairenz Slack Bot Running"

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    # Slack verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # Event callback
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        print("Event:", event)

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
