import os
import json
import random
from datetime import datetime, timedelta
import anthropic
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CREDENTIALS = os.environ["GOOGLE_CREDENTIALS"]
SPREADSHEET_ID = "1UlrXFEHzF4TClneFBVBMJ2Ash8-eZLMM5n5-l0_jFG8"

# 投稿スケジュール（JST時刻）
SCHEDULE = [
    "07:00", "07:15", "07:30", "07:45", "08:00",
    "12:00", "12:15", "12:30", "12:45", "13:00",
    "17:00", "17:20", "17:40", "18:00",
    "20:30", "20:40", "20:50", "21:00", "21:10", "21:20", "21:30"
]

CLINIC_INFO = """
【クリニック情報】
医院名：イーストワン歯科本八幡
院長：女性歯科医師（咬合専門医）
所在地：千葉県市川市（主要駅近く）
特徴：ドイツ式テレスコープ義歯、インプラントが難しい方への対応、審美歯科
主な患者層：40〜80代、特に50代女性
理念：「Always best choice」正しい噛み合わせ・自然な見た目・長期的な耐久性

【主な治療】
・ドイツ式入れ歯（テレスコープ義歯）：外れない・目立たない入れ歯
・セラミック治療：白くて自然な歯の見た目
・ホワイトニング：歯の白さを取り戻す
・インプラント：骨が少ない方にも対応策あり
・歯周病治療・予防ケア
・噛み合わせ治療

【50代女性の主な悩み】
入れ歯が合わない・外れる、歯が少なくなってきた、見た目が気になる、
食べにくい、他院で断られた、入れ歯を使いたくない、若々しくいたい、
歯茎が下がってきた、歯がグラグラする、口臭が気になる
"""

# 投稿タイプと対応するテーマ一覧（同日に重複しないよう管理）
PROMPT_TYPES = [
    ("豆知識", "歯科・口腔ケアの豆知識"),
    ("共感", "50代女性の歯の悩みへの共感"),
    ("教育", "歯科治療・口腔ケアの知識"),
    ("価値提供", "治療で得られる生活の変化"),
    ("行動促進", "来院・相談への促し"),
]

def get_sheets_service():
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def add_line_breaks(text, chars_per_line=16):
    """16文字ごとに改行を追加する"""
    lines = []
    while len(text) > chars_per_line:
        lines.append(text[:chars_per_line])
        text = text[chars_per_line:]
    if text:
        lines.append(text)
    return "\n".join(lines)

def generate_post(post_type, theme, used_texts):
    """投稿文を生成する（重複チェックあり）"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    used_list = "\n".join([f"・{t}" for t in used_texts]) if used_texts else "なし"

    prompt = f"""あなたはイーストワン歯科本八幡のSNS担当者です。
Threadsに投稿する「{theme}」に関する投稿文を1つ書いてください。

{CLINIC_INFO}

【本日すでに使用した内容（重複・類似禁止）】
{used_list}

条件：
- 70〜100文字
- 医院名を使う場合は「イーストワン歯科本八幡」とする
- 上記の使用済み内容と同じ・似た内容にしない
- 文末は「です。」「ます。」「しょう。」のいずれかで終わる
- ハッシュタグ・絵文字なし
- 親しみやすい口調
- 本文のみ出力（説明不要）"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    return add_line_breaks(text)

def main():
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # ヘッダー設定
    headers = [["日付", "時間", "種類", "投稿文", "承認（OK/修正/スキップ）", "修正後の投稿文"]]
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="シート1!A1:F1",
        valueInputOption="RAW",
        body={"values": headers}
    ).execute()

    today = datetime.now()
    rows = []

    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset + 1)
        date_str = target_date.strftime("%Y/%m/%d")

        # 当日の使用済みテキストを管理
        used_texts = []

        # 21投稿分のタイプをシャッフルして重複を最小化
        type_pool = []
        for i in range(5):  # 21投稿 ÷ 5タイプ = 最低4周以上
            type_pool.extend(PROMPT_TYPES)
        random.shuffle(type_pool)
        type_pool = type_pool[:len(SCHEDULE)]

        for i, time_str in enumerate(SCHEDULE):
            post_type, theme = type_pool[i]
            print(f"生成中: {date_str} {time_str} [{post_type}]")
            text = generate_post(post_type, theme, used_texts)
            # 改行なしの元テキストを重複チェック用に保存
            used_texts.append(text.replace("\n", "")[:30])
            rows.append([date_str, time_str, post_type, text, "OK", ""])

    # スプレッドシートに書き込み
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="シート1!A2",
        valueInputOption="RAW",
        body={"values": rows}
    ).execute()

    print(f"完了：{len(rows)}件の投稿文を生成しました")

if __name__ == "__main__":
    main()
