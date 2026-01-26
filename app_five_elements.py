# -*- coding: utf-8 -*-
"""赛博道体 · 真八卦灵石盘（Streamlit 单文件，可执行）

目标（按用户最新要求）：
- 视觉上更像“八卦盘”：8 卦围绕阵眼（核心槽），后天八卦方位布局。
- 同时更明确体现“五行区域”：每个卦位归属五行，卡片头条与边框按五行着色，并有五行图例。
- 纯槽位界面：不出现“武器/防具/戒指”等部位概念。
- 保留：五行灵石 + 核心 BIOS。

运行：
  streamlit run app_visual_fixed.py
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import streamlit as st

# =========================================================
# 0) 页面配置 + 亮色 UI
# =========================================================
st.set_page_config(layout="wide", page_title="赛博道体·真八卦灵石盘", page_icon="☯️")

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700&display=swap');

  :root {
    --void: #050505;
    --cyan: #00ffff;
    --blue: #2aa1ff;
    --fire: #ff3b30;
    --water: #2f80ff;
    --wood: #2dff6f;
    --metal: #f5f5f5;
    --earth: #ffd34d;
  }

  .stApp {
    background: var(--void);
    color: #dffbff;
    font-family: 'Orbitron', 'Courier New', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  }

  html, body, [class*="css"], p, span, label, div {
    color: #dffbff;
  }

  h1, h2, h3, h4 {
    letter-spacing: 1px;
    text-shadow: 0 0 12px rgba(0,255,255,0.35);
  }

  .card {
    border: 1px solid rgba(0,255,255,0.25);
    border-radius: 14px;
    background: rgba(5, 8, 12, 0.85);
    box-shadow: 0 0 20px rgba(0,255,255,0.12);
    padding: 14px;
  }

  .bagua {
    --spirit-load: 0.72turn;
    border: 1px solid rgba(0,255,255,0.35);
    border-radius: 999px;
    background: radial-gradient(circle at 50% 45%, rgba(8,16,28,0.98) 0%, rgba(5,10,18,0.98) 60%, rgba(5,5,5,1) 100%);
    padding: 30px;
    box-shadow: 0 0 0 1px rgba(0,255,255,0.15), 0 0 40px rgba(0,255,255,0.2), inset 0 0 60px rgba(0,0,0,0.8);
    position: relative;
    overflow: hidden;
    max-width: 980px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .bagua-ring-wrap {
    position: relative;
    width: min(760px, 92vw);
    aspect-ratio: 1;
    margin: 10px auto 2px;
    --r-logic: 90px;
    --r-inner: 145px;
    --r-middle: 205px;
    --r-outer: 265px;
    --r-label: 320px;
    z-index: 5;
  }

  .ring-layer { position: absolute; inset: 0; }

  .ring-layer .slot {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: rotate(var(--angle)) translate(var(--radius)) rotate(calc(-1 * var(--angle)));
    transform-origin: center;
  }

  .bagua-svg {
    width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
  }

  .hex-slot {
    transition: opacity 0.2s ease, transform 0.2s ease;
  }

  .hex-slot:hover {
    opacity: 0.85;
    filter: drop-shadow(0 0 10px rgba(0,255,255,0.8));
  }

  .ring-label .slot { --radius: var(--r-label); pointer-events: none; }
  .ring-logic .slot { --radius: var(--r-logic); }
  .ring-inner .slot { --radius: var(--r-inner); }
  .ring-middle .slot { --radius: var(--r-middle); }
  .ring-outer .slot { --radius: var(--r-outer); }

  .tri-label {
    min-width: 94px;
    text-align: center;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(0,255,255,0.45);
    background: rgba(6,12,20,0.7);
    color: #dffbff;
    box-shadow: 0 0 16px rgba(0,255,255,0.25);
    font-size: 11px;
    letter-spacing: 0.8px;
  }

  .elem-tag {
    display: inline-flex;
    gap: 8px;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    border: 1px solid rgba(0,255,255,0.35);
    background: rgba(6,12,20,0.7);
    font-size: 12px;
    color: #dffbff;
    box-shadow: 0 0 14px rgba(0,255,255,0.2);
  }

  .tri-head {
    border-radius: 14px;
    padding: 8px 10px;
    border: 1px solid rgba(0,255,255,0.35);
    background: rgba(6,12,20,0.75);
    box-shadow: inset 0 0 18px rgba(0,255,255,0.15);
    margin-bottom: 10px;
  }

  .tri-title { font-weight: 700; font-size: 14px; }
  .tri-sub { font-size: 12px; opacity: 0.7; }


  .ring-core .core-center {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: min(240px, 42%);
  }

  .bagua div[data-testid="stButton"] > button {
    border-radius: 12px !important;
    border: 1px solid rgba(0,255,255,0.4) !important;
    background: rgba(6,12,20,0.85) !important;
    color: #dffbff !important;
    box-shadow: 0 0 16px rgba(0,255,255,0.25), inset 0 0 12px rgba(0,120,255,0.2);
    text-shadow: 0 0 10px rgba(0,255,255,0.35);
    clip-path: polygon(25% 6%, 75% 6%, 96% 50%, 75% 94%, 25% 94%, 4% 50%);
  }

  .bagua div[data-testid="stButton"] > button:hover {
    animation: glitchFlicker 1.2s infinite;
    box-shadow: 0 0 24px rgba(0,255,255,0.55), inset 0 0 16px rgba(0,120,255,0.35);
  }

  .ring-layer div[data-testid="stButton"] > button {
    width: 44px !important;
    height: 44px !important;
    padding: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
  }

  .ring-logic div[data-testid="stButton"] > button {
    width: 34px !important;
    height: 34px !important;
    font-size: 12px !important;
  }

  .ring-outer div[data-testid="stButton"] > button {
    width: 48px !important;
    height: 48px !important;
  }

  .core-shell {
    position: relative;
    min-height: 180px;
  }

  .core-shell > * {
    position: relative;
    z-index: 2;
  }

  .core-orb {
    position: absolute;
    inset: 14px;
    border-radius: 999px;
    background:
      radial-gradient(circle at 35% 35%, rgba(255,255,255,0.95) 0 18%, rgba(0,0,0,0) 19% 100%),
      radial-gradient(circle at 65% 65%, rgba(0,0,0,0.95) 0 18%, rgba(0,0,0,0) 19% 100%),
      conic-gradient(from 90deg, rgba(255,255,255,0.9) 0 50%, rgba(0,0,0,0.9) 50% 100%),
      repeating-linear-gradient(90deg, rgba(0,255,255,0.25) 0 2px, transparent 2px 6px);
    border: 1px solid rgba(0,255,255,0.45);
    box-shadow: 0 0 26px rgba(0,255,255,0.5), inset 0 0 40px rgba(0,0,0,0.7);
    animation: floatPulse 6s ease-in-out infinite;
    opacity: 0.9;
    z-index: 1;
    pointer-events: none;
  }

  .bagua .tiny { color: rgba(200, 235, 255, 0.65); }

  @keyframes rotateSlow {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes rotateOuter {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(-360deg); }
  }

  @keyframes floatPulse {
    0% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-6px) scale(1.02); }
    100% { transform: translateY(0) scale(1); }
  }

  @keyframes glitchFlicker {
    0%, 100% { opacity: 1; transform: translate(0, 0) skew(0deg); }
    20% { opacity: 0.8; transform: translate(1px, -1px) skew(0.6deg); }
    40% { opacity: 1; transform: translate(-1px, 0) skew(-0.6deg); }
    60% { opacity: 0.7; transform: translate(1px, 1px) skew(0.8deg); }
    80% { opacity: 1; transform: translate(-1px, 0) skew(-0.4deg); }
  }

  @media (max-width: 1200px) {
    .bagua { padding: 20px; }
    .bagua-ring-wrap {
      --r-logic: 72px;
      --r-inner: 120px;
      --r-middle: 170px;
      --r-outer: 220px;
      --r-label: 260px;
      width: min(640px, 90vw);
    }
  }
</style>
"""


