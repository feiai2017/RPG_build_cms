STEP 1 — Fix layout & centering (remove right blank)

Goal: Plot fills container, centered, no huge right whitespace, perfect circular aspect.

Tasks

In Streamlit, ensure plot uses full width: use_container_width=True.

In Plotly figure:

lock aspect ratio (scaleanchor).

tighten margins.

set consistent height (e.g., 760–900).

set paper/bg to dark.

Acceptance

Plot centered with minimal margins.

Circle not stretched.

WORKLOG must include

Before/after description, exact layout params used.

STEP 2 — Visual hierarchy like POE (nodes are king, lines are subtle)

Goal: Nodes pop first; lines are secondary. Default view should not look like engineering wiring.

Tasks

Reduce edge visual weight:

intra edges: thin + low alpha

bridge edges: slightly thicker + higher alpha

Add interaction hierarchy:

Default: all edges very subtle

On hover/select a node: only its incident edges brighten; others fade further.

Acceptance

At a glance, you notice nodes before lines.

Hover shows “local neighborhood” clearly.

STEP 3 — POE-style node tiers (small/medium/keystone obvious without legend)

Goal: Make node types distinguishable by 4 signals:
shape + size + outline + glow.

Tasks
Implement consistent marker styles:

SMALL: circle, size ~8–10, outline 1

MEDIUM: rounded-square/diamond, size ~12–14, outline 1.5

KEYSTONE: hexagon, size ~18–22, outline 2.5, brightest glow

SOCKET: diamond, size ~16–18, outline 2, inner hole marker

CONVERT: hexagon, size ~16–18, outline 2 + “⇄” text overlay (or symbol)

BRIDGE: small hexagon, size ~12–14, outline 2, edge color brighter

If Plotly cannot do “glow”, approximate via:

thicker outline + lighter outline color + slight alpha halo by drawing a second marker behind (same x,y bigger size, low alpha).

Acceptance

You can point at a keystone instantly.

Socket/convert/bridge visually distinct.

STEP 4 — Add POE-like “regional plates” and ring guides (readability)

Goal: Clear five sectors and ring structure; still subtle and elegant.

Tasks

Draw 5 translucent sector wedges (polygons) behind nodes.

very low alpha (0.06–0.12)

Add ring guide lines:

dashed circles per ring (low alpha)

Add big element labels (木火土金水) near outer ring, subtle glow.

Acceptance

Element regions are readable at a glance.

Rings show progression/tiers.

STEP 5 — Legend & filters redesigned (POE-like, compact, not scattered)

Goal: Controls grouped and compact; right side dominated by the tree.

Tasks

Layout:

Use st.columns([3,1]) or [4,1]

Left: big plot

Right: filter panel card (element + node type + toggles)

Replace scattered buttons with:

segmented controls / radio / multiselect

“Reset highlight” button

Implement highlight logic:

selecting element => highlight element nodes, dim others (alpha down)

selecting node type => highlight that type, dim others

toggles: show bridges, show labels, show ring guides

Acceptance

UI looks “product-like”, not debug panel.

Filtering feels like POE search/highlight.

STEP 6 — Add search/highlight by node_id or keyword (POE essential)

Goal: POE tree uses search to highlight passives.

Tasks

Add a text input “Search node”

If matches node_id / tags / keyword:

highlight matching nodes

optionally show a small list of matches

Acceptance

Searching “keystone” / “socket” / specific id highlights nodes.

STEP 7 — Final polish & docs

Tasks

Add a “Theme: POE” section in README (how to adjust sizes/colors).

Ensure WORKLOG contains each step.

Acceptance

One command runs app.

Visual clearly POE-like.
