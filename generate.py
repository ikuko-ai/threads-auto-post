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
医院名：eastone dental（イーストワンデンタル）
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

PROMPTS = [
    ("豆知識", """あなたはeastone dentalのSNS担当者です。
歯科・口腔ケアに関する豆知識を1つ投稿してください。

{clinic}

条件：
- 70〜100文字
- 50代女性が「へえ！」と思える内容
- 親しみやすい口調
- ハッシュタグ・絵文字なし
- 本文のみ出力（説明不要）"""),

    ("共感", """あなたはeastone dentalのSNS担当者です。
50代女性が抱える歯や口の悩みに共感する投稿を書いてください。

{clinic}

条件：
- 100〜150文字
- 「わかります」「ありますよね」「感じていませんか」など共感の言葉を使う
- 悩みに寄り添う温かい口調
- ハッシュタグ・絵文字なし
- 本文のみ出力（説明不要）"""),

    ("教育", """あなたはeastone dentalのSNS担当者です。
50代女性に役立つ歯科知識・治療に関する教育的な投稿を書いてください。

{clinic}

条件：
- 100〜150文字
- 「実は〜」「知っていましたか」など気づきを促す表現を使う
- 親しみやすい口調
- ハッシュタグ・絵文字なし
- 本文のみ出力（説明不要）"""),

    ("価値提供", """あなたはeastone dentalのSNS担当者です。
eastone dentalの治療・サービスの価値を伝える投稿を書いてください。

{clinic}

条件：
- 100〜150文字
- 治療で得られる生活の変化・メリットを具体的に伝える
- 50代女性の「食べる・話す・笑う」生活の質向上にフォーカス
- ハッシュタグ・絵文字なし
- 本文のみ出力（説明不要）"""),

    ("行動促進", """あなたはeastone dentalのSNS担当者です。
50代女性に相談・来院を促す投稿を書いてください。

{clinic}

条件：
- 100〜150文字
- 「一人で悩まないで」「まずはご相談を」など行動を促す言葉を使う
- 敷居を低く、気軽に来院できる雰囲気を出す
- ハッシュタグ・絵文字なし
- 本文のみ出力（説明不要）""")
]

def get_sheets_service():
    creds_info = json.loads(GOOGLE_CREDENTIALS)
    creds = Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def generate_post(prompt_template):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = prompt_template.format(clinic=CLINIC_INFO)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

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

    # 来週分の投稿を生成（今日から7日間）
    today = datetime.now()
    rows = []

    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset + 1)
        date_str = target_date.strftime("%Y/%m/%d")

        for time_str in SCHEDULE:
            post_type, prompt_template = random.choice(PROMPTS)
            print(f"生成中: {date_str} {time_str} [{post_type}]")
            text = generate_post(prompt_template)
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
