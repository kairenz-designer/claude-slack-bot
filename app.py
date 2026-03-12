from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/slack/events", methods=["POST"])
def slack_events():

    data = request.json

    # Slack URL verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    return jsonify({"ok": True})
