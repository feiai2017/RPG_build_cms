from __future__ import annotations

import hashlib
import json
import math
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

import streamlit as st

from board_state import BoardState, Edge, Node

st.set_page_config(layout="wide", page_title="五行天赋盘 · 旋转装置", page_icon="⚙️")

CONFIG_DIR = Path("board_configs")
PRESET_DIR = Path("presets")

REALMS = {
    "炼气": {"qi_cap": 10, "rings": ["inner", "mid"]},
    "筑基": {"qi_cap": 14, "rings": ["inner", "mid"]},
    "金丹": {"qi_cap": 18, "rings": ["inner", "mid", "outer"]},
    "元婴": {"qi_cap": 22, "rings": ["inner", "mid", "outer", "inner_core"]},
    "化神": {"qi_cap": 26, "rings": ["inner", "mid", "outer", "inner_core"]},
    "合体": {"qi_cap": 30, "rings": ["inner", "mid", "outer", "inner_core"]},
    "大乘": {"qi_cap": 34, "rings": ["inner", "mid", "outer", "inner_core"]},
    "陆地神仙": {"qi_cap": 40, "rings": ["inner", "mid", "outer", "inner_core"]},
}

CSS = """
<style>
  .stApp { background: #050505; color: #dffbff; font-family: 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif; }
  .board-wrap { display:flex; justify-content:center; }
  .board { width: 760px; max-width: 90vw; aspect-ratio: 1; margin: 12px auto; }
  .panel { background: rgba(8,12,18,0.85); border: 1px solid rgba(0,255,255,0.2); border-radius: 12px; padding: 12px; }
  .kv { display:flex; justify-content:space-between; padding: 4px 0; }
  .badge { padding: 2px 8px; border-radius: 999px; border:1px solid rgba(0,255,255,0.3); }
  .svg-edge { stroke: rgba(120,160,180,0.2); stroke-width: 1.2; }
  .svg-edge.active { stroke: rgba(0,255,255,0.6); stroke-width: 1.6; }
  .svg-edge.off { stroke: rgba(180,80,80,0.35); stroke-dasharray: 4 4; }
  .svg-node { fill: rgba(6,10,18,0.85); stroke-width: 1.4; }
  .svg-node.powered { filter: drop-shadow(0 0 6px rgba(0,255,255,0.7)); }
  .svg-node.invested { fill: rgba(14,24,36,0.9); }
  .svg-node.off { fill: rgba(20,20,20,0.7); stroke: #666; }
  .tiny { font-size: 12px; color: #9fb7c5; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def read_json(path: Path) -> Tuple[dict, str, float]:
    raw = path.read_bytes()
    cfg_hash = hashlib.sha256(raw).hexdigest()[:10]
    mtime = path.stat().st_mtime
    data = json.loads(raw.decode("utf-8-sig"))
    return data, cfg_hash, mtime


def default_config_path() -> Path:
    return CONFIG_DIR / "base.json"


def build_nodes(cfg: dict) -> List[Node]:
    nodes: List[Node] = []
    trigrams = cfg["trigrams"]
    trigram_elements = cfg["trigram_elements"]

    # core
    nodes.append(
        Node(
            id="core",
            elem="土",
            ring="inner",
            slot_idx=-1,
            base_theta=0.0,
            r=0.0,
            size="major",
            trigram="坤",
            effects={"core": 1},
            invested=True,
        )
    )

    for ring_id, ring_cfg in cfg["rings"].items():
        slots = ring_cfg["slots"]
        radius = ring_cfg["radius"]
        for idx in range(slots):
            theta = 360.0 * idx / slots
            tri = trigrams[int(idx / slots * len(trigrams)) % len(trigrams)]
            elem = trigram_elements.get(tri, "土")
            size = "major" if idx == 0 else ring_cfg.get("size", "small")
            nodes.append(
                Node(
                    id=f"{ring_id}_{idx}",
                    elem=elem,
                    ring=ring_id,
                    slot_idx=idx,
                    base_theta=theta,
                    r=radius,
                    size=size,
                    trigram=tri,
                    effects={"power": 1 if size == "small" else 2},
                )
            )
    return nodes


def load_preset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def init_board_state(cfg: dict, cfg_hash: str, preset: dict | None = None) -> BoardState:
    nodes = build_nodes(cfg)
    ring_rot = {rid: 0.0 for rid in cfg["rings"].keys()}
    ring_rot.setdefault("inner", 0.0)
    if preset:
        ring_rot.update(preset.get("rot", {}))
        invested = set(preset.get("invested", []))
        for node in nodes:
            if node.id in invested:
                node.invested = True
    realm = preset.get("realm", "金丹") if preset else "金丹"
    qi_cap = REALMS[realm]["qi_cap"]
    return BoardState(
        realm=realm,
        qi_cap=qi_cap,
        qi_used=0.0,
        ring_rot_deg=ring_rot,
        nodes=nodes,
        edges=[],
        ruleset_version=cfg.get("ruleset_version", "v1"),
        cfg_hash=cfg_hash,
    )


def node_theta(node: Node, rot: Dict[str, float]) -> float:
    return node.base_theta + rot.get(node.ring, 0.0)


def angle_diff(a: float, b: float) -> float:
    diff = abs((a - b) % 360)
    return min(diff, 360 - diff)


def build_edges(state: BoardState, cfg: dict) -> List[Edge]:
    nodes = {n.id: n for n in state.nodes}
    edges: List[Edge] = []

    # ring edges
    for ring_id, ring_cfg in cfg["rings"].items():
        slots = ring_cfg["slots"]
        for idx in range(slots):
            a = f"{ring_id}_{idx}"
            b = f"{ring_id}_{(idx + 1) % slots}"
            if a in nodes and b in nodes:
                edges.append(Edge(a=a, b=b, kind="link", active=True))

    # bridges across rings
    threshold = cfg.get("bridge_threshold_deg", 12)
    bridges = cfg.get("bridges", [{"a": "inner", "b": "mid"}, {"a": "mid", "b": "outer"}])
    for bridge in bridges:
        ra = bridge["a"]
        rb = bridge["b"]
        if ra not in cfg["rings"] or rb not in cfg["rings"]:
            continue
        slots_a = cfg["rings"][ra]["slots"]
        slots_b = cfg["rings"][rb]["slots"]
        elig_a = set(cfg["rings"][ra].get("bridge_slots", []))
        elig_b = set(cfg["rings"][rb].get("bridge_slots", []))
        for idx in elig_a:
            a = f"{ra}_{idx}"
            if a not in nodes:
                continue
            theta_a = node_theta(nodes[a], state.ring_rot_deg)
            best = None
            best_diff = 999
            for j in elig_b:
                b = f"{rb}_{j}"
                if b not in nodes:
                    continue
                diff = angle_diff(theta_a, node_theta(nodes[b], state.ring_rot_deg))
                if diff < best_diff:
                    best = b
                    best_diff = diff
            if not best:
                continue
            active = best_diff <= threshold
            reason = "" if active else "旋转后不相邻断线"
            edges.append(Edge(a=a, b=best, kind="link", active=active, reason=reason))

    return edges


def recompute_connectivity(state: BoardState, cfg: dict) -> Dict[str, str]:
    ring_allowed = set(REALMS[state.realm]["rings"])
    node_map = {n.id: n for n in state.nodes}
    for node in state.nodes:
        node.powered = False

    edges = build_edges(state, cfg)
    for edge in edges:
        if node_map[edge.a].ring not in ring_allowed or node_map[edge.b].ring not in ring_allowed:
            edge.active = False
            edge.reason = "境界未解锁"

    # BFS for power
    qi_cap = REALMS[state.realm]["qi_cap"]
    state.qi_cap = qi_cap
    qi_used = 0.0
    powered = set(["core"])
    queue = ["core"]
    node_reason: Dict[str, str] = {}

    while queue:
        current = queue.pop(0)
        for edge in edges:
            if not edge.active:
                continue
            if edge.a != current and edge.b != current:
                continue
            nxt = edge.b if edge.a == current else edge.a
            if nxt in powered:
                continue
            node = node_map[nxt]
            if not node.invested:
                continue
            cost = 1.0 if node.size == "small" else 2.0
            if qi_used + cost > qi_cap:
                node_reason[nxt] = "带宽不足"
                continue
            qi_used += cost
            powered.add(nxt)
            queue.append(nxt)

    for node in state.nodes:
        if node.id in powered:
            node.powered = True
        elif node.invested and node.id not in node_reason:
            node_reason[node.id] = "断电：连接断开"

    state.qi_used = round(qi_used, 1)
    state.edges = edges
    return node_reason


def build_svg(state: BoardState, cfg: dict, node_reason: Dict[str, str]) -> str:
    size = 760
    cx = cy = size / 2
    nodes = {n.id: n for n in state.nodes}

    def polar(r: float, deg: float) -> Tuple[float, float]:
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    svg = [
        f"<svg class='board' viewBox='0 0 {size} {size}' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<filter id='glow'><feGaussianBlur stdDeviation='3'/></filter>",
        "</defs>",
    ]

    # rings
    for ring_id, ring_cfg in cfg["rings"].items():
        if ring_id not in REALMS[state.realm]["rings"]:
            continue
        svg.append(
            f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{ring_cfg['radius']}' fill='none' stroke='rgba(60,90,110,0.5)' stroke-width='1.2' />"
        )

    # edges
    for edge in state.edges:
        a = nodes.get(edge.a)
        b = nodes.get(edge.b)
        if not a or not b:
            continue
        if a.ring not in REALMS[state.realm]["rings"] or b.ring not in REALMS[state.realm]["rings"]:
            continue
        ax, ay = polar(a.r, node_theta(a, state.ring_rot_deg))
        bx, by = polar(b.r, node_theta(b, state.ring_rot_deg))
        cls = "svg-edge active" if edge.active else "svg-edge off"
        svg.append(f"<line class='{cls}' x1='{ax:.1f}' y1='{ay:.1f}' x2='{bx:.1f}' y2='{by:.1f}' />")

    # nodes
    for node in state.nodes:
        if node.ring not in REALMS[state.realm]["rings"]:
            continue
        x, y = polar(node.r, node_theta(node, state.ring_rot_deg))
        size = 8 if node.size == "small" else 12
        cls = "svg-node"
        if node.invested:
            cls += " invested"
        if node.powered:
            cls += " powered"
        if node.invested and not node.powered:
            cls += " off"
        color = cfg["colors"].get(node.elem, "#00ffff")
        svg.append(
            f"<circle class='{cls}' cx='{x:.1f}' cy='{y:.1f}' r='{size}' stroke='{color}' />"
        )
        svg.append(f"<text x='{x:.1f}' y='{y - 10:.1f}' fill='#8fd0df' font-size='10' text-anchor='middle'>{node.slot_idx if node.slot_idx>=0 else '核'}</text>")

    svg.append("</svg>")
    return "".join(svg)


def export_board_state(state: BoardState) -> str:
    return json.dumps(asdict(state), ensure_ascii=False, indent=2)


def get_board_state(cfg: dict, cfg_hash: str) -> BoardState:
    if "board_state" not in st.session_state:
        st.session_state.board_state = init_board_state(cfg, cfg_hash)
    return st.session_state.board_state


def apply_rotation(state: BoardState, ring: str, delta: float, animate: bool, cfg: dict, placeholder) -> Dict[str, str]:
    if ring not in state.ring_rot_deg:
        return {}
    if not animate:
        state.ring_rot_deg[ring] = (state.ring_rot_deg[ring] + delta) % 360
        return recompute_connectivity(state, cfg)

    frames = 30
    step = delta / frames
    node_reason: Dict[str, str] = {}
    for _ in range(frames):
        state.ring_rot_deg[ring] = (state.ring_rot_deg[ring] + step) % 360
        node_reason = recompute_connectivity(state, cfg)
        svg = build_svg(state, cfg, node_reason)
        placeholder.markdown(f"<div class='board-wrap'>{svg}</div>", unsafe_allow_html=True)
        time.sleep(0.02)
    return node_reason


def ensure_dirs():
    CONFIG_DIR.mkdir(exist_ok=True)
    PRESET_DIR.mkdir(exist_ok=True)


def load_presets() -> List[Path]:
    return sorted(PRESET_DIR.glob("*.json"))


def update_board_state_hash(state: BoardState, cfg_hash: str, ruleset: str):
    state.cfg_hash = cfg_hash
    state.ruleset_version = ruleset


def main():
    ensure_dirs()

    cfg_path = default_config_path()
    cfg, cfg_hash, cfg_mtime = read_json(cfg_path)

    state = get_board_state(cfg, cfg_hash)
    update_board_state_hash(state, cfg_hash, cfg.get("ruleset_version", "v1"))

    st.sidebar.markdown("### 配置")
    st.sidebar.markdown(f"cfg_hash: `{state.cfg_hash}`")
    st.sidebar.markdown(f"ruleset_version: `{state.ruleset_version}`")
    st.sidebar.markdown(f"cfg_mtime: `{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cfg_mtime))}`")

    if st.sidebar.button("Reload Config"):
        cfg, cfg_hash, cfg_mtime = read_json(cfg_path)
        st.session_state.board_state = init_board_state(cfg, cfg_hash)
        st.rerun()

    st.sidebar.download_button("Export Current", export_board_state(state), file_name="board_state.json")

    if st.sidebar.button("Reset Session"):
        st.session_state.pop("board_state", None)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Presets")
    preset_files = load_presets()
    preset_names = [p.stem for p in preset_files]
    preset_sel = st.sidebar.selectbox("选择预设", preset_names) if preset_names else None
    if preset_sel and st.sidebar.button("Load Preset"):
        preset = load_preset(PRESET_DIR / f"{preset_sel}.json")
        st.session_state.board_state = init_board_state(cfg, cfg_hash, preset)
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 操作")
    state.realm = st.sidebar.selectbox("境界", list(REALMS.keys()), index=list(REALMS.keys()).index(state.realm))

    ring_sel = st.sidebar.selectbox("旋转环", ["inner", "mid", "outer", "inner_core"])
    continuous = st.sidebar.toggle("连续旋转", value=False)

    rot_placeholder = st.empty()

    if st.sidebar.button("↺ -15°"):
        node_reason = apply_rotation(state, ring_sel, -15, continuous, cfg, rot_placeholder)
        st.session_state.board_state = state
        st.rerun()

    if st.sidebar.button("↻ +15°"):
        node_reason = apply_rotation(state, ring_sel, 15, continuous, cfg, rot_placeholder)
        st.session_state.board_state = state
        st.rerun()

    node_reason = recompute_connectivity(state, cfg)

    # header
    st.markdown("## 五行天赋盘 · 电路旋转装置")
    st.caption("点击节点投资，旋转改变连通性。带宽不足会断电。")

    # info panels
    left, center, right = st.columns([1.1, 2.2, 1.2])

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("**BoardState**")
        st.markdown(f"<div class='kv'><span>境界</span><span class='badge'>{state.realm}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>Qi</span><span>{state.qi_used}/{state.qi_cap}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>旋转</span><span>{state.ring_rot_deg}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>cfg_hash</span><span>{state.cfg_hash}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kv'><span>ruleset</span><span>{state.ruleset_version}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with center:
        svg = build_svg(state, cfg, node_reason)
        st.markdown(f"<div class='board-wrap'>{svg}</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        node_ids = [n.id for n in state.nodes if n.ring in REALMS[state.realm]["rings"]]
        selected_id = st.selectbox("节点详情", node_ids, index=node_ids.index("core") if "core" in node_ids else 0)
        selected = next(n for n in state.nodes if n.id == selected_id)
        st.markdown(f"**元素**: {selected.elem}")
        st.markdown(f"**卦象**: {selected.trigram}")
        st.markdown(f"**状态**: {'通电' if selected.powered else ('已点亮' if selected.invested else '未点亮')}")
        if selected.invested and not selected.powered:
            st.markdown(f"**断电原因**: {node_reason.get(selected.id, '断电')}")
        if st.button("切换点亮"):
            selected.invested = not selected.invested
            st.session_state.board_state = state
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # re-slot for land realm
    if state.realm == "陆地神仙":
        st.markdown("### 槽位重构")
        outer_nodes = [n for n in state.nodes if n.ring == "outer"]
        node_pick = st.selectbox("选择外环节点", [n.id for n in outer_nodes])
        target_slot = st.selectbox("目标槽位", list(range(cfg["rings"]["outer"]["slots"])))
        if st.button("应用重构"):
            node = next(n for n in state.nodes if n.id == node_pick)
            other = next((n for n in outer_nodes if n.slot_idx == target_slot and n.id != node.id), None)
            if other:
                other.slot_idx, node.slot_idx = node.slot_idx, other.slot_idx
                other.base_theta = 360.0 * other.slot_idx / cfg["rings"]["outer"]["slots"]
                node.base_theta = 360.0 * node.slot_idx / cfg["rings"]["outer"]["slots"]
                other.id = f"outer_{other.slot_idx}"
                node.id = f"outer_{node.slot_idx}"
            else:
                node.slot_idx = target_slot
                node.base_theta = 360.0 * target_slot / cfg["rings"]["outer"]["slots"]
                node.id = f"outer_{target_slot}"
            st.session_state.board_state = state
            st.rerun()


if __name__ == "__main__":
    main()
