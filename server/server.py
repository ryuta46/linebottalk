from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify, abort
import cf_deployment_tracker
import os
import json
import urllib.request, urllib.parse

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)


# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

config_file = open('config.json' , 'r')
config = json.load(config_file)
talk_api_key = config["talkApiKey"]
line_channel_token = config["lineChannelToken"]
line_channel_secret = config["lineChannelSecret"]

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('PORT', 8080))


line_bot_api = LineBotApi(line_channel_token)
handler = WebhookHandler(line_channel_secret)


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    data = {
        "apikey": talk_api_key,
        "query": event.message.text
    }

    data = urllib.parse.urlencode(data).encode("utf-8")
    with urllib.request.urlopen("https://api.a3rt.recruit-tech.co.jp/talk/v1/smalltalk", data=data) as res:
        #response = res.read().decode("utf-8")
        reply_json = json.loads(res.read().decode("unicode_escape"))

        if reply_json['status'] == 0:
            reply = reply_json['results'][0]['reply']
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply))
   


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