st.markdown(CSS, unsafe_allow_html=True)

# =========================================================
# 1) 五行 / 相生相克
# =========================================================
ELEMENTS = ["木", "火", "土", "金", "水"]
ELEMENT_META = {
    "木": {"color": "#2E7D32", "bg": "rgba(46,125,50,0.10)", "icon": "🌿"},
    "火": {"color": "#C62828", "bg": "rgba(198,40,40,0.10)", "icon": "🔥"},
    "土": {"color": "#8D6E63", "bg": "rgba(141,110,99,0.12)", "icon": "🪨"},
    "金": {"color": "#B8860B", "bg": "rgba(184,134,11,0.12)", "icon": "🗡️"},
    "水": {"color": "#1565C0", "bg": "rgba(21,101,192,0.10)", "icon": "💧"},
    "无": {"color": "#444", "bg": "rgba(0,0,0,0.05)", "icon": "∅"},
}

# 相生：木→火→土→金→水→木
GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 相克：木克土，土克水，水克火，火克金，金克木
OVERCOME = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def is_generate(a: str, b: str) -> bool:
    return GENERATE.get(a) == b


def is_overcome(a: str, b: str) -> bool:
    return OVERCOME.get(a) == b


def counter_element(e: str) -> str:
    """返回克制该元素的元素（谁克它）"""
    for k, v in OVERCOME.items():
        if v == e:
            return k
    return "无"


# =========================================================
# 2) 八卦：后天八卦方位 + 五行归属
# =========================================================
# 后天八卦（常见）五行归属：
# 乾/兑=金，离=火，震/巽=木，坎=水，艮/坤=土
TRIGRAMS = {
    "QIAN": {"name": "乾", "symbol": "☰", "elem": "金", "pos": (1, 1)},  # NW
    "DUI": {"name": "兑", "symbol": "☱", "elem": "金", "pos": (2, 0)},   # W
    "LI": {"name": "离", "symbol": "☲", "elem": "火", "pos": (0, 2)},    # S (placed top for aesthetics)
    "ZHEN": {"name": "震", "symbol": "☳", "elem": "木", "pos": (2, 4)}, # E
    "XUN": {"name": "巽", "symbol": "☴", "elem": "木", "pos": (3, 3)},  # SE
    "KAN": {"name": "坎", "symbol": "☵", "elem": "水", "pos": (4, 2)},  # N
    "GEN": {"name": "艮", "symbol": "☶", "elem": "土", "pos": (1, 3)},  # NE
    "KUN": {"name": "坤", "symbol": "☷", "elem": "土", "pos": (3, 1)},  # SW
}

# 环形顺序（按“离→坤→兑→乾→坎→艮→震→巽→回离”）
BAGUA_RING = ["LI", "KUN", "DUI", "QIAN", "KAN", "GEN", "ZHEN", "XUN"]

# =========================================================
# 3) 境界与解锁
# =========================================================
# 每卦槽位：1=逻辑位（仅逻辑灵石），2/3/4=内/中/外环（五行灵石）
TRI_SLOT_MAX = 4

REALMS = {
    "炼气": {"tri_unlock": 2, "core_slots": 1, "bw_safe": 18, "bw_max": 26},
    "筑基": {"tri_unlock": 3, "core_slots": 1, "bw_safe": 24, "bw_max": 34},
    "金丹": {"tri_unlock": 4, "core_slots": 2, "bw_safe": 30, "bw_max": 42},
    "元婴": {"tri_unlock": 4, "core_slots": 2, "bw_safe": 36, "bw_max": 50},
    "化神": {"tri_unlock": 4, "core_slots": 3, "bw_safe": 42, "bw_max": 58},
}

LAYER_NAME = {2: "内", 3: "中", 4: "外"}
LAYER_KEY = {2: "inner", 3: "middle", 4: "outer"}

# =========================================================
# 4) 灵石数据
# =========================================================
@dataclass
class Stone:
    id: str
    name: str
    element: str  # 木火土金水 or 无
    icon: str
    rarity: str
    bandwidth: int
    stock_total: int
    kind: str  # gem / logic / core
    effects: Dict[str, Dict[str, float]] = field(default_factory=dict)  # inner/middle/outer
    logic: Dict[str, str] = field(default_factory=dict)
    core_rules: Dict[str, str] = field(default_factory=dict)
    desc: str = ""


