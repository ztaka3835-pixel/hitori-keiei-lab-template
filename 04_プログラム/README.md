# 支援ツール

いずれも追加費用ゼロ、ローカル完結のPython CLIツール。`data/`フォルダは初回実行時に自動生成される（リポジトリには含めない＝個人の売上データを誤って公開しないため）。

## content_tracker.py
コンテンツの企画〜公開〜売上をローカルのJSONファイルだけで管理する。

```
python content_tracker.py add-content --title "..." --theme "..." --platform note --price 980
python content_tracker.py update-status --id <id> --status 公開済み
python content_tracker.py log-sale --content-id <id> --views 120 --sales 3 --revenue 3000
python content_tracker.py report
```

## x_post_helper.py
X(旧Twitter)の公式Web Intent機能を使い、投稿文を入力済みの状態で投稿画面を開くだけのツール。実際に投稿ボタンを押すのは必ず手動（自動投稿・自動ログインは行わない）。

```
python x_post_helper.py "../03_コンテンツ制作/X投稿/posts/post1_自己紹介.txt"
python x_post_helper.py --next
```

## note_post_helper.py
note.comの新規投稿ページを自動で開き、タイトル・本文・価格・ハッシュタグを順番にクリップボードにコピーする。貼り付け・公開操作は必ず手動（`pip install pyperclip`が必要）。

```
python note_post_helper.py "../03_コンテンツ制作/note記事/第1弾_本文ドラフト.md"
```

## なぜ「開く」「コピーする」までしか自動化しないか
投稿ボタンを自動で押す・自動ログインする実装は、各プラットフォームの規約違反やアカウント停止のリスクがあるため採用していない。最終確認・実行は必ず人間が行う設計にしている。
