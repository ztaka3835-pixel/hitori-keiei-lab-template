#!/usr/bin/env python3
"""コンテンツ管理・進捗トラッカー

note/Kindle/X向けコンテンツの企画〜公開〜売上を、外部サービス・APIを一切使わず
ローカルのJSONファイルのみで管理するCLIツール。追加費用は発生しない。

使い方:
    python content_tracker.py add-content --title "..." --theme "AI活用術" --platform note --price 980
    python content_tracker.py update-status --id <id> --status 公開済み
    python content_tracker.py log-sale --content-id <id> --views 120 --sales 3 --revenue 3000
    python content_tracker.py list
    python content_tracker.py report
"""

import argparse
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONTENTS_FILE = os.path.join(DATA_DIR, "contents.json")
SALES_FILE = os.path.join(DATA_DIR, "sales.json")
REPORT_DIR = os.path.join(os.path.dirname(BASE_DIR), "05_評価・分析")

STATUSES = ["企画中", "執筆中", "レビュー中", "公開済み"]


@dataclass
class ContentItem:
    id: str
    title: str
    theme: str
    platform: str
    status: str
    price_yen: int
    created_at: str
    published_at: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ContentItem":
        return ContentItem(**data)


@dataclass
class SalesRecord:
    id: str
    content_id: str
    date: str
    views: int
    sales_count: int
    revenue_yen: int

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "SalesRecord":
        return SalesRecord(**data)


class ContentRepository:
    def __init__(self, file_path: str = CONTENTS_FILE):
        self.file_path = file_path
        self.items: List[ContentItem] = []
        self.load()

    def load(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.items = [ContentItem.from_dict(d) for d in raw]
        else:
            self.items = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([i.to_dict() for i in self.items], f, ensure_ascii=False, indent=2)

    def add(self, item: ContentItem) -> None:
        self.load()
        self.items.append(item)
        self.save()

    def update_status(self, content_id: str, status: str, url: Optional[str] = None) -> Optional[ContentItem]:
        self.load()
        item = self.find(content_id)
        if item is None:
            return None
        item.status = status
        if status == "公開済み" and not item.published_at:
            item.published_at = date.today().isoformat()
        if url:
            item.url = url
        self.save()
        return item

    def find(self, content_id: str) -> Optional[ContentItem]:
        for item in self.items:
            if item.id == content_id:
                return item
        return None

    def list_all(self) -> List[ContentItem]:
        self.load()
        return self.items


class SalesRepository:
    def __init__(self, file_path: str = SALES_FILE):
        self.file_path = file_path
        self.records: List[SalesRecord] = []
        self.load()

    def load(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.records = [SalesRecord.from_dict(d) for d in raw]
        else:
            self.records = []

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.records], f, ensure_ascii=False, indent=2)

    def add(self, record: SalesRecord) -> None:
        self.load()
        self.records.append(record)
        self.save()

    def list_by_content(self, content_id: str) -> List[SalesRecord]:
        self.load()
        return [r for r in self.records if r.content_id == content_id]


class ReportGenerator:
    def __init__(self, content_repo: ContentRepository, sales_repo: SalesRepository):
        self.content_repo = content_repo
        self.sales_repo = sales_repo

    def flag_underperforming(self, min_revenue_yen: int = 1000) -> List[ContentItem]:
        flagged = []
        for item in self.content_repo.list_all():
            if item.status != "公開済み":
                continue
            records = self.sales_repo.list_by_content(item.id)
            total_revenue = sum(r.revenue_yen for r in records)
            if total_revenue < min_revenue_yen:
                flagged.append(item)
        return flagged

    def build_revenue_report(self) -> str:
        items = self.content_repo.list_all()
        lines = ["# 売上分析レポート", ""]
        lines.append(f"作成日: {date.today().isoformat()}")
        lines.append("")
        lines.append("| タイトル | プラットフォーム | ステータス | 累計PV | 累計販売数 | 累計売上(円) |")
        lines.append("|---|---|---|---|---|---|")

        total_revenue = 0
        for item in items:
            records = self.sales_repo.list_by_content(item.id)
            views = sum(r.views for r in records)
            sales = sum(r.sales_count for r in records)
            revenue = sum(r.revenue_yen for r in records)
            total_revenue += revenue
            lines.append(
                f"| {item.title} | {item.platform} | {item.status} | {views} | {sales} | {revenue} |"
            )

        lines.append("")
        lines.append(f"**合計売上: {total_revenue}円**（目標: 100,000円/月）")

        flagged = self.flag_underperforming()
        if flagged:
            lines.append("")
            lines.append("## 要改善（売上が伸びていないコンテンツ）")
            for item in flagged:
                lines.append(f"- {item.title}（{item.platform}） - 売れない理由を評価者役として分析すること")

        return "\n".join(lines)

    def build_progress_report(self) -> str:
        items = self.content_repo.list_all()
        lines = ["# 進捗レポート", "", f"作成日: {date.today().isoformat()}", ""]
        for status in STATUSES:
            count = len([i for i in items if i.status == status])
            lines.append(f"- {status}: {count}件")
        return "\n".join(lines)


