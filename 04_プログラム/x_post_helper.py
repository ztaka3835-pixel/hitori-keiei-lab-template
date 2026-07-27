#!/usr/bin/env python3
"""X（旧Twitter）投稿補助スクリプト

X公式のAPIは2026年2月に無料枠が廃止され、投稿1件ごとに従量課金される
（$0.015/件、リンク付きは$0.20/件）方式に変わった。本プロジェクトは
「支払いを伴う方法は禁止」のため、有料のAPIは使わない
（詳細: 07_セキュリティ確認/X投稿自動化_リスク評価.md 参照。X関連は非公式APIすら使わず、公式のWeb Intent機能のみ利用）。

このスクリプトが使うのは、Xが「シェアボタン」用に公式に公開している
Web Intent URL（https://twitter.com/intent/tweet?text=...）のみ。
これは長年、外部サイトの「Xでシェア」ボタンなどで広く使われている
公式サポート済みの仕組みであり、非公式API・自動ログイン・スクレイピングとは異なる。
投稿文をあらかじめ入力した状態でXの投稿画面を開くだけで、
実際に「投稿する」ボタンを押すのは必ず手動。

使い方:
    # ファイルを指定して開く
    python x_post_helper.py "../03_コンテンツ制作/X投稿/posts/post1_自己紹介.txt"

    # posts/フォルダの中から、まだ開いていない一番若い番号のポストを自動で選んで開く
    python x_post_helper.py --next
"""

import argparse
import os
import re
import sys
import webbrowser
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(BASE_DIR, "..", "03_コンテンツ制作", "X投稿", "posts")
POSTED_LOG = os.path.join(POSTS_DIR, ".posted.txt")

INTENT_URL = "https://twitter.com/intent/tweet?text={text}"
MAX_LENGTH_WARNING = 280  # 無料アカウントの目安。実際の文字数カウントはX側が最終判定する


def _post_number(filename: str) -> int:
    match = re.match(r"post(\d+)_", filename)
    return int(match.group(1)) if match else 10**9


def load_posted() -> set[str]:
    if not os.path.exists(POSTED_LOG):
        return set()
    with open(POSTED_LOG, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}


def mark_posted(filename: str) -> None:
    with open(POSTED_LOG, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


def find_next_post() -> str | None:
    posted = load_posted()
    candidates = sorted(
        (f for f in os.listdir(POSTS_DIR) if f.endswith(".txt") and f not in posted),
        key=_post_number,
    )
    return os.path.join(POSTS_DIR, candidates[0]) if candidates else None


def open_post(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if len(text) > MAX_LENGTH_WARNING:
        print(f"注意: 本文が{len(text)}文字あります。Xの文字数上限を超える可能性があるので、開いた画面で確認してください。", file=sys.stderr)

    url = INTENT_URL.format(text=quote(text))
    print(f"Xの投稿画面を開きます（{os.path.basename(path)} / 本文は入力済み、投稿ボタンは手動で押してください）...")
    webbrowser.open(url)


def main() -> None:
    parser = argparse.ArgumentParser(description="X投稿補助（公式Web Intentで投稿画面を事前入力状態で開く）")
    parser.add_argument("file", nargs="?", help="投稿文が書かれたテキストファイルのパス")
    parser.add_argument("--next", action="store_true", help="posts/フォルダ内でまだ開いていない一番若い番号のポストを自動で選んで開く")
    args = parser.parse_args()

    if args.next:
        path = find_next_post()
        if path is None:
            print("posts/フォルダに未投稿のポストはありません。")
            return
        open_post(path)
        mark_posted(os.path.basename(path))
        print(f"（{os.path.basename(path)}を投稿済みとして記録しました。実際に投稿ボタンを押さなかった場合は04_プログラム/data/../03_コンテンツ制作/X投稿/posts/.posted.txt から該当行を削除してください）")
    elif args.file:
        open_post(args.file)
    else:
        parser.error("file を指定するか、--next を指定してください")


if __name__ == "__main__":
    main()