def make_stones() -> Dict[str, Stone]:
    stones: List[Stone] = []

    # 五行灵石：同一颗放在“内/中/外环”效果不同（暗黑宝石的“槽位差异”抽象版）
    stones += [
        Stone(
            id="gem_wood",
            name="翠灵石",
            element="木",
            icon="🟩",
            rarity="rare",
            bandwidth=5,
            stock_total=2,
            kind="gem",
            effects={
                "inner": {"crit_dmg": 12, "elem_dmg_木": 10},
                "middle": {"hp": 160, "elem_res_木": 8},
                "outer": {"def": 10, "cooling": 2},
            },
            desc="木系：偏持续/韧性。内环偏伤，外环偏稳。",
        ),
        Stone(
            id="gem_fire",
            name="赤焰石",
            element="火",
            icon="🟥",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "inner": {"atk": 14, "elem_dmg_火": 11},
                "middle": {"crit": 3, "burn": 6},
                "outer": {"elem_res_火": 12, "stability": -1},
            },
            desc="火系：爆发/灼烧。强但更躁（外环略降稳定）。",
        ),
        Stone(
            id="gem_earth",
            name="厚土石",
            element="土",
            icon="🟧",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "inner": {"vuln": 8, "elem_dmg_土": 10},
                "middle": {"hp": 220, "def": 8},
                "outer": {"elem_res_土": 12, "stability": 1},
            },
            desc="土系：厚重稳态。中外环非常抗压。",
        ),
        Stone(
            id="gem_metal",
            name="金魄石",
            element="金",
            icon="⬜",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "inner": {"atk": 10, "crit_dmg": 6, "elem_dmg_金": 10},
                "middle": {"def": 10, "crit": 2},
                "outer": {"elem_res_金": 10, "stability": 1},
            },
            desc="金系：锋锐均衡。内环攻，外环稳。",
        ),
        Stone(
            id="gem_water",
            name="玄冰石",
            element="水",
            icon="🟦",
            rarity="rare",
            bandwidth=5,
            stock_total=2,
            kind="gem",
            effects={
                "inner": {"crit": 3, "elem_dmg_水": 10},
                "middle": {"def": 14, "cooling": 3},
                "outer": {"elem_res_水": 12, "stability": 1},
            },
            desc="水系：冷静护体。外环提供稳定。",
        ),
    ]

    # 逻辑灵石：放在每卦第 1 位（逻辑位）
    stones += [
        Stone(
            id="logic_blood",
            name="逻辑灵石·血危",
            element="无",
            icon="🧩",
            rarity="epic",
            bandwidth=1,
            stock_total=1,
            kind="logic",
            logic={"gate": "HP_LT_30"},
            desc="该卦常态不通电；生命低于 30% 时整卦激活。",
        ),
        Stone(
            id="logic_heat",
            name="逻辑灵石·过热",
            element="无",
            icon="🧩",
            rarity="epic",
            bandwidth=1,
            stock_total=1,
            kind="logic",
            logic={"gate": "HEAT_GT_50"},
            desc="热量>50 时启动保护：降低故障率，但该卦效能下降。",
        ),
    ]

    # 核心 BIOS：只能装入核心槽
    stones += [
        Stone(
            id="core_mad",
            name="核心BIOS·疯狂义体",
            element="无",
            icon="🧠",
            rarity="legendary",
            bandwidth=4,
            stock_total=1,
            kind="core",
            core_rules={"bios": "MAD_CYBER"},
            desc="防御收益会被部分折算为攻击；更极端的进攻型。",
        ),
        Stone(
            id="core_invert",
            name="核心BIOS·五行逆转",
            element="无",
            icon="🧠",
            rarity="legendary",
            bandwidth=4,
            stock_total=1,
            kind="core",
            core_rules={"bios": "INVERT_5"},
            desc="火↔水、木↔金：重写五行伤害/抗性分布。",
        ),
        Stone(
            id="core_overclock",
            name="核心BIOS·算力超频",
            element="无",
            icon="🧠",
            rarity="legendary",
            bandwidth=4,
            stock_total=1,
            kind="core",
            core_rules={"bios": "OVERCLOCK"},
            desc="提高带宽阈值，但热量更易积累，故障风险上升。",
        ),
    ]

    return {s.id: s for s in stones}


STONES = make_stones()

# =========================================================
# 5) Session State（含版本迁移）
# =========================================================
SCHEMA_VER = 3


def reset_state() -> None:
    st.session_state.schema_ver = SCHEMA_VER
    st.session_state.realm = "金丹"
    st.session_state.seed = 184023
    st.session_state.disciple = "李长风"
    st.session_state.affinity_main = "木"

    # 八卦盘：每卦 1..TRI_SLOT_MAX
    st.session_state.board = {tri: {i: None for i in range(1, TRI_SLOT_MAX + 1)} for tri in TRIGRAMS}
    # 核心槽：1..3
    st.session_state.core = {i: None for i in range(1, 4)}

    st.session_state.stock = {sid: STONES[sid].stock_total for sid in STONES}

    st.session_state.picked_stone = None
    st.session_state.selected_slot = None
    st.session_state.sim_result = None


def init_state() -> None:
    if st.session_state.get("schema_ver") != SCHEMA_VER:
        reset_state()


init_state()

# =========================================================
# 6) 规则工具
# =========================================================

def element_affinity_multiplier(elem: str) -> float:
    """主灵根加成：
    - 主灵根元素：+20%
    - 主灵根所生：+5%
    - 克主灵根的元素：-5%（不利）
    """
    main = st.session_state.affinity_main
    if elem not in ELEMENTS:
        return 1.0
    if elem == main:
        return 1.20
    if is_generate(main, elem):
        return 1.05
    if is_overcome(elem, main):
        return 0.95
    return 1.0


def get_bios() -> Optional[str]:
    for i in range(1, 4):
        sid = st.session_state.core.get(i)
        if sid and STONES[sid].kind == "core":
            return STONES[sid].core_rules.get("bios")
    return None


def invert_element(e: str) -> str:
    # 火↔水、木↔金、土不变
    if e == "火":
        return "水"
    if e == "水":
        return "火"
    if e == "木":
        return "金"
    if e == "金":
        return "木"
    return e


# =========================================================
# 7) 编译（构筑评估）
# =========================================================

