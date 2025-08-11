from flask import Flask, request, abort
import os, re, datetime as dt
from dotenv import load_dotenv

# v3 SDK
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage, Configuration
from linebot.v3 import ApiClient

load_dotenv()
app = Flask(__name__)

CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(CHANNEL_SECRET)
config = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
messaging_api = MessagingApi(ApiClient(config))

# --- 占いロジック（星座＋数秘） ---
ZODIAC = [
    ("やぎ座",  (12,22), (1,19)),
    ("みずがめ座",(1,20), (2,18)),
    ("うお座",  (2,19), (3,20)),
    ("おひつじ座",(3,21), (4,19)),
    ("おうし座",(4,20), (5,20)),
    ("ふたご座",(5,21), (6,21)),
    ("かに座",  (6,22), (7,22)),
    ("しし座",  (7,23), (8,22)),
    ("おとめ座",(8,23), (9,22)),
    ("てんびん座",(9,23),(10,23)),
    ("さそり座",(10,24),(11,22)),
    ("いて座",  (11,23),(12,21))
]

def which_zodiac(month: int, day: int) -> str:
    for name, (m1,d1), (m2,d2) in ZODIAC:
        if   (month==m1 and day>=d1) or (month==m2 and day<=d2):
            return name
    # 12/22～1/19以外の端はやぎ座でフォールバック
    return "やぎ座"

def life_path_number(y: int, m: int, d: int) -> int:
    s = sum(int(c) for c in f"{y}{m:02d}{d:02d}" if c.isdigit())
    # マスターナンバー対応したければここで11/22を許可してもOK（今回は1〜9に圧縮）
    while s > 9:
        s = sum(int(c) for c in str(s))
    return s

DATE_PATTERN = re.compile(
    r"(\d{4})[./年\-](\d{1,2})[./月\-](\d{1,2})日?"
)

def build_reading(y:int,m:int,d:int) -> str:
    zodiac = which_zodiac(m,d)
    lp = life_path_number(y,m,d)
    tips = {
        1:"新しいことを始めると運が動く。小さな一歩を。",
        2:"人との“間”が鍵。聞き役に回ると良縁が育つ。",
        3:"軽やかな行動が幸運を連れてくる。遊び心を忘れずに。",
        4:"整える日に。財布や机を整頓すると金運が目を覚ます。",
        5:"予定に余白を。偶然の出会いが次の扉になる。",
        6:"身近な誰かを労わると、巡り巡ってあなたに返る。",
        7:"一人の時間が質を上げる。静けさの中で決めよう。",
        8:"手堅い投資。長期目線が勝ち筋。",
        9:"手放しの妙。古い習慣をひとつ捨てて軽くなる。"
    }
    # “掌の中の人”っぽい文体で
    return (
        f"……見えたよ。きみは **{y}年{m}月{d}日** 生まれ。\n"
        f"手のひらが囁く星は **{zodiac}**、数の響きは **{lp}**。\n\n"
        f"今日の合図：{tips.get(lp,'静かな準備が吉。')}\n"
        f"―― さあ、手のひらの写真も送ってごらん？この線の語りも、続きがある。"
    )

# --- Webhook ---
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
    text = (event.message.text or "").strip()
    m = DATE_PATTERN.search(text)
    if m:
        y, mo, d = map(int, m.groups())
        # 日付の妥当性チェック（雑でもOK）
        try:
            dt.date(y, mo, d)
        except Exception:
            reply = "その生まれ日の形、少し歪んでいるね…… 例：1990-03-10 のように教えて。"
        else:
            reply = build_reading(y, mo, d)
    else:
        reply = (
            "私は“掌の中の人”。\n"
            "生年月日を **1990-03-10** のように教えてごらん。\n"
            "そして手のひらの写真も送って……線たちの声を、訳してあげる。"
        )
    messaging_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
    )

@handler.add(MessageEvent, message=ImageMessageContent)
def on_image(event):
    # まずは受付だけ。後でAI解析をここに接続する
    messaging_api.reply_message(
        ReplyMessageRequest(
            replyToken=event.reply_token,
            messages=[TextMessage(text="その手のひら……受け取ったよ。生年月日を 1990-03-10 のように教えて？")]
        )
    )

# Health/Index
@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    return "掌の中の人：ここにいる。/health は 200 を返す。/callback は LINE からのみ。", 200

if __name__ == "__main__":
    app.run()
