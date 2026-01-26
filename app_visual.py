import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import streamlit as st

# =========================================================
# 赛博道体·灵石构筑台（可执行 Streamlit 单文件）
# - 5 行五行区域（木火土金水）
# - 所有槽位集中在一个面板内（含核心槽）
# - 灵石库存有限（必须做均衡/偏科取舍）
# - 同一灵石在不同“插槽区域（列段）”效果不同（暗黑4宝石风格）
# - 进阶机制：相邻共鸣/线路导通、核心 BIOS 重写、过载走火入魔、空槽利用、逻辑灵石
# =========================================================

st.set_page_config(layout="wide", page_title="赛博道体·灵石构筑台", page_icon="☯️")

# ----------------------
# 样式（尽量沿用你现有风格）
# ----------------------
CSS = """
<style>
  .stApp { background-color: #0E1117; }

  .guofeng-box {
    border: 2px solid #444;
    border-radius: 10px;
    background-color: #161B22;
    padding: 16px;
    margin-bottom: 16px;
    position: relative;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
  }
  .guofeng-box::before {
    content: "";
    position: absolute; top: -2px; left: -2px; width: 15px; height: 15px;
    border-top: 3px solid #D4AC0D; border-left: 3px solid #D4AC0D;
  }
  .guofeng-box::after {
    content: "";
    position: absolute; bottom: -2px; right: -2px; width: 15px; height: 15px;
    border-bottom: 3px solid #D4AC0D; border-right: 3px solid #D4AC0D;
  }

  .hud-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
  .tiny { font-size: 12px; color: #9aa4b2; }

  .row-label {
    font-family: "KaiTi", "SimKai", "Microsoft YaHei", serif;
    font-weight: 800;
    letter-spacing: 2px;
    padding: 8px 10px;
    border-radius: 8px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(0,0,0,0.25);
  }

  .slot-help {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #9aa4b2;
    font-size: 12px;
  }

  .pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(255,255,255,0.06);
    font-size: 12px;
    color: #d9e2ef;
    margin-right: 6px;
  }

  /* 让按钮更紧凑一些 */
  div[data-testid="stButton"] > button {
    padding: 0.45rem 0.55rem;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.04);
  }

  /* 选中态提示：用边框模拟 */
  .selected-hint {
    border-left: 3px solid #FFD700;
    padding-left: 10px;
  }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ----------------------
# 五行与相生相克
# ----------------------
ELEMENT_ORDER = ["木", "火", "土", "金", "水"]
ELEMENT_META = {
    "木": {"color": "#2ECC71", "icon": "🌿"},
    "火": {"color": "#E74C3C", "icon": "🔥"},
    "土": {"color": "#D35400", "icon": "🪨"},
    "金": {"color": "#E6B800", "icon": "🗡️"},
    "水": {"color": "#3498DB", "icon": "💧"},
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
    """返回克制该元素的元素（即谁克它）"""
    for k, v in OVERCOME.items():
        if v == e:
            return k
    return ""  # should not


# ----------------------
# 插槽区域（列段）= 暗黑4“放武器/防具/戒指效果不同”
# - 8 列：1-2 武器，3-4 防具，5-6 饰品，7-8 经脉
# ----------------------
REGIONS = [
    (1, 2, "weapon", "⚔️武器"),
    (3, 4, "armor", "🛡️防具"),
    (5, 6, "jewelry", "💍饰品"),
    (7, 8, "meridian", "☯️经脉"),
]


def region_of_col(col: int) -> str:
    for a, b, rid, _ in REGIONS:
        if a <= col <= b:
            return rid
    return "meridian"


def region_label(rid: str) -> str:
    for _, _, rr, name in REGIONS:
        if rr == rid:
            return name
    return rid


# ----------------------
# Realm presets（境界解锁与带宽阈值）
# - 每个境界解锁的列数（每行）
# - 核心槽数量
# - 带宽安全阈值与极限阈值
# ----------------------
REALMS = {
    "炼气": {"unlock_cols": 4, "core_slots": 1, "bw_safe": 18, "bw_max": 26},
    "筑基": {"unlock_cols": 5, "core_slots": 1, "bw_safe": 24, "bw_max": 34},
    "金丹": {"unlock_cols": 6, "core_slots": 2, "bw_safe": 30, "bw_max": 42},
    "元婴": {"unlock_cols": 7, "core_slots": 2, "bw_safe": 36, "bw_max": 50},
    "化神": {"unlock_cols": 8, "core_slots": 3, "bw_safe": 42, "bw_max": 58},
}


# ----------------------
# 数据结构
# ----------------------
@dataclass
class Stone:
    id: str
    name: str
    element: str  # 木火土金水 or "无"
    icon: str
    rarity: str
    bandwidth: int
    stock_total: int
    kind: str  # gem / logic / core
    # 不同区域效果不同：stat_key -> base_value
    effects: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # 逻辑 stone 的参数：例如 gate 条件
    logic: Dict[str, str] = field(default_factory=dict)
    # core stone 的规则重写
    core_rules: Dict[str, str] = field(default_factory=dict)
    desc: str = ""


def make_stones() -> Dict[str, Stone]:
    """定义灵石库（示例值，后续你可以直接调数值）"""
    stones: List[Stone] = []

    # 五行宝石（同一颗在不同区域不同效果）
    stones += [
        Stone(
            id="gem_emerald",
            name="翠灵石",
            element="木",
            icon="🟩",
            rarity="rare",
            bandwidth=5,
            stock_total=2,
            kind="gem",
            effects={
                "weapon": {"crit_dmg": 12},
                "armor": {"hp": 160},
                "jewelry": {"elem_dmg_木": 10},
                "meridian": {"elem_res_木": 10},
            },
            desc="木系灵石。偏向毒/持续/韧性构筑。",
        ),
        Stone(
            id="gem_ruby",
            name="赤焰石",
            element="火",
            icon="🟥",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "weapon": {"atk": 14},
                "armor": {"elem_res_火": 12},
                "jewelry": {"elem_dmg_火": 11},
                "meridian": {"burn": 6},
            },
            desc="火系灵石。爆发/灼烧/极限输出倾向。",
        ),
        Stone(
            id="gem_sapphire",
            name="玄冰石",
            element="水",
            icon="🟦",
            rarity="rare",
            bandwidth=5,
            stock_total=2,
            kind="gem",
            effects={
                "weapon": {"crit": 3},
                "armor": {"def": 14},
                "jewelry": {"elem_dmg_水": 10},
                "meridian": {"cooling": 3},
            },
            desc="水系灵石。防御/冷却/护体倾向。",
        ),
        Stone(
            id="gem_topaz",
            name="厚土石",
            element="土",
            icon="🟧",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "weapon": {"vuln": 8},
                "armor": {"hp": 220},
                "jewelry": {"elem_dmg_土": 10},
                "meridian": {"elem_res_土": 12},
            },
            desc="土系灵石。生命/易伤/稳态倾向。",
        ),
        Stone(
            id="gem_diamond",
            name="金魄石",
            element="金",
            icon="⬜",
            rarity="rare",
            bandwidth=6,
            stock_total=2,
            kind="gem",
            effects={
                "weapon": {"atk": 10, "crit_dmg": 6},
                "armor": {"def": 10},
                "jewelry": {"elem_dmg_金": 10},
                "meridian": {"elem_res_金": 10},
            },
            desc="金系灵石。攻防均衡、偏向穿透/锋锐。",
        ),
    ]

    # 逻辑灵石（只能插在每行第1格“逻辑位”）
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
            desc="该行平时不通电；生命低于30%时整行激活。",
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
            desc="过热时启动保护：降低故障率，但该行效能下降。",
        ),
    ]

    # 核心（BIOS重写规则）只能插核心槽
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
            desc="防御收益会被部分折算为攻击；极端进攻型。",
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
            desc="五行标签逆转（火↔水、木↔金），重新定义共鸣与弱点。",
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
            desc="提高带宽阈值，但热量更易积累，走火入魔风险上升。",
        ),
    ]

    return {s.id: s for s in stones}


STONES = make_stones()


# ----------------------
# Session init
# ----------------------

def init_state() -> None:
    if "realm" not in st.session_state:
        st.session_state.realm = "金丹"
    if "seed" not in st.session_state:
        st.session_state.seed = 184023
    if "disciple" not in st.session_state:
        st.session_state.disciple = "李长风"
    if "affinity_main" not in st.session_state:
        st.session_state.affinity_main = "木"

    # board: dict[row][col] => stone_id or None
    if "board" not in st.session_state:
        st.session_state.board = {row: {c: None for c in range(1, 9)} for row in ELEMENT_ORDER}
    if "core" not in st.session_state:
        st.session_state.core = {i: None for i in range(1, 4)}  # core slots 1..3

    # inventory (remaining)
    if "stock" not in st.session_state:
        st.session_state.stock = {sid: STONES[sid].stock_total for sid in STONES}

    # currently picked stone from library
    if "picked_stone" not in st.session_state:
        st.session_state.picked_stone = None

    # selected slot for detail panel
    if "selected_slot" not in st.session_state:
        st.session_state.selected_slot = None  # (kind, row, col) or ("core", idx)

    # simulation last result
    if "sim_result" not in st.session_state:
        st.session_state.sim_result = None


init_state()


# ----------------------
# Helper: affinity multipliers
# ----------------------

def element_affinity_multiplier(elem: str) -> float:
    # 主灵根：该元素 +20%，被其克制的元素 -5%，其生成的元素 +5%
    main = st.session_state.affinity_main
    if elem not in ELEMENT_META:
        return 1.0
    if elem == main:
        return 1.20
    if is_generate(main, elem):
        return 1.05
    if is_overcome(elem, main):
        # elem 克 main（对主灵根不友好）
        return 0.95
    return 1.0


# ----------------------
# Build compilation
# ----------------------

def get_bios() -> Optional[str]:
    # 取第一个已装 BIOS
    for i in range(1, 4):
        sid = st.session_state.core.get(i)
        if not sid:
            continue
        s = STONES[sid]
        if s.kind == "core":
            return s.core_rules.get("bios")
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


def compile_context(is_crisis: bool) -> Dict[str, float]:
    """编译并返回统计结果（给右侧面板使用）。

    is_crisis:
      False = 常态
      True  = 危机态（HP<30%）
    """

    realm_cfg = REALMS[st.session_state.realm]
    unlock_cols = realm_cfg["unlock_cols"]
    core_slots_unlocked = realm_cfg["core_slots"]

    bios = get_bios()

    # stats container
    stats: Dict[str, float] = {
        "atk": 0,
        "def": 0,
        "hp": 0,
        "crit": 0,
        "crit_dmg": 0,
        "vuln": 0,
        "burn": 0,
        "cooling": 0,
        "stability": 80.0,  # base
        "bandwidth": 0,
    }

    # per-element damage/resist
    for e in ELEMENT_META:
        stats[f"elem_dmg_{e}"] = 0
        stats[f"elem_res_{e}"] = 0

    # collect active sockets
    # gating: each row col1 is logic slot, may gate the row
    row_active: Dict[str, bool] = {r: True for r in ELEMENT_ORDER}
    for r in ELEMENT_ORDER:
        logic_sid = st.session_state.board[r][1]
        if logic_sid and STONES[logic_sid].kind == "logic":
            gate = STONES[logic_sid].logic.get("gate")
            if gate == "HP_LT_30":
                row_active[r] = is_crisis
            elif gate == "HEAT_GT_50":
                # 过热逻辑在后面根据 heat 再判定，本阶段先保留 True
                row_active[r] = True

    # element counts（用于共鸣/弱点）
    elem_counts: Dict[str, int] = {e: 0 for e in ELEMENT_META}

    # adjacency notes
    notes: List[str] = []

    # slot multipliers computed per socket
    socket_mult: Dict[Tuple[str, int], float] = {}

    # 线路导通奖励统计
    circuits_on: List[str] = []

    # first pass: base effects + per-socket multipliers
    for r in ELEMENT_ORDER:
        for c in range(1, 9):
            if c > unlock_cols:
                continue
            sid = st.session_state.board[r][c]
            if not sid:
                continue
            stone = STONES[sid]

            # logic stone is only meaningful in col1
            if stone.kind == "logic":
                # logic stones consume bandwidth only when row is considered (always) -
                # 但如果是血危门控，常态下不通电 -> 常态不占带宽
                if stone.logic.get("gate") == "HP_LT_30" and (not is_crisis):
                    continue
                stats["bandwidth"] += stone.bandwidth
                continue

            # row gated off
            if not row_active[r]:
                continue

            # bandwidth
            stats["bandwidth"] += stone.bandwidth

            # counts (exclude core/logic)
            if stone.element in elem_counts:
                elem_counts[stone.element] += 1

            # base multiplier: element affinity of stone element
            mult = element_affinity_multiplier(stone.element) if stone.element in ELEMENT_META else 1.0

            # row-domain interaction: gem element vs row element
            if stone.element in ELEMENT_META:
                if is_generate(stone.element, r):
                    mult *= 1.5
                    notes.append(f"相生：{stone.element} 生 {r}（{r}{c} +50%）")
                elif is_overcome(stone.element, r):
                    mult *= 0.8
                    notes.append(f"相克：{stone.element} 克 {r}（{r}{c} -20%）")

            socket_mult[(r, c)] = mult

    # neighbor synergy inside row (position matters)
    for r in ELEMENT_ORDER:
        if not row_active[r]:
            continue
        for c in range(1, 8):
            if c + 1 > unlock_cols:
                continue
            sid_a = st.session_state.board[r][c]
            sid_b = st.session_state.board[r][c + 1]
            if not sid_a or not sid_b:
                continue
            a = STONES[sid_a]
            b = STONES[sid_b]
            if a.kind != "gem" or b.kind != "gem":
                continue
            if a.element in ELEMENT_META and b.element in ELEMENT_META:
                if is_generate(a.element, b.element):
                    socket_mult[(r, c + 1)] = socket_mult.get((r, c + 1), 1.0) * 1.2
                    notes.append(f"相邻链：{a.element}→{b.element}（{r}{c+1} +20%）")
                elif is_overcome(a.element, b.element):
                    socket_mult[(r, c + 1)] = socket_mult.get((r, c + 1), 1.0) * 0.85
                    notes.append(f"相邻冲：{a.element}×{b.element}（{r}{c+1} -15%）")

    # empty-slot utility + solitude bonus
    for r in ELEMENT_ORDER:
        # only consider unlocked sockets excluding logic slot (col1)
        usable_cols = list(range(2, unlock_cols + 1))
        filled: List[int] = [c for c in usable_cols if st.session_state.board[r][c] and STONES[st.session_state.board[r][c]].kind == "gem" and row_active[r]]
        empty = [c for c in usable_cols if not st.session_state.board[r][c]]

        # cooling from empty slots
        if row_active[r]:
            stats["cooling"] += 0.8 * len(empty)

        # solitude multiplier if exactly one filled
        if len(filled) == 1 and row_active[r]:
            c = filled[0]
            empties = len(empty)
            m = 1.0 + min(1.2, 0.2 * empties)  # cap +120%
            socket_mult[(r, c)] = socket_mult.get((r, c), 1.0) * m
            notes.append(f"留白·独尊：{r}{c} ×{m:.2f}")

    # circuit connectivity: define 2 lines per row
    CIRCUITS = [
        [2, 3, 4],
        [5, 6, 7, 8],
    ]

    for r in ELEMENT_ORDER:
        if not row_active[r]:
            continue
        for seg in CIRCUITS:
            # only if segment within unlock
            if any(c > unlock_cols for c in seg):
                continue
            # all filled with non-empty (gem or logic? treat gem only)
            if any(st.session_state.board[r][c] is None for c in seg):
                continue
            # conflict check: if any adjacent pair is overcome (hard conflict) -> fail
            ok = True
            for i in range(len(seg) - 1):
                sa = STONES[st.session_state.board[r][seg[i]]]
                sb = STONES[st.session_state.board[r][seg[i + 1]]]
                if sa.kind != "gem" or sb.kind != "gem":
                    continue
                if sa.element in ELEMENT_META and sb.element in ELEMENT_META and is_overcome(sa.element, sb.element):
                    ok = False
                    break
            if not ok:
                continue

            # success: grant hidden effect
            circuits_on.append(f"{r}线{seg[0]}-{seg[-1]}")
            stats[f"elem_dmg_{r}"] += 5  # row element bonus
            stats["stability"] += 2

    # second pass: apply effects
    for r in ELEMENT_ORDER:
        for c in range(1, 9):
            if c > unlock_cols:
                continue
            sid = st.session_state.board[r][c]
            if not sid:
                continue
            stone = STONES[sid]

            # logic stones handled earlier
            if stone.kind != "gem":
                continue
            if not row_active[r]:
                continue

            rid = region_of_col(c)
            eff = stone.effects.get(rid, {})
            mult = socket_mult.get((r, c), 1.0)

            # if HEAT gate logic is present in this row and heat > 50, later apply; placeholder now.
            for k, v in eff.items():
                stats[k] = stats.get(k, 0) + v * mult

    # Apply core stones bandwidth and BIOS influence
    for i in range(1, core_slots_unlocked + 1):
        sid = st.session_state.core.get(i)
        if not sid:
            continue
        stone = STONES[sid]
        stats["bandwidth"] += stone.bandwidth

    # BIOS rewrites
    bw_safe = realm_cfg["bw_safe"]
    bw_max = realm_cfg["bw_max"]

    if bios == "OVERCLOCK":
        bw_safe += 6
        bw_max += 10
        stats["stability"] -= 3
    elif bios == "MAD_CYBER":
        # defensive stats partially convert to atk
        convert = 0.25 * (stats.get("def", 0) + 0.02 * stats.get("hp", 0))
        stats["atk"] += convert
        stats["stability"] -= 2
    elif bios == "INVERT_5":
        # swap element dmg/res based on inversion
        for e in list(ELEMENT_META.keys()):
            inv = invert_element(e)
            if inv == e:
                continue
            stats[f"elem_dmg_{e}"] , stats[f"elem_dmg_{inv}"] = stats.get(f"elem_dmg_{inv}", 0), stats.get(f"elem_dmg_{e}", 0)
            stats[f"elem_res_{e}"] , stats[f"elem_res_{inv}"] = stats.get(f"elem_res_{inv}", 0), stats.get(f"elem_res_{e}", 0)

    # Compute elemental resonance & weakness
    # Determine dominant element among gems
    counts_list = [(e, elem_counts[e]) for e in ELEMENT_META]
    counts_list.sort(key=lambda x: x[1], reverse=True)
    dom_e, dom_n = counts_list[0]
    second_n = counts_list[1][1]
    min_n = min(n for _, n in counts_list)

    # balanced if all close
    if dom_n > 0 and (dom_n - min_n) <= 1:
        stats["stability"] += 6
        for e in ELEMENT_META:
            stats[f"elem_res_{e}"] += 4
        notes.append("均衡：五行相对平衡（稳定+6 / 全抗+4）")
    elif dom_n >= 3 and (dom_n - second_n) >= 3:
        # specialization
        stats[f"elem_dmg_{dom_e}"] += (dom_n - 2) * 4
        weak = counter_element(dom_e)
        stats[f"elem_res_{weak}"] -= (dom_n - 2) * 4
        stats["stability"] -= (dom_n - 2) * 1.5
        notes.append(f"偏科：{dom_e}共鸣（{dom_e}伤害提升），弱点：{weak}抗性下降")
    elif dom_n >= 3:
        stats[f"elem_dmg_{dom_e}"] += (dom_n - 2) * 3
        notes.append(f"共鸣：{dom_e}数量≥3（{dom_e}伤害提升）")

    # Overclock & heat
    bw = stats["bandwidth"]
    over = max(0.0, bw - bw_safe)
    filled_slots = sum(
        1
        for r in ELEMENT_ORDER
        for c in range(1, unlock_cols + 1)
        if st.session_state.board[r][c]
    )
    filled_core = sum(1 for i in range(1, core_slots_unlocked + 1) if st.session_state.core.get(i))

    # base heat: more slots + overage, reduced by cooling
    heat = 10 + 0.8 * (filled_slots + filled_core) + 3.2 * over - 1.2 * stats.get("cooling", 0)
    heat = max(0.0, min(100.0, heat))

    # If row has logic_heat, then when heat>50 reduce glitch but reduce that row effect: approximate
    if heat > 50:
        for r in ELEMENT_ORDER:
            sid = st.session_state.board[r][1]
            if sid and STONES[sid].kind == "logic" and STONES[sid].logic.get("gate") == "HEAT_GT_50":
                stats["stability"] += 2
                notes.append(f"逻辑·过热：{r}行进入保护（稳定+2，效能-10%已体现在统计）")
                # apply -10% to row element dmg (cheap approximation)
                stats[f"elem_dmg_{r}"] *= 0.9

    # glitch probability
    # - if bw <= safe: very low
    # - if safe < bw <= max: grows with heat and over
    # - if bw > max: impossible (fail)
    if bw > bw_max:
        status = "FAIL"
        glitch_p = 1.0
    else:
        status = "OK"
        base_p = 0.01
        glitch_p = base_p + (heat / 200.0) + (over / max(1.0, bw_max)) * 0.35
        glitch_p = min(0.65, max(base_p, glitch_p))

    # circuits contribute to notes
    if circuits_on:
        notes.append(f"导通：{', '.join(circuits_on)}（隐藏特效已激活）")

    # final sanity
    stats["heat"] = heat
    stats["bw_safe"] = bw_safe
    stats["bw_max"] = bw_max
    stats["glitch_p"] = glitch_p
    stats["status"] = 1.0 if status == "OK" else 0.0

    # return with extra
    stats["_dom_elem"] = 0  # placeholder
    return {
        "stats": stats,
        "notes": notes,
        "elem_counts": elem_counts,
        "row_active": row_active,
        "bios": bios,
        "unlock_cols": unlock_cols,
        "core_unlocked": core_slots_unlocked,
        "circuits": circuits_on,
        "status": status,
    }


def simulate(seed: int, is_crisis: bool) -> Dict:
    """确定性模拟：按 seed 决定是否走火入魔并熔断一个槽位（演示用）。"""
    ctx = compile_context(is_crisis=is_crisis)
    s = ctx["stats"]

    rng = random.Random(seed)
    burnt = None
    if ctx["status"] == "FAIL":
        burnt = "带宽超限（无法运行）"
        return {"ctx": ctx, "burnt": burnt, "seed": seed}

    if rng.random() < s["glitch_p"]:
        # pick a random active gem slot
        candidates = []
        unlock_cols = ctx["unlock_cols"]
        for r in ELEMENT_ORDER:
            if not ctx["row_active"][r]:
                continue
            for c in range(1, unlock_cols + 1):
                sid = st.session_state.board[r][c]
                if sid and STONES[sid].kind == "gem":
                    candidates.append((r, c, sid))
        if candidates:
            r, c, sid = rng.choice(candidates)
            burnt = f"熔断：{r}{c} {STONES[sid].name}"

    return {"ctx": ctx, "burnt": burnt, "seed": seed}


# ----------------------
# UI helpers
# ----------------------

def format_stat_line(stats: Dict[str, float]) -> List[str]:
    lines = []
    lines.append(f"ATK {stats.get('atk',0):.1f}  DEF {stats.get('def',0):.1f}  HP {stats.get('hp',0):.0f}")
    lines.append(f"暴击 {stats.get('crit',0):.1f}%  暴伤 {stats.get('crit_dmg',0):.1f}%  易伤 {stats.get('vuln',0):.1f}%")
    lines.append(f"稳定 {stats.get('stability',0):.1f}  冷却散热 {stats.get('cooling',0):.1f}")
    return lines


def slot_label(stone_id: Optional[str], locked: bool, is_logic_slot: bool, row: str, col: int) -> str:
    if locked:
        return "🔒"
    if stone_id:
        s = STONES[stone_id]
        if s.kind == "logic":
            return f"{s.icon}逻辑"
        return f"{s.icon}{s.name[:2]}"
    # empty
    if is_logic_slot:
        return "＋逻辑"
    return "＋"


def can_place(stone_id: str, target_kind: str, row: Optional[str], col: Optional[int]) -> Tuple[bool, str]:
    s = STONES[stone_id]
    if target_kind == "core":
        if s.kind != "core":
            return False, "该槽为核心槽，只能放核心BIOS。"
        return True, ""

    # normal board
    if s.kind == "core":
        return False, "核心BIOS只能装入核心槽。"
    if row and col:
        if col == 1:
            if s.kind != "logic":
                return False, "该格为逻辑位，只能放逻辑灵石。"
        else:
            if s.kind == "logic":
                return False, "逻辑灵石只能放在每行第1格逻辑位。"
    return True, ""


def place_on_board(row: str, col: int, stone_id: str) -> None:
    # stock check
    if st.session_state.stock.get(stone_id, 0) <= 0:
        st.toast("库存不足", icon="⚠️")
        return

    # return old
    old = st.session_state.board[row][col]
    if old:
        st.session_state.stock[old] += 1

    st.session_state.board[row][col] = stone_id
    st.session_state.stock[stone_id] -= 1


def place_on_core(idx: int, stone_id: str) -> None:
    if st.session_state.stock.get(stone_id, 0) <= 0:
        st.toast("库存不足", icon="⚠️")
        return
    old = st.session_state.core.get(idx)
    if old:
        st.session_state.stock[old] += 1
    st.session_state.core[idx] = stone_id
    st.session_state.stock[stone_id] -= 1


def remove_slot(kind: str, row: Optional[str] = None, col: Optional[int] = None, idx: Optional[int] = None) -> None:
    if kind == "core" and idx is not None:
        old = st.session_state.core.get(idx)
        if old:
            st.session_state.stock[old] += 1
        st.session_state.core[idx] = None
        return
    if kind == "board" and row and col:
        old = st.session_state.board[row][col]
        if old:
            st.session_state.stock[old] += 1
        st.session_state.board[row][col] = None


# ----------------------
# HUD / Top
# ----------------------

ctx_normal = compile_context(is_crisis=False)
ctx_crisis = compile_context(is_crisis=True)

hud1, hud2, hud3, hud4 = st.columns([2.2, 1, 1, 1.5])
with hud1:
    st.markdown(f"### ☯️ **灵石构筑台**")
    st.caption(f"弟子：{st.session_state.disciple} | 境界：{st.session_state.realm} | 主灵根：{st.session_state.affinity_main}")
with hud2:
    unlock_cols = ctx_normal["unlock_cols"]
    total_slots = len(ELEMENT_ORDER) * unlock_cols
    used = sum(1 for r in ELEMENT_ORDER for c in range(1, unlock_cols + 1) if st.session_state.board[r][c])
    st.metric("插槽", f"{used} / {total_slots}")
with hud3:
    s = ctx_normal["stats"]
    st.metric("带宽", f"{int(s['bandwidth'])} / {int(s['bw_safe'])}", delta=f"极限 {int(s['bw_max'])}")
with hud4:
    s = ctx_normal["stats"]
    stable_pct = max(0.0, min(100.0, 100.0 - s["glitch_p"] * 100.0))
    color = "#00FF7F" if stable_pct >= 80 else ("#FFD700" if stable_pct >= 60 else "#FF4500")
    st.markdown(
        f"""
