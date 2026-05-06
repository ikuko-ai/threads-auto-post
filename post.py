import os
import time
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
import anthropic

JST = timezone(timedelta(hours=9))
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

THREADS_TOKEN = os.environ["THREADS_ACCESS_TOKEN"]
THREADS_USER_ID = os.environ["THREADS_USER_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
SPREADSHEET_ID = "1UlrXFEHzF4TClneFBVBMJ2Ash8-eZLMM5n5-l0_jFG8"
BASE = "https://graph.threads.net/v1.0"

def get_sheets_service():
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def get_post_from_sheet():
    """スプレッドシートから今日・今の時間の投稿文を取得"""
    service = get_sheets_service()
    sheet = service.spreadsheets()

    now = datetime.now(JST)
    today_str = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M")

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="シート1!A2:F1000"
    ).execute()

    rows = result.get("values", [])

    for i, row in enumerate(rows):
        if len(row) < 4:
            continue
        row_date = row[0]
        row_time = row[1]
        row_status = row[4] if len(row) > 4 else "OK"
        row_text = row[3]
        row_revised = row[5] if len(row) > 5 else ""

        if row_date == today_str and row_time == time_str:
            if row_status == "スキップ":
                print(f"スキップ: {today_str} {time_str}")
                return None

            # 修正後の投稿文があればそちらを使用
            if row_revised.strip():
                return row_revised.strip()
            return row_text.strip()

    print(f"スプレッドシートに該当なし: {today_str} {time_str} → AI生成で投稿")
    return generate_fallback_text()

def generate_fallback_text():
    """スプレッドシートに投稿文がない場合はAIで生成"""
    import random
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompts = [
        "歯科・口腔ケアに関する豆知識を1つ、70〜100文字で書いてください。ハッシュタグ・絵文字なし。本文のみ。",
        "50代女性の歯の悩みに共感する投稿を100〜150文字で書いてください。ハッシュタグ・絵文字なし。本文のみ。",
    ]
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": random.choice(prompts)}]
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

text = get_post_from_sheet()
if text:
    post_to_threads(text)
