import os
import time
import urllib.request
import urllib.parse
import json
import anthropic

THREADS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID = os.environ["THREADS_USER_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BASE = "https://graph.threads.net/v1.0"

def generate_text():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": """あなたは歯科医院のSNS担当者です。
Threadsに投稿する歯科・口腔ケアに関する豆知識を1つ書いてください。

条件：
- 70〜100文字以内
- 患者さんが「へえ！」と思える内容
- 親しみやすい口調
- ハッシュタグ・絵文字は使わない
- 本文のみ出力（説明不要）"""
            }
        ]
    )
    return message.content[0].text

def post_to_threads(text):
    # コンテナ作成
    url = f"{BASE}/{THREADS_USER_ID}/threads"
    params = urllib.parse.urlencode({
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_TOKEN
    }).encode()
    req = urllib.request.Request(url, data=params, method="POST")
    with urllib.request.urlopen(req) as res:
        container_id = json.loads(res.read())["id"]

    time.sleep(5)

    # 公開
    url = f"{BASE}/{THREADS_USER_ID}/threads_publish"
    params = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": THREADS_TOKEN
    }).encode()
    req = urllib.request.Request(url, data=params, method="POST")
    with urllib.request.urlopen(req) as res:
        post_id = json.loads(res.read())["id"]

    print(f"投稿完了: {post_id}")
    print(f"内容: {text}")

text = generate_text()
post_to_threads(text)