def cmd_add_content(args) -> None:
    repo = ContentRepository()
    item = ContentItem(
        id=str(uuid.uuid4())[:8],
        title=args.title,
        theme=args.theme,
        platform=args.platform,
        status="企画中",
        price_yen=args.price,
        created_at=date.today().isoformat(),
    )
    repo.add(item)
    print(f"登録しました: id={item.id} title={item.title}")


def cmd_update_status(args) -> None:
    if args.status not in STATUSES:
        raise SystemExit(f"statusは次のいずれかにしてください: {STATUSES}")
    repo = ContentRepository()
    item = repo.update_status(args.id, args.status, url=args.url)
    if item is None:
        raise SystemExit(f"id={args.id} が見つかりません")
    print(f"更新しました: id={item.id} status={item.status} url={item.url}")


def cmd_log_sale(args) -> None:
    content_repo = ContentRepository()
    if content_repo.find(args.content_id) is None:
        raise SystemExit(f"content_id={args.content_id} が見つかりません")
    sales_repo = SalesRepository()
    record = SalesRecord(
        id=str(uuid.uuid4())[:8],
        content_id=args.content_id,
        date=args.date or date.today().isoformat(),
        views=args.views,
        sales_count=args.sales,
        revenue_yen=args.revenue,
    )
    sales_repo.add(record)
    print(f"売上を記録しました: content_id={args.content_id} revenue={args.revenue}円")


def cmd_daily_update(args) -> None:
    cmd_log_sale(args)
    cmd_report(args)


def cmd_list(_args) -> None:
    repo = ContentRepository()
    for item in repo.list_all():
        print(f"[{item.id}] {item.title} ({item.platform}) - {item.status}")


def cmd_report(_args) -> None:
    content_repo = ContentRepository()
    sales_repo = SalesRepository()
    generator = ReportGenerator(content_repo, sales_repo)

    os.makedirs(REPORT_DIR, exist_ok=True)
    filename = f"売上分析レポート_{date.today().strftime('%Y%m')}.md"
    path = os.path.join(REPORT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(generator.build_revenue_report())
        f.write("\n\n")
        f.write(generator.build_progress_report())
        f.write("\n")
    print(f"レポートを出力しました: {path}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="コンテンツ管理・進捗トラッカー")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add-content", help="新しいコンテンツを登録する")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--theme", required=True)
    p_add.add_argument("--platform", required=True, choices=["note", "Kindle", "X", "blog"])
    p_add.add_argument("--price", type=int, default=0)
    p_add.set_defaults(func=cmd_add_content)

    p_status = sub.add_parser("update-status", help="ステータスを更新する")
    p_status.add_argument("--id", required=True)
    p_status.add_argument("--status", required=True)
    p_status.add_argument("--url", default=None, help="公開後の記事URL（任意）")
    p_status.set_defaults(func=cmd_update_status)

    p_sale = sub.add_parser("log-sale", help="売上・PVを記録する")
    p_sale.add_argument("--content-id", required=True)
    p_sale.add_argument("--views", type=int, default=0)
    p_sale.add_argument("--sales", type=int, default=0)
    p_sale.add_argument("--revenue", type=int, default=0)
    p_sale.add_argument("--date", default=None)
    p_sale.set_defaults(func=cmd_log_sale)

    p_daily = sub.add_parser("daily-update", help="売上・PVの記録とレポート生成を1コマンドで行う")
    p_daily.add_argument("--content-id", required=True)
    p_daily.add_argument("--views", type=int, default=0)
    p_daily.add_argument("--sales", type=int, default=0)
    p_daily.add_argument("--revenue", type=int, default=0)
    p_daily.add_argument("--date", default=None)
    p_daily.set_defaults(func=cmd_daily_update)

    p_list = sub.add_parser("list", help="登録済みコンテンツ一覧を表示する")
    p_list.set_defaults(func=cmd_list)

    p_report = sub.add_parser("report", help="売上・進捗レポートを生成する")
    p_report.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
