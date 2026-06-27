from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    from common import read_json, today_output_dir, write_json
except ImportError:
    from .common import read_json, today_output_dir, write_json


SCORING_RULES = {
    "profit_impact": {
        "label": "利润影响",
        "max_score": 30,
        "keywords": [
            "佣金",
            "FBA",
            "FBA费用",
            "仓储费",
            "广告费",
            "广告成本",
            "促销成本",
            "退款",
            "退货",
            "现金流",
            "利润",
            "成本",
            "毛利",
            "亏损",
            "配送费",
            "物流费",
            "fee",
            "fees",
            "refund",
            "return",
            "cash flow",
        ],
    },
    "operation_risk": {
        "label": "运营风险",
        "max_score": 20,
        "keywords": [
            "账户健康",
            "账号健康",
            "政策违规",
            "违规",
            "Listing下架",
            "下架",
            "评价合规",
            "评论合规",
            "品牌备案",
            "侵权",
            "封号",
            "账户",
            "账号",
            "合规",
            "政策",
            "审核",
            "suspension",
            "policy",
            "compliance",
            "trademark",
        ],
    },
    "traffic_impact": {
        "label": "流量影响",
        "max_score": 20,
        "keywords": [
            "搜索排名",
            "排名",
            "广告位",
            "视频展示位",
            "Amazon Inspire",
            "Inspire",
            "Posts",
            "Influencer",
            "A+",
            "主图视频",
            "Listing",
            "流量",
            "转化率",
            "点击率",
            "降权",
            "曝光",
            "traffic",
            "ranking",
            "video",
        ],
    },
    "sharing_value": {
        "label": "传播价值",
        "max_score": 20,
        "keywords": [
            "收藏",
            "转发",
            "评论",
            "争议",
            "讨论",
            "避坑",
            "案例",
            "实测",
            "复盘",
            "清单",
            "教程",
            "提醒",
            "爆料",
            "变化",
            "新规",
            "小红书",
            "抖音",
            "公众号",
            "论坛",
            "红人",
            "UGC",
        ],
    },
}

RECENCY_MAX_SCORE = 10
CONTENT_GENERATION_MIN_SCORE = 70

HIGH_RISK_KEYWORDS = {
    "fees": [
        "FBA",
        "FBA费用",
        "仓储费",
        "配送费",
        "佣金",
        "广告费",
        "广告成本",
        "促销成本",
        "退款",
        "退货",
        "现金流",
        "fee",
        "fees",
        "storage",
        "commission",
        "refund",
        "return",
    ],
    "policy": [
        "政策",
        "规则",
        "合规",
        "违规",
        "账户健康",
        "账号健康",
        "封号",
        "暂停销售",
        "Listing下架",
        "下架",
        "评价合规",
        "品牌备案",
        "侵权",
        "AI内容合规",
        "suspension",
        "policy",
        "compliance",
        "trademark",
    ],
    "effective_date": [
        "生效",
        "执行",
        "调整",
        "更新",
        "新规",
        "变化",
        "effective",
        "update",
        "change",
    ],
}


def combine_text(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    return " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("summary") or ""),
            str(source.get("name") or ""),
            str(source.get("platform") or ""),
        ]
    )


def keyword_score(text: str, rule: dict[str, Any]) -> tuple[int, list[str]]:
    keywords = rule["keywords"]
    max_score = int(rule["max_score"])
    matched = sorted({word for word in keywords if word.lower() in text.lower()})

    if not matched:
        return 0, []

    # 命中越多，说明越贴近该维度；保留上限，避免某一维度溢出。
    base_score = max_score * 0.35
    per_keyword_score = max_score * 0.18
    score = min(max_score, round(base_score + len(matched) * per_keyword_score))
    return score, matched


def recency_score(published_at: str) -> tuple[int, str]:
    if not published_at:
        return 3, "未获取到发布时间，保留少量时效分，需人工核查"

    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if not published.tzinfo:
            published = published.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - published.astimezone(timezone.utc)).days
    except (ValueError, TypeError):
        return 3, "发布时间格式无法识别，需人工核查"

    if age_days < 0:
        return 4, "发布时间晚于当前日期，需人工核查"
    if age_days <= 7:
        return 10, f"{age_days}天内的新内容"
    if age_days <= 30:
        return 8, f"{age_days}天内的新内容"
    return 0, f"已超过30天，时效性较弱：{age_days}天"


def source_priority(item: dict[str, Any]) -> int:
    source = item.get("source") or {}
    try:
        return int(source.get("priority") or 0)
    except ValueError:
        return 0


def matched_keywords(text: str, keywords: list[str]) -> list[str]:
    return sorted({word for word in keywords if word.lower() in text.lower()})


