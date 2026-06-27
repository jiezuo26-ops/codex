from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from common import ROOT_DIR
except ImportError:
    from .common import ROOT_DIR


DEFAULT_BASE_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
TIMEOUT_SECONDS = 90


def env_enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def use_llm() -> bool:
    return env_enabled("USE_LLM", False)


def prompt_template() -> str:
    path = ROOT_DIR / "prompts" / "content_prompt.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source") or {}
    return {
        "title": item.get("title", ""),
        "summary": item.get("summary", ""),
        "url": item.get("url", ""),
        "published_at": item.get("published_at", ""),
        "score": item.get("score", 0),
        "score_details": item.get("score_details", {}),
        "source": {
            "platform": source.get("platform", ""),
            "name": source.get("name", ""),
            "type": source.get("type", ""),
            "priority": source.get("priority", ""),
        },
    }


def build_messages(item: dict[str, Any], index: int) -> list[dict[str, str]]:
    system_prompt = prompt_template() or "你是亚马逊卖家的经营判断内容编辑。"
    user_prompt = f"""
请基于下面热点生成待审核内容草稿。

要求：
- 不要做普通新闻搬运。
- 必须判断：哪些平台变化会影响利润、哪些流量变化值得跟、哪些内容趋势能提高转化、哪些视觉/视频动作现在更值得做。
- 内容最后自然承接到：红人视频、亚马逊可购买视频、主图视频、A+、Listing视觉优化、AI视频内容。
- 必须包含：今日热点标题、为什么值得做、小红书图文脚本、公众号文章、抖音口播、论坛帖、配图建议、风险提醒、参考来源。
- 必须读取并保留事实核查字段：fact_check_required、risk_level、source_urls、uncertain_points、publish_warning。
- 如果 risk_level=high，必须明确写“高风险，发布前必须人工核查”，不能把费用、政策、生效日期、封号、合规结论写死。
- 不要编造事实、数据、生效日期或官方结论。
- 输出 Markdown。

热点序号：{index}
热点数据：
{json.dumps(compact_item(item), ensure_ascii=False, indent=2)}
""".strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_with_llm(item: dict[str, Any], index: int) -> str:
    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("USE_LLM=true，但没有设置 LLM_API_KEY 或 OPENAI_API_KEY")

    base_url = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": build_messages(item, index),
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
    }
    if os.getenv("LLM_MAX_TOKENS"):
        payload["max_tokens"] = int(os.getenv("LLM_MAX_TOKENS", "3000"))

    request = Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API HTTP {exc.code}: {body}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"LLM API 调用失败：{exc}") from exc

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"LLM API 返回格式无法识别：{result}") from exc
