from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

STEPS = [
    ("更新热点", "fetch_hotspots.py"),
    ("筛选 TOP 5", "score_hotspots.py"),
    ("生成内容草稿", "generate_content.py"),
    ("导出今日发布包", "export_today_package.py"),
]


def run_step(label: str, script_name: str) -> None:
    print(f"\n=== {label} ===")
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "scripts" / script_name)],
        cwd=ROOT_DIR,
        check=True,
    )


def main() -> None:
    for label, script_name in STEPS:
        run_step(label, script_name)
    print("\n每日流程完成。")


if __name__ == "__main__":
    main()
