from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from common import read_json, today_output_dir, today_text
except ImportError:
    from .common import read_json, today_output_dir, today_text


TIMEOUT_SECONDS = 30


def load_json_if_exists(path, default: Any) -> Any:
    if not path.exists():
        return default
    return read_json(path)


def hotspot_title(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    return str(item.get("title") or source.get("name") or item.get("url") or "未命名热点")


def build_summary() -> str:
    output_dir = today_output_dir()
    raw_items = load_json_if_exists(output_dir / "raw_hotspots.json", [])
    top5 = load_json_if_exists(output_dir / "top5_hotspots.json", [])
    drafts = load_json_if_exists(output_dir / "draft_index.json", [])

    failed_items = [item for item in raw_items if not item.get("success")]
    need_manual = [item for item in raw_items if item.get("need_manual_input")]
    high_risk = [item for item in top5 if item.get("risk_level") == "high"]

    lines = [
        f"亚马逊卖家热点日报：{today_text()}",
        "",
        f"抓取来源：{len(raw_items)} 条",
        f"抓取失败：{len(failed_items)} 条",
        f"需要人工补充：{len(need_manual)} 条",
        f"进入内容生成：{len(top5)} 条",
        f"生成草稿：{len(drafts)} 篇",
        f"高风险需核查：{len(high_risk)} 条",
        "",
    ]

    if top5:
        lines.append("今日 TOP 热点：")
        for index, item in enumerate(top5, start=1):
            lines.append(f"{index}. {hotspot_title(item)}（{item.get('score', 0)}分，risk={item.get('risk_level', 'unknown')}）")
    else:
        lines.append("今日没有超过 70 分的热点，未生成可发布草稿。")

    if need_manual:
        lines.extend(["", "需要人工补充的来源："])
        for item in need_manual[:10]:
            source = item.get("source") or {}
            lines.append(f"- {source.get('name') or item.get('url')}：{item.get('error', '抓取结果不足')}")

    lines.extend(
        [
            "",
            f"发布包目录：outputs/{today_text()}/publish_package/",
            "提示：涉及费用、政策、生效日期、封号、账户健康、合规的内容，发布前必须人工核查。",
        ]
    )

    return "\n".join(lines)


def webhook_payload(summary: str) -> dict[str, Any]:
    webhook_type = os.getenv("SUMMARY_WEBHOOK_TYPE", "generic").strip().lower()

    if webhook_type in {"feishu", "lark"}:
        return {"msg_type": "text", "content": {"text": summary}}
    if webhook_type in {"wecom", "wechat_work", "enterprise_wechat"}:
        return {"msgtype": "text", "text": {"content": summary}}
    if webhook_type in {"dingtalk", "dingding"}:
        return {"msgtype": "text", "text": {"content": summary}}

    return {"text": summary}


def send_webhook(summary: str) -> None:
    webhook_url = os.getenv("SUMMARY_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("未配置 SUMMARY_WEBHOOK_URL，本次只在日志输出摘要。")
        print(summary)
        return

    payload = webhook_payload(summary)
    request = Request(
        webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"摘要已发送，HTTP {response.status}")
            if body:
                print(body[:1000])
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"摘要发送失败，HTTP {exc.code}: {body}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"摘要发送失败：{exc}") from exc


def main() -> None:
    summary = build_summary()
    send_webhook(summary)


if __name__ == "__main__":
    main()
