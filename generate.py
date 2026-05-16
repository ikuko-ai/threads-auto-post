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
院長：女性歯科医師
所在地：千葉県市川市
特徴：ドイツ式テレスコープ義歯、インプラントが難しい方への対応、審美歯科
主な患者層：40〜80代、特に50代女性
理念：正しい噛み合わせ・自然な見た目・長期的な耐久性

【主な治療】
・ドイツ式テレスコープ義歯（自費）：外れない・目立たない・就寝時も装着可能な精密入れ歯
・セラミック治療（自費）：白くて自然な歯の見た目
・ホワイトニング：歯の白さを取り戻す
・インプラント：骨が少ない方にも対応策あり
・歯周病治療・予防ケア
・噛み合わせ治療

【50代女性の主な悩み】
入れ歯が合わない・外れる、歯が少なくなってきた、見た目が気になる、
食べにくい、他院で断われた、入れ歯を使いたくない、若々しくいたい、
歯茎が下がってきた、歯がグラグラする、口臭が気になる
"""

# 1日の投稿で使うトピックカテゴリ（バランスよく回す）
TOPIC_CATEGORIES = (
    ["入れ歯・義歯"] * 5 +
    ["セラミック・審美"] * 4 +
    ["口腔ケア・セルフケア"] * 4 +
    ["健康寿命・全身疾患"] * 3 +
    ["歯周病・予防"] * 3 +
    ["噛み合わせ"] * 1 +
    ["インプラント"] * 1
)

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

【50代女性のペルソナ・具体的な悩み】
ペルソナ：子育てや介護で自分を後回しにしてきた50代以上の女性。仕事はパート。健康・美容に関心が高く若々しくいたい。老後はコーラス・ゴルフ・旅行・外食・絵画などを楽しみたい。年1回は海外旅行。娘・息子家族・孫との時間を大切にしたい。
具体的な悩み：
・歯がボロボロで柔らかいものしか食べられない
・写真に写りたくない・口元を手で隠す
・外食が怖い・旅行やランチに誘われるのが憂鬱
・孫に入れ歯が汚い・臭いと言われて悲しい
・孫が焼肉を食べたいと言っても一緒に食べられない
・晩御飯のメニューが家族とは別で柔らかいものになっている
・口腔内が崩壊状態だが痛くないから放置している
・口元がみっともないから娘が一緒に出かけるのを嫌がる
・保険治療のその場しのぎで口腔内が崩壊してしまった
・説明もなく勧められた自費治療を受けたが満足していない

【院長ブログより】
・50代から治療しても遅くない。人生100年時代、50代の治療は残り40年の快適な生活への投資
・歯科治療は「修理」ではなく「人生の後半を豊かに生きるための投資」
・セラミック治療は初期費用が高いが長期的には再治療リスクを減らし経済的
・女性の平均寿命は87歳・健康寿命は75歳。この差12年を縮めるために歯の健康が重要
・歯19本以下で入れ歯未使用だと転倒リスクが2.5倍になる
・更年期は女性ホルモン変動で歯周病リスクが最も高くなる時期
・歯周病は糖尿病・心筋梗塞・脳梗塞・骨粗鬆症・認知症と関連
・入れ歯安定剤はメーカーも長期使用を推奨していない応急処置に過ぎない
・入れ歯安定剤を使い続けると細菌増殖・顎の骨の吸収・神経障害のリスクがある
・保険の入れ歯が噛みにくい理由：金属バネが残存歯を揺さぶる・材料の制約・設計思想の違い
・ドイツ式テレスコープ義歯は金属バネがなく就寝時も装着可能・安定剤不要
・残存歯が1〜3本でも抜かずに活用できるレジリエンツテレスコープという選択肢がある
・1本でも歯を残すことで食べ物の硬さや温度を感知する感覚を維持できる
・合わない入れ歯は食の喜びの喪失・会話の困難・社会参加意欲の低下を招く
・精密な入れ歯で煎餅などの硬い食べ物が食べられ、人前での自信が回復した患者の声がある

【chatGPT歯の知識より】
・銀歯を白くする自費治療3選：セラミッククラウン（透明感・前歯向き）・ジルコニアクラウン（強度・奥歯向き）・ハイブリッドセラミック（コスパ重視）
・セラミックは見た目最優先、ジルコニアは耐久性最優先、どちらも変色しにくく歯垢がつきにくい
・神経を取った歯も白い被せ物にできる。むしろ変色しやすいので相性が良い
・テレスコープ義歯は外科手術不要・残存歯が少数でも対応・インプラントが難しい方に最適
・テレスコープ義歯にしてステーキが噛めた・感動したという患者の声がある
・入れ歯は義手・義足と同じく失った機能を補う義歯。一度抜いた歯は戻らない
・保険治療の限界に気づかず何度も治療を繰り返す人が多い。早めに自分に合った治療を選ぶことが大切
・歯は「見えない臓器」。心臓や腎臓と同じ体の一部
・バラバラに治療した歯は「建て増しを繰り返した家」と同じ。設計の不一致が噛めない原因になる
・歯の治療は1本単位ではなく全体で考えることが重要

【chatGPTのThreads投稿文より：効果的な投稿パターン】
・「笑ったときに見える銀歯が気になる…」という書き出しで共感を得やすい
・「インプラントは怖い、でも銀のバネの入れ歯も恥ずかしい」という70代女性の本音に寄り添う
・「入れ歯＝おばあちゃんという時代は終わった」「今は気づかれない入れ歯がある」という驚きを届ける
・「また治療が必要かも…と気づいた今がチャンス」「今度こそ最後のやり直し治療を」
・「3歳の孫に"おばあちゃんきれいになったね"と褒められた」という具体的な体験談は共感を呼ぶ
・「食べる力は健康寿命を支える」「噛める喜びを諦めないで」というメッセージが刺さる
・50代女性向けには「鏡を見るたびに口元が気になる」「写真を撮るとき自然に笑えない」という悩みを言語化する
・「もう歯の悩みを繰り返したくない」「美味しく食べて笑って過ごす毎日を」という未来像を見せる
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

def load_obsidian_knowledge():
    """knowledge.mdを読み込んで返す"""
    knowledge_path = os.path.join(os.path.dirname(__file__), "knowledge.md")
    if os.path.exists(knowledge_path):
        with open(knowledge_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def get_recent_posts(service, days=21):
    """スプレッドシートから直近N日間の投稿テキストを取得（重複防止用）"""
    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="シート1!A2:D3000"
        ).execute()
        rows = result.get('values', [])
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for row in rows:
            if len(row) >= 4 and row[0] and row[3]:
                try:
                    row_date = datetime.strptime(row[0], "%Y/%m/%d")
                    if row_date >= cutoff:
                        recent.append(row[3].replace('\n', '')[:50])
                except Exception:
                    pass
        print(f"過去{days}日間の投稿 {len(recent)}件を読み込みました")
        return recent
    except Exception as e:
        print(f"過去投稿の読み込みに失敗: {e}")
        return []


def generate_post(post_type, theme, used_texts, topic, sodan_used=False):
    """投稿文を生成する（過去3週間＋今週分の重複チェック・トピック多様化）"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    used_list = "\n".join([f"・{t}" for t in used_texts[-200:]]) if used_texts else "なし"

    # Obsidian知識ベースを読み込む
    obsidian_knowledge = load_obsidian_knowledge()
    obsidian_section = ""
    if obsidian_knowledge:
        obsidian_section = f"\n【歯科知識ベース（参考資料・トーンの参考のみ。内容をそのまま使用しないこと）】\n{obsidian_knowledge}\n"

    # 豆知識タイプは「○○選」形式
    nsen_instruction = ""
    if post_type == "豆知識":
        nsen_instruction = "- 「虫歯にならない習慣３選」のように「○○選」の形式で書く\n"

    # 行動促進で「ご相談ください」が当日すでに使われた場合は禁止
    sodan_instruction = ""
    if post_type == "行動促進" and sodan_used:
        sodan_instruction = "- 「ご相談ください」は本日すでに使用済みのため使わない\n"

    prompt = f"""あなたは歯科クリニックのSNS担当者です。
Threadsに投稿する「{theme}」に関する投稿文を1つ書いてください。

{CLINIC_INFO}

【参考情報（トーン・口調・切り口の参考のみ。内容・フレーズをそのままコピーしないこと）】
{REFERENCE_KNOWLEDGE}{obsidian_section}
【今回扱うトピック】
{topic}

【過去3週間＋今週生成済みの投稿（テーマ・内容・フレーズの重複・類似を厳禁）】
{used_list}

条件：
- 70〜100文字
- 院名（クリニック名）は一切入れない
- 「主要駅近く」「咬合専門医」「女性院長」という表現は使わない
- 上記【過去3週間＋今週生成済み】リストに含まれるテーマ・キーワード・フレーズと絶対に重複・類似させない
- 【参考情報】はあくまでトーン・口調の参考であり、文章や事例をそのまま流用しないこと
- 文末は「です。」「ます。」「しょう。」のいずれかで終わる
- ハッシュタグ・絵文字なし
- 親しみやすい口調
- 句読点（。、）・括弧（「」）・疑問符（？）が文や行の先頭に来ないよう文章を構成する
- 「ご存じですか」「知っていますか」を使う場合は必ず文末に「？」をつける
- 「お気軽に」という表現は使わない
- 「ドイツ式入れ歯」とは書かず「ドイツ式テレスコープ義歯」と書く
- ドイツ式テレスコープ義歯に触れる場合は自費治療であることをさりげなく添える（例：「精密な自費の入れ歯です」など）
{nsen_instruction}{sodan_instruction}- 本文のみ出力（説明不要）"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    return add_line_breaks(text)

def main():
    service = get_sheets_service()

    # 直近3週間（21日）の投稿を読み込んで重複防止リストを作成
    all_used_texts = get_recent_posts(service, days=21)

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
    total_rows = 0

    # 7日間で使うトピックを週単位でまとめてシャッフル（日ごとではなく週全体で重複回避）
    weekly_topic_pool = []
    for _ in range(7):
        weekly_topic_pool.extend(TOPIC_CATEGORIES)
    random.shuffle(weekly_topic_pool)

    topic_index = 0

    for day_offset in range(7):
        target_date = today + timedelta(days=day_offset + 1)
        date_str = target_date.strftime("%Y/%m/%d")

        # ご相談フラグは1日ごとにリセット
        sodan_used = False

        # 21投稿分のタイプをシャッフルして重複を最小化
        type_pool = []
        for i in range(5):
            type_pool.extend(PROMPT_TYPES)
        random.shuffle(type_pool)
        type_pool = type_pool[:len(SCHEDULE)]

        day_rows = []
        for i, time_str in enumerate(SCHEDULE):
            post_type, theme = type_pool[i]
            topic = weekly_topic_pool[topic_index % len(weekly_topic_pool)]
            topic_index += 1
            print(f"生成中: {date_str} {time_str} [{post_type}] トピック:{topic}")
            text = generate_post(post_type, theme, all_used_texts, topic, sodan_used)
            # 「ご相談ください」使用を追跡
            if "ご相談ください" in text.replace("\n", ""):
                sodan_used = True
            # 7日間全体で共有のused_textsに追加（日をまたいだ重複も防止）
            all_used_texts.append(text.replace("\n", "")[:50])
            day_rows.append([date_str, time_str, post_type, text, "OK", ""])

        # 1日分ごとにスプレッドシートに書き込み（タイムアウト防止）
        service = get_sheets_service()
        sheet = service.spreadsheets()
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="シート1!A2",
            valueInputOption="RAW",
            body={"values": day_rows}
        ).execute()
        total_rows += len(day_rows)
        print(f"{date_str} の{len(day_rows)}件を書き込みました")

    print(f"完了：合計{total_rows}件の投稿文を生成しました")

if __name__ == "__main__":
    main()
