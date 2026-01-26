# -*- coding: utf-8 -*-
"""
五行棋盘数据模型与布局生成
"""

from dataclasses import dataclass, field
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)

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
    index: int
    type: NodeType
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


def _node_type_for_position(ring: int, slot_index: int) -> NodeType:
    if ring == 1:
        return NodeType.SMALL
    if ring == 2:
        return NodeType.MEDIUM
    if ring == 3:
        return NodeType.SOCKET if slot_index % 3 == 0 else NodeType.MEDIUM
    return NodeType.KEYSTONE if slot_index % 2 == 0 else NodeType.CONVERT


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


def is_node_unlocked(node: BoardNode, realm: str) -> bool:
    return realm_rank(realm) >= realm_rank(node.unlock_realm)


def _bridge_node_id(element_a: str, element_b: str, ring: int, index: int) -> str:
    return f"bridge-{element_a}-{element_b}-R{ring}-B{index}"


def generate_wuxing_board(
    realm: str = "炼气",
    rings: int = 4,
    slots_per_ring: int = 6,
    bridges_per_boundary: int = 2,
) -> BoardLayout:
    """生成对称、可扩展的五行棋盘布局。"""
    logger.info(
        "wuxing_board.generate start realm=%s rings=%s slots=%s bridges=%s",
        realm,
        rings,
        slots_per_ring,
        bridges_per_boundary,
    )
    nodes: List[BoardNode] = []
    edges: List[BoardEdge] = []
    node_lookup: Dict[str, BoardNode] = {}

    # 1) 生成元素扇区节点
    for element in ELEMENTS:
        for ring in range(1, rings + 1):
            for slot_idx in range(1, slots_per_ring + 1):
                node_id = f"{element}-R{ring}-S{slot_idx}"
                node_type = _node_type_for_position(ring, slot_idx)
                node = BoardNode(
                    node_id=node_id,
                    element=element,
                    ring=ring,
                    index=slot_idx,
                    type=node_type,
                    tags=("element", element),
                    unlock_realm=_unlock_realm_for_type(node_type),
                )
                nodes.append(node)
                node_lookup[node_id] = node

    # 2) 同元素环内与跨环连接
    for element in ELEMENTS:
        for ring in range(1, rings + 1):
            for slot_idx in range(1, slots_per_ring):
                a = f"{element}-R{ring}-S{slot_idx}"
                b = f"{element}-R{ring}-S{slot_idx + 1}"
                edges.append(BoardEdge(source=a, target=b, kind="intra"))
            if slots_per_ring > 1:
                a = f"{element}-R{ring}-S{slots_per_ring}"
                b = f"{element}-R{ring}-S1"
                edges.append(BoardEdge(source=a, target=b, kind="intra"))

        for ring in range(1, rings):
            for slot_idx in range(1, slots_per_ring + 1):
                a = f"{element}-R{ring}-S{slot_idx}"
                b = f"{element}-R{ring + 1}-S{slot_idx}"
                edges.append(BoardEdge(source=a, target=b, kind="radial"))

    # 3) 元素边界桥接节点 + 桥接边
    for idx, element in enumerate(ELEMENTS):
        next_element = ELEMENTS[(idx + 1) % len(ELEMENTS)]
        for ring in range(1, rings + 1):
            for bridge_idx in range(1, bridges_per_boundary + 1):
                bridge_id = _bridge_node_id(element, next_element, ring, bridge_idx)
                bridge_node = BoardNode(
                    node_id=bridge_id,
                    element=element,
                    ring=ring,
                    index=bridge_idx,
                    type=NodeType.BRIDGE,
                    tags=("bridge", f"to:{next_element}"),
                    unlock_realm=_unlock_realm_for_type(NodeType.BRIDGE),
                )
                nodes.append(bridge_node)
                node_lookup[bridge_id] = bridge_node

                slot_a = ((bridge_idx - 1) % slots_per_ring) + 1
                slot_b = ((bridge_idx) % slots_per_ring) + 1
                left = f"{element}-R{ring}-S{slot_a}"
                right = f"{next_element}-R{ring}-S{slot_b}"
                edges.append(BoardEdge(source=bridge_id, target=left, kind="bridge"))
                edges.append(BoardEdge(source=bridge_id, target=right, kind="bridge"))

    layout = BoardLayout(
        nodes=nodes,
        edges=edges,
        rings=rings,
        slots_per_ring=slots_per_ring,
        bridges_per_boundary=bridges_per_boundary,
    )
    logger.info(
        "wuxing_board.generate done nodes=%s edges=%s",
        len(layout.nodes),
        len(layout.edges),
    )
    return layout


def count_nodes_by_element(layout: BoardLayout) -> Dict[str, int]:
    counts = {element: 0 for element in ELEMENTS}
    for node in layout.nodes:
        if node.element in counts and node.type != NodeType.BRIDGE:
            counts[node.element] += 1
    return counts


def total_node_count(layout: BoardLayout) -> int:
    return len(layout.nodes)


def validate_symmetry(layout: BoardLayout) -> None:
    counts = count_nodes_by_element(layout)
    values = set(counts.values())
    if len(values) != 1:
        raise ValueError(f"元素槽位数量不一致: {counts}")


if __name__ == "__main__":
    board = generate_wuxing_board()
    counts = count_nodes_by_element(board)
    print("element_counts:", counts)
    validate_symmetry(board)
    old_total = 8 * 4 + 3
    assert total_node_count(board) > old_total, "新棋盘节点数应大于旧版本"