def compile_context(is_crisis: bool) -> Dict:
    realm_cfg = REALMS[st.session_state.realm]
    tri_unlock = realm_cfg["tri_unlock"]
    core_unlocked = realm_cfg["core_slots"]

    bios = get_bios()

    # base stats
    stats: Dict[str, float] = {
        "atk": 0,
        "def": 0,
        "hp": 0,
        "crit": 0,
        "crit_dmg": 0,
        "vuln": 0,
        "burn": 0,
        "cooling": 0,
        "stability": 80.0,
        "bandwidth": 0,
    }
    for e in ELEMENTS:
        stats[f"elem_dmg_{e}"] = 0
        stats[f"elem_res_{e}"] = 0

    notes: List[str] = []

    # 逻辑门控：每卦 slot1
    tri_active: Dict[str, bool] = {tri: True for tri in TRIGRAMS}
    tri_heat_gate: Dict[str, bool] = {tri: False for tri in TRIGRAMS}

    for tri in TRIGRAMS:
        sid = st.session_state.board[tri][1]
        if not sid:
            continue
        s = STONES[sid]
        if s.kind != "logic":
            continue
        gate = s.logic.get("gate")
        if gate == "HP_LT_30":
            tri_active[tri] = is_crisis
        elif gate == "HEAT_GT_50":
            tri_heat_gate[tri] = True

    # 统计五行数量（仅激活且为 gem）
    elem_counts = {e: 0 for e in ELEMENTS}

    # 每个槽位 multiplier
    mult: Dict[Tuple[str, int], float] = {}

    # 先收集带宽 + 初始 multiplier
    for tri, tinfo in TRIGRAMS.items():
        if not tri_active[tri]:
            continue
        tri_elem = tinfo["elem"]
        for idx in range(1, tri_unlock + 1):
            sid = st.session_state.board[tri][idx]
            if not sid:
                continue
            stone = STONES[sid]

            # logic：常态若被血危门控则不耗带宽
            if stone.kind == "logic":
                if stone.logic.get("gate") == "HP_LT_30" and (not is_crisis):
                    continue
                stats["bandwidth"] += stone.bandwidth
                continue

            if stone.kind != "gem":
                continue

            stats["bandwidth"] += stone.bandwidth
            if stone.element in elem_counts:
                elem_counts[stone.element] += 1

            m = element_affinity_multiplier(stone.element)

            # 卦域相生相克：灵石元素 vs 卦五行
            if is_generate(stone.element, tri_elem):
                m *= 1.50
                notes.append(f"卦域相生：{stone.element}生{tri_elem}（{tinfo['name']}{idx} +50%）")
            elif is_overcome(stone.element, tri_elem):
                m *= 0.80
                notes.append(f"卦域相克：{stone.element}克{tri_elem}（{tinfo['name']}{idx} -20%）")

            mult[(tri, idx)] = m

    # 卦内链路：内→中→外（2->3->4）
    for tri in TRIGRAMS:
        if not tri_active[tri]:
            continue
        for idx in range(2, tri_unlock):
            sid_a = st.session_state.board[tri][idx]
            sid_b = st.session_state.board[tri][idx + 1]
            if not sid_a or not sid_b:
                continue
            a = STONES[sid_a]
            b = STONES[sid_b]
            if a.kind != "gem" or b.kind != "gem":
                continue
            if is_generate(a.element, b.element):
                mult[(tri, idx + 1)] = mult.get((tri, idx + 1), 1.0) * 1.15
                notes.append(f"卦内相生链：{a.element}→{b.element}（{TRIGRAMS[tri]['name']}{idx+1} +15%）")
            elif is_overcome(a.element, b.element):
                mult[(tri, idx + 1)] = mult.get((tri, idx + 1), 1.0) * 0.90
                notes.append(f"卦内相克链：{a.element}×{b.element}（{TRIGRAMS[tri]['name']}{idx+1} -10%）")

    # 环形链路：以每卦“内环位(2)”为节点，按 BAGUA_RING 连成一圈
    ring_nodes: List[Tuple[str, str]] = []  # (tri, elem)
    for tri in BAGUA_RING:
        if not tri_active[tri]:
            ring_nodes.append((tri, "无"))
            continue
        sid = st.session_state.board[tri][2] if tri_unlock >= 2 else None
        if sid and STONES[sid].kind == "gem":
            ring_nodes.append((tri, STONES[sid].element))
        else:
            ring_nodes.append((tri, "无"))

    for i in range(len(BAGUA_RING)):
        tri_prev, e_prev = ring_nodes[i]
        tri_next, e_next = ring_nodes[(i + 1) % len(BAGUA_RING)]
        if e_prev == "无" or e_next == "无":
            continue
        if is_generate(e_prev, e_next):
            mult[(tri_next, 2)] = mult.get((tri_next, 2), 1.0) * 1.20
            notes.append(f"卦环相生：{e_prev}→{e_next}（{TRIGRAMS[tri_next]['name']}内 +20%）")
        elif is_overcome(e_prev, e_next):
            mult[(tri_next, 2)] = mult.get((tri_next, 2), 1.0) * 0.85
            notes.append(f"卦环相克：{e_prev}×{e_next}（{TRIGRAMS[tri_next]['name']}内 -15%）")

    # 留白：空槽散热 & 独尊
    filled_gems = 0
    for tri in TRIGRAMS:
        if not tri_active[tri]:
            continue
        gem_slots = [i for i in range(2, tri_unlock + 1)]
        filled = [i for i in gem_slots if st.session_state.board[tri][i] and STONES[st.session_state.board[tri][i]].kind == "gem"]
        empty_n = len([i for i in gem_slots if not st.session_state.board[tri][i]])

        filled_gems += len(filled)
        stats["cooling"] += 1.0 * empty_n

        if len(filled) == 1:
            idx = filled[0]
            m = 1.0 + min(0.60, 0.15 * empty_n)  # cap +60%
            mult[(tri, idx)] = mult.get((tri, idx), 1.0) * m
            notes.append(f"留白·独尊：{TRIGRAMS[tri]['name']}{idx} ×{m:.2f}")

    # 核心联动：每装一个核心槽，全盘内环(2)加成 +5%
    core_filled = 0
    for i in range(1, core_unlocked + 1):
        sid = st.session_state.core.get(i)
        if sid:
            stats["bandwidth"] += STONES[sid].bandwidth
            core_filled += 1

    if core_filled > 0:
        for tri in TRIGRAMS:
            if tri_active[tri] and tri_unlock >= 2:
                if st.session_state.board[tri][2] and STONES[st.session_state.board[tri][2]].kind == "gem":
                    mult[(tri, 2)] = mult.get((tri, 2), 1.0) * (1.0 + 0.05 * core_filled)
        stats["stability"] += 1.5 * core_filled
        notes.append(f"阵眼连脉：核心联动 x{core_filled}（内环整体增强）")

    # 卦脉导通：三连卦段触发（用内环位判断）
    CIRCUITS = [
        ("LI", "KUN", "DUI"),
        ("DUI", "QIAN", "KAN"),
        ("KAN", "GEN", "ZHEN"),
        ("ZHEN", "XUN", "LI"),
    ]
    circuits_on: List[str] = []
    for a, b, c in CIRCUITS:
        ok = True
        for tri in (a, b, c):
            if not tri_active[tri]:
                ok = False
            sid = st.session_state.board[tri][2] if tri_unlock >= 2 else None
            if not (sid and STONES[sid].kind == "gem"):
                ok = False
        if not ok:
            continue
        ea = STONES[st.session_state.board[a][2]].element
        eb = STONES[st.session_state.board[b][2]].element
        ec = STONES[st.session_state.board[c][2]].element
        # 连段内不允许强相克
        if is_overcome(ea, eb) or is_overcome(eb, ec):
            continue
        circuits_on.append(f"{TRIGRAMS[a]['name']}-{TRIGRAMS[b]['name']}-{TRIGRAMS[c]['name']}")
        stats["stability"] += 2
        stats["atk"] += 6

    if circuits_on:
        notes.append("卦脉导通：" + ", ".join(circuits_on) + "（稳定+2/段，攻+6/段）")

    # 应用灵石效果
    for tri in TRIGRAMS:
        if not tri_active[tri]:
            continue
        for idx in range(2, tri_unlock + 1):
            sid = st.session_state.board[tri][idx]
            if not sid:
                continue
            stone = STONES[sid]
            if stone.kind != "gem":
                continue
            layer = LAYER_KEY[idx]
            eff = stone.effects.get(layer, {})
            m = mult.get((tri, idx), 1.0)
            for k, v in eff.items():
                stats[k] = stats.get(k, 0.0) + float(v) * m

    # BIOS 重写
    bw_safe = float(realm_cfg["bw_safe"])
    bw_max = float(realm_cfg["bw_max"])

    if bios == "OVERCLOCK":
        bw_safe += 6
        bw_max += 10
        stats["stability"] -= 3
    elif bios == "MAD_CYBER":
        convert = 0.25 * (stats.get("def", 0) + 0.02 * stats.get("hp", 0))
        stats["atk"] += convert
        stats["stability"] -= 2
    elif bios == "INVERT_5":
        for e in ELEMENTS:
            inv = invert_element(e)
            if inv == e:
                continue
            stats[f"elem_dmg_{e}"], stats[f"elem_dmg_{inv}"] = stats.get(f"elem_dmg_{inv}", 0), stats.get(f"elem_dmg_{e}", 0)
            stats[f"elem_res_{e}"], stats[f"elem_res_{inv}"] = stats.get(f"elem_res_{inv}", 0), stats.get(f"elem_res_{e}", 0)

    # 五行共鸣与弱点
    total_elem = sum(elem_counts.values())
    if total_elem >= 4:
        counts_sorted = sorted(elem_counts.items(), key=lambda x: x[1], reverse=True)
        dom_e, dom_n = counts_sorted[0]
        second_n = counts_sorted[1][1]
        min_n = min(n for _, n in counts_sorted)

        if (dom_n - min_n) <= 1:
            stats["stability"] += 6
            for e in ELEMENTS:
                stats[f"elem_res_{e}"] += 4
            notes.append("均衡：五行接近平衡（稳定+6 / 全抗+4）")
        elif dom_n >= 3:
            stats[f"elem_dmg_{dom_e}"] += (dom_n - 2) * 3
            notes.append(f"共鸣：{dom_e}数量≥3（{dom_e}伤害提升）")
            if dom_n >= 4 and (dom_n - second_n) >= 3:
                weak = counter_element(dom_e)
                stats[f"elem_res_{weak}"] -= (dom_n - 2) * 4
                stats["stability"] -= (dom_n - 2) * 1.5
                notes.append(f"偏科弱点：{dom_e}过盛 → 弱{weak}（抗性下降/稳定下降）")

    # 过载/热量/故障率
    bw = float(stats["bandwidth"])
    over = max(0.0, bw - bw_safe)

    heat = 15.0 + 1.3 * filled_gems + 3.0 * over - 1.1 * stats.get("cooling", 0)
    if bios == "OVERCLOCK":
        heat += 10.0
    heat = max(0.0, min(100.0, heat))

    # 过热保护（任意卦安装过热逻辑，且 heat>50）：降低故障率，但该卦效能略降
    heat_protect = False
    if heat > 50:
        for tri in TRIGRAMS:
            if tri_active[tri] and tri_heat_gate[tri]:
                heat_protect = True
                stats["stability"] += 2
                # 简化：降低该卦所属元素的伤害 10%
                te = TRIGRAMS[tri]["elem"]
                stats[f"elem_dmg_{te}"] *= 0.90
        if heat_protect:
            notes.append("逻辑·过热：触发保护（稳定+2，部分效能-10%）")

    if bw > bw_max:
        status = "FAIL"
        glitch_p = 1.0
    else:
        status = "OK"
        glitch_p = 0.01 + (heat / 200.0) + (over / max(1.0, bw_max)) * 0.35
        glitch_p = min(0.65, max(0.01, glitch_p))
        if heat_protect:
            glitch_p *= 0.70

    stats["heat"] = heat
    stats["bw_safe"] = bw_safe
    stats["bw_max"] = bw_max
    stats["glitch_p"] = glitch_p

    return {
        "stats": stats,
        "notes": notes,
        "elem_counts": elem_counts,
        "tri_active": tri_active,
        "tri_unlock": tri_unlock,
        "core_unlocked": core_unlocked,
        "bios": bios,
        "circuits": circuits_on,
        "status": status,
    }


