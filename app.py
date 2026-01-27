import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="五行同心环棋盘", layout="wide")

st.markdown(
    """
<style>
html, body, [class*="css"], .stApp {
  font-family: "Microsoft YaHei", "Noto Sans CJK SC", Arial, sans-serif;
}
</style>
""",
    unsafe_allow_html=True,
)

ELEMENTS = ["金", "木", "水", "火", "土"]
ELEMENT_COLORS = {
    "金": "#E6E6E6",
    "木": "#39D98A",
    "水": "#3AA0FF",
    "火": "#FF4D4D",
    "土": "#FFD166",
}
CORE_COLOR = "#9FE6FF"

TYPE_SYMBOL = {
    "small": "circle",
    "medium": "diamond",
    "keystone": "hexagon",
    "socket": "circle-open",
    "bridge": "square",
    "convert": "triangle-up",
    "core": "circle",
}
TYPE_SIZE = {
    "small": 9,
    "medium": 12,
    "keystone": 16,
    "socket": 14,
    "bridge": 12,
    "convert": 12,
    "core": 20,
}
TYPE_LINE = {
    "small": 1.2,
    "medium": 1.4,
    "keystone": 2.0,
    "socket": 1.8,
    "bridge": 1.6,
    "convert": 1.6,
    "core": 2.4,
}


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
    sector_idx: int
    slot_idx: int


@dataclass
class Edge:
    source: str
    target: str
    kind: str


@dataclass
class BoardData:
    nodes: List[Node]
    edges: List[Edge]
    radii: Dict[str, float]
    sector_span: float


def distribute_slots(total: int, sectors: int = 5) -> List[int]:
    base = total // sectors
    rem = total % sectors
    return [base + (1 if i < rem else 0) for i in range(sectors)]


def assign_type(ring: str, slot_idx: int, count: int) -> str:
    if ring == "Core":
        return "core"
    if ring == "Ring3" and slot_idx == 0:
        return "keystone"
    if ring == "Ring2" and slot_idx % 4 == 0:
        base = "medium"
    elif ring == "Ring1" and slot_idx % 3 == 0:
        base = "medium"
    else:
        base = "small"

    if base != "keystone":
        if slot_idx % 11 == 0:
            return "convert"
        if slot_idx % 7 == 0:
            return "socket"
        if slot_idx % 9 == 0:
            return "bridge"
    return base


def build_nodes() -> BoardData:
    nodes: List[Node] = []
    edges: List[Edge] = []

    sector_span = 2 * math.pi / 5
    base_radius = 1.2
    ring_gap = 0.9
    rings = [("Ring1", 12), ("Ring2", 20), ("Ring3", 28)]

    def polar(radius: float, angle: float) -> Tuple[float, float]:
        return radius * math.cos(angle), radius * math.sin(angle)

    nodes.append(
        Node(
            node_id="Core",
            ring="Core",
            element="Core",
            ntype="core",
            angle=0.0,
            radius=0.0,
            x=0.0,
            y=0.0,
            label="Core",
            sector_idx=-1,
            slot_idx=0,
        )
    )

    for ring_idx, (ring_name, total) in enumerate(rings, start=1):
        counts = distribute_slots(total, 5)
        for sector_idx, element in enumerate(ELEMENTS):
            count = counts[sector_idx]
            sector_start = sector_idx * sector_span
            for k in range(count):
                angle = sector_start + sector_span * (k + 0.5) / count
                radius = base_radius + ring_idx * ring_gap
                x, y = polar(radius, angle)
                ntype = assign_type(ring_name, k, count)
                node_id = f"{ring_name}-{element}-{k+1}"
                nodes.append(
                    Node(
                        node_id=node_id,
                        ring=ring_name,
                        element=element,
                        ntype=ntype,
                        angle=angle,
                        radius=radius,
                        x=x,
                        y=y,
                        label=f"{k+1}",
                        sector_idx=sector_idx,
                        slot_idx=k,
                    )
                )

    radii = {
        "Ring1": base_radius + 1 * ring_gap,
        "Ring2": base_radius + 2 * ring_gap,
        "Ring3": base_radius + 3 * ring_gap,
    }
    return BoardData(nodes=nodes, edges=edges, radii=radii, sector_span=sector_span)