<div style="text-align:right;" class="hud-mono">
  <div style="color:{color}; font-size:18px; font-weight:800;">● 稳定 {stable_pct:.0f}%</div>
  <div style="color:#777; font-size:12px;">Seed: {st.session_state.seed}</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.divider()

# ----------------------
# Main layout
# ----------------------
col_lib, col_center, col_status = st.columns([1.25, 2.4, 1.1])

# ========== Left: Stone Library ==========
with col_lib:
    st.markdown("##### 📦 灵石库")

    # realm and affinity controls
    with st.expander("⚙️ 弟子/境界设置", expanded=True):
        st.session_state.disciple = st.text_input("弟子名", value=st.session_state.disciple)
        st.session_state.realm = st.selectbox("境界", list(REALMS.keys()), index=list(REALMS.keys()).index(st.session_state.realm))
        st.session_state.affinity_main = st.selectbox("主灵根", ELEMENT_ORDER, index=ELEMENT_ORDER.index(st.session_state.affinity_main))
        st.session_state.seed = st.number_input("Seed", min_value=0, max_value=999999999, value=int(st.session_state.seed), step=1)

    query = st.text_input("🔍 搜索灵石", placeholder="如：翠 / 逻辑 / BIOS")
    elem_filter = st.selectbox("元素筛选", ["全部"] + ELEMENT_ORDER + ["无"], index=0)

    st.caption("点击灵石进入“待装配”状态，然后点击中间面板的槽位进行镶嵌。")

    def match(stone: Stone) -> bool:
        if query and query.strip() and (query.strip() not in stone.name and query.strip() not in stone.id):
            return False
        if elem_filter != "全部":
            if elem_filter == "无":
                if stone.element != "无":
                    return False
            else:
                if stone.element != elem_filter:
                    return False
        return True

    # show stones grouped by kind
    def render_group(title: str, kind: str):
        st.markdown(f"**{title}**")
        for sid, stone in STONES.items():
            if stone.kind != kind:
                continue
            if not match(stone):
                continue
            left = st.session_state.stock.get(sid, 0)
            label = f"{stone.icon} {stone.name}  ({left}/{stone.stock_total})"
            disabled = left <= 0
            if st.button(label, use_container_width=True, disabled=disabled, key=f"lib_{sid}"):
                st.session_state.picked_stone = sid
                st.session_state.selected_slot = None

    render_group("五行灵石", "gem")
    st.markdown("---")
    render_group("逻辑灵石", "logic")
    st.markdown("---")
    render_group("核心 BIOS", "core")

    # picked stone detail
    if st.session_state.picked_stone:
        stone = STONES[st.session_state.picked_stone]
        st.markdown("---")
        st.markdown("##### 🧾 待装配")
        st.markdown(f"<div class='selected-hint'><b>{stone.icon} {stone.name}</b> <span class='pill'>{stone.kind}</span> <span class='pill'>{stone.element}</span></div>", unsafe_allow_html=True)
        st.caption(stone.desc)
        if stone.kind == "gem":
            st.markdown("**不同插槽区域效果**")
            for rid in ["weapon", "armor", "jewelry", "meridian"]:
                eff = stone.effects.get(rid, {})
                if not eff:
                    continue
                pretty = ", ".join([f"{k}+{v}" for k, v in eff.items()])
                st.markdown(f"- {region_label(rid)}：{pretty}")
        elif stone.kind == "logic":
            st.markdown(f"**逻辑条件**：{stone.logic.get('gate')}")
        elif stone.kind == "core":
            st.markdown(f"**规则重写**：{stone.core_rules.get('bios')}")
        if st.button("取消选择", use_container_width=True):
            st.session_state.picked_stone = None


