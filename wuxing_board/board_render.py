# -*- coding: utf-8 -*-
"""五行棋盘渲染（Plotly）"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set
import plotly.graph_objects as go

from .board_gen import BoardEdge, BoardNode, NodeType


ELEMENT_COLORS = {
    "木": "#2dff6f",
    "火": "#ff3b30",
    "土": "#ffd34d",
    "金": "#f5f5f5",
    "水": "#2f80ff",
}

NODE_STYLE = {
    NodeType.SMALL: {"symbol": "circle", "size": 9, "line_width": 1.0},
    NodeType.MEDIUM: {"symbol": "diamond", "size": 13, "line_width": 1.5},
    NodeType.KEYSTONE: {"symbol": "hexagon", "size": 19, "line_width": 2.5},
    NodeType.SOCKET: {"symbol": "diamond", "size": 17, "line_width": 2.0},
    NodeType.BRIDGE: {"symbol": "hexagon", "size": 13, "line_width": 2.0},
    NodeType.CONVERT: {"symbol": "hexagon", "size": 17, "line_width": 2.0},
}


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"rgba(255,255,255,{alpha})"
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _edge_trace(
    nodes: Dict[str, BoardNode],
    edges: Iterable[BoardEdge],
    kind: str,
    color: str,
    width: float,
) -> go.Scatter:
    xs: List[float] = []
    ys: List[float] = []
    for edge in edges:
        if edge.kind != kind:
            continue
        src = nodes.get(edge.source)
        tgt = nodes.get(edge.target)
        if not src or not tgt:
            continue
        xs.extend([src.x, tgt.x, None])
        ys.extend([src.y, tgt.y, None])
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(color=color, width=width),
        hoverinfo="skip",
        showlegend=False,
    )


def render_board_plotly(
    nodes: List[BoardNode],
    edges: List[BoardEdge],
    highlight_element: Optional[str] = None,
    highlight_type: Optional[NodeType] = None,
    show_bridges: bool = True,
    show_labels: bool = True,
    show_ring_guides: bool = True,
    selected_nodes: Optional[Set[str]] = None,
    height: int = 780,
    hovered_node: Optional[str] = None,
    search_matches: Optional[Set[str]] = None,
) -> go.Figure:
    node_lookup = {node.node_id: node for node in nodes}

    fig = go.Figure()

    # sector plates (behind nodes)
    sector_span = 360 / len(ELEMENT_COLORS)
    sector_margin = 6.0
    radii = [(n.x ** 2 + n.y ** 2) ** 0.5 for n in nodes if n.type != NodeType.BRIDGE]
    outer_radius = max(radii) + 0.6 if radii else 4.0
    inner_radius = 0.4

    def _polar(radius: float, angle_deg: float) -> tuple[float, float]:
        import math

        rad = math.radians(angle_deg)
        return radius * math.cos(rad), radius * math.sin(rad)

    for idx, element in enumerate(ELEMENT_COLORS.keys()):
        base = -90 + idx * sector_span
        start = base + sector_margin
        end = base + sector_span - sector_margin
        x1, y1 = _polar(outer_radius, start)
        x2, y2 = _polar(outer_radius, end)
        x3, y3 = _polar(inner_radius, end)
        x4, y4 = _polar(inner_radius, start)
        large = 1 if (end - start) % 360 > 180 else 0
        path = (
            f"M {x1:.3f},{y1:.3f} "
            f"A {outer_radius:.3f},{outer_radius:.3f} 0 {large} 1 {x2:.3f},{y2:.3f} "
            f"L {x3:.3f},{y3:.3f} "
            f"A {inner_radius:.3f},{inner_radius:.3f} 0 {large} 0 {x4:.3f},{y4:.3f} Z"
        )
        fill = _hex_to_rgba(ELEMENT_COLORS[element], 0.10)
        stroke = _hex_to_rgba(ELEMENT_COLORS[element], 0.18)
        fig.add_shape(
            type="path",
            path=path,
            fillcolor=fill,
            line=dict(color=stroke, width=1),
            layer="below",
        )

    # edges
    active_nodes = set(selected_nodes or [])
    if hovered_node:
        active_nodes.add(hovered_node)
    if search_matches:
        active_nodes.update(search_matches)
    dimmed = bool(active_nodes)

    base_intra_alpha = 0.05 if dimmed else 0.12
    base_bridge_alpha = 0.10 if dimmed else 0.22

    fig.add_trace(
        _edge_trace(node_lookup, edges, "intra", f"rgba(255,255,255,{base_intra_alpha})", 0.8)
    )
    fig.add_trace(
        _edge_trace(node_lookup, edges, "radial", f"rgba(255,255,255,{base_intra_alpha})", 0.8)
    )
    if show_bridges:
        fig.add_trace(
            _edge_trace(node_lookup, edges, "bridge", f"rgba(0,255,255,{base_bridge_alpha})", 1.4)
        )

    if active_nodes:
        highlight_edges = [
            e for e in edges if e.source in active_nodes or e.target in active_nodes
        ]
        fig.add_trace(
            _edge_trace(node_lookup, highlight_edges, "intra", "rgba(0,255,255,0.65)", 2.0)
        )
        fig.add_trace(
            _edge_trace(node_lookup, highlight_edges, "radial", "rgba(0,255,255,0.65)", 2.0)
        )
        if show_bridges:
            fig.add_trace(
                _edge_trace(node_lookup, highlight_edges, "bridge", "rgba(0,255,255,0.85)", 2.4)
            )

    # ring guides (based on radius from origin)
    if show_ring_guides:
        rings = sorted({node.ring for node in nodes if node.type != NodeType.BRIDGE})
        for ring in rings:
            ring_nodes = [n for n in nodes if n.ring == ring and n.type != NodeType.BRIDGE]
            if not ring_nodes:
                continue
            radius = (sum((n.x ** 2 + n.y ** 2) ** 0.5 for n in ring_nodes) / len(ring_nodes))
            fig.add_shape(
                type="circle",
                xref="x",
                yref="y",
                x0=-radius,
                y0=-radius,
                x1=radius,
                y1=radius,
                line=dict(color="rgba(0,255,255,0.10)", width=1, dash="dot"),
            )

    # nodes by type for distinct symbols
    for node_type in NodeType:
        if node_type == NodeType.BRIDGE and not show_bridges:
            continue
        type_nodes = [n for n in nodes if n.type == node_type]
        if not type_nodes:
            continue
        xs = [n.x for n in type_nodes]
        ys = [n.y for n in type_nodes]
        colors = []
        line_colors = []
        opacities = []
        labels = []
        customdata = []
        texts = []
        for n in type_nodes:
            color = ELEMENT_COLORS.get(n.element, "#888")
            dim = 1.0
            if highlight_element and n.element != highlight_element:
                dim = 0.25
            if highlight_type and n.type != highlight_type:
                dim = min(dim, 0.2)
            if selected_nodes and n.node_id in selected_nodes:
                dim = max(dim, 0.9)
            if search_matches:
                if n.node_id in search_matches:
                    dim = max(dim, 0.95)
                else:
                    dim = min(dim, 0.15)
            colors.append(color)
            line_colors.append("#00ffff" if node_type == NodeType.BRIDGE else color)
            opacities.append(dim)
            labels.append(
                f"{n.node_id}<br>element={n.element}<br>ring={n.ring}<br>idx={n.idx}<br>type={n.type}"
            )
            customdata.append(n.node_id)
            if node_type == NodeType.CONVERT:
                texts.append("⇄")
            elif show_labels:
                texts.append(str(n.idx))
            else:
                texts.append("")
        style = NODE_STYLE[node_type]
        halo_boost = 8 if node_type == NodeType.KEYSTONE else 5
        halo_alpha = 0.3 if node_type == NodeType.KEYSTONE else 0.18
        halo_colors = [_hex_to_rgba(c, max(0.05, halo_alpha * o)) for c, o in zip(colors, opacities)]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(
                    symbol=style["symbol"],
                    size=[style["size"] + halo_boost for _ in type_nodes],
                    color=halo_colors,
                    line=dict(color="rgba(0,0,0,0)", width=0),
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text" if (show_labels or node_type == NodeType.CONVERT) else "markers",
                text=texts if (show_labels or node_type == NodeType.CONVERT) else None,
                textposition="middle center",
                textfont=dict(color="#f4ffff", size=12 if node_type == NodeType.CONVERT else 10),
                marker=dict(
                    symbol=style["symbol"],
                    size=style["size"],
                    color=colors,
                    opacity=opacities,
                    line=dict(color=line_colors, width=style["line_width"]),
                ),
                customdata=customdata,
                hovertext=labels,
                hoverinfo="text",
                name=node_type.value,
                showlegend=False,
            )
        )
        if node_type == NodeType.SOCKET:
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers",
                    marker=dict(
                        symbol="circle",
                        size=6,
                        color="#050505",
                        line=dict(color="#c8ffff", width=1.2),
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    # element labels (outer ring)
    element_labels_x = []
    element_labels_y = []
    element_labels = []
    for element in ELEMENT_COLORS.keys():
        elem_nodes = [n for n in nodes if n.element == element and n.type != NodeType.BRIDGE]
        if not elem_nodes:
            continue
        avg_x = sum(n.x for n in elem_nodes) / len(elem_nodes)
        avg_y = sum(n.y for n in elem_nodes) / len(elem_nodes)
        r = (avg_x ** 2 + avg_y ** 2) ** 0.5
        if r == 0:
            continue
        scale = (r + 0.8) / r
        element_labels_x.append(avg_x * scale)
        element_labels_y.append(avg_y * scale)
        element_labels.append(element)
    fig.add_trace(
        go.Scatter(
            x=element_labels_x,
            y=element_labels_y,
            mode="text",
            text=element_labels,
            textfont=dict(color="rgba(220,255,255,0.35)", size=20),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=element_labels_x,
            y=element_labels_y,
            mode="text",
            text=element_labels,
            textfont=dict(color="#e8ffff", size=14),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.update_layout(
        autosize=True,
        height=height,
        paper_bgcolor="#050505",
        plot_bgcolor="#050505",
        margin=dict(l=6, r=6, t=6, b=6),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig
