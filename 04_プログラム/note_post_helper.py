#!/usr/bin/env python3
"""note投稿補助スクリプト

note.comには投稿用の公式APIが存在せず、非公式APIの直接呼び出しや
エディタへの自動入力（Selenium/Playwright等）は規約違反・アカウント停止の
リスクがあるため採用しない（詳細: 07_セキュリティ確認/note投稿自動化_リスク評価.md）。

このスクリプトが自動化するのは次の2点のみ:
  1. note.comの新規投稿ページをブラウザで自動的に開く（公式ショートカットURL）
  2. タイトル・本文・価格・ハッシュタグをクリップボードに順番にコピーする
     （貼り付け・有料エリア設定・公開操作は手動）

使い方:
    python note_post_helper.py "../03_コンテンツ制作/note記事/第1弾_本文ドラフト.md"
"""

import argparse
import re
import sys
import webbrowser
from dataclasses import dataclass

try:
    import pyperclip
except ImportError:
    sys.exit("pyperclipが必要です。`pip install pyperclip` を実行してください。")

NOTE_NEW_POST_URL = "https://note.com/new"


@dataclass
class DraftContent:
    title: str
    body: str
    price: str
    hashtags: list[str]


def parse_draft(path: str) -> DraftContent:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.splitlines()
    title_line = next(line for line in lines if line.startswith("# "))
    title = title_line.lstrip("#").strip()
    title = re.sub(r"^【.*?】", "", title).strip()

    price_match = re.search(r"想定価格[:：]\s*([0-9,]+)\s*円", text)
    price = price_match.group(1).replace(",", "") if price_match else ""

    hashtag_match = re.search(r"ハッシュタグ[:：]\s*(.+)", text)
    hashtags: list[str] = []
    if hashtag_match:
        raw = hashtag_match.group(1)
        for tag in re.split(r"[,、]", raw):
            tag = tag.strip().lstrip("#")
            if tag:
                hashtags.append(tag)

    marker = "\n---\n"
    body_start = text.find(marker)
    if body_start == -1:
        raise ValueError("本文区切り(---)が見つかりません。ドラフトの形式を確認してください。")
    body = text[body_start + len(marker):].strip()

    # 編集メモ（内部向けの申し送り）は投稿本文に含めない
    body = re.sub(r"\n+### 編集メモ.*", "", body, flags=re.DOTALL).strip()
    # 有料エリアの目印はnote側の機能で設定するため、貼り付け後に手動で削除する目印として残す
    return DraftContent(title=title, body=body, price=price, hashtags=hashtags)


def copy_step(label: str, value: str) -> None:
    input(f"\n{label}をクリックしてからEnterを押してください（クリップボードにコピーします）> ")
    pyperclip.copy(value)
    print(f"クリップボードにコピーしました。Ctrl+Vで貼り付けてください。\n  → {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="note投稿補助（ブラウザを開き、クリップボードにコピーするだけ）")
    parser.add_argument("file", help="本文ドラフトのMarkdownファイルパス")
    args = parser.parse_args()

    draft = parse_draft(args.file)

    print("noteの新規投稿ページを開きます...")
    webbrowser.open(NOTE_NEW_POST_URL)

    copy_step("タイトル欄", draft.title)
    copy_step("本文欄", draft.body)
    print("\n本文中の「▼ここから先は有料エリア▼」の位置で、note投稿画面の有料エリア設定機能を使ってください。")

    if draft.price:
        copy_step("価格欄", draft.price)
    else:
        print("\n（ドラフトに想定価格の記載がないため、価格のコピーはスキップします）")

    if draft.hashtags:
        print(f"\nハッシュタグを{len(draft.hashtags)}個、1個ずつコピーします。note側でEnter/Tabで確定しながら進めてください。")
        for i, tag in enumerate(draft.hashtags, start=1):
            copy_step(f"ハッシュタグ欄（{i}/{len(draft.hashtags)}個目: {tag}）", tag)
    else:
        print("\n（ドラフトにハッシュタグの記載がないため、ハッシュタグのコピーはスキップします）")

    print("\n価格設定・有料エリア設定・公開ボタンは、必ずご自身の目で内容を確認してから手動で行ってください。")


if __name__ == "__main__":
    main()
