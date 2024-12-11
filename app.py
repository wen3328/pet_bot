from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

# ======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import traceback
# ======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

# 定義 GPT 回應函數
def GPT_response(text):
    try:
        # 使用 ChatCompletion.create 方法呼叫 OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # 確保使用正確的模型名稱
            messages=[
                {"role": "system", "content": "你是寵物專家，幫助飼主判斷寵物問題，回答應簡短明確，盡可能在100~200字內的回應。"},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=200  # 限制回應字數
        )
        print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text  # 使用者輸入訊息
    try:
        GPT_answer = GPT_response(msg)  # 呼叫 GPT_response 函數
        print(GPT_answer)  # 打印回應
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))  # 回傳訊息
    except Exception as e:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('抱歉，目前無法處理您的請求，請稍後再試。'))

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