# ========== Center: Unified Slot Panel (Core + 5 rows) ==========
with col_center:
    st.markdown("<div class='guofeng-box'>", unsafe_allow_html=True)

    realm_cfg = REALMS[st.session_state.realm]
    unlock_cols = realm_cfg["unlock_cols"]
    core_unlocked = realm_cfg["core_slots"]

    st.markdown("#### 🧷 槽位面板（核心 + 五行）")
    st.caption("所有槽位都在这里：上方为核心 BIOS 槽；下方五行各一行（第1格为逻辑位）。")

    # Core slots row (inside the same panel)
    st.markdown("**🧠 核心槽（BIOS）**")
    core_cols = st.columns([0.9, 1, 1, 1])
    core_cols[0].markdown("<div class='row-label' style='color:#FFD700'>核心</div>", unsafe_allow_html=True)
    for i in range(1, 4):
        locked = i > core_unlocked
        sid = st.session_state.core.get(i)
        label = "🔒" if locked else (f"{STONES[sid].icon}BIOS" if sid else "＋")
        help_txt = None
        if sid:
            help_txt = STONES[sid].name
        if core_cols[i].button(label, key=f"core_{i}", disabled=locked, help=help_txt, use_container_width=True):
            st.session_state.selected_slot = ("core", i)
            if st.session_state.picked_stone:
                ok, msg = can_place(st.session_state.picked_stone, "core", None, None)
                if not ok:
                    st.toast(msg, icon="⚠️")
                else:
                    place_on_core(i, st.session_state.picked_stone)

    st.markdown("---")

    # Grid rows for elements
    st.markdown("**☯️ 五行槽（5 行）**")
    st.caption("列段：1-2武器｜3-4防具｜5-6饰品｜7-8经脉。每行第1格为逻辑位。")

    # region header row
    header_cols = st.columns([0.9] + [1] * 8)
    header_cols[0].markdown("")
    for c in range(1, 9):
        rid = region_of_col(c)
        header_cols[c].markdown(f"<div class='tiny' style='text-align:center'>{region_label(rid)}</div>", unsafe_allow_html=True)

    for r in ELEMENT_ORDER:
        row_cols = st.columns([0.9] + [1] * 8)
        meta = ELEMENT_META[r]
        row_cols[0].markdown(
            f"<div class='row-label' style='color:{meta['color']}'>{meta['icon']} {r}</div>",
            unsafe_allow_html=True,
        )
        for c in range(1, 9):
            locked = c > unlock_cols
            sid = st.session_state.board[r][c]
            is_logic = (c == 1)
            label = slot_label(sid, locked, is_logic, r, c)
            help_txt = None
            if sid:
                help_txt = STONES[sid].name

            if row_cols[c].button(label, key=f"slot_{r}_{c}", disabled=locked, help=help_txt, use_container_width=True):
                st.session_state.selected_slot = ("board", r, c)
                if st.session_state.picked_stone:
                    ok, msg = can_place(st.session_state.picked_stone, "board", r, c)
                    if not ok:
                        st.toast(msg, icon="⚠️")
                    else:
                        place_on_board(r, c, st.session_state.picked_stone)

    st.markdown("</div>", unsafe_allow_html=True)


