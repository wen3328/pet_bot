from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# 接收來自 LINE 的 Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({"status": "error", "message": "Invalid signature"}), 400

    return jsonify({"status": "success"}), 200


# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    try:
        # 呼叫 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 替換為正確的模型名稱
            messages=[
                {"role": "system", "content": "你是寵物專家，回答應簡短明確，控制在 50 字內。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=50
        )
        ai_reply = response.choices[0].message.get("content", "抱歉，目前無法生成回應，請稍後再試。")

        # 回覆使用者訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        print(f"Error while calling OpenAI API: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，我無法回應您的問題，請稍後再試。")
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
