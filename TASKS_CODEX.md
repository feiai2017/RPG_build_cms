# TASKS_CODEX.md (Streamlit)

## Rule
Execute steps strictly in order.
After EACH step, append an entry to WORKLOG.md:
- what you did
- files changed
- commands run + results
- screenshots/notes (if applicable)

---

## Step 1 — Repo scan & entrypoint
- Find the Streamlit entry file (app.py/main.py/etc).
- Identify current board rendering code and data model.
- Update README.md with exact run instructions using:
  - python -m venv .venv
  - source .venv/bin/activate
  - pip install -r requirements.txt (or generate it)
  - python -m streamlit run <entry>.py
- Log to WORKLOG.md.

Verify: app starts locally with python -m streamlit.

---

## Step 2 — Environment & dependencies
- Ensure requirements.txt exists and includes streamlit (and plot lib used).
- Prefer Plotly for interactive nodes/hover/legend (if already in repo ok; if not, ask before adding).
- If no plot lib exists, propose 2 options:
  A) plotly (interactive)
  B) matplotlib (static)
  Ask user before adding new dep.
- Log to WORKLOG.md.

Verify: `python -m streamlit --version` works inside venv.

---

## Step 3 — Implement board generator module
- Create `wuxing_board/board_gen.py` (or similar) with:
  - generate_board(params) -> nodes, edges
  - assert symmetry: count per element equal
  - compute polar coordinates for rings/sectors => convert to x,y
  - create bridge nodes/edges between adjacent elements
- Add minimal unit check function `validate_board(nodes, edges)`.

Log to WORKLOG.md.

Verify: run a small script inside app to print node counts and assert equality.

---

## Step 4 — Implement Streamlit renderer
- Create `wuxing_board/board_render.py`:
  - render_board_plotly(nodes, edges, ui_state) -> plotly fig
  - node type => marker symbol/size/outline style clearly different
  - element => color mapping
  - edges: intra vs bridge thickness difference
  - hover tooltip as spec
- Integrate into Streamlit page.

Log to WORKLOG.md.

Verify: UI shows board; node types visually distinct; hover works.

---

## Step 5 — Legend & filters
- Add UI controls:
  - select element highlight
  - select node type highlight
  - toggles: show bridges / show labels / show ring guides
- Legend bar at bottom (Streamlit components or plotly legend + custom controls).
- Log to WORKLOG.md.

Verify: toggles and filters affect visualization.

---

## Step 6 — Replace old board with new one (minimal disruption)
- Keep old code behind a toggle "Legacy board" for now (optional).
- New board is default.
- Log to WORKLOG.md.

Verify: no runtime errors; README instructions valid.

---

## Step 7 — Final polish
- Improve spacing, typography, color alpha, glow-like outlines.
- Ensure title & element labels match reference layout.
- Provide final summary + verification commands in README and WORKLOG.md.

