# -*- coding: utf-8 -*-
"""Minimal v2 checks for board data."""
from __future__ import annotations

import json
from pathlib import Path

ALLOWED = {"skill", "mechanic", "stat", "unknown"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    root = Path(__file__).resolve().parents[1]
    board = load(root / "web" / "board.json")
    nodes = board.get("nodes", [])
    unknown = 0
    missing_template = 0
    for n in nodes:
        t = n.get("node_type")
        if t not in ALLOWED:
            raise SystemExit(f"node_type invalid: {n.get('id')} {t}")
        if t == "unknown":
            unknown += 1
        if not n.get("template_id"):
            missing_template += 1
    print(f"nodes: {len(nodes)}, unknown: {unknown}, missing_template: {missing_template}")


if __name__ == "__main__":
    main()
