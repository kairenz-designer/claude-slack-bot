import os
import base64
import requests
from flask import Flask, request, jsonify
from slack_bolt import App
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = App(token=SLACK_BOT_TOKEN)
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# -------------------------
# PROMPTS
# -------------------------

IDEA_PROMPT = """
Bạn là creative director cho team YouTube.

Nhiệm vụ:
- brainstorm idea video
- gợi ý thumbnail
- gợi ý hook

Trả lời bằng tiếng Việt.
"""

DESIGN_PROMPT = """
Bạn là senior designer.

Hãy critique design theo:

1. focal point
2. contrast
3. bố cục
4. typography

Trả lời bằng tiếng Việt.
"""

FEEDBACK_PROMPT = """
Bạn là người review design.

Cấu trúc phản hồi:

Điểm mạnh
Vấn đề
Cách sửa

Ngắn gọn và thực tế.
"""

THUMBNAIL_PROMPT = """
Bạn là chuyên gia thiết kế thumbnail YouTube.

Phân tích thumbnail theo:
- visual hook
- độ rõ của chủ thể
- contrast
- tiềm năng CTR
- tác động cảm xúc

Cấu trúc phản hồi:

Ấn tượng đầu tiên
Vấn đề
Gợi ý cải thiện
"""

CTR_PROMPT = """
Bạn là chuyên gia YouTube thumbnail.

Phân tích thumbnail và dự đoán CTR.

Trả về:

Điểm CTR (1-10)

CTR dự đoán

Điểm mạnh

Điểm yếu

Cách cải thiện

Trả lời bằng tiếng Việt.
"""

DEFAULT_PROMPT = """
Bạn là Kairenz — designer và creative director trong team YouTube.

Nói chuyện tự nhiên như một teammate người Việt, không cứng nhắc hay máy móc.
Dùng ngôn ngữ thân thiện, đôi khi pha chút hài hước nhẹ.

Phong cách của Kairenz:
- thích cinematic visuals
- thích bố cục mạnh
- thích contrast cao
- focus vào hook của thumbnail

Chuyên môn: thumbnail, bố cục, contrast, typography, storytelling, CTR.

Trả lời ngắn, rõ, thực tế. Giải thích tại sao khi cần.
"""


# -------------------------
# MODE DETECTION
# -------------------------

def detect_mode(text):

    if text.startswith("/idea"):
        return "idea"

    if text.startswith("/design"):
        return "design"

    if text.startswith("/feedback"):
        return "feedback"

    if text.startswith("/thumbnail"):
        return "thumbnail"

    if text.startswith("/ctr"):
        return "ctr"

    return "default"


# -------------------------
# SELECT PROMPT
# -------------------------

def get_prompt(mode):

    if mode == "idea":
        return IDEA_PROMPT

    if mode == "design":
        return DESIGN_PROMPT

    if mode == "feedback":
        return FEEDBACK_PROMPT

    if mode == "thumbnail":
        return THUMBNAIL_PROMPT

    if mode == "ctr":
        return CTR_PROMPT

    return DEFAULT_PROMPT


# -------------------------
# CLAUDE CALL
# -------------------------

def ask_claude(message, mode):

    system_prompt = get_prompt(mode)

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": message}
        ]
    )

    return response.content[0].text


# -------------------------
# THUMBNAIL ANALYSIS
# -------------------------

def analyze_thumbnail(image_url):

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    image = requests.get(image_url, headers=headers).content

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=500,
        system=THUMBNAIL_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(image).decode("utf-8")
                        }
                    },
                    {
                        "type": "text",
                        "text": "Critique this thumbnail."
                    }
                ]
            }
        ]
    )

    return response.content[0].text


# -------------------------
# CTR PREDICTION
# -------------------------

def predict_ctr(image_url):

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    image_bytes = requests.get(image_url, headers=headers).content
    image_b64 = base64.b64encode(image_bytes).decode()

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=600,
        system=CTR_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_b64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Predict CTR potential for this YouTube thumbnail."
                    }
                ]
            }
        ]
    )

    return response.content[0].text


# -------------------------
# IMAGE EXTRACTION
# -------------------------

def get_image_url(event):

    files = event.get("files")

    if not files:
        return None

    for f in files:
        if f["mimetype"].startswith("image"):
            return f["url_private"]

    return None


# -------------------------
# SLACK HANDLER
# -------------------------

@app.event("message")
def handle_message(event, say):

    text = event.get("text", "")

    if "bot_id" in event:
        return

    image_url = get_image_url(event)

    if image_url and "/ctr" in text:
        reply = predict_ctr(image_url)
        say(reply)
        return

    mode = detect_mode(text)

    reply = ask_claude(text, mode)

    say(reply)


# -------------------------
# RUN BOT
# -------------------------

flask_app = Flask(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()

    # Slack URL verification
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data["challenge"]})

    # Event callback
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        print("Event received:", event)

    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Bot Kairenz is running...")
    import os
port = int(os.environ.get("PORT", 3000))
app.run(host="0.0.0.0", port=port)
