from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from common import read_json, today_output_dir, write_json
    from fetch_hotspots import fetch_one
except ImportError:
    from .common import read_json, today_output_dir, write_json
    from .fetch_hotspots import fetch_one


def first_filled(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def summarize_text(text: str, max_length: int = 800) -> str:
    compact = " ".join(text.split())
    return compact[:max_length]


def read_multiline_text() -> str:
    print("请粘贴正文。输入单独一行 END 后结束：")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def prompt_if_empty(label: str, value: str, required: bool = False) -> str:
    if value:
        return value
    while True:
        answer = input(f"{label}: ").strip()
        if answer or not required:
            return answer


def build_manual_record(args: argparse.Namespace) -> dict[str, Any]:
    platform = first_filled(args.platform, "manual")
    source_name = first_filled(args.source_name, "manual_input")
    url = first_filled(args.url)
    title = first_filled(args.title)
    text = first_filled(args.text)
    published_at = first_filled(args.published_at)

    if args.interactive:
        platform = prompt_if_empty("平台，例如 xiaohongshu/douyin/wechat", platform)
        source_name = prompt_if_empty("来源名称", source_name)
        url = prompt_if_empty("链接，可留空", url)
        title = prompt_if_empty("标题", title)
        if not text:
            text = read_multiline_text()
        published_at = prompt_if_empty("发布时间，可留空，例如 2026-06-26", published_at)

    source = {
        "platform": platform,
        "name": source_name,
        "url": url,
        "type": "manual_article",
        "priority": str(args.priority),
    }

    if url and not text:
        fetched = fetch_one(source)
        if fetched.get("success"):
            fetched["source"]["type"] = "manual_article"
            fetched["manual_input"] = True
            return fetched

        return {
            "source": source,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "success": False,
            "title": title,
            "summary": "",
            "published_at": published_at,
            "error": f"手动链接再次抓取失败，请补充正文后重试。原始错误：{fetched.get('error', '')}",
            "manual_input": True,
            "need_manual_input": True,
        }

    return {
        "source": source,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "success": True,
        "title": title or summarize_text(text, 60) or source_name,
        "summary": summarize_text(text),
        "published_at": published_at,
        "error": "",
        "manual_input": True,
        "need_manual_input": False,
        "full_text": text,
    }


def append_record(output_dir: Path, record: dict[str, Any]) -> None:
    raw_path = output_dir / "raw_hotspots.json"
    if raw_path.exists():
        raw_items = read_json(raw_path)
    else:
        raw_items = []

    raw_items.append(record)
    write_json(raw_path, raw_items)

    manual_path = output_dir / "manual_hotspots.json"
    manual_items = read_json(manual_path) if manual_path.exists() else []
    manual_items.append(record)
    write_json(manual_path, manual_items)

    raw_items_dir = output_dir / "raw_items"
    raw_items_dir.mkdir(parents=True, exist_ok=True)
    write_json(raw_items_dir / f"manual_{len(manual_items):03d}.json", record)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="手动补充抓不到的热点链接或正文。")
    parser.add_argument("--url", default="", help="热点链接")
    parser.add_argument("--title", default="", help="热点标题")
    parser.add_argument("--text", default="", help="正文或要分析的内容")
    parser.add_argument("--platform", default="manual", help="平台，例如 xiaohongshu/douyin/wechat")
    parser.add_argument("--source-name", default="manual_input", help="来源名称")
    parser.add_argument("--published-at", default="", help="发布时间，例如 2026-06-26")
    parser.add_argument("--priority", type=int, default=10, help="手动补充内容优先级，默认 10")
    parser.add_argument("--no-interactive", action="store_true", help="不进入问答式录入")
    args = parser.parse_args()
    args.interactive = not args.no_interactive and not any([args.url, args.title, args.text])
    return args


def main() -> None:
    args = parse_args()
    output_dir = today_output_dir()
    record = build_manual_record(args)
    append_record(output_dir, record)

    status = "可进入评分" if record.get("success") else "需要补充正文"
    print(f"已保存手动热点：{record.get('title') or record.get('url')}")
    print(f"状态：{status}")
    print("下一步运行：python scripts/score_hotspots.py")
    print("再运行：python scripts/generate_content.py")


if __name__ == "__main__":
    main()
