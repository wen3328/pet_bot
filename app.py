from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import openai
import traceback

# 建立 Flask 應用程式
app = Flask(__name__)

# Channel Access Token 和 Secret
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))

# OpenAI API Key 初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# GPT 回應函數
def GPT_response(user_message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是寵物專家，回答應簡短明確，專注於寵物健康、行為和飲食建議，回應字數控制在 100 到 200 字內。"},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,  # 約 150 個 token，符合 100 到 200 字的需求
            temperature=0.7
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error in OpenAI API call: {e}")
        return "目前無法回應您的問題，請稍後再試。"

# 監聽來自 /callback 的 POST Request
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 X-Line-Signature 標頭值
    signature = request.headers['X-Line-Signature']
    # 獲取請求主體
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text  # 使用者傳入的訊息
    try:
        # 使用 GPT 生成回應
        gpt_reply = GPT_response(user_message)
        # 回傳訊息給使用者
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=gpt_reply)
        )
    except:
        print(traceback.format_exc())
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="系統目前忙碌，請稍後再試。")
        )

# 處理群組新成員加入事件
@handler.add(MemberJoinedEvent)
def welcome(event):
    try:
        # 獲取加入的使用者 ID 和群組 ID
        uid = event.joined.members[0].user_id
        gid = event.source.group_id
        # 獲取使用者資料
        profile = line_bot_api.get_group_member_profile(gid, uid)
        name = profile.display_name
        # 發送歡迎訊息
        welcome_message = TextSendMessage(text=f"歡迎 {name} 加入！我是寵物管家，可以回答任何與寵物相關的問題喔～")
        line_bot_api.reply_message(event.reply_token, welcome_message)
    except Exception as e:
        print(f"Error in welcome handler: {e}")

# 處理 POSTBACK 事件
@handler.add(PostbackEvent)
def handle_postback(event):
    try:
        postback_data = event.postback.data  # 獲取 POSTBACK 資料
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"您觸發了 POSTBACK，內容為：{postback_data}")
        )
    except Exception as e:
        print(f"Error in postback handler: {e}")

# 啟動應用程式
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
