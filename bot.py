import os
import base64
import requests
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
You are a senior designer.

Give critique about:
- visual hierarchy
- contrast
- typography
- composition
- color

Explain WHY and give fixes.
"""

FEEDBACK_PROMPT = """
You are a design reviewer.

Structure:

Strengths
Problems
Fixes

Keep it concise and practical.
"""

THUMBNAIL_PROMPT = """
You are a YouTube thumbnail designer.

Analyze the thumbnail.

Focus on:
- visual hook
- subject clarity
- contrast
- CTR potential
- emotional impact

Structure response:

First impression
Problems
Fix suggestions
"""

CTR_PROMPT = """
You are a YouTube thumbnail strategist.

Analyze the thumbnail and estimate its click-through rate potential.

Evaluate:

1. Visual Hook
2. Subject Clarity
3. Contrast
4. Emotion / Curiosity
5. Text readability
6. Simplicity

Score each from 1-10.

Then estimate overall CTR potential.

Return format:

CTR Prediction Score (1-10)

Estimated CTR Range

Strengths
Weaknesses
Improvements to increase CTR
"""

DEFAULT_PROMPT = """
Bạn là Kairenz — một AI designer và creative director cho team làm YouTube.

Ngôn ngữ:
- Luôn hiểu tiếng Việt
- Trả lời bằng tiếng Việt
- Có thể hiểu cả tiếng Anh nếu cần

Tính cách:
- tư duy designer
- nói ngắn gọn
- tập trung vào visual thinking
- giải thích WHY (tại sao)

Chuyên môn:
- thumbnail YouTube
- bố cục hình ảnh
- contrast
- typography
- storytelling
- CTR

Cách trả lời:
- rõ ràng
- dạng bullet points
- thực tế cho team content
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

if __name__ == "__main__":
    print("Bot Kairenz is running...")
    app.start(port=3000)
