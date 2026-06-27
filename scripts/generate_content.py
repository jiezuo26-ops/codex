from __future__ import annotations

from typing import Any

try:
    from common import clean_filename, read_json, today_output_dir, write_json
    from llm_client import generate_with_llm, use_llm
except ImportError:
    from .common import clean_filename, read_json, today_output_dir, write_json
    from .llm_client import generate_with_llm, use_llm


CONTENT_GENERATION_MIN_SCORE = 70


def clear_old_drafts(drafts_dir) -> None:
    for path in drafts_dir.glob("*.md"):
        path.unlink()


def hotspot_name(item: dict[str, Any]) -> str:
    source = item.get("source") or {}
    return str(item.get("title") or source.get("name") or item.get("url") or "未命名热点")


def summary_text(item: dict[str, Any]) -> str:
    summary = str(item.get("summary") or "").strip()
    if summary:
        return summary
    error = str(item.get("error") or "").strip()
    if error:
        return f"自动抓取没有拿到正文，需要人工打开来源核查。失败原因：{error}"
    return "暂无正文摘要，请人工补充事实信息后再发布。"


def title_candidates(name: str) -> list[str]:
    return [
        "亚马逊卖家注意：这个变化可能正在影响你的利润",
        "很多卖家还没发现，亚马逊这个流量入口正在变重要",
        "FBA成本又变了？真正该看的不是新闻，而是利润模型",
        "为什么现在越来越多卖家开始补红人视频？",
        "亚马逊Listing转化差，不一定是价格问题",
        f"{name}：卖家该不该跟？",
        "主图视频、A+、UGC：这条变化该怎么看",
        "卖家判断平台变化，先看这四个问题",
        "这件事对广告费、转化率和现金流有什么影响",
        f"从利润、流量、转化角度看{name}",
    ]


