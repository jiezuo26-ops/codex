from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

try:
    from common import clean_filename, read_json, today_output_dir, today_text, write_json
except ImportError:
    from .common import clean_filename, read_json, today_output_dir, today_text, write_json


def remove_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def load_json_if_exists(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return read_json(path)


def hotspot_title(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    return str(item.get("title") or source.get("name") or item.get("url") or "未命名热点")


def hotspot_summary(item: dict[str, Any]) -> str:
    summary = str(item.get("summary") or "").strip()
    if summary:
        return summary
    if item.get("error"):
        return f"自动抓取未拿到正文，需要人工核查。抓取提示：{item.get('error')}"
    return "暂无正文摘要，需要人工补充事实信息。"


def source_text(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    lines = [
        f"- 来源名称：{source.get('name', '')}",
        f"- 来源平台：{source.get('platform', '')}",
        f"- 来源类型：{source.get('type', '')}",
        f"- 原始链接：{item.get('url', '')}",
        f"- 发布时间：{item.get('published_at') or '未获取到'}",
        f"- 抓取时间：{item.get('fetched_at', '')}",
    ]
    if item.get("manual_input"):
        lines.append("- 来源方式：人工补充")
    return "\n".join(lines)


def why_worth_doing(item: dict[str, Any]) -> str:
    details = item.get("score_details") or {}
    lines = [
        "这条内容值得做，不是因为它是“新闻”，而是因为它可以帮助卖家判断经营动作：",
        "",
    ]

    mapping = [
        ("profit_impact", "是否影响利润", "佣金、FBA、仓储、广告费、促销、退款、退货、现金流"),
        ("traffic_impact", "是否影响流量", "搜索排名、广告位、视频展示位、Inspire、Posts、Influencer"),
        ("sharing_value", "是否有内容传播价值", "卖家是否愿意收藏、转发、评论、补充案例"),
        ("operation_risk", "是否涉及运营风险", "账户健康、政策违规、Listing下架、评价合规、品牌备案、侵权"),
        ("recency", "是否具备时效性", "最近 7-30 天内是否值得跟进"),
    ]

    for key, question, focus in mapping:
        detail = details.get(key) or {}
        score = detail.get("score", 0)
        matched = detail.get("matched_keywords") or []
        matched_text = f"；命中：{'、'.join(matched)}" if matched else ""
        lines.append(f"- {question}：{score}分。关注点：{focus}{matched_text}")

    lines.extend(
        [
            "",
            "内容角度：不要搬运事件本身，要输出“卖家该不该跟、先看什么、怎么低成本测试”。最后自然落到红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容这些可执行动作。",
        ]
    )
    return "\n".join(lines)


def xiaohongshu_script(item: dict[str, Any]) -> str:
    title = hotspot_title(item)
    summary = hotspot_summary(item)
    return f"""1. 封面：亚马逊卖家注意：这个变化可能正在影响你的利润
2. 发生了什么：{summary}
3. 利润判断：它会不会影响佣金、FBA、仓储、广告费、退货或现金流？
4. 流量判断：它会不会影响搜索排名、广告位、视频展示位、红人内容入口？
5. 转化判断：它是否提示你该做A+、主图视频、UGC、红人视频或视觉升级？
6. 行动清单：先核查来源，再看后台数据，最后决定是否低成本测试红人视频、可购买视频、主图视频、A+或AI视频内容。
7. 结尾：亚马逊Listing转化差，不一定是价格问题，很多时候是视觉和视频素材没有回答买家的疑问。"""


def wechat_article(item: dict[str, Any]) -> str:
    title = hotspot_title(item)
    summary = hotspot_summary(item)
    return f"""# {title}

这条内容不适合做成普通亚马逊新闻搬运。对卖家来说，真正重要的是判断它会不会改变利润、流量、转化和视觉/视频投入优先级。

## 发生了什么

{summary}

## 哪些平台变化会影响利润

先看它是否涉及佣金、FBA费用、仓储费、广告费、促销成本、退款、退货和现金流。如果不能影响这些指标，就不一定值得优先跟。

## 哪些流量变化值得跟

重点看搜索排名、广告位、视频展示位、Amazon Inspire、Posts、Influencer 等入口是否发生变化。能改变曝光分配的变化，才值得进入运营复盘。

## 哪些内容趋势能提高转化

如果热点指向A+、主图视频、UGC、红人视频、买家信任素材，就要判断它是否能提高点击率、停留、加购和转化。

## 哪些视觉/视频动作现在更值得做

优先选择低成本可测试的动作，例如补充红人视频、亚马逊可购买视频、主图视频、更新A+对比模块、做Listing视觉优化、用AI视频内容测试不同卖点，而不是一次性大改全套Listing。

## 自然引流方向

如果卖家发现流量有了但转化差，不一定先降价。更值得先检查：主图视频有没有解释卖点，A+有没有解决顾虑，红人视频和UGC有没有建立信任，可购买视频有没有承接站内视频流量，AI视频内容能不能帮助快速测试不同脚本。

## 建议动作

- 先核查原始来源和发布时间。
- 对照自己的站点、类目、配送方式和广告结构。
- 只要涉及费用和政策，必须确认适用范围和生效日期。
- 只要涉及视觉和视频，先小范围测试再放大。"""


def douyin_script(item: dict[str, Any]) -> str:
    summary = hotspot_summary(item)
    return f"""0-5秒：亚马逊卖家注意，这条别当新闻看，要看它会不会影响利润、流量和转化。

5-15秒：先说发生了什么：{summary[:120]}

15-35秒：判断值不值得跟，看四个问题。第一，会不会影响FBA、仓储、佣金、广告费、退货和现金流。第二，会不会影响搜索排名、广告位、视频展示位和红人入口。第三，会不会提示你做A+、主图视频、UGC或红人视频。第四，有没有账号、合规、侵权风险。

35-50秒：如果命中两个以上，就放进运营复盘表；如果只是泛新闻，先观察，不要盲目改Listing。

50-60秒：亚马逊Listing转化差，不一定是价格问题，可能是红人视频、可购买视频、主图视频、A+或视觉素材没跟上。你现在更想解决利润、流量还是转化？"""


def forum_post(item: dict[str, Any]) -> str:
    title = hotspot_title(item)
    url = item.get("url", "")
    return f"""标题：{title}

不想把这个当普通新闻搬运，想从卖家经营角度讨论一下。

我会先看四个问题：
- 哪些平台变化会影响利润：佣金、FBA、仓储、广告费、退款退货、现金流？
- 哪些流量变化值得跟：搜索排名、广告位、视频展示位、Inspire、Posts、Influencer？
- 哪些内容趋势能提高转化：A+、主图视频、UGC、红人视频、视觉信任素材？
- 哪些视觉/视频动作现在更值得做：红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容，还是先不动？

参考来源：{url}

大家有没有真实后台数据或测试结果？欢迎补充。"""


def image_suggestions() -> str:
    return """- “利润-流量-转化-风险”四象限判断图。
- 后台广告、费用、账户健康、Listing状态的打码截图。
- 红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容优先级对比图。
- “亚马逊Listing转化差，不一定是价格问题”的诊断图。
- 适合做一张“该不该跟”的决策清单图。"""


def risk_reminders(item: dict[str, Any]) -> str:
    lines = [
        f"- fact_check_required：{str(item.get('fact_check_required', True)).lower()}",
        f"- risk_level：{item.get('risk_level', 'medium')}",
        f"- publish_warning：{item.get('publish_warning', '发布前必须人工核查。')}",
    ]

    source_urls = item.get("source_urls") or []
    if source_urls:
        lines.append("- source_urls：")
        lines.extend([f"  - {url}" for url in source_urls])
    else:
        lines.append("- source_urls：[]，发布前必须补充可追溯来源。")

    uncertain_points = item.get("uncertain_points") or []
    if uncertain_points:
        lines.append("- uncertain_points：")
        lines.extend([f"  - {point}" for point in uncertain_points])

    lines.extend(
        [
            "- 不要把单个卖家案例写成平台普遍规则。",
            "- 涉及费用、佣金、FBA、仓储费时，必须确认站点、类目、生效日期和费用口径。",
            "- 涉及封号、侵权、评价合规、AI内容合规时，只做风险提醒，不提供规避规则的方法。",
            "- 涉及视觉、视频、UGC趋势时，强调先小范围测试，不建议盲目大改。",
        ]
    )
    return "\n".join(lines)


def build_package_item(item: dict[str, Any], index: int) -> str:
    title = hotspot_title(item)
    return f"""# {index}. 今日热点标题

{title}

## 为什么值得做

{why_worth_doing(item)}

## 小红书图文脚本

{xiaohongshu_script(item)}

## 公众号文章

{wechat_article(item)}

## 抖音口播

{douyin_script(item)}

## 论坛帖

{forum_post(item)}

## 配图建议

{image_suggestions()}

## 风险提醒

{risk_reminders(item)}

## 参考来源

{source_text(item)}
"""


def write_package(package_dir: Path, top5: list[dict[str, Any]]) -> list[str]:
    files = ["README.md", "today_publish_package.md"]

    readme_lines = [
        f"# 今日发布包：{today_text()}",
        "",
        "定位：不是亚马逊新闻搬运，而是帮助卖家判断：哪些平台变化会影响利润？哪些流量变化值得跟？哪些内容趋势能提高转化？哪些视觉/视频动作现在更值得做？内容应自然承接到红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容。",
        "",
    ]

    if not top5:
        readme_lines.extend(
            [
                "今天没有超过 70 分的热点，系统未生成可发布内容。",
                "",
                "建议查看当天的 `scored_hotspots.json`，必要时用 `python scripts/add_manual_hotspot.py` 手动补充链接或正文后重新生成。",
            ]
        )
        (package_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
        (package_dir / "today_publish_package.md").write_text(
            f"# 今日发布包：{today_text()}\n\n今天没有超过 70 分的热点，暂无可发布内容。\n",
            encoding="utf-8",
        )
        return files

    items_dir = package_dir / "items"
    items_dir.mkdir(parents=True, exist_ok=True)

    combined = [f"# 今日发布包：{today_text()}", ""]
    readme_lines.extend(["## 热点清单", ""])

    for index, item in enumerate(top5, start=1):
        title = hotspot_title(item)
        content = build_package_item(item, index)
        filename = f"{index:02d}_{clean_filename(title)}.md"
        (items_dir / filename).write_text(content, encoding="utf-8")
        files.append(f"items/{filename}")
        combined.extend([content, "\n---\n"])
        readme_lines.append(f"{index}. {title}（{item.get('score', 0)}分）")

    (package_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
    (package_dir / "today_publish_package.md").write_text("\n".join(combined), encoding="utf-8")
    return files


def main() -> None:
    output_dir = today_output_dir()
    package_dir = output_dir / "publish_package"

    remove_dir(package_dir)

    top5 = load_json_if_exists(output_dir / "top5_hotspots.json", [])
    files = write_package(package_dir, top5)

    manifest = {
        "date": today_text(),
        "top_hotspots_count": len(top5),
        "package_dir": str(package_dir),
        "positioning": "帮助亚马逊卖家判断：哪些平台变化会影响利润？哪些流量变化值得跟？哪些内容趋势能提高转化？哪些视觉/视频动作现在更值得做？自然引流到红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容。",
        "required_sections": [
            "今日热点标题",
            "为什么值得做",
            "小红书图文脚本",
            "公众号文章",
            "抖音口播",
            "论坛帖",
            "配图建议",
            "风险提醒",
            "参考来源",
        ],
        "files": files,
    }
    write_json(package_dir / "manifest.json", manifest)

    print(f"今日发布包已导出：{package_dir}")


if __name__ == "__main__":
    main()
