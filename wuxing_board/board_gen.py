# -*- coding: utf-8 -*-
"""五行棋盘生成器（对称 + 可扩展）"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple
import math

ELEMENTS = ["木", "火", "土", "金", "水"]
GENERATION_ORDER = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}
DESTRUCTION_ORDER = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}
REALM_ORDER = ["炼气", "筑基", "金丹", "元婴", "化神"]


class NodeType(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    KEYSTONE = "keystone"
    SOCKET = "socket"
    BRIDGE = "bridge"
    CONVERT = "convert"


@dataclass(frozen=True)
class BoardNode:
    node_id: str
    element: str
    ring: int
    idx: int
    type: NodeType
    x: float
    y: float
    tags: Tuple[str, ...] = field(default_factory=tuple)
    unlock_realm: str = "炼气"


@dataclass(frozen=True)
class BoardEdge:
    source: str
    target: str
    kind: str


@dataclass(frozen=True)
class BoardLayout:
    nodes: List[BoardNode]
    edges: List[BoardEdge]
    rings: int
    slots_per_ring: int
    bridges_per_boundary: int


def _node_type_for_position(ring: int, slot_idx: int) -> NodeType:
    if ring == 1:
        return NodeType.SMALL
    if ring == 2:
        return NodeType.MEDIUM
    if ring == 3:
        return NodeType.SOCKET if slot_idx % 3 == 0 else NodeType.MEDIUM
    return NodeType.KEYSTONE if slot_idx % 2 == 0 else NodeType.CONVERT


def _unlock_realm_for_type(node_type: NodeType) -> str:
    if node_type == NodeType.BRIDGE:
        return "筑基"
    if node_type == NodeType.CONVERT:
        return "金丹"
    if node_type == NodeType.SOCKET:
        return "元婴"
    if node_type == NodeType.KEYSTONE:
        return "化神"
    return "炼气"


def realm_rank(realm: str) -> int:
    if realm in REALM_ORDER:
        return REALM_ORDER.index(realm)
    return 0


def generate_board(
    rings: int = 4,
    slots_per_ring: int = 6,
    bridges_per_boundary: int = 2,
    ring_start: float = 1.2,
    ring_gap: float = 0.7,
    sector_margin_deg: float = 6.0,
) -> BoardLayout:
    """生成对称五行棋盘数据（含坐标）"""
    nodes: List[BoardNode] = []
    edges: List[BoardEdge] = []

    sector_span = 360 / len(ELEMENTS)

    def polar(angle_deg: float, radius: float) -> Tuple[float, float]:
        rad = math.radians(angle_deg)
        return radius * math.cos(rad), radius * math.sin(rad)

    # 生成元素节点
    for e_idx, element in enumerate(ELEMENTS):
        base_angle = -90 + e_idx * sector_span
        for ring in range(1, rings + 1):
            radius = ring_start + (ring - 1) * ring_gap
            for slot_idx in range(1, slots_per_ring + 1):
                slot_span = sector_span - 2 * sector_margin_deg
                if slots_per_ring == 1:
                    angle = base_angle + sector_span / 2
                else:
                    angle = (
                        base_angle
                        + sector_margin_deg
                        + (slot_idx - 1) * slot_span / (slots_per_ring - 1)
                    )
                x, y = polar(angle, radius)
                node_type = _node_type_for_position(ring, slot_idx)
                node_id = f"{element}-R{ring}-S{slot_idx}"
                nodes.append(
                    BoardNode(
                        node_id=node_id,
                        element=element,
                        ring=ring,
                        idx=slot_idx,
                        type=node_type,
                        x=x,
                        y=y,
                        tags=("element", element),
                        unlock_realm=_unlock_realm_for_type(node_type),
                    )
                )

    # 同元素环内与径向连接
    for element in ELEMENTS:
        for ring in range(1, rings + 1):
            for slot_idx in range(1, slots_per_ring):
                a = f"{element}-R{ring}-S{slot_idx}"
                b = f"{element}-R{ring}-S{slot_idx + 1}"
                edges.append(BoardEdge(a, b, "intra"))
            if slots_per_ring > 1:
                a = f"{element}-R{ring}-S{slots_per_ring}"
                b = f"{element}-R{ring}-S1"
                edges.append(BoardEdge(a, b, "intra"))

        for ring in range(1, rings):
            for slot_idx in range(1, slots_per_ring + 1):
                a = f"{element}-R{ring}-S{slot_idx}"
                b = f"{element}-R{ring + 1}-S{slot_idx}"
                edges.append(BoardEdge(a, b, "radial"))

    # 桥接节点与桥接边
    for e_idx, element in enumerate(ELEMENTS):
        next_element = ELEMENTS[(e_idx + 1) % len(ELEMENTS)]
        base_angle = -90 + (e_idx + 1) * sector_span
        for ring in range(1, rings + 1):
            radius = ring_start + (ring - 1) * ring_gap
            for bridge_idx in range(1, bridges_per_boundary + 1):
                offset = (bridge_idx - 0.5) * (sector_margin_deg / max(1, bridges_per_boundary))
                x, y = polar(base_angle + offset, radius)
                node_id = f"bridge-{element}-{next_element}-R{ring}-B{bridge_idx}"
                nodes.append(
                    BoardNode(
                        node_id=node_id,
                        element=element,
                        ring=ring,
                        idx=bridge_idx,
                        type=NodeType.BRIDGE,
                        x=x,
                        y=y,
                        tags=("bridge", f"to:{next_element}"),
                        unlock_realm=_unlock_realm_for_type(NodeType.BRIDGE),
                    )
                )
                left = f"{element}-R{ring}-S{bridge_idx}"
                right = f"{next_element}-R{ring}-S{bridge_idx}"
                edges.append(BoardEdge(node_id, left, "bridge"))
                edges.append(BoardEdge(node_id, right, "bridge"))

    return BoardLayout(
        nodes=nodes,
        edges=edges,
        rings=rings,
        slots_per_ring=slots_per_ring,
        bridges_per_boundary=bridges_per_boundary,
    )


def validate_board(nodes: List[BoardNode], edges: List[BoardEdge]) -> None:
    counts: Dict[str, int] = {e: 0 for e in ELEMENTS}
    for node in nodes:
        if node.type == NodeType.BRIDGE:
            continue
        if node.element in counts:
            counts[node.element] += 1
    values = set(counts.values())
    if len(values) != 1:
        raise ValueError(f"元素节点数量不一致: {counts}")


def count_per_element(nodes: List[BoardNode]) -> Dict[str, int]:
    counts: Dict[str, int] = {e: 0 for e in ELEMENTS}
    for node in nodes:
        if node.type == NodeType.BRIDGE:
            continue
        counts[node.element] += 1
    return counts
