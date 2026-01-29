from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Node:
    id: str
    elem: str
    ring: str  # inner/mid/outer/inner_core
    slot_idx: int
    base_theta: float
    r: float
    size: str  # small/major
    trigram: str
    effects: Dict[str, float]
    invested: bool = False
    powered: bool = False


@dataclass
class Edge:
    a: str
    b: str
    kind: str  # link/power
    active: bool = False
    reason: str = ''


@dataclass
class BoardState:
    realm: str
    qi_cap: float
    qi_used: float
    ring_rot_deg: Dict[str, float]
    nodes: List[Node]
    edges: List[Edge]
    ruleset_version: str
    cfg_hash: str
