from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key 初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# 接收來自 LINE 的 Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    # 取得 X-Line-Signature 標頭
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    # 打印日誌以檢查 Webhook 的請求內容
    print("Received Webhook Body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid Signature Error")
        return jsonify({"status": "error", "message": "Invalid signature"}), 400

    return jsonify({"status": "success"}), 200


# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text  # 從 LINE 獲取使用者訊息
    print("User Message:", user_message)  # 打印日誌檢查使用者輸入

    try:
        # 呼叫 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是寵物專家，回答應簡短明確，控制在 100 字內。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100,  # 控制回應字數
            temperature=0.7
        )
        # 取得回應內容
        ai_reply = response.choices[0].message.get("content", "").strip()
        print("AI Reply:", ai_reply)  # 打印日誌檢查 AI 回應

        # 回覆使用者訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=ai_reply)
        )
    except Exception as e:
        print(f"Error while calling OpenAI API: {e}")
        # 回應錯誤訊息
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="抱歉，我無法回應您的問題，請稍後再試。")
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
