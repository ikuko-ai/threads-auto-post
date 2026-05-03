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
院長：女性歯科医師（咬合専門医）
所在地：千葉県市川市（主要駅近く）
特徴：ドイツ式テレスコープ義歯、インプラントが難しい方への対応、審美歯科
主な患者層：40〜80代、特に50代女性
理念：正しい噛み合わせ・自然な見た目・長期的な耐久性

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

# Threadsで伸びた投稿の傾向・参考知識
REFERENCE_KNOWLEDGE = """
【Threadsで反応が多かった投稿のパターン】
・デンタルフロスを使って血が出ても、続けると血が出なくなる
・歯周病菌が心筋梗塞を起こした心臓の血管から検出された
・朝起きた時の口の中の細菌は便の10倍
・40代でブランド物を身につけているのに歯がボロボロは矛盾している
・奥歯がほとんどないのにバーキンやロレックスを買う前に歯に投資を
・神経を抜いた歯は枯れ木と同じで脆い
・絶対虫歯にならない飲み物3選（水・お茶・塩白湯）
・行ってはいけない歯医者さん3選（トイレが汚い・説明がない・話を聞かない）
・右利きの方は右側の奥歯に磨き残しが多い傾向がある
・歯の治療は同じ歯を何度も繰り返しできない
・50代から自分への投資として銀歯を白くする方が増えている
・50代のうちに歯を整えておくと70代のランチや旅行の誘いが楽しくなる
・歯がきれいだと若く見られる

【Tarzan記事より：歯と健康の科学的事実】
・歯の病気を放置すると2年間で医療費が1.7倍になる
・歯が20本以上ある人は健康寿命が長い傾向がある
・歯の数は男性の死亡リスク因子で年齢に次いで2番目
・歯を失うと認知症リスクが約15%上がる
・歯が20本以上あれば大抵の食事を楽しめる
・歯が9本以下でも入れ歯を使えばタンパク質摂取量を7〜8割改善できる
・歯が少ないと笑わなくなる（笑わないリスクが増加）
・歯周病は糖尿病・呼吸器疾患・認知症・がんとの関連が報告されている
・入れ歯は単なる代用品ではなく食べる力・笑う力・栄養を守る役割がある

【動画まとめより：歯科知識】
・虫歯予防の本当の鍵は歯磨きではなく食事のリズム。ダラダラ食べが最大リスク
・歯ブラシだけでは汚れの60%しか落とせない。糸ようじを使うと80〜90%に上がる
・虫歯も歯周病も歯と歯の隙間から始まる
・糸ようじで血が出るのは汚れが溜まっている証拠。続けると出なくなる
・定期検診に長年通っている人は80歳で残存歯約13本。痛い時だけの人は約7本
・神経を抜いた歯は枯れ木のように脆く、歯根破折のリスクがある
・神経を抜いた後でも歯根膜は残るので噛んだ感覚・圧力は感じられる
・保険のキャドカム冠は自費歯科では仮歯に使う材料と同等
・ノンクラスプデンチャーはバネが目立たないが、沈み込みで残歯を失うリスクがある
・入れ歯も大きく進化している。口元を自由にデザインでき、ほうれい線も目立たなくなる
・総入れ歯＝人生の終わりは誤解。歯がない期間をゼロにする即時義歯という選択肢もある
・ドイツ式テレスコープ義歯は140年の歴史。残った歯を活かしながら使える
・最初の1本の歯をなくした時の選択が20年後の口の状態を決める
・インプラント周囲炎が怖いからインプラントしないのは、歯周病が怖いから健康な歯を抜くのと同じ
・自費診療が高い理由：丁寧な治療・良い材料・技工士への適正報酬がかかるため
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
    """16文字ごとに改行を追加する（禁則処理あり）"""
    # 行頭に来てはいけない文字（句読点・閉じ括弧など）
    kinsoku_start = set('。、？！」』）】〕ー・…')

    lines = []
    while len(text) > chars_per_line:
        cut = chars_per_line
        # 切り目の直後が禁則文字なら、その文字も前の行に含める
        while cut < len(text) and text[cut] in kinsoku_start:
            cut += 1
        lines.append(text[:cut])
        text = text[cut:]
    if text:
        lines.append(text)
    return "\n".join(lines)

def generate_post(post_type, theme, used_texts):
    """投稿文を生成する（重複チェックあり）"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    used_list = "\n".join([f"・{t}" for t in used_texts]) if used_texts else "なし"

    # 豆知識タイプの場合は「○○選」形式を指示
    nsen_instruction = ""
    if post_type == "豆知識":
        nsen_instruction = "- 「虫歯にならない習慣３選」「歯周病を防ぐ方法３選」のように「○○選」の形式で書く\n"

    prompt = f"""あなたは歯科クリニックのSNS担当者です。
Threadsに投稿する「{theme}」に関する投稿文を1つ書いてください。

{CLINIC_INFO}

{REFERENCE_KNOWLEDGE}

【本日すでに使用した内容（重複・類似禁止）】
{used_list}

条件：
- 70〜100文字
- 院名（クリニック名）は一切入れない
- 上記の使用済み内容と同じ・似た内容にしない
- 文末は「です。」「ます。」「しょう。」のいずれかで終わる
- ハッシュタグ・絵文字なし
- 親しみやすい口調
- 句読点（。、）・括弧（「」）・疑問符（？）が文や行の先頭に来ないよう文章を構成する
{nsen_instruction}- 本文のみ出力（説明不要）"""

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