def simulate(seed: int, is_crisis: bool) -> Dict:
    ctx = compile_context(is_crisis)
    s = ctx["stats"]
    rng = random.Random(seed)

    burnt = None
    if ctx["status"] == "FAIL":
        return {"ctx": ctx, "burnt": "带宽超限（无法运行）", "seed": seed}

    if rng.random() < s["glitch_p"]:
        candidates: List[Tuple[str, int, str]] = []
        tri_unlock = ctx["tri_unlock"]
        for tri in TRIGRAMS:
            if not ctx["tri_active"][tri]:
                continue
            for idx in range(2, tri_unlock + 1):
                sid = st.session_state.board[tri][idx]
                if sid and STONES[sid].kind == "gem":
                    candidates.append((tri, idx, sid))
        if candidates:
            tri, idx, sid = rng.choice(candidates)
            burnt = f"熔断：{TRIGRAMS[tri]['name']}{LAYER_NAME[idx]} {STONES[sid].name}"

    return {"ctx": ctx, "burnt": burnt, "seed": seed}


# =========================================================
# 8) UI 工具（放置/卸下/校验）
# =========================================================

def can_place(stone_id: str, target: Tuple) -> Tuple[bool, str]:
    s = STONES[stone_id]
    kind = target[0]
    if kind == "core":
        if s.kind != "core":
            return False, "核心槽只能放核心BIOS。"
        return True, ""

    # tri slot
    _, tri, idx = target
    if s.kind == "core":
        return False, "核心BIOS只能装入阵眼核心槽。"
    if idx == 1:
        if s.kind != "logic":
            return False, "该位为逻辑位，只能放逻辑灵石。"
    else:
        if s.kind == "logic":
            return False, "逻辑灵石只能放在每卦的逻辑位（第1位）。"
    return True, ""


def place(target: Tuple, stone_id: str) -> None:
    if st.session_state.stock.get(stone_id, 0) <= 0:
        st.toast("库存不足", icon="⚠️")
        return

    kind = target[0]
    if kind == "core":
        _, idx = target
        old = st.session_state.core.get(idx)
        if old:
            st.session_state.stock[old] += 1
        st.session_state.core[idx] = stone_id
        st.session_state.stock[stone_id] -= 1
        return

    _, tri, slot_idx = target
    old = st.session_state.board[tri][slot_idx]
    if old:
        st.session_state.stock[old] += 1
    st.session_state.board[tri][slot_idx] = stone_id
    st.session_state.stock[stone_id] -= 1


def remove(target: Tuple) -> None:
    kind = target[0]
    if kind == "core":
        _, idx = target
        old = st.session_state.core.get(idx)
        if old:
            st.session_state.stock[old] += 1
        st.session_state.core[idx] = None
        return

    _, tri, idx = target
    old = st.session_state.board[tri][idx]
    if old:
        st.session_state.stock[old] += 1
    st.session_state.board[tri][idx] = None