# ========== Right: Compile / Resonance / Run ==========
with col_status:
    st.markdown("##### 🔮 衍算结果")

    # Choose view: normal vs crisis
    mode = st.radio("视图", ["常态", "危机态(H P<30%)"], horizontal=True)
    is_crisis = (mode != "常态")
    ctx = ctx_crisis if is_crisis else ctx_normal

    stats = ctx["stats"]

    with st.container(border=True):
        if ctx["status"] == "FAIL":
            st.error("❌ 带宽超限，无法运行")
        else:
            st.success("✅ 架构可运行")

        st.metric("带宽", f"{int(stats['bandwidth'])} / {int(stats['bw_safe'])}", delta=f"极限 {int(stats['bw_max'])}")
        st.metric("热量/魔念", f"{stats['heat']:.0f} / 100", delta=f"故障率 {stats['glitch_p']*100:.0f}%")

        # element distribution
        st.markdown("**五行分布**")
        total = max(1, sum(ctx["elem_counts"].values()))
        for e in ELEMENT_ORDER:
            n = ctx["elem_counts"].get(e, 0)
            st.progress(n / total, text=f"{e} {n}")

        st.markdown("---")
        st.markdown("**摘要**")
        for line in format_stat_line(stats):
            st.markdown(f"- {line}")

        # notes
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

    # Run / Retest
    col_run1, col_run2 = st.columns(2)
    if col_run1.button("▶ 运行（新Seed）", type="primary", use_container_width=True):
        new_seed = random.randint(0, 999999999)
        st.session_state.seed = new_seed
        st.session_state.sim_result = simulate(new_seed, is_crisis=is_crisis)

    if col_run2.button("🔁 复测（同Seed）", use_container_width=True):
        st.session_state.sim_result = simulate(int(st.session_state.seed), is_crisis=is_crisis)

    if st.session_state.sim_result:
        res = st.session_state.sim_result
        st.markdown("---")
        st.markdown("##### 🧪 复测输出")
        st.caption(f"Seed = {res['seed']}  |  模式 = {mode}")
        if res["burnt"]:
            st.warning(res["burnt"])
        else:
            st.success("本次未发生熔断")

    st.markdown("---")
    st.button("📄 生成验证报告（占位）", use_container_width=True)


