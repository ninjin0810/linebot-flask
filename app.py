from flask import Flask, request, abort
import os
from dotenv import load_dotenv

# v3 SDK
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, Configuration
from linebot.v3 import ApiClient  # ApiClient はここ

load_dotenv()
app = Flask(__name__)

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# ✅ v3の正しい初期化
handler = WebhookHandler(CHANNEL_SECRET)
config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
messaging_api = MessagingApi(ApiClient(config))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def on_text(event):
    user_text = event.message.text
    messaging_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=f"掌の中の人は聞いている…「{user_text}」")]
        )
    )

@handler.add(MessageEvent, message=ImageMessageContent)
def on_image(event):
    messaging_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="その手のひら…受け取ったよ。少し待ってて。")]
        )
    )

# ヘルスチェック
@app.route("/health")
def health():
    return "ok", 200

if __name__ == "__main__":
    app.run()