def slot_label(tri: str, idx: int, locked: bool) -> str:
    if locked:
        return "🔒"
    sid = st.session_state.board[tri][idx]
    if sid:
        s = STONES[sid]
        if s.kind == "logic":
            return "🧩"
        return s.icon
    return "＋"


def core_label(idx: int, locked: bool) -> str:
    if locked:
        return "🔒"
    sid = st.session_state.core.get(idx)
    if sid:
        return "🧠"
    return "＋"


def stat_lines(stats: Dict[str, float]) -> List[str]:
    return [
        f"ATK {stats.get('atk',0):.1f}  DEF {stats.get('def',0):.1f}  HP {stats.get('hp',0):.0f}",
        f"暴击 {stats.get('crit',0):.1f}%  暴伤 {stats.get('crit_dmg',0):.1f}%  易伤 {stats.get('vuln',0):.1f}%",
        f"稳定 {stats.get('stability',0):.1f}  散热 {stats.get('cooling',0):.1f}",
    ]


# =========================================================
# 9) 顶部 HUD
# =========================================================
ctx_normal = compile_context(is_crisis=False)
ctx_crisis = compile_context(is_crisis=True)

hud1, hud2, hud3, hud4 = st.columns([2.1, 1.0, 1.0, 1.6])
with hud1:
    st.markdown("### ☯️ 赛博道体 · 真八卦灵石盘")
    st.caption(f"弟子：{st.session_state.disciple} | 境界：{st.session_state.realm} | 主灵根：{st.session_state.affinity_main}")

with hud2:
    tri_unlock = ctx_normal["tri_unlock"]
    used = 0
    total = 0
    for tri in TRIGRAMS:
        total += tri_unlock
        for idx in range(1, tri_unlock + 1):
            if st.session_state.board[tri][idx]:
                used += 1
    st.metric("槽位", f"{used}/{total}")

with hud3:
    s = ctx_normal["stats"]
    st.metric("带宽", f"{int(s['bandwidth'])}/{int(s['bw_safe'])}", delta=f"极限 {int(s['bw_max'])}")

