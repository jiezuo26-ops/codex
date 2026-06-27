from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCES_FILE = ROOT_DIR / "sources" / "sources.csv"
OUTPUTS_DIR = ROOT_DIR / "outputs"
ALLOWED_SOURCE_TYPES = {
    "official",
    "official_forum",
    "industry_media",
    "creator",
    "creator_search",
    "manual_article",
}


def today_text() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def today_output_dir() -> Path:
    path = OUTPUTS_DIR / today_text()
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_sources(path: Path = SOURCES_FILE) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"找不到数据源文件: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    sources: list[dict[str, str]] = []
    for row in rows:
        if row.get("url"):
            source = {key: (value or "").strip() for key, value in row.items()}
            source_type = source.get("type", "")
            if source_type and source_type not in ALLOWED_SOURCE_TYPES:
                print(f"提示：发现未登记的来源类型 {source_type}，来源：{source.get('name', source.get('url', ''))}")
            sources.append(source)
    return sources


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def clean_filename(text: str, max_length: int = 60) -> str:
    allowed = []
    for char in text:
        if char.isalnum() or char in "-_":
            allowed.append(char)
        elif char.isspace():
            allowed.append("_")
    result = "".join(allowed).strip("_")
    return (result[:max_length] or "untitled")
