from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    from common import read_sources, today_output_dir, write_json
except ImportError:
    from .common import read_sources, today_output_dir, write_json


TIMEOUT_SECONDS = 20
MANUAL_FALLBACK_PLATFORMS = ("xiaohongshu", "douyin", "wechat")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36"
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.meta: dict[str, str] = {}
        self.paragraphs: list[str] = []
        self.times: list[str] = []
        self._current_tag = ""
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag == "meta":
            key = (attr.get("name") or attr.get("property") or "").lower()
            content = attr.get("content") or ""
            if key and content:
                self.meta[key] = html.unescape(content).strip()
        elif tag in {"title", "p", "time", "h1"}:
            self._current_tag = tag
            self._buffer = []
            if tag == "time" and attr.get("datetime"):
                self.times.append(attr["datetime"].strip())

    def handle_data(self, data: str) -> None:
        if self._current_tag:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self._current_tag:
            return

        text = normalize_text(" ".join(self._buffer))
        if tag == "title" and text and not self.title:
            self.title = text
        elif tag == "h1" and text and not self.title:
            self.title = text
        elif tag == "p" and len(text) >= 20:
            self.paragraphs.append(text)
        elif tag == "time" and text:
            self.times.append(text)

        self._current_tag = ""
        self._buffer = []


def text_or_empty(value: Optional[str]) -> str:
    return value.strip() if value else ""


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def get_meta_content(page: PageParser, names: list[str]) -> str:
    for name in names:
        value = page.meta.get(name.lower())
        if value:
            return text_or_empty(value)
    return ""


def extract_title(page: PageParser) -> str:
    meta_title = get_meta_content(page, ["og:title", "twitter:title"])
    if meta_title:
        return meta_title
    return page.title


def parse_date(value: str) -> str:
    value = value.strip()
    if not value:
        return ""

    iso_value = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_value).isoformat()
    except ValueError:
        pass

    patterns = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%b %d, %Y",
        "%B %d, %Y",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(value, pattern).isoformat()
        except ValueError:
            continue
    return ""


def extract_published_at(page: PageParser) -> str:
    candidates = [
        get_meta_content(page, ["article:published_time", "article:modified_time", "date", "pubdate", "publishdate", "timestamp"])
    ]
    candidates.extend(page.times)

    for candidate in candidates:
        parsed = parse_date(candidate)
        if parsed:
            return parsed
    return ""


def extract_summary(page: PageParser) -> str:
    description = get_meta_content(page, ["description", "og:description", "twitter:description"])
    if description:
        return description[:500]

    text = " ".join(page.paragraphs[:8])
    text = normalize_text(text)
    return text[:800]


def fetch_one(source: dict[str, str]) -> dict[str, object]:
    started_at = datetime.now(timezone.utc).isoformat()
    record: dict[str, object] = {
        "source": source,
        "url": source["url"],
        "fetched_at": started_at,
        "success": False,
        "title": "",
        "summary": "",
        "published_at": "",
        "error": "",
        "need_manual_input": False,
    }

    try:
        request = Request(
            source["url"],
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            content_type = response.headers.get("content-type", "")
            charset_match = re.search(r"charset=([\w-]+)", content_type, re.I)
            charset = charset_match.group(1) if charset_match else "utf-8"
            text = raw.decode(charset, errors="replace")
            status_code = response.status

        page = PageParser()
        page.feed(text)

        record.update(
            {
                "success": True,
                "status_code": status_code,
                "title": extract_title(page),
                "summary": extract_summary(page),
                "published_at": extract_published_at(page),
            }
        )
        platform = str(source.get("platform", "")).lower()
        source_type = str(source.get("type", "")).lower()
        is_social_source = any(name in platform for name in MANUAL_FALLBACK_PLATFORMS) or source_type in {"creator", "creator_search"}
        if is_social_source and not (record["title"] or record["summary"]):
            record["success"] = False
            record["need_manual_input"] = True
            record["error"] = "页面可访问，但未提取到有效标题或正文，建议人工补充标题、链接、正文。"
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError) as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        record["need_manual_input"] = True

    return record


def main() -> None:
    output_dir = today_output_dir()
    raw_dir = output_dir / "raw_items"
    raw_dir.mkdir(parents=True, exist_ok=True)

    sources = read_sources()
    records = []

    for index, source in enumerate(sources, start=1):
        record = fetch_one(source)
        records.append(record)
        write_json(raw_dir / f"{index:03d}.json", record)

        status = "成功" if record["success"] else "失败"
        print(f"[{index}/{len(sources)}] {status}: {source.get('name', source['url'])}")

    write_json(output_dir / "raw_hotspots.json", records)
    print(f"抓取完成，结果已保存到: {output_dir}")


if __name__ == "__main__":
    main()