with hud4:
    s = ctx_normal["stats"]
    stable_pct = max(0.0, min(100.0, 100.0 - s["glitch_p"] * 100.0))
    st.markdown(
        f"<div class='card mono' style='text-align:right; padding:10px 12px;'>"
        f"<div style='font-size:18px; font-weight:900;'>稳定 {stable_pct:.0f}%</div>"
        f"<div class='tiny'>Seed: {st.session_state.seed}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.divider()

# =========================================================
# 10) 三栏布局
# =========================================================
col_lib, col_center, col_status = st.columns([1.25, 2.55, 1.15])

# -------------------------
# 左：灵石库
# -------------------------
with col_lib:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### 📦 灵石库")

    with st.expander("⚙️ 弟子/境界", expanded=True):
        st.session_state.disciple = st.text_input("弟子名", value=st.session_state.disciple)
        st.session_state.realm = st.selectbox("境界", list(REALMS.keys()), index=list(REALMS.keys()).index(st.session_state.realm))
        st.session_state.affinity_main = st.selectbox("主灵根", ELEMENTS, index=ELEMENTS.index(st.session_state.affinity_main))
        st.session_state.seed = int(st.number_input("Seed", min_value=0, max_value=999_999_999, value=int(st.session_state.seed), step=1))

    query = st.text_input("🔍 搜索", placeholder="如：翠 / 过热 / BIOS")
    elem_filter = st.selectbox("元素筛选", ["全部"] + ELEMENTS + ["无"], index=0)

    st.markdown("---")

    def match(stone: Stone) -> bool:
        q = (query or "").strip()
        if q and (q not in stone.name and q not in stone.id):
            return False
        if elem_filter != "全部":
            if elem_filter == "无":
                if stone.element != "无":
                    return False
            else:
                if stone.element != elem_filter:
                    return False
        return True

    def render_group(title: str, kind: str):
        st.markdown(f"**{title}**")
        for sid, stone in STONES.items():
            if stone.kind != kind:
                continue
            if not match(stone):
                continue
            left = st.session_state.stock.get(sid, 0)
            label = f"{stone.icon} {stone.name}  ({left}/{stone.stock_total})"
            if st.button(label, key=f"lib_{sid}", use_container_width=True, disabled=(left <= 0)):
                st.session_state.picked_stone = sid
                st.session_state.selected_slot = None

    render_group("五行灵石", "gem")
    st.markdown("---")
    render_group("逻辑灵石", "logic")
    st.markdown("---")
    render_group("核心 BIOS", "core")

    # 待装配详情
    if st.session_state.picked_stone:
        stone = STONES[st.session_state.picked_stone]
        meta = ELEMENT_META.get(stone.element, ELEMENT_META["无"])
        st.markdown("---")
        st.markdown("##### 🧾 待装配")
        st.markdown(
            f"<div class='selected-hint'><b>{stone.icon} {stone.name}</b> "
            f"<span class='elem-tag' style='border-color:{meta['color']}; background:{meta['bg']};'>"
            f"{meta['icon']} {stone.element}</span>"
            f"<span class='elem-tag' style='opacity:0.85;'>类型：{stone.kind}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(stone.desc)
        if stone.kind == "gem":
            st.markdown("**环位效果（内/中/外）**")
            for k in ("inner", "middle", "outer"):
                eff = stone.effects.get(k, {})
                if not eff:
                    continue
                pretty = ", ".join([f"{kk}+{vv}" for kk, vv in eff.items()])
                st.markdown(f"- {k}：{pretty}")
        elif stone.kind == "logic":
            st.markdown(f"**门控**：{stone.logic.get('gate')}")
        else:
            st.markdown(f"**规则重写**：{stone.core_rules.get('bios')}")
        if st.button("取消选择", use_container_width=True):
            st.session_state.picked_stone = None

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# 中：真八卦盘
# -------------------------
with col_center:
    realm_cfg = REALMS[st.session_state.realm]
    tri_unlock = realm_cfg["tri_unlock"]
    core_unlocked = realm_cfg["core_slots"]

    # --- Sector + Hex slot SVG ---
    import math

    SECTORS = [
        ("fire", "火域", "#ff3b30", -90),
        ("earth", "土域", "#ffd34d", -18),
        ("metal", "金域", "#f5f5f5", 54),
        ("water", "水域", "#2f80ff", 126),
        ("wood", "木域", "#2dff6f", 198),
    ]
    SECTOR_SPAN = 72

    TRI_SECTOR = {
        "LI": ("fire", 0),
        "KAN": ("water", 0),
        "QIAN": ("metal", -10),
        "DUI": ("metal", 10),
        "ZHEN": ("wood", -10),
        "XUN": ("wood", 10),
        "KUN": ("earth", -10),
        "GEN": ("earth", 10),
    }

    R_LOGIC = 120
    R_INNER = 175
    R_MIDDLE = 230
    R_OUTER = 285

    slot_q = st.query_params.get("slot")
    if isinstance(slot_q, list):
        slot_q = slot_q[0] if slot_q else None
    if slot_q:
        try:
            if slot_q.startswith("CORE_"):
                idx = int(slot_q.split("_")[1])
                st.session_state.selected_slot = ("core", idx)
                if st.session_state.picked_stone:
                    ok, msg = can_place(st.session_state.picked_stone, ("core", idx))
                    if not ok:
                        st.toast(msg, icon="!")
                    else:
                        place(("core", idx), st.session_state.picked_stone)
            else:
                tri, idx_str = slot_q.split("_")
                idx = int(idx_str)
                st.session_state.selected_slot = ("tri", tri, idx)
                if st.session_state.picked_stone:
                    ok, msg = can_place(st.session_state.picked_stone, ("tri", tri, idx))
                    if not ok:
                        st.toast(msg, icon="!")
                    else:
                        place(("tri", tri, idx), st.session_state.picked_stone)
        finally:
            st.query_params.clear()
            st.rerun()

    def polar(cx, cy, r, deg):
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    def arc_path(cx, cy, r_outer, r_inner, start_deg, end_deg):
        x1, y1 = polar(cx, cy, r_outer, start_deg)
        x2, y2 = polar(cx, cy, r_outer, end_deg)
        x3, y3 = polar(cx, cy, r_inner, end_deg)
        x4, y4 = polar(cx, cy, r_inner, start_deg)
        large = 1 if (end_deg - start_deg) % 360 > 180 else 0
        return (
            f"M {x1:.1f},{y1:.1f} "
            f"A {r_outer},{r_outer} 0 {large} 1 {x2:.1f},{y2:.1f} "
            f"L {x3:.1f},{y3:.1f} "
            f"A {r_inner},{r_inner} 0 {large} 0 {x4:.1f},{y4:.1f} Z"
        )

    def hex_points(cx, cy, size):
        pts = []
        for i in range(6):
            ang = math.radians(60 * i - 30)
            pts.append((cx + size * math.cos(ang), cy + size * math.sin(ang)))
        return " ".join([f"{x:.1f},{y:.1f}" for x, y in pts])

    def slot_label_svg(tri, idx, locked):
        if locked:
            return "LOCK"
        sid = st.session_state.board[tri][idx]
        if sid:
            s = STONES[sid]
            if s.kind == "logic" or idx == 1:
                return "L"
            return s.icon
        return "+"

    size = 720
    cx = cy = size / 2
    r_outer = 320
    r_inner = 180
    ring_color = {1: "#00ffff", 2: "#2aa1ff", 3: "#2dff6f", 4: "#ffd34d"}

    svg = [
        f"<svg class='bagua-svg' width='{size}' height='{size}' viewBox='0 0 {size} {size}' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<filter id='glow'><feGaussianBlur stdDeviation='3' result='blur'/><feMerge><feMergeNode in='blur'/><feMergeNode in='SourceGraphic'/></feMerge></filter>",
        "</defs>",
    ]

    # ?????
    svg.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r_outer + 28}' fill='none' stroke='#00ffff' stroke-width='2' opacity='0.7' />")
    svg.append(f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r_outer + 18}' fill='none' stroke='rgba(0,255,255,0.2)' stroke-width='10' />")
    svg.append(f"<text x='{cx + r_outer + 40:.1f}' y='{cy:.1f}' text-anchor='start' alignment-baseline='middle' fill='#00ffff' font-size='12'>SPIRIT LOAD</text>")

    for key, label, color, center in SECTORS:
        start = center - SECTOR_SPAN / 2
        end = center + SECTOR_SPAN / 2
        path = arc_path(cx, cy, r_outer, r_inner, start, end)
        svg.append(
            f"<path d='{path}' fill='{color}' opacity='0.22' stroke='{color}' stroke-width='2' filter='url(#glow)' />"
        )
        lx, ly = polar(cx, cy, 300, center)
        svg.append(
            f"<text x='{lx:.1f}' y='{ly:.1f}' text-anchor='middle' alignment-baseline='middle' fill='{color}' font-size='12' style='text-shadow:0 0 8px {color};'>{label}</text>"
        )

    # ?????????/?/???
    for r, c in [(R_LOGIC, ring_color[1]), (R_INNER, ring_color[2]), (R_MIDDLE, ring_color[3]), (R_OUTER, ring_color[4])]:
        svg.append(
            f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{r}' fill='none' stroke='{c}' stroke-width='1.6' opacity='0.55' />"
        )

    # ?????
    for _, _, color, center in SECTORS:
        start = center - SECTOR_SPAN / 2
        end = center + SECTOR_SPAN / 2
        for angle in (start, end):
            x1, y1 = polar(cx, cy, r_inner, angle)
            x2, y2 = polar(cx, cy, r_outer, angle)
            svg.append(
                f"<line x1='{x1:.1f}' y1='{y1:.1f}' x2='{x2:.1f}' y2='{y2:.1f}' stroke='{color}' stroke-width='1.4' opacity='0.5' />"
            )

    # ????
    svg.append(
        f"<circle cx='{cx:.1f}' cy='{cy:.1f}' r='{R_LOGIC - 24}' fill='rgba(0,0,0,0.75)' stroke='rgba(0,255,255,0.45)' stroke-width='1.4' />"
    )

    ring_map = {1: R_LOGIC, 2: R_INNER, 3: R_MIDDLE, 4: R_OUTER}
    for tri in TRIGRAMS.keys():
        sector_key, offset = TRI_SECTOR[tri]
        center_angle = next(s[3] for s in SECTORS if s[0] == sector_key)
        angle = center_angle + offset
        for idx in (1, 2, 3, 4):
            locked = idx > tri_unlock
            r = ring_map[idx]
            x, y = polar(cx, cy, r, angle)
            pts = hex_points(x, y, 16 if idx == 1 else 18)
            label = slot_label_svg(tri, idx, locked)
            href = f"?slot={tri}_{idx}"
            stroke = ring_color[idx] if not locked else "#333"
            fill = "rgba(6,12,20,0.85)" if not locked else "rgba(20,20,20,0.6)"
            svg.append(
                f"<a href='{href}'><polygon class='hex-slot' points='{pts}' fill='{fill}' stroke='{stroke}' stroke-width='1.2' filter='url(#glow)'/></a>"
            )
            svg.append(
                f"<text x='{x:.1f}' y='{y+1:.1f}' text-anchor='middle' alignment-baseline='middle' fill='#dffbff' font-size='12'>{label}</text>"
            )

    core_positions = [(cx, cy - 32), (cx - 48, cy + 32), (cx + 48, cy + 32)]
    for i, (x, y) in enumerate(core_positions, start=1):
        locked = i > core_unlocked
        label = "LOCK" if locked else ("BIOS" if st.session_state.core.get(i) else "+")
        href = f"?slot=CORE_{i}"
        pts = hex_points(x, y, 20)
        stroke = "#00ffff" if not locked else "#333"
        fill = "rgba(6,12,20,0.9)" if not locked else "rgba(20,20,20,0.6)"
        svg.append(
            f"<a href='{href}'><polygon class='hex-slot' points='{pts}' fill='{fill}' stroke='{stroke}' stroke-width='1.2' filter='url(#glow)'/></a>"
        )
        svg.append(
            f"<text x='{x:.1f}' y='{y+1:.1f}' text-anchor='middle' alignment-baseline='middle' fill='#dffbff' font-size='10'>{label}</text>"
        )

    svg.append("</svg>")

    bagua_html = "<div class='bagua'><div class='bagua-ring-wrap'>" + "".join(svg) + "</div></div>"
    st.markdown(bagua_html, unsafe_allow_html=True)

    legend_items = [
        ("木", "🌿", "#2dff6f", "rgba(45,255,111,0.12)"),
        ("火", "🔥", "#ff3b30", "rgba(255,59,48,0.12)"),
        ("土", "🪨", "#ffd34d", "rgba(255,211,77,0.14)"),
        ("金", "⚔️", "#f5f5f5", "rgba(245,245,245,0.12)"),
        ("水", "💧", "#2f80ff", "rgba(47,128,255,0.12)"),
    ]
    legend_cols = st.columns(5)
    for i, (label, icon, color, bg) in enumerate(legend_items):
        legend_cols[i].markdown(
            f"<div class='elem-tag' style='justify-content:center; width:100%; border-color:{color}; background:{bg};'>"
            f"{icon} <b>{label}</b></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div class='tiny' style='margin-top:8px;'>提示：每卦第1位为逻辑位（L），其余为内/中/外环位（+）。</div>", unsafe_allow_html=True)
    st.markdown("<div class='tiny' style='margin-bottom:8px;'>八卦方位：上离下坎，左兑右震，左上乾右上艮，左下坤右下巽。</div>", unsafe_allow_html=True)
# -------------------------
# 右：衍算结果/运行
# -------------------------
with col_status:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("#### 🔮 衍算结果")

    mode = st.radio("视图", ["常态", "危机态(HP<30%)"], horizontal=True)
    is_crisis = (mode != "常态")
    ctx = ctx_crisis if is_crisis else ctx_normal
    stats = ctx["stats"]

    if ctx["status"] == "FAIL":
        st.error("❌ 带宽超限，无法运行")
    else:
        st.success("✅ 架构可运行")

    st.metric("带宽", f"{int(stats['bandwidth'])}/{int(stats['bw_safe'])}", delta=f"极限 {int(stats['bw_max'])}")
    st.metric("热量/魔念", f"{stats['heat']:.0f}/100", delta=f"故障率 {stats['glitch_p']*100:.0f}%")

    st.markdown("---")
    st.markdown("**五行分布**")
    total = max(1, sum(ctx["elem_counts"].values()))
    for e in ELEMENTS:
        n = ctx["elem_counts"].get(e, 0)
        st.progress(n / total, text=f"{ELEMENT_META[e]['icon']} {e} {n}")

    st.markdown("---")
    st.markdown("**摘要**")
    for line in stat_lines(stats):
        st.markdown(f"- {line}")

    st.markdown("---")
    st.markdown("**机制触发**")
    if not ctx["notes"]:
        st.caption("（无）")
    else:
        for n in ctx["notes"][:10]:
            st.caption("• " + n)
        if len(ctx["notes"]) > 10:
            st.caption(f"… 还有 {len(ctx['notes'])-10} 条")

    st.markdown("---")
    c1, c2 = st.columns(2)
    if c1.button("▶ 运行(新Seed)", type="primary", use_container_width=True):
        st.session_state.seed = random.randint(0, 999_999_999)
        st.session_state.sim_result = simulate(st.session_state.seed, is_crisis)

    if c2.button("🔁 复测(同Seed)", use_container_width=True):
        st.session_state.sim_result = simulate(int(st.session_state.seed), is_crisis)

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown("##### 🧪 复测输出")
        st.caption(f"Seed={res['seed']} | 模式={mode}")
        if res["burnt"]:
            st.warning(res["burnt"])
        else:
            st.success("本次未发生熔断")

    st.markdown("</div>", unsafe_allow_html=True)

# =========================================================
# 11) 槽位详情（底部）
# =========================================================
st.markdown("### 📝 槽位详情")
with st.container(border=True):
    sel = st.session_state.selected_slot
    if not sel:
        st.caption("点击八卦盘任意槽位查看/卸下。")
    else:
        if sel[0] == "core":
            _, idx = sel
            sid = st.session_state.core.get(idx)
            st.markdown(f"**阵眼核心槽 #{idx}**")
            if sid:
                stone = STONES[sid]
                st.markdown(f"- 当前：{stone.icon} {stone.name}")
                st.caption(stone.desc)
                if st.button("卸下核心", key="rm_core", use_container_width=True):
                    remove(sel)
            else:
                st.caption("（空）可装入核心BIOS")
        else:
            _, tri, idx = sel
            info = TRIGRAMS[tri]
            sid = st.session_state.board[tri][idx]
            st.markdown(f"**{info['symbol']} {info['name']}（{info['elem']}域） · 槽位 {idx}**")
            if idx == 1:
                st.caption("逻辑位（🧩）：装入逻辑灵石以门控该卦。")
            else:
                st.caption(f"{LAYER_NAME[idx]}环位：同一灵石在不同环位效果不同。")

            if sid:
                stone = STONES[sid]
                meta = ELEMENT_META.get(stone.element, ELEMENT_META["无"])
                st.markdown(
                    f"<div class='selected-hint'><b>{stone.icon} {stone.name}</b> "
                    f"<span class='elem-tag' style='border-color:{meta['color']}; background:{meta['bg']};'>"
                    f"{meta['icon']} {stone.element}</span>"
                    f"<span class='elem-tag' style='opacity:0.85;'>类型：{stone.kind}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.caption(stone.desc)
                if stone.kind == "gem" and idx in LAYER_KEY:
                    layer = LAYER_KEY[idx]
                    eff = stone.effects.get(layer, {})
                    pretty = ", ".join([f"{k}+{v}" for k, v in eff.items()]) if eff else "（无）"
                    st.markdown(f"**该环位效果**：{pretty}")
                elif stone.kind == "logic":
                    st.markdown(f"**门控**：{stone.logic.get('gate')}")
                elif stone.kind == "core":
                    st.markdown(f"**规则重写**：{stone.core_rules.get('bios')}")

                if st.button("卸下", key="rm_slot", use_container_width=True):
                    remove(sel)
            else:
                st.caption("（空）")