def build_edges(nodes: List[Node]) -> List[Edge]:
    edges: List[Edge] = []

    by_ring = {r: [] for r in ["Ring1", "Ring2", "Ring3"]}
    by_ring_sector: Dict[Tuple[str, int], List[Node]] = {}

    for n in nodes:
        if n.ring in by_ring:
            by_ring[n.ring].append(n)
            key = (n.ring, n.sector_idx)
            by_ring_sector.setdefault(key, []).append(n)

    for ring in by_ring:
        ring_nodes = sorted(by_ring[ring], key=lambda n: n.angle)
        for i in range(len(ring_nodes)):
            a = ring_nodes[i]
            b = ring_nodes[(i + 1) % len(ring_nodes)]
            edges.append(Edge(a.node_id, b.node_id, "ring"))

    def connect_radial(r1: str, r2: str, per_sector: int = 3) -> None:
        for sector_idx in range(5):
            a_list = sorted(by_ring_sector.get((r1, sector_idx), []), key=lambda n: n.angle)
            b_list = sorted(by_ring_sector.get((r2, sector_idx), []), key=lambda n: n.angle)
            if not a_list or not b_list:
                continue
            k = min(per_sector, len(a_list), len(b_list))
            for i in range(k):
                idx_a = int(round((len(a_list) - 1) * (i + 0.5) / k))
                idx_b = int(round((len(b_list) - 1) * (i + 0.5) / k))
                edges.append(Edge(a_list[idx_a].node_id, b_list[idx_b].node_id, "radial"))

    connect_radial("Ring1", "Ring2", per_sector=3)
    connect_radial("Ring2", "Ring3", per_sector=3)

    core = next(n for n in nodes if n.ring == "Core")
    for sector_idx in range(5):
        ring1 = sorted(by_ring_sector.get(("Ring1", sector_idx), []), key=lambda n: n.angle)
        if ring1:
            mid = ring1[len(ring1) // 2]
            edges.append(Edge(core.node_id, mid.node_id, "core"))

    return edges


def build_figure(nodes: List[Node], edges: List[Edge], show_edges: bool, show_rings: bool, show_sectors: bool,
                 show_labels: bool, highlight_ids: List[str], visible_ids: set[str]) -> go.Figure:
    fig = go.Figure()

    fig.update_layout(
        paper_bgcolor="#0b0f14",
        plot_bgcolor="#0b0f14",
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family="Microsoft YaHei, Noto Sans CJK SC, Arial", color="#E6F0FF"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    # Compute ranges (centered)
    max_radius = max(n.radius for n in nodes if n.ring != "Core")
    label_pad = 0.8
    r_limit = max_radius + label_pad
    fig.update_xaxes(range=[-r_limit, r_limit])
    fig.update_yaxes(range=[-r_limit, r_limit])

    # Vignette using multiple faint circles
    for i, alpha in enumerate([0.07, 0.05, 0.04, 0.03]):
        r = r_limit * (1.1 + i * 0.08)
        fig.add_shape(
            type="circle",
            xref="x",
            yref="y",
            x0=-r,
            y0=-r,
            x1=r,
            y1=r,
            line=dict(color=f"rgba(0,0,0,{alpha})", width=1),
            fillcolor=f"rgba(0,0,0,{alpha})",
            layer="below",
        )

    # Sector faint lines / plates
    sector_span = 2 * math.pi / 5
    inner_r = min(n.radius for n in nodes if n.ring != "Core")
    outer_r = max_radius

    if show_sectors:
        for idx, element in enumerate(ELEMENTS):
            start = idx * sector_span
            end = start + sector_span
            # faint radial lines
            for ang in [start, end]:
                x1, y1 = inner_r * math.cos(ang), inner_r * math.sin(ang)
                x2, y2 = outer_r * math.cos(ang), outer_r * math.sin(ang)
                fig.add_trace(
                    go.Scatter(
                        x=[x1, x2],
                        y=[y1, y2],
                        mode="lines",
                        line=dict(color="rgba(200,210,220,0.08)", width=1),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            # faint sector plate
            fig.add_shape(
                type="path",
                path=f"M {inner_r*math.cos(start):.4f},{inner_r*math.sin(start):.4f} "
                     f"L {outer_r*math.cos(start):.4f},{outer_r*math.sin(start):.4f} "
                     f"A {outer_r:.4f},{outer_r:.4f} 0 0 1 {outer_r*math.cos(end):.4f},{outer_r*math.sin(end):.4f} "
                     f"L {inner_r*math.cos(end):.4f},{inner_r*math.sin(end):.4f} "
                     f"A {inner_r:.4f},{inner_r:.4f} 0 0 0 {inner_r*math.cos(start):.4f},{inner_r*math.sin(start):.4f} Z",
                line=dict(color="rgba(0,0,0,0)"),
                fillcolor=f"rgba(255,255,255,0.04)",
                layer="below",
            )

    # Ring lines
    if show_rings:
        ring_radii = [inner_r, inner_r + 0.9, inner_r + 1.8]
        for i, r in enumerate(ring_radii):
            opacity = 0.35 + i * 0.07
            fig.add_shape(
                type="circle",
                xref="x",
                yref="y",
                x0=-r,
                y0=-r,
                x1=r,
                y1=r,
                line=dict(color=f"rgba(42,52,64,{opacity})", width=1.2),
                layer="below",
            )

    # Labels
    label_radius = outer_r + 0.5
    if show_labels:
        label_x = []
        label_y = []
        label_text = []
        for i, element in enumerate(ELEMENTS):
            angle = i * sector_span + sector_span / 2
            x, y = label_radius * math.cos(angle), label_radius * math.sin(angle)
            label_x.append(x)
            label_y.append(y)
            label_text.append(element)
        fig.add_trace(
            go.Scatter(
                x=label_x,
                y=label_y,
                mode="text",
                text=label_text,
                textfont=dict(color="#DFE8F2", size=18, family="Microsoft YaHei, Noto Sans CJK SC, Arial"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Edges
    if show_edges:
        ring_x, ring_y = [], []
        radial_x, radial_y = [], []
        for e in edges:
            if e.source not in visible_ids or e.target not in visible_ids:
                continue
            a = next(n for n in nodes if n.node_id == e.source)
            b = next(n for n in nodes if n.node_id == e.target)
            if e.kind == "ring":
                ring_x += [a.x, b.x, None]
                ring_y += [a.y, b.y, None]
            else:
                radial_x += [a.x, b.x, None]
                radial_y += [a.y, b.y, None]

        fig.add_trace(
            go.Scatter(
                x=ring_x,
                y=ring_y,
                mode="lines",
                line=dict(color="rgba(110,140,160,0.22)", width=1),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=radial_x,
                y=radial_y,
                mode="lines",
                line=dict(color="rgba(110,150,180,0.3)", width=1.1),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Node glow
    glow_x = []
    glow_y = []
    glow_color = []
    glow_size = []
    for n in nodes:
        if n.node_id not in visible_ids:
            continue
        color = CORE_COLOR if n.ring == "Core" else ELEMENT_COLORS[n.element]
        glow_x.append(n.x)
        glow_y.append(n.y)
        glow_color.append(color)
        size = TYPE_SIZE[n.ntype] + (6 if n.ntype == "keystone" or n.ring == "Core" else 4)
        glow_size.append(size)

    fig.add_trace(
        go.Scatter(
            x=glow_x,
            y=glow_y,
            mode="markers",
            marker=dict(
                symbol="circle",
                size=glow_size,
                color=glow_color,
                opacity=0.12,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Nodes
    xs, ys, colors, symbols, sizes, lines, texts, hovers = [], [], [], [], [], [], [], []
    for n in nodes:
        if n.node_id not in visible_ids:
            continue
        color = CORE_COLOR if n.ring == "Core" else ELEMENT_COLORS[n.element]
        base_size = TYPE_SIZE[n.ntype]
        if n.node_id in highlight_ids:
            base_size += 4
        xs.append(n.x)
        ys.append(n.y)
        colors.append(color)
        symbols.append(TYPE_SYMBOL[n.ntype])
        sizes.append(base_size)
        lines.append(TYPE_LINE[n.ntype])
        texts.append(n.label if show_labels and n.ring != "Core" else "")
        hovers.append(
            f"{n.node_id}<br>元素: {n.element}<br>环: {n.ring}<br>类型: {n.ntype}<br>角度: {n.angle:.2f}<br>半径: {n.radius:.2f}"
        )

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=texts,
            textposition="top center",
            textfont=dict(color="#CFE0F2", size=10),
            marker=dict(
                symbol=symbols,
                size=sizes,
                color=["rgba(10,15,20,0.8)" if n != "Core" else CORE_COLOR for n in ["X"]],
                line=dict(color=colors, width=lines),
            ),
            hovertext=hovers,
            hoverinfo="text",
            showlegend=False,
        )
    )

    return fig


def main() -> None:
    st.title("规整的五行同心环棋盘")
    st.caption("严格几何规则生成：五行扇区 + 同心环 + 规则连线")

    board = build_nodes()
    edges = build_edges(board.nodes)

    with st.sidebar:
        st.header("筛选与显示")
        element_filter = st.selectbox("五行筛选", ["All"] + ELEMENTS)
        ring_filter = st.selectbox("环筛选", ["All", "Core", "Ring1", "Ring2", "Ring3"])
        type_filter = st.selectbox(
            "类型筛选", ["All", "small", "medium", "keystone", "socket", "bridge", "convert", "core"]
        )
        search_query = st.text_input("搜索 node_id / 关键字")
        st.markdown("---")
        show_sectors = st.toggle("显示扇区底色", value=True)
        show_edges = st.toggle("显示连线", value=True)
        show_rings = st.toggle("显示环线", value=True)
        show_labels = st.toggle("显示节点编号", value=False)

    def node_visible(n: Node) -> bool:
        if element_filter != "All" and n.element != element_filter:
            return False
        if ring_filter != "All" and n.ring != ring_filter:
            return False
        if type_filter != "All" and n.ntype != type_filter:
            return False
        return True

    visible_nodes = [n for n in board.nodes if node_visible(n)]
    visible_ids = {n.node_id for n in visible_nodes}

    highlight_ids = []
    if search_query:
        q = search_query.strip().lower()
        for n in board.nodes:
            if q in n.node_id.lower() or q in n.element.lower() or q in n.ntype.lower() or q in n.ring.lower():
                highlight_ids.append(n.node_id)

    fig = build_figure(
        board.nodes,
        edges,
        show_edges,
        show_rings,
        show_sectors,
        show_labels,
        highlight_ids,
        visible_ids,
    )

    # auto height based on container width
    height = 820
    fig.update_layout(height=height)

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
