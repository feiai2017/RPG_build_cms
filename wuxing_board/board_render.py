# -*- coding: utf-8 -*-
"""五行棋盘渲染（Plotly）"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional
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
    NodeType.SMALL: {"symbol": "circle", "size": 10, "line_width": 1.2},
    NodeType.MEDIUM: {"symbol": "square", "size": 12, "line_width": 1.6},
    NodeType.KEYSTONE: {"symbol": "hexagon", "size": 16, "line_width": 2.2},
    NodeType.SOCKET: {"symbol": "diamond-open", "size": 16, "line_width": 2.0},
    NodeType.BRIDGE: {"symbol": "hexagon", "size": 9, "line_width": 1.6},
    NodeType.CONVERT: {"symbol": "hexagon", "size": 14, "line_width": 2.0},
}


def _edge_trace(nodes: Dict[str, BoardNode], edges: Iterable[BoardEdge], kind: str) -> go.Scatter:
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
    color = "rgba(0,255,255,0.28)" if kind == "bridge" else "rgba(255,255,255,0.12)"
    width = 2.4 if kind == "bridge" else 1.1
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
    selected_nodes: Optional[set[str]] = None,
) -> go.Figure:
    node_lookup = {node.node_id: node for node in nodes}

    fig = go.Figure()

    # edges
    fig.add_trace(_edge_trace(node_lookup, edges, "intra"))
    fig.add_trace(_edge_trace(node_lookup, edges, "radial"))
    if show_bridges:
        fig.add_trace(_edge_trace(node_lookup, edges, "bridge"))

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
                line=dict(color="rgba(0,255,255,0.12)", width=1, dash="dot"),
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
        opacities = []
        labels = []
        customdata = []
        for n in type_nodes:
            color = ELEMENT_COLORS.get(n.element, "#888")
            dim = 1.0
            if highlight_element and n.element != highlight_element:
                dim = 0.25
            if highlight_type and n.type != highlight_type:
                dim = min(dim, 0.2)
            if selected_nodes and n.node_id in selected_nodes:
                dim = max(dim, 0.9)
            colors.append(color)
            opacities.append(dim)
            labels.append(
                f"{n.node_id}<br>element={n.element}<br>ring={n.ring}<br>idx={n.idx}<br>type={n.type}"
            )
            customdata.append(n.node_id)
        style = NODE_STYLE[node_type]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text" if show_labels else "markers",
                text=[n.idx for n in type_nodes] if show_labels else None,
                textposition="middle center",
                marker=dict(
                    symbol=style["symbol"],
                    size=style["size"],
                    color=colors,
                    opacity=opacities,
                    line=dict(color=colors, width=style["line_width"]),
                ),
                customdata=customdata,
                hovertext=labels,
                hoverinfo="text",
                name=node_type.value,
                showlegend=False,
            )
        )

    # element labels
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
            textfont=dict(color="#dffbff", size=14),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.update_layout(
        width=820,
        height=820,
        paper_bgcolor="#050505",
        plot_bgcolor="#050505",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    return fig