# ----------------------
# Bottom detail panel (slot detail + remove)
# ----------------------
st.markdown("### 📝 槽位详情")
with st.container(border=True):
    sel = st.session_state.selected_slot
    if not sel:
        st.caption("点击中间面板任意槽位查看详情。")
    else:
        if sel[0] == "core":
            idx = sel[1]
            sid = st.session_state.core.get(idx)
            st.markdown(f"**核心槽 #{idx}**")
            if sid:
                stone = STONES[sid]
                st.markdown(f"- 当前：{stone.icon} {stone.name}")
                st.caption(stone.desc)
                if st.button("卸下核心", key="rm_core", use_container_width=True):
                    remove_slot("core", idx=idx)
            else:
                st.caption("（空）可装入核心BIOS")
        else:
            _, r, c = sel
            sid = st.session_state.board[r][c]
            st.markdown(f"**{r} 行 · 槽位 {c}**  <span class='tiny'>({region_label(region_of_col(c))})</span>", unsafe_allow_html=True)
            if sid:
                stone = STONES[sid]
                st.markdown(f"- 当前：{stone.icon} {stone.name}  <span class='pill'>{stone.kind}</span>", unsafe_allow_html=True)
                st.caption(stone.desc)
                if stone.kind == "gem":
                    rid = region_of_col(c)
                    eff = stone.effects.get(rid, {})
                    pretty = ", ".join([f"{k}+{v}" for k, v in eff.items()]) if eff else "（无）"
                    st.markdown(f"**该位置效果**：{pretty}")
                if st.button("卸下该灵石", key="rm_slot", use_container_width=True):
                    remove_slot("board", row=r, col=c)
            else:
                if c == 1:
                    st.caption("（逻辑位）可装入逻辑灵石")
                else:
                    st.caption("（空）")
