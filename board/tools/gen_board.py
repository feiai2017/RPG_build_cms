# -*- coding: utf-8 -*-
"""Generate board.json for the five-element concentric board."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

SECTOR_ORDER = ["木", "金", "土", "火", "水"]
COLORS = {
    "金": "#E6E6E6",
    "木": "#39D98A",
    "水": "#3AA0FF",
    "火": "#FF4D4D",
    "土": "#FFD166",
}
RINGS = [
    {"id": "core", "radius": 0},
    {"id": "r1", "radius": 140, "slots": 16},
    {"id": "r2", "radius": 220, "slots": 24},
    {"id": "r3", "radius": 305, "slots": 32},
]


@dataclass
class Node:
    node_id: str
    ring: str
    element: str
    ntype: str
    angle: float
    radius: float
    x: float
    y: float
    label: str
    tags: List[str]


@dataclass
class Edge:
    a: str
    b: str
    kind: str


def polar(radius: float, angle: float) -> tuple[float, float]:
    return radius * math.cos(angle), radius * math.sin(angle)


def distribute_indices(total: int) -> List[int]:
    return [int(i * 5 / total) for i in range(total)]


def assign_type(k: int, count: int) -> str:
    if k == 0:
        return "keystone"
    if k % 7 == 0:
        return "socket"
    if k % 4 == 0:
        return "medium"
    return "small"


def generate_nodes() -> tuple[List[Node], Dict[str, List[Node]]]:
    nodes: List[Node] = []
    sector_span = 2 * math.pi / 5

    nodes.append(
        Node(
            node_id="core",
            ring="core",
            element="土",
            ntype="core",
            angle=0.0,
            radius=0.0,
            x=0.0,
            y=0.0,
            label="BIOS",
            tags=["core", "bios"],
        )
    )

    ring_sector_nodes: Dict[str, List[Node]] = {}

    for ring in RINGS[1:]:
        ring_id = ring["id"]
        radius = ring["radius"]
        total = ring["slots"]
        sector_index_for_slot = distribute_indices(total)
        sector_slots: Dict[int, List[int]] = {i: [] for i in range(5)}
        for i, sector_idx in enumerate(sector_index_for_slot):
            sector_slots[sector_idx].append(i)

        for sector_idx in range(5):
            element = SECTOR_ORDER[sector_idx]
            indices = sector_slots[sector_idx]
            count = len(indices)
            for k in range(count):
                angle = sector_idx * sector_span + sector_span * (k + 0.5) / count
                x, y = polar(radius, angle)
                ntype = assign_type(k, count)
                node_id = f"{ring_id}-{element}-{k+1}"
                node = Node(
                    node_id=node_id,
                    ring=ring_id,
                    element=element,
                    ntype=ntype,
                    angle=angle,
                    radius=radius,
                    x=x,
                    y=y,
                    label=str(k + 1),
                    tags=[f"ring:{ring_id}", f"sector:{element}", f"type:{ntype}"],
                )
                nodes.append(node)
                key = f"{ring_id}:{sector_idx}"
                ring_sector_nodes.setdefault(key, []).append(node)

            # Assign bridge/convert for r2/r3 if enough nodes
            if ring_id in ("r2", "r3") and count >= 3:
                key = f"{ring_id}:{sector_idx}"
                sorted_nodes = sorted(ring_sector_nodes[key], key=lambda n: n.angle)
                bridge_idx = count - 2
                convert_idx = count - 3
                if bridge_idx == 0:
                    bridge_idx = 1
                if convert_idx == 0:
                    convert_idx = 2
                sorted_nodes[bridge_idx].ntype = "bridge"
                sorted_nodes[convert_idx].ntype = "convert"

    return nodes, ring_sector_nodes


def generate_edges(nodes: List[Node], ring_sector_nodes: Dict[str, List[Node]]) -> List[Edge]:
    edges: List[Edge] = []

    # Ring edges: only within each sector (no cross-sector)
    for ring in ("r1", "r2", "r3"):
        for sector_idx in range(5):
            key = f"{ring}:{sector_idx}"
            sector_nodes = sorted(ring_sector_nodes.get(key, []), key=lambda n: n.angle)
            for i in range(len(sector_nodes) - 1):
                edges.append(Edge(sector_nodes[i].node_id, sector_nodes[i + 1].node_id, "ring"))

    # Radial r1->r2 and r2->r3
    def connect_radial(r1: str, r2: str, per_sector: int = 2) -> None:
        for sector_idx in range(5):
            a_list = sorted(ring_sector_nodes.get(f"{r1}:{sector_idx}", []), key=lambda n: n.angle)
            b_list = sorted(ring_sector_nodes.get(f"{r2}:{sector_idx}", []), key=lambda n: n.angle)
            if not a_list or not b_list:
                continue
            k = min(per_sector, len(a_list), len(b_list))
            for i in range(k):
                idx_a = int(round((len(a_list) - 1) * (i + 0.5) / k))
                idx_b = int(round((len(b_list) - 1) * (i + 0.5) / k))
                edges.append(Edge(a_list[idx_a].node_id, b_list[idx_b].node_id, "radial"))

    connect_radial("r1", "r2")
    connect_radial("r2", "r3")

    # Core to r1 keystones
    core = next(n for n in nodes if n.ring == "core")
    for sector_idx in range(5):
        sector_nodes = sorted(ring_sector_nodes.get(f"r1:{sector_idx}", []), key=lambda n: n.angle)
        if not sector_nodes:
            continue
        keystone = next((n for n in sector_nodes if n.ntype == "keystone"), sector_nodes[0])
        edges.append(Edge(core.node_id, keystone.node_id, "radial"))

    # Special edges: bridge/convert to neighbor sector middle node
    for ring in ("r2", "r3"):
        for sector_idx in range(5):
            key = f"{ring}:{sector_idx}"
            sector_nodes = sorted(ring_sector_nodes.get(key, []), key=lambda n: n.angle)
            for n in sector_nodes:
                if n.ntype not in ("bridge", "convert"):
                    continue
                if n.ntype == "bridge":
                    neighbor = (sector_idx + 1) % 5
                else:
                    neighbor = (sector_idx - 1) % 5
                neighbor_nodes = sorted(
                    ring_sector_nodes.get(f"{ring}:{neighbor}", []), key=lambda n: n.angle
                )
                if not neighbor_nodes:
                    continue
                mid = neighbor_nodes[len(neighbor_nodes) // 2]
                edges.append(Edge(n.node_id, mid.node_id, "special"))

    return edges


def write_board(nodes: List[Node], edges: List[Edge]) -> None:
    data = {
        "meta": {
            "version": 1,
            "elements": SECTOR_ORDER,
            "colors": COLORS,
        },
        "rings": [{"id": r["id"], "radius": r["radius"]} for r in RINGS],
        "nodes": [
            {
                "id": n.node_id,
                "ring": n.ring,
                "element": n.element,
                "type": n.ntype,
                "angle": round(n.angle, 6),
                "radius": n.radius,
                "x": round(n.x, 3),
                "y": round(n.y, 3),
                "label": n.label,
                "tags": n.tags,
            }
            for n in nodes
        ],
        "edges": [{"a": e.a, "b": e.b, "kind": e.kind} for e in edges],
    }

    root = Path(__file__).resolve().parents[1]
    web_path = root / "web" / "board.json"
    godot_path = root / "godot" / "board.json"
    web_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    godot_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    nodes, ring_sector_nodes = generate_nodes()
    edges = generate_edges(nodes, ring_sector_nodes)
    write_board(nodes, edges)
    print("Generated web/board.json and godot/board.json")
