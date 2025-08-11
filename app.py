from flask import Flask, request, abort
import os
from dotenv import load_dotenv

# v3 SDK
from linebot.v3.webhook import WebhookHandler, MessageEvent
from linebot.v3.messaging import TextMessageContent, ImageMessageContent
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage

load_dotenv()
app = Flask(__name__)

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(CHANNEL_SECRET)
messaging_api = MessagingApi.from_access_token(CHANNEL_ACCESS_TOKEN)

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

#（任意：画像受信の下地。後で手相解析をここに繋ぐ）
@handler.add(MessageEvent, message=ImageMessageContent)
def on_image(event):
    messaging_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="その手のひら…受け取ったよ。少し待ってて。")]
        )
    )

if __name__ == "__main__":
    app.run()

@app.route("/health")
def health():
    return "ok", 200