def build_markdown(item: dict[str, Any], index: int) -> str:
    name = hotspot_name(item)
    source = item.get("source") or {}
    summary = summary_text(item)
    score = item.get("score", 0)
    url = item.get("url", "")
    source_urls = item.get("source_urls") or [url]
    uncertain_points = item.get("uncertain_points") or []
    uncertain_points_md = "\n".join([f"- {point}" for point in uncertain_points]) or "- 暂无结构化不确定点，但发布前仍需核查来源。"
    source_urls_md = "\n".join([f"- {source_url}" for source_url in source_urls if source_url]) or "- 暂无来源链接，发布前必须补充。"
    titles = title_candidates(name)
    titles_md = "\n".join([f"{i}. {title}" for i, title in enumerate(titles, start=1)])

    return f"""# 热点 {index}: {name}

分数：{score}
来源：{source.get("name", "")}
平台：{source.get("platform", "")}
链接：{url}
发布时间：{item.get("published_at") or "未获取到"}

## 事实摘要

{summary}

## 经营判断

这条内容不要按“新闻搬运”处理，要判断它是否会改变卖家的经营动作：

- 利润：是否影响佣金、FBA费用、仓储费、广告费、促销成本、退款、退货、现金流？
- 流量：是否影响搜索排名、广告位、视频展示位、Amazon Inspire、Posts、Influencer？
- 转化：是否提示卖家要调整A+、主图视频、UGC、红人视频、视觉表达？
- 风险：是否涉及账户健康、政策违规、Listing下架、评价合规、品牌备案、侵权？
- 视觉/视频动作：哪些视觉/视频动作现在更值得做？

可自然承接的业务动作：

- 红人视频：适合需要真实使用场景、信任背书和站外素材的产品。
- 亚马逊可购买视频：适合承接站内视频流量和购物决策。
- 主图视频：适合解释卖点、使用方法、尺寸对比和痛点解决。
- A+：适合补充品牌信任、对比模块、场景图和FAQ。
- Listing视觉优化：适合点击率低、转化差、卖点表达不清的Listing。
- AI视频内容：适合快速测试不同卖点、脚本和视觉方向。

## 小红书图文脚本

1. 封面：{titles[0]}
2. 发生了什么：{summary}
3. 卖家判断1：它会不会影响利润？重点看费用、广告、退货和现金流。
4. 卖家判断2：它会不会影响流量？重点看搜索、广告位、视频入口和红人内容。
5. 卖家判断3：它能不能提高转化？重点看A+、主图视频、UGC和视觉信任感。
6. 行动清单：核查来源、对照后台数据、决定是否跟进、评论区收集卖家反馈。
7. 自然引导：如果你的Listing转化差，不一定先降价，可以先检查主图视频、A+、UGC和红人视频素材是否缺位。

## 公众号文章

### 标题
{titles[0]}

### 开头
这条热点不适合只做新闻复述。对亚马逊卖家来说，更重要的是判断它会不会影响利润、流量、转化和运营风险。

### 发生了什么
{summary}

### 卖家真正要判断的四件事
第一，它会不会影响利润。重点看佣金、FBA费用、仓储费、广告费、促销成本、退款、退货和现金流。

第二，它会不会影响流量。重点看搜索排名、广告位、视频展示位、Amazon Inspire、Posts和Influencer。

第三，它会不会影响转化。重点看A+、主图视频、UGC、红人视频、视觉素材和卖点表达。

第四，它会不会带来风险。重点看账户健康、政策违规、Listing下架、评价合规、品牌备案和侵权。

第五，它能不能自然落到视觉和视频动作。比如红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容，哪些更适合先做低成本测试。

### 建议动作
- 先核查原始来源和发布时间。
- 对照自己的站点、类目、配送方式和广告结构。
- 如果涉及视觉或视频趋势，优先做低成本测试，不要一次性大改。
- 如果涉及费用或政策，发布前必须确认适用范围和生效日期。
- 如果Listing转化差，不要只盯价格，先检查图片、A+、主图视频和红人素材是否支撑了购买决策。

## 抖音口播

0-5秒：亚马逊卖家注意，这条热点别只当新闻看，关键是判断它会不会影响你的利润、流量和转化。

5-15秒：先说发生了什么：{summary[:120]}

15-35秒：判断值不值得跟，看四个点。第一，会不会影响佣金、FBA、仓储、广告费和退货。第二，会不会影响搜索排名、广告位和视频入口。第三，会不会提示你该做A+、主图视频、UGC或者红人内容。第四，有没有账号、合规、侵权风险。

35-50秒：如果四个里面命中两个以上，就值得进你的运营复盘表；如果只是一条泛新闻，就先观察，不要盲目跟。

50-60秒：亚马逊Listing转化差，不一定是价格问题，也可能是主图视频、A+、红人视频和视觉素材没跟上。你最近更关心利润、流量还是转化？

## 论坛帖

标题：{titles[1]}

最近看到一个亚马逊相关热点，想从经营角度和大家讨论，不想只做新闻搬运。

我建议按这几个问题判断：
- 它会不会影响利润：佣金、FBA、仓储、广告费、促销、退款、退货、现金流？
- 它会不会影响流量：搜索排名、广告位、视频展示位、Inspire、Posts、Influencer？
- 它会不会影响转化：A+、主图视频、UGC、红人视频、视觉信任感？
- 它会不会带来风险：账户健康、政策违规、Listing下架、评价合规、品牌备案、侵权？
- 它能不能落到具体动作：补红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化或AI视频内容？

参考来源：{url}

大家觉得这个变化值得跟吗？有没有真实后台数据或测试结果？

## 标题备选 10 个

{titles_md}

## 配图建议

- 后台费用、广告、账户健康、Listing状态页面的打码截图。
- “利润-流量-转化-风险”四象限判断图。
- 红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容的优先级对比图。
- “Listing转化差，不一定是价格问题”的诊断图。
- 小红书用收藏型清单图，抖音用字幕卡和后台截图切换。

## 风险提醒

- fact_check_required：{str(item.get("fact_check_required", True)).lower()}
- risk_level：{item.get("risk_level", "medium")}
- publish_warning：{item.get("publish_warning", "发布前必须人工核查。")}
- source_urls：
{source_urls_md}
- uncertain_points：
{uncertain_points_md}
- 不要把个别卖家案例写成平台普遍规则。
- 涉及费用、佣金、FBA、仓储费时，发布前必须确认站点和生效日期。
- 涉及封号、合规、侵权、评价时，只做风险提醒，不提供规避规则的方法。
- 涉及视觉、视频、UGC趋势时，要强调先小范围测试。

## 参考来源

- 来源名称：{source.get("name", "")}
- 平台：{source.get("platform", "")}
- 链接：{url}
"""


def build_draft(item: dict[str, Any], index: int) -> str:
    if not use_llm():
        return build_markdown(item, index)

    try:
        return generate_with_llm(item, index)
    except Exception as exc:
        print(f"LLM 生成失败，已退回本地模板：{exc}")
        return build_markdown(item, index)


def main() -> None:
    output_dir = today_output_dir()
    top_path = output_dir / "top5_hotspots.json"
    if not top_path.exists():
        raise FileNotFoundError("请先运行 scripts/score_hotspots.py 生成 top5_hotspots.json")

    top5 = [item for item in read_json(top_path) if item.get("score", 0) > CONTENT_GENERATION_MIN_SCORE]
    drafts_dir = output_dir / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    clear_old_drafts(drafts_dir)

    index_records = []
    if not top5:
        write_json(output_dir / "draft_index.json", index_records)
        print(f"没有超过 {CONTENT_GENERATION_MIN_SCORE} 分的热点，本次不生成内容草稿。")
        return

    for index, item in enumerate(top5, start=1):
        name = hotspot_name(item)
        markdown = build_draft(item, index)
        filename = f"{index:02d}_{clean_filename(name)}.md"
        path = drafts_dir / filename
        path.write_text(markdown, encoding="utf-8")
        index_records.append({"title": name, "file": str(path), "score": item.get("score", 0)})
        print(f"已生成草稿: {path}")

    write_json(output_dir / "draft_index.json", index_records)
    print(f"内容生成完成，结果已保存到: {drafts_dir}")


if __name__ == "__main__":
    main()
