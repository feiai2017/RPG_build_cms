# -*- coding: utf-8 -*-
"""
五行棋盘规则评估（相生/相克/循环奖励）
"""

from dataclasses import dataclass
import logging
from typing import Dict, List, Set, Tuple

from wuxing_board import (
    BoardLayout,
    BoardNode,
    NodeType,
    ELEMENTS,
    GENERATION_ORDER,
    DESTRUCTION_ORDER,
    realm_rank,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleEffect:
    kind: str
    detail: str


@dataclass(frozen=True)
class RuleResult:
    generation_links: List[Tuple[str, str]]
    generation_bonus: float
    destruction_effects: List[RuleEffect]
    loop_unlocked: bool
    loop_effect: RuleEffect | None


def evaluate_wuxing_rules(
    layout: BoardLayout,
    selected_nodes: Set[str],
    realm: str = "炼气",
) -> RuleResult:
    logger.info(
        "wuxing_rules.evaluate start realm=%s selected=%s",
        realm,
        len(selected_nodes),
    )
    node_lookup: Dict[str, BoardNode] = {node.node_id: node for node in layout.nodes}

    selected_elements = set()
    selected_convert_elements = set()
    selected_bridges: List[BoardNode] = []

    for node_id in selected_nodes:
        node = node_lookup.get(node_id)
        if not node:
            continue
        if node.type == NodeType.BRIDGE:
            selected_bridges.append(node)
            continue
        if node.element in ELEMENTS:
            selected_elements.add(node.element)
        if node.type == NodeType.CONVERT:
            selected_convert_elements.add(node.element)

    # 相生链路
    generation_links: List[Tuple[str, str]] = []
    for bridge in selected_bridges:
        to_tag = next((tag for tag in bridge.tags if tag.startswith("to:")), None)
        if not to_tag:
            continue
        target = to_tag.split(":", 1)[1]
        source = bridge.element
        if source in selected_elements and target in selected_elements:
            if (source, target) not in generation_links:
                generation_links.append((source, target))

    generation_bonus = 0.05 * len(generation_links)

    # 相克规则重写（需达到金丹）
    destruction_effects: List[RuleEffect] = []
    if realm_rank(realm) >= realm_rank("金丹"):
        for source in selected_convert_elements:
            target = DESTRUCTION_ORDER.get(source)
            if target and target in selected_elements:
                destruction_effects.append(
                    RuleEffect(
                        kind="convert",
                        detail=f"{source} 克 {target}：触发元素转化/成本减免",
                    )
                )

    if realm_rank(realm) >= realm_rank("元婴"):
        socket_nodes = [
            node_id for node_id in selected_nodes
            if node_lookup.get(node_id) and node_lookup[node_id].type == NodeType.SOCKET
        ]
        if socket_nodes:
            destruction_effects.append(
                RuleEffect(
                    kind="socket",
                    detail=f"元婴解锁：{len(socket_nodes)} 个插槽触发范围增益",
                )
            )

    # 五行循环奖励
    loop_required = {(element, GENERATION_ORDER[element]) for element in ELEMENTS}
    loop_unlocked = loop_required.issubset(set(generation_links))
    loop_effect = None
    if loop_unlocked:
        loop_effect = RuleEffect(
            kind="circuit",
            detail="形成完整五行循环：解锁回路效果（周期触发/连击增幅）",
        )

    result = RuleResult(
        generation_links=generation_links,
        generation_bonus=generation_bonus,
        destruction_effects=destruction_effects,
        loop_unlocked=loop_unlocked,
        loop_effect=loop_effect,
    )
    logger.info(
        "wuxing_rules.evaluate done gen_links=%s effects=%s loop=%s",
        len(result.generation_links),
        len(result.destruction_effects),
        result.loop_unlocked,
    )
    return result


def example_builds(layout: BoardLayout) -> List[Dict[str, object]]:
    """提供示例构筑，用于快速验证规则输出。"""
    logger.info("wuxing_rules.presets load layout_nodes=%s", len(layout.nodes))
    nodes_by_id = {node.node_id: node for node in layout.nodes}
    builds: List[Dict[str, object]] = []

    # 示例1：完整相生循环
    chain_nodes = set()
    for element in ELEMENTS:
        chain_nodes.add(f"{element}-R1-S1")
    for element in ELEMENTS:
        next_element = GENERATION_ORDER[element]
        chain_nodes.add(f"bridge-{element}-{next_element}-R1-B1")
    builds.append({
        "name": "相生循环构筑",
        "selected_nodes": {n for n in chain_nodes if n in nodes_by_id},
        "description": "五行全链路连接，触发循环奖励",
    })

    # 示例2：相克转化构筑
    convert_nodes = set()
    convert_nodes.add("木-R4-S1")  # CONVERT节点
    convert_nodes.add("土-R1-S1")
    builds.append({
        "name": "相克转化构筑",
        "selected_nodes": {n for n in convert_nodes if n in nodes_by_id},
        "description": "触发相克规则重写效果",
    })

    return builds
