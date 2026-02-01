# -*- coding: utf-8 -*-
"""Migrate board.json nodes into v2 schema with node_type/template/ports/ui."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def node_type_for(ntype: str) -> str:
    if ntype in ("core", "bridge", "convert"):
        return "mechanic"
    if ntype in ("keystone", "socket", "medium", "small"):
        return "stat"
    return "unknown"


def template_for(ntype: str) -> str:
    if ntype == "core":
        return "SOURCE_CORE"
    if ntype == "bridge":
        return "NODE_BRIDGE"
    if ntype == "convert":
        return "NODE_CONVERT"
    return "SLOT_STAT"


def ensure_list(value) -> List:
    return value if isinstance(value, list) else []


def migrate_board(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for node in data.get("nodes", []):
        ntype = node.get("type", "unknown")
        node.setdefault("node_type", node_type_for(ntype))
        node.setdefault("template_id", template_for(ntype))
        node.setdefault("ports", {"in": [], "out": []})
        node.setdefault("params", {})
        node.setdefault("ui", {"shape": ntype, "ring": node.get("ring"), "color": "#7f8c99"})
        node["tags"] = ensure_list(node.get("tags", []))
        if node["node_type"] == "unknown":
            node["tags"].append("needs_fix")

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"migrated {path}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    migrate_board(root / "web" / "board.json")
    migrate_board(root / "godot" / "board.json")


if __name__ == "__main__":
    main()
