from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Kairenz Slack Bot Running"

@app.route("/slack/events", methods=["POST"])
def slack_events():

    data = request.json

    # Slack URL verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    return jsonify({"ok": True})