def source_urls(item: dict[str, Any]) -> list[str]:
    urls = []
    for value in [item.get("url"), (item.get("source") or {}).get("url")]:
        if value and value not in urls:
            urls.append(str(value))
    return urls


def build_fact_check(item: dict[str, Any], text: str) -> dict[str, Any]:
    fee_matches = matched_keywords(text, HIGH_RISK_KEYWORDS["fees"])
    policy_matches = matched_keywords(text, HIGH_RISK_KEYWORDS["policy"])
    date_matches = matched_keywords(text, HIGH_RISK_KEYWORDS["effective_date"])

    uncertain_points = []
    if fee_matches:
        uncertain_points.append("涉及费用、佣金、广告成本、退款、退货或现金流，必须核查具体站点、类目、费用口径和计算方式。")
    if policy_matches:
        uncertain_points.append("涉及政策、合规、账户健康、封号、下架或侵权，必须核查亚马逊官方政策或后台通知。")
    if date_matches or not item.get("published_at"):
        uncertain_points.append("涉及规则变化或发布时间不明确，必须核查生效日期、适用站点和适用范围。")
    if not source_urls(item):
        uncertain_points.append("缺少可追溯来源链接，发布前必须补充参考来源。")
    if item.get("error"):
        uncertain_points.append(f"抓取存在异常，需人工打开原始页面确认。错误：{item.get('error')}")
    if item.get("need_manual_input"):
        uncertain_points.append("自动抓取结果不足，需要人工补充或确认标题、链接、正文。")

    if fee_matches or policy_matches or date_matches:
        risk_level = "high"
    elif uncertain_points:
        risk_level = "medium"
    else:
        risk_level = "low"

    if risk_level == "high":
        publish_warning = "发布前必须人工核查：该热点涉及费用、政策、生效日期、封号、账户健康或合规等高风险信息。"
    elif risk_level == "medium":
        publish_warning = "发布前需要人工核查：该热点存在来源、时间或正文不完整等不确定点。"
    else:
        publish_warning = "发布前建议快速核查来源和上下文。"

    return {
        "fact_check_required": risk_level in {"high", "medium"},
        "risk_level": risk_level,
        "source_urls": source_urls(item),
        "uncertain_points": uncertain_points,
        "publish_warning": publish_warning,
        "risk_keywords": {
            "fees": fee_matches,
            "policy": policy_matches,
            "effective_date": date_matches,
        },
    }


def score_one(item: dict[str, Any]) -> dict[str, Any]:
    text = combine_text(item)
    details: dict[str, Any] = {}
    total = 0

    for key, rule in SCORING_RULES.items():
        score, matched = keyword_score(text, rule)
        details[key] = {
            "label": rule["label"],
            "score": score,
            "max_score": rule["max_score"],
            "matched_keywords": matched,
        }
        total += score

    recent, recent_reason = recency_score(str(item.get("published_at") or ""))
    details["recency"] = {
        "label": "时效性",
        "score": recent,
        "max_score": RECENCY_MAX_SCORE,
        "reason": recent_reason,
    }
    total += recent

    if not item.get("success"):
        total = max(0, total - 20)
        details["fetch_penalty"] = {
            "label": "抓取失败扣分",
            "score": -20,
            "reason": item.get("error", ""),
        }

    scored = dict(item)
    scored["need_manual_input"] = bool(item.get("need_manual_input", False))
    scored["score"] = min(100, total)
    scored["score_details"] = details
    scored.update(build_fact_check(item, text))
    scored["scoring_version"] = "profit30_risk20_traffic20_share20_recency10"
    return scored


def main() -> None:
    output_dir = today_output_dir()
    raw_path = output_dir / "raw_hotspots.json"
    if not raw_path.exists():
        raise FileNotFoundError("请先运行 scripts/fetch_hotspots.py 生成 raw_hotspots.json")

    items = read_json(raw_path)
    scored = sorted(
        (score_one(item) for item in items),
        key=lambda item: (item["score"], source_priority(item)),
        reverse=True,
    )
    top5 = [item for item in scored if item["score"] > CONTENT_GENERATION_MIN_SCORE][:5]

    write_json(output_dir / "scored_hotspots.json", scored)
    write_json(output_dir / "top5_hotspots.json", top5)

    print("TOP 5 热点:")
    if not top5:
        print(f"没有超过 {CONTENT_GENERATION_MIN_SCORE} 分的热点，今天不进入内容生成。")
        return

    for index, item in enumerate(top5, start=1):
        source = item.get("source") or {}
        title = item.get("title") or source.get("name") or item.get("url")
        print(f"{index}. {item['score']}分 - {title}")


if __name__ == "__main__":
    main()
