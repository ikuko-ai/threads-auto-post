# 投稿文から「投稿文以外のもの」（AIが付け足す文字数表記・見出し・区切り線など）を取り除く。
# generate.py（シートに書く前）と post.py（Threadsに送る直前）の両方で通す二重の防御。
import re

# 数字＋「文字/字」の文字数表記（例：全68文字・文字数：68字・約70字程度）
_COUNT = r"(?:全|本文|合計|計)?\s*(?:文字数)?\s*[:：]?\s*約?\s*[0-9０-９]+\s*(?:文字|字)(?:程度|以内)?"

# 行まるごとが文字数表記（括弧つき・括弧なし）
_COUNT_LINE = re.compile(rf"^[（(【\[〔<＜]?\s*{_COUNT}\s*[)）】\]〕>＞]?$")
# 「文字数：68」のように単位なしで始まる行
_COUNT_LABEL_LINE = re.compile(r"^[（(【\[]?\s*(?:全|本文)?文字数\s*[:：].*$")
# 文中・行末に括弧つきで付いた文字数表記（例：「〜大切です。（全68文字）」）
_COUNT_INLINE = re.compile(rf"\s*[（(【\[〔]\s*{_COUNT}\s*[)）】\]〕]")
# 区切り線
_RULE_LINE = re.compile(r"^[-—―ー=＝_＿*＊・]{3,}$")


def clean_post_text(text):
    """投稿文以外の付け足し（文字数表記・markdown見出し・区切り線）を除去して返す"""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if _COUNT_LINE.match(s) or _COUNT_LABEL_LINE.match(s) or _RULE_LINE.match(s):
            continue
        lines.append(_COUNT_INLINE.sub("", line).rstrip())
    out = "\n".join(lines).strip()
    # 除去で生じた3行以上の空行を1行空きにまとめる
    return re.sub(r"\n{3,}", "\n\n", out)
