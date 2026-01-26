import streamlit as st
import yaml
import pandas as pd
import copy
import json
import hashlib
import os
import shutil
import datetime
import glob
import streamlit.components.v1 as components
from typing import List, Dict, Any, Optional
from engine import DiabloEngine, SkillNode
import generate_doc

st.set_page_config(page_title="RPG Build CMS", layout="wide", page_icon="⚔️")


def stable_hash(obj: Any) -> str:
    """对任意 JSON 兼容对象做稳定 hash（用于实验快照/确定性校验标识）。"""
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def stable_hash(obj: Any) -> str:
    """Stable hash for determinism snapshots (JSON with sorted keys)."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

# ==========================================
# 0. 通用组件: 可视化选择器 (带状态记忆)
# ==========================================
def render_visual_selector(data_source, obj_type, key_prefix, default_selection=None, multiselect_mode=False):
    """
    通用可视化选择器 (修复版：带状态记忆)
    :param default_selection: 初始默认选中的ID (仅在初始化时使用)
    """
    objects = data_source.get(obj_type, [])
    if not objects:
        st.warning(f"暂无 {obj_type} 数据")
        return [] if multiselect_mode else None

    # --- 0. 状态同步逻辑 ---
    state_key = f"{key_prefix}_selection_state"

    # 初始化状态
    if state_key not in st.session_state:
        st.session_state[state_key] = default_selection if default_selection is not None else ([] if multiselect_mode else None)

    current_selection = st.session_state[state_key]

    # --- 1. 顶部工具栏 ---
    c1, c2 = st.columns([1, 2])
    with c1:
        all_tags = sorted(list(set([t for o in objects for t in o.get('tags', [])])))
        if not all_tags and obj_type == 'modifiers':
            filter_tags = []
        else:
            filter_tags = st.multiselect("🏷️ 标签筛选", all_tags, key=f"{key_prefix}_tags")

    with c2:
        search_term = st.text_input("🔍 搜索", placeholder=f"搜索 {obj_type}...", key=f"{key_prefix}_search")

    # --- 2. 过滤逻辑 ---
    filtered_objs = []
    for o in objects:
        if filter_tags and not set(filter_tags).issubset(set(o.get('tags', []))): continue
        if search_term and search_term.lower() not in o['name'].lower(): continue
        filtered_objs.append(o)

    # --- 3. 布局 ---
    col_grid, col_detail = st.columns([1.5, 1])

    view_key = f"{key_prefix}_viewing_id"
    if view_key not in st.session_state: st.session_state[view_key] = None

    # === 左侧：图标网格 ===
    with col_grid:
        st.caption(f"共 {len(filtered_objs)} 个")
        cols = st.columns(3)
        for i, obj in enumerate(filtered_objs):
            # Emoji
            emoji = "📦"
            if obj_type == 'skills':
                tags = obj.get('tags', [])
                if "fire" in tags: emoji = "🔥"
                elif "cold" in tags: emoji = "❄️"
                elif "lightning" in tags: emoji = "⚡"
                elif "physical" in tags: emoji = "⚔️"
            else:
                emoji = "💍"

            # 选中状态判断
            is_selected = False
            if multiselect_mode:
                if isinstance(current_selection, list) and obj['id'] in current_selection:
                    is_selected = True
            else:
                if current_selection == obj['id']:
                    is_selected = True

            label = f"{emoji} {obj['name']}"
            btn_type = "primary" if is_selected else "secondary"

            # 点击逻辑
            if cols[i % 3].button(label, key=f"{key_prefix}_btn_{obj['id']}", type=btn_type, use_container_width=True):
                st.session_state[view_key] = obj['id']

                # 更新状态
                if multiselect_mode:
                    if not isinstance(st.session_state[state_key], list): st.session_state[state_key] = []
                    if obj['id'] in st.session_state[state_key]:
                        st.session_state[state_key].remove(obj['id'])
                    else:
                        st.session_state[state_key].append(obj['id'])
                else:
                    st.session_state[state_key] = obj['id']

                st.rerun()

    # === 右侧：详情面板 ===
    with col_detail:
        viewing_id = st.session_state[view_key]
        if not viewing_id:
            if not multiselect_mode and current_selection: viewing_id = current_selection
            elif multiselect_mode and current_selection: viewing_id = current_selection[-1]

        if viewing_id:
            obj = next((x for x in objects if x['id'] == viewing_id), None)
            if obj:
                with st.container(border=True):
                    st.subheader(obj['name'])
                    st.caption(f"ID: {obj['id']}")
                    if obj.get('desc'): st.info(obj['desc'])
                    st.divider()

                    if obj_type == 'skills':
                        for comp in obj.get('damage_components', []):
                            icon = "🗡️"
                            ctype = comp.get('type', 'phys')
                            if ctype=='fire': icon="🔥"
                            elif ctype=='cold': icon="❄️"
                            elif ctype=='lightning': icon="⚡"
                            st.markdown(f"**{icon} {ctype.upper()} 伤害**")
                            st.code(f"{comp.get('min')}-{comp.get('max')} (+{int(comp.get('scaling_coef',0)*100)}% {comp.get('scaling_source')})")
                    elif obj_type == 'modifiers':
                        st.markdown("**属性:**")
                        for k, v in obj.get('stats', {}).items():
                            st.write(f"- {k}: `{v}`")
        else:
            st.info("👈 点击图标查看详情")

    return st.session_state[state_key]


# ==========================================
# 1. 核心工具函数
# ==========================================
DATA_FILE = "data.yaml"
BACKUP_DIR = "backup"
MAX_BACKUPS = 50

def load_yaml():
    if not os.path.exists(DATA_FILE):
        return {"models": [], "talents": [], "skills": [], "modifiers": [], "rules": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def manage_backups():
    try:
        files = glob.glob(os.path.join(BACKUP_DIR, "data_*.yaml"))
        files.sort(key=os.path.getmtime)
        if len(files) > MAX_BACKUPS:
            for f in files[:len(files) - MAX_BACKUPS]:
                os.remove(f)
    except: pass

def save_yaml(data, manual_tag=None):
    try:
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(DATA_FILE):
            suffix = f"_{manual_tag}" if manual_tag else ""
            backup_name = f"data_{timestamp}{suffix}.yaml"
            shutil.copy(DATA_FILE, os.path.join(BACKUP_DIR, backup_name))
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        manage_backups()
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def restore_backup(filename):
    try:
        src = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(src):
            save_yaml(load_yaml(), manual_tag="BeforeRestore")
            shutil.copy(src, DATA_FILE)
            return True
        return False
    except Exception as e:
        st.error(f"恢复失败: {e}")
        return False

def get_index_by_id(data_list, target_id):
    for i, item in enumerate(data_list):
        if item['id'] == target_id: return i
    return -1

# 初始化
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = load_yaml()
data = st.session_state.data_cache

KNOWN_STATS = [
    "max_hp", "base_atk", "crit_rate", "crit_dmg", "atk_spd",
    "str", "agi", "int",
    "flat_physical", "flat_fire", "flat_cold", "flat_lightning",
    "inc_physical", "inc_fire", "inc_cold", "inc_lightning", "inc_elemental", "inc_spell", "inc_all",
    "more_damage", "more_fire", "more_physical",
    "penetration_fire", "penetration_physical"
]

# ==========================================
# 2. 页面导航
# ==========================================
st.sidebar.title("🎛️ RPG 工具箱")
page_mode = st.sidebar.radio(
    "功能导航",
    [
        "⚔️ 简单战斗模拟 (旧)",
        "⛓️ 技能链构建 (新)",
        "🧪 MVP 验证 Demo",
        "🎨 可视化编辑器",
        "📄 原始 YAML / 时光机",
        "📖 在线白皮书"
    ]
)

# ==================================================================
# PAGE 1: 简单战斗模拟 (旧)
# ==================================================================
if page_mode == "⚔️ 简单战斗模拟 (旧)":
    st.title("⚔️ 单技能数值验证")
    st.caption("快速查看单个技能在特定配装下的基础伤害。")

    models = {m['id']: m for m in data.get('models', [])}
    talents = {t['id']: t for t in data.get('talents', [])}
    skills = {s['id']: s for s in data.get('skills', [])}
    mods = {m['id']: m for m in data.get('modifiers', [])}

    if not models or not skills:
        st.warning("⚠️ 数据库为空，请先去【可视化编辑器】添加数据！")
        st.stop()

    with st.expander("👤 基础配置", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            mid = st.selectbox("素体", list(models.keys()), format_func=lambda x: models[x]['name'])
        with c2:
            tid = st.selectbox("天赋", list(talents.keys()), format_func=lambda x: talents[x]['name'])

    st.markdown("### 1. 选择技能")
    # 初始化
    if 'sim_selected_skill' not in st.session_state:
        st.session_state.sim_selected_skill = list(skills.keys())[0] if skills else None

    st.session_state.sim_selected_skill = render_visual_selector(
        data, 'skills', "sim_skill_sel",
        default_selection=st.session_state.sim_selected_skill
    )
    sid = st.session_state.sim_selected_skill

    st.markdown("### 2. 添加 Buff / 装备")
    if 'sim_selected_mods' not in st.session_state:
        st.session_state.sim_selected_mods = []

    st.session_state.sim_selected_mods = render_visual_selector(
        data, 'modifiers', "sim_mod_sel",
        default_selection=st.session_state.sim_selected_mods,
        multiselect_mode=True
    )
    selected_mod_ids = st.session_state.sim_selected_mods

    if selected_mod_ids:
        st.caption(f"已选: {', '.join([mods[m]['name'] for m in selected_mod_ids if m in mods])}")

    st.divider()
    if st.button("🚀 计算面板", type="primary", use_container_width=True):
        if not sid:
            st.error("请选择一个技能")
            st.stop()

        eng = DiabloEngine(data)
        eng.build_hero(models[mid], talents[tid])
        mod_objects = [mods[m_id] for m_id in selected_mod_ids if m_id in mods]

        res = eng.calculate_skill_damage(skills[sid], mod_objects)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("DPS", int(res['DPS']))
        k2.metric("单发伤害", int(res['Avg_Hit']))
        k3.metric("暴击率", f"{res['Crit_Info']['rate']*100:.1f}%")
        k4.metric("攻速", f"{res['Crit_Info']['aps']:.2f}")

        with st.expander("🔍 查看详细数据"):
            st.json(res)

# ==================================================================
# PAGE 2: 技能链构建 (新)
# ==================================================================
elif page_mode == "⛓️ 技能链构建 (新)":
    st.title("⛓️ 深度 BD 构建台")
    st.caption("组装 [主技能] + [触发器] + [子技能]，测试联动伤害。")

    if not data.get('models') or not data.get('skills'):
        st.error("数据库为空，请先去编辑器添加内容")
        st.stop()

    with st.expander("👤 角色底座配置", expanded=True):
        c1, c2 = st.columns(2)
        mid = c1.selectbox("素体", [m['id'] for m in data['models']], format_func=lambda x: next(d['name'] for d in data['models'] if d['id']==x))
        tid = c2.selectbox("天赋", [t['id'] for t in data['talents']], format_func=lambda x: next(d['name'] for d in data['talents'] if d['id']==x))
        model_obj = next(m for m in data['models'] if m['id'] == mid)
        talent_obj = next(t for t in data['talents'] if t['id'] == tid)

    if 'build_chain' not in st.session_state:
        st.session_state.build_chain = {"main_skill": None, "main_mods": [], "triggers": []}
    chain = st.session_state.build_chain

    st.subheader("1. 核心技能 (Main Skill)")

    curr_s_name = "未选择"
    if chain['main_skill']:
        found = next((s['name'] for s in data['skills'] if s['id'] == chain['main_skill']), None)
        if found: curr_s_name = found

    with st.expander(f"🔮 主技能: {curr_s_name}", expanded=True):
        chain['main_skill'] = render_visual_selector(
            data, 'skills', "chain_main_skill",
            default_selection=chain['main_skill']
        )
        st.markdown("---")
        st.caption("💍 挂载模组")
        chain['main_mods'] = render_visual_selector(
            data, 'modifiers', "chain_main_mods",
            default_selection=chain['main_mods'],
            multiselect_mode=True
        )

    st.subheader("2. 触发回路 (Triggers)")

    if chain['triggers']:
        for i, t in enumerate(chain['triggers']):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                c1.markdown(f"⚡ **触发 {i+1}**")
                c1.caption(f"条件: {t['condition']}")

                skill_name = next((s['name'] for s in data['skills'] if s['id'] == t['skill']), t['skill'])
                c2.markdown(f"👉 释放: **{skill_name}**")
                c2.caption(f"模组: {len(t['mods'])}")

                if c3.button("🗑️ 移除", key=f"del_trig_{i}"):
                    chain['triggers'].pop(i)
                    st.rerun()

    st.markdown("---")

    with st.expander("🛠️ 配置新触发器 (添加连接)", expanded=False):
        t_cond = st.selectbox("触发条件", ["on_crit", "on_hit", "fixed_chance_20"], key="new_trig_cond")

        st.markdown("**1️⃣ 选择子技能:**")
        if "temp_trig_skill_id" not in st.session_state: st.session_state["temp_trig_skill_id"] = None
        st.session_state["temp_trig_skill_id"] = render_visual_selector(
            data, 'skills', "new_trig_skill_sel",
            default_selection=st.session_state["temp_trig_skill_id"]
        )

        st.markdown("**2️⃣ 选择子技能模组:**")
        if "temp_trig_mod_ids" not in st.session_state: st.session_state["temp_trig_mod_ids"] = []
        st.session_state["temp_trig_mod_ids"] = render_visual_selector(
            data, 'modifiers', "new_trig_mod_sel",
            default_selection=st.session_state["temp_trig_mod_ids"],
            multiselect_mode=True
        )

        if st.button("确认添加连接", type="primary"):
            if not st.session_state["temp_trig_skill_id"]:
                st.error("请选择一个子技能！")
            else:
                chain['triggers'].append({
                    "condition": t_cond,
                    "skill": st.session_state["temp_trig_skill_id"],
                    "mods": st.session_state["temp_trig_mod_ids"]
                })
                st.session_state["temp_trig_skill_id"] = None
                st.session_state["temp_trig_mod_ids"] = []
                st.rerun()

    st.divider()
    if st.button("🚀 运行完整模拟", type="primary", use_container_width=True):
        try:
            def get_skill(id): return next(s for s in data['skills'] if s['id'] == id)
            def get_mod(id): return next(m for m in data['modifiers'] if m['id'] == id)

            if not chain['main_skill']:
                st.error("请先选择主技能！")
                st.stop()

            root = SkillNode(
                get_skill(chain['main_skill']),
                [get_mod(m) for m in chain['main_mods']]
            )
            for t in chain['triggers']:
                child = SkillNode(get_skill(t['skill']), [get_mod(m) for m in t['mods']])
                root.triggers.append({"condition": t['condition'], "node": child})

            eng = DiabloEngine(data)
            eng.build_hero(model_obj, talent_obj)
            total_dps, logs, _ = eng.simulate_chain_with_profile(root)

            st.success(f"🔥 总 DPS: {int(total_dps):,}")

            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                import altair as alt
                chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="dps", type="quantitative"),
                    color=alt.Color(field="skill", type="nominal"),
                    tooltip=["skill", "dps", "role", "info"]
                )
                st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.error(f"模拟失败: {e}")


# ==================================================================
# PAGE 2.5: MVP 验证 Demo
# ==================================================================
elif page_mode == "🧪 MVP 验证 Demo":
    st.title("🧪 MVP 验证 Demo")
    st.caption("把这里当作“实验台”：固定试炼 + 固定 Seed + 固定 Build → 反复复测、对比、定位问题（而不是拼操作）。")

    rules = data.get("rules", {}) or {}
    mvp = (rules.get("mvp", {}) or {})
    if not mvp:
        st.error("data.yaml 中缺少 rules.mvp 配置。")
        st.stop()

    # ---- 白名单过滤（MVP 只开放少量内容，方便验证）----
    allowed_models = set(mvp.get("allowed_models", []))
    allowed_talents = set(mvp.get("allowed_talents", []))
    allowed_skills = set(mvp.get("allowed_skills", []))
    allowed_mods = set(mvp.get("allowed_modifiers", []))
    allowed_conds = mvp.get("allowed_conditions", ["on_hit", "on_crit", "fixed_chance_20", "hp_lt_30"])
    max_triggers = int(mvp.get("max_triggers", 2))
    max_depth = int(mvp.get("max_depth", 1))

    models_list = [x for x in data.get("models", []) if (not allowed_models or x.get("id") in allowed_models)]
    talents_list = [x for x in data.get("talents", []) if (not allowed_talents or x.get("id") in allowed_talents)]
    skills_list = [x for x in data.get("skills", []) if (not allowed_skills or x.get("id") in allowed_skills)]
    mods_list = [x for x in data.get("modifiers", []) if (not allowed_mods or x.get("id") in allowed_mods)]

    if not models_list or not talents_list or not skills_list:
        st.error("MVP 白名单过滤后数据不足：请检查 rules.mvp.allowed_* 是否与实际数据 id 匹配。")
        st.stop()

    # 为 selector 构造简化 data_source
    mvp_data_source = {"skills": skills_list, "modifiers": mods_list}

    # ---- session state：build ----
    if "mvp_build" not in st.session_state:
        st.session_state.mvp_build = {
            "model": models_list[0]["id"],
            "talent": talents_list[0]["id"],
            "main_skill": skills_list[0]["id"],
            "main_mods": [],
            "triggers": [
                {"enabled": True, "condition": "on_crit", "skill": "mvp_crit_execute", "mods": []},
                {"enabled": True, "condition": "hp_lt_30", "skill": "mvp_emergency_mend", "mods": []},
            ]
        }
    build = st.session_state.mvp_build

    # ---- 三套预置 BD ----
    presets = {
        "⚡ 输出爆发": {
            "tags": ["爆发", "DPS"],
            "note": "核心：主技能堆伤 + 暴击触发斩杀。适合 DPS Check。",
            "main_skill": "mvp_basic_attack",
            "main_mods": ["mvp_mod_damage_20", "mvp_mod_haste"],
            "triggers": [
                {"enabled": True, "condition": "on_crit", "skill": "mvp_crit_execute", "mods": ["mvp_mod_damage_20"]},
                {"enabled": False, "condition": "hp_lt_30", "skill": "mvp_emergency_mend", "mods": []},
            ]
        },
        "🛡️ 铁王八": {
            "tags": ["生存", "减伤"],
            "note": "核心：提高承伤能力，低血触发应急治疗。适合 Survival / Spike。",
            "main_skill": "mvp_basic_attack",
            "main_mods": ["mvp_mod_tough"],
            "triggers": [
                {"enabled": False, "condition": "on_crit", "skill": "mvp_crit_execute", "mods": []},
                {"enabled": True, "condition": "hp_lt_30", "skill": "mvp_emergency_mend", "mods": []},
            ]
        },
        "🔁 闭环翻盘": {
            "tags": ["闭环", "续航"],
            "note": "核心：攻速/暴击提高触发频率，形成斩杀+保命闭环。适合综合验证。",
            "main_skill": "mvp_basic_attack",
            "main_mods": ["mvp_mod_haste", "mvp_mod_crit_10"],
            "triggers": [
                {"enabled": True, "condition": "on_crit", "skill": "mvp_crit_execute", "mods": ["mvp_mod_damage_20"]},
                {"enabled": True, "condition": "hp_lt_30", "skill": "mvp_emergency_mend", "mods": []},
            ]
        }
    }

    # ---- 工具：显示技能/模组详情 ----
    def show_skill_help(skill_id: str):
        sk = next((s for s in skills_list if s["id"] == skill_id), None)
        if not sk:
            return
        with st.container(border=True):
            st.markdown(f"**📘 {sk['name']}**")
            if sk.get("desc"):
                st.caption(sk["desc"])
            comps = sk.get("damage_components") or []
            if comps:
                comp = comps[0]
                st.write(f"伤害: `{comp.get('type','?')}` {comp.get('min',0)}-{comp.get('max',0)}  (coef={comp.get('scaling_coef',1.0)} src={comp.get('scaling_source','base_atk')})")
            eff = sk.get("effects") or {}
            if eff:
                st.write("effects:")
                st.json(eff, expanded=False)

    def show_mods_help(mod_ids: List[str]):
        picked = [m for m in mods_list if m["id"] in (mod_ids or [])]
        if not picked:
            st.info("未选择模组")
            return
        total = {}
        with st.container(border=True):
            st.markdown("**💍 已选模组效果**")
            for m in picked:
                st.write(f"- **{m['name']}**：{m.get('desc','')}")
                for k, v in (m.get("stats") or {}).items():
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if str(k).endswith("_mult"):
                        total[k] = (total.get(k, 1.0) * fv)
                    else:
                        total[k] = (total.get(k, 0.0) + fv)
            st.markdown("**汇总 stats**")
            st.json(total, expanded=False)

    # ==========================================================
    # 布局：左（Build） / 右（试炼 + 运行 + 报告）
    # ==========================================================
    left, right = st.columns([1.25, 1.0], gap="large")

    with left:
        st.subheader("🧩 Build 组装")
        st.caption("提示：先用预置 BD 快速得到可用起点，再微调一两处去验证差异。")

        with st.container(border=True):
            st.markdown("#### 0) 一键载入预置 BD")
            pcols = st.columns(3)
            for i, (pname, pcfg) in enumerate(presets.items()):
                if pcols[i % 3].button(pname, use_container_width=True, key=f"mvp_preset_{i}"):
                    main_skill_id = pcfg.get("main_skill")
                    main_mod_ids = [x for x in (pcfg.get("main_mods") or []) if (not allowed_mods or x in allowed_mods)]

                    st.session_state["mvp_main_skill_selection_state"] = main_skill_id
                    st.session_state["mvp_main_mods_selection_state"] = main_mod_ids

                    trig_list = pcfg.get("triggers") or []
                    for ti in range(max_triggers):
                        tcfg = trig_list[ti] if ti < len(trig_list) else {"enabled": False, "condition": "on_hit", "skill": skills_list[0]["id"], "mods": []}
                        st.session_state[f"mvp_t_en_{ti}"] = bool(tcfg.get("enabled", False))
                        cond = tcfg.get("condition", "on_hit")
                        st.session_state[f"mvp_t_cond_{ti}"] = cond if cond in allowed_conds else allowed_conds[0]
                        sk = tcfg.get("skill") or skills_list[0]["id"]
                        st.session_state[f"mvp_t_skill_{ti}"] = sk if sk in [s["id"] for s in skills_list] else skills_list[0]["id"]
                        st.session_state[f"mvp_t_mods_{ti}"] = [x for x in (tcfg.get("mods") or []) if (not allowed_mods or x in allowed_mods)]

                    build["main_skill"] = main_skill_id
                    build["main_mods"] = main_mod_ids
                    build["triggers"] = []
                    for ti in range(max_triggers):
                        build["triggers"].append({
                            "enabled": bool(st.session_state.get(f"mvp_t_en_{ti}", False)),
                            "condition": st.session_state.get(f"mvp_t_cond_{ti}", allowed_conds[0]),
                            "skill": st.session_state.get(f"mvp_t_skill_{ti}", skills_list[0]["id"]),
                            "mods": st.session_state.get(f"mvp_t_mods_{ti}", []),
                        })

                    st.session_state.mvp_build = build
                    st.rerun()

        with st.container(border=True):
            st.markdown("#### 1) 角色底座")
            c1, c2 = st.columns(2)
            build["model"] = c1.selectbox(
                "素体",
                [m["id"] for m in models_list],
                index=[m["id"] for m in models_list].index(build.get("model", models_list[0]["id"])) if build.get("model") in [m["id"] for m in models_list] else 0,
                format_func=lambda x: next(mm["name"] for mm in models_list if mm["id"] == x),
            )
            build["talent"] = c2.selectbox(
                "天赋",
                [t["id"] for t in talents_list],
                index=[t["id"] for t in talents_list].index(build.get("talent", talents_list[0]["id"])) if build.get("talent") in [t["id"] for t in talents_list] else 0,
                format_func=lambda x: next(tt["name"] for tt in talents_list if tt["id"] == x),
            )

            model_obj = next(m for m in models_list if m["id"] == build["model"])
            talent_obj = next(t for t in talents_list if t["id"] == build["talent"])

            # 一个小的概览
            bs = model_obj.get("base_stats") or {}
            attrs = model_obj.get("attributes") or {}
            st.caption("素体面板（只展示关键项）")
            kpi_cols = st.columns(4)
            kpi_cols[0].metric("HP", int(bs.get("max_hp", 0) or 0))
            kpi_cols[1].metric("ATK", int(bs.get("base_atk", 0) or 0))
            kpi_cols[2].metric("STR", int(attrs.get("str", 0) or 0))
            kpi_cols[3].metric("AGI", int(attrs.get("agi", 0) or 0))

        with st.container(border=True):
            st.markdown("#### 2) 主技能")
            build["main_skill"] = render_visual_selector(
                mvp_data_source, "skills", "mvp_main_skill", default_selection=build.get("main_skill")
            )
            with st.expander("📘 查看主技能详情", expanded=False):
                show_skill_help(build["main_skill"])

            st.markdown("#### 3) 主技能模组")
            build["main_mods"] = render_visual_selector(
                mvp_data_source,
                "modifiers",
                "mvp_main_mods",
                default_selection=build.get("main_mods", []),
                multiselect_mode=True
            )
            with st.expander("💍 查看主模组汇总", expanded=False):
                show_mods_help(build["main_mods"])

        with st.container(border=True):
            st.markdown(f"#### 4) 触发器（最多 {max_triggers} 个，深度锁死 {max_depth}）")
            st.caption("触发器是 MVP 的核心：你用它来做“闭环/保命/破盾/斩杀”。")

            while len(build["triggers"]) < max_triggers:
                build["triggers"].append({"enabled": False, "condition": "on_hit", "skill": skills_list[0]["id"], "mods": []})
            if len(build["triggers"]) > max_triggers:
                build["triggers"] = build["triggers"][:max_triggers]

            for i in range(max_triggers):
                t = build["triggers"][i]
                with st.container(border=True):
                    h1, h2, h3 = st.columns([1, 2, 2])
                    t["enabled"] = h1.checkbox(f"启用 T{i+1}", value=bool(t.get("enabled", False)), key=f"mvp_t_en_{i}")
                    t["condition"] = h2.selectbox(
                        "条件",
                        allowed_conds,
                        index=allowed_conds.index(t.get("condition", allowed_conds[0])) if t.get("condition") in allowed_conds else 0,
                        key=f"mvp_t_cond_{i}"
                    )
                    t["skill"] = h3.selectbox(
                        "子技能",
                        [s["id"] for s in skills_list],
                        index=[s["id"] for s in skills_list].index(t.get("skill", skills_list[0]["id"])) if t.get("skill") in [s["id"] for s in skills_list] else 0,
                        format_func=lambda x: next(ss["name"] for ss in skills_list if ss["id"] == x),
                        key=f"mvp_t_skill_{i}"
                    )

                    with st.expander(f"📘 子技能详情：{next(ss['name'] for ss in skills_list if ss['id']==t['skill'])}", expanded=False):
                        show_skill_help(t["skill"])

                    t["mods"] = st.multiselect(
                        "子技能模组",
                        [m["id"] for m in mods_list],
                        default=[x for x in (t.get("mods") or []) if (not allowed_mods or x in allowed_mods)],
                        format_func=lambda x: next(mm["name"] for mm in mods_list if mm["id"] == x),
                        key=f"mvp_t_mods_{i}"
                    )
                    with st.expander("💍 子技能模组汇总", expanded=False):
                        show_mods_help(t["mods"])



        # ---- BD 总览 / 快速微调（不重复渲染所有控件，避免 key 冲突）----
        with st.container(border=True):
            st.markdown("#### 5) BD 总览 / 快速微调")
            st.caption("用途：导入预设后，快速查看整条 BD，并针对某一个槽位/全局做替换，再 Run/Replay 对比。")

            def _skill_name(sid: str) -> str:
                s = next((x for x in skills_list if x.get('id') == sid), None)
                return (s.get('name') if s else sid)

            def _mods_names(mids):
                mids = mids or []
                name_map = {m.get('id'): m.get('name') for m in mods_list}
                return [name_map.get(x, x) for x in mids]

            def _sync_widgets_from_build(b: Dict[str, Any]):
                # 主技能
                st.session_state["mvp_main_skill_selection_state"] = b.get("main_skill")
                st.session_state["mvp_main_mods_selection_state"] = b.get("main_mods", [])
                # 触发器
                trs = b.get("triggers") or []
                while len(trs) < max_triggers:
                    trs.append({"enabled": False, "condition": allowed_conds[0], "skill": skills_list[0]["id"], "mods": []})
                for ti in range(max_triggers):
                    t = trs[ti]
                    st.session_state[f"mvp_t_en_{ti}"] = bool(t.get("enabled", False))
                    st.session_state[f"mvp_t_cond_{ti}"] = (t.get("condition") if t.get("condition") in allowed_conds else allowed_conds[0])
                    sk = t.get("skill") or skills_list[0]["id"]
                    st.session_state[f"mvp_t_skill_{ti}"] = sk if sk in [s["id"] for s in skills_list] else skills_list[0]["id"]
                    st.session_state[f"mvp_t_mods_{ti}"] = [x for x in (t.get("mods") or []) if (not allowed_mods or x in allowed_mods)]

            # —— 可视化总览 ——
            lines = []
            lines.append(f"**主技能**：`{_skill_name(build.get('main_skill'))}`  |  mods：{', '.join(_mods_names(build.get('main_mods'))) or '（无）'}")
            trs = build.get('triggers') or []
            for i in range(max_triggers):
                t = trs[i] if i < len(trs) else {"enabled": False, "condition": allowed_conds[0], "skill": skills_list[0]["id"], "mods": []}
                onoff = "✅" if t.get('enabled') else "⛔"
                lines.append(f"**触发器{i+1}**：{onoff} `{t.get('condition')}` → `{_skill_name(t.get('skill'))}`  |  mods：{', '.join(_mods_names(t.get('mods'))) or '（无）'}")
            st.markdown("\n\n".join(lines))

            st.markdown("---")
            st.markdown("**A) 快速编辑某个槽位**")
            slot = st.selectbox("编辑目标", ["主技能", "触发器1", "触发器2"], key="mvp_quick_slot")

            skill_ids = [s["id"] for s in skills_list]
            mod_ids = [m["id"] for m in mods_list]

            if slot == "主技能":
                q_skill = st.selectbox("技能", skill_ids, index=skill_ids.index(build.get('main_skill', skill_ids[0])) if build.get('main_skill') in skill_ids else 0,
                                       format_func=_skill_name, key="mvp_q_main_skill")
                q_mods = st.multiselect("模组", mod_ids, default=[x for x in (build.get('main_mods') or []) if (not allowed_mods or x in allowed_mods)],
                                        format_func=lambda x: next((m.get('name') for m in mods_list if m.get('id')==x), x), key="mvp_q_main_mods")

                if st.button("✅ 应用到主技能", use_container_width=True, key="mvp_q_apply_main"):
                    build["main_skill"] = q_skill
                    build["main_mods"] = list(q_mods)
                    _sync_widgets_from_build(build)
                    st.session_state.mvp_build = build
                    st.rerun()

            else:
                idx = 0 if slot == "触发器1" else 1
                while len(build.get('triggers') or []) < max_triggers:
                    build.setdefault('triggers', []).append({"enabled": False, "condition": allowed_conds[0], "skill": skill_ids[0], "mods": []})
                t = build['triggers'][idx]

                c1, c2 = st.columns(2)
                q_en = c1.checkbox("启用", value=bool(t.get('enabled', False)), key=f"mvp_q_t_en_{idx}")
                q_cond = c2.selectbox("条件", allowed_conds, index=allowed_conds.index(t.get('condition')) if t.get('condition') in allowed_conds else 0, key=f"mvp_q_t_cond_{idx}")
                q_skill = st.selectbox("子技能", skill_ids, index=skill_ids.index(t.get('skill')) if t.get('skill') in skill_ids else 0,
                                       format_func=_skill_name, key=f"mvp_q_t_skill_{idx}")
                q_mods = st.multiselect("子技能模组", mod_ids, default=[x for x in (t.get('mods') or []) if (not allowed_mods or x in allowed_mods)],
                                        format_func=lambda x: next((m.get('name') for m in mods_list if m.get('id')==x), x), key=f"mvp_q_t_mods_{idx}")

                if st.button("✅ 应用到该触发器", use_container_width=True, key=f"mvp_q_apply_t_{idx}"):
                    t["enabled"] = bool(q_en)
                    t["condition"] = q_cond
                    t["skill"] = q_skill
                    t["mods"] = list(q_mods)
                    build['triggers'][idx] = t
                    _sync_widgets_from_build(build)
                    st.session_state.mvp_build = build
                    st.rerun()

            st.markdown("---")
            st.markdown("**B) 全局技能替换（快速对比 Build）**")

            def _collect_used_skills(b: Dict[str, Any]):
                used = []
                ms = b.get('main_skill')
                if ms:
                    used.append(ms)
                for tt in (b.get('triggers') or []):
                    if tt.get('skill'):
                        used.append(tt.get('skill'))
                # 去重保序
                out = []
                seen = set()
                for x in used:
                    if x not in seen:
                        out.append(x)
                        seen.add(x)
                return out

            used = _collect_used_skills(build)
            r1, r2 = st.columns(2)
            old = r1.selectbox("把这个技能…", used if used else skill_ids, format_func=_skill_name, key="mvp_replace_old")
            new = r2.selectbox("替换成…", skill_ids, index=skill_ids.index(old) if old in skill_ids else 0, format_func=_skill_name, key="mvp_replace_new")
            scope = st.radio("替换范围", ["全局（主技能+触发器）", "仅主技能", "仅触发器"], horizontal=True, key="mvp_replace_scope")

            if st.button("🔁 执行替换", use_container_width=True, key="mvp_replace_apply"):
                if old == new:
                    st.warning("old 和 new 一样，没有变化。")
                else:
                    if scope != "仅触发器":
                        if build.get('main_skill') == old and scope in ("全局（主技能+触发器）", "仅主技能"):
                            build['main_skill'] = new
                    if scope != "仅主技能":
                        for tt in (build.get('triggers') or []):
                            if tt.get('skill') == old:
                                tt['skill'] = new
                    _sync_widgets_from_build(build)
                    st.session_state.mvp_build = build
                    st.rerun()

            with st.expander("导出 Build JSON", expanded=False):
                st.code(json.dumps(build, ensure_ascii=False, indent=2), language="json")
    # 右侧：试炼 + Run/Replay + 报告
    with right:
        st.subheader("🎯 试炼 / 运行 / 报告")

        # ---- 选择敌人预设（试炼用例库）----
        presets_enemy = mvp.get("enemy_presets", []) or []
        if not presets_enemy:
            presets_enemy = [{"id": "dummy", "name": "木桩", "enemy_hp": 3000, "enemy_dps": 20, "max_time": 20, "boss_crit_interval": 4.0, "boss_crit_mult": 2.5}]

        with st.container(border=True):
            st.markdown("#### 1) 选择试炼（用例库）")
            eid = st.selectbox(
                "试炼",
                [e["id"] for e in presets_enemy],
                format_func=lambda x: next(e["name"] for e in presets_enemy if e["id"] == x),
                key="mvp_trial_select"
            )
            enemy = next(e for e in presets_enemy if e["id"] == eid)

            c1, c2, c3 = st.columns(3)
            c1.metric("敌人HP", int(enemy.get("enemy_hp", 3000)))
            c2.metric("持续DPS", int(enemy.get("enemy_dps", 20)))
            c3.metric("时限(s)", float(enemy.get("max_time", 20)))

            st.caption(f"机制：每 **{enemy.get('boss_crit_interval', 4.0)}s** 一次重击，倍率 **x{enemy.get('boss_crit_mult', 2.5)}**")

        def get_skill(sid: str):
            return next(s for s in skills_list if s["id"] == sid)

        def get_mod(mid: str):
            return next(m for m in mods_list if m["id"] == mid)

        def build_node(skill_id: str, mod_ids: List[str]) -> SkillNode:
            return SkillNode(get_skill(skill_id), [get_mod(m) for m in (mod_ids or []) if (not allowed_mods or m in allowed_mods)])

        # ---- 实验控制台：Seed / dt / Run / Replay ----
        with st.container(border=True):
            st.markdown("#### 2) 实验控制台（确定性 / Seed 复测）")

            top = st.columns([1, 1, 1.2])
            with top[0]:
                seed = st.number_input("Seed", min_value=0, value=int(st.session_state.get("mvp_seed", 12345)), step=1, key="mvp_seed")
            with top[1]:
                dt = st.number_input("dt (秒)", min_value=0.01, max_value=1.0, value=float(st.session_state.get("mvp_dt", 0.10)), step=0.01, format="%.2f", key="mvp_dt")
            with top[2]:
                preview = {
                    "model": model_obj.get("id"),
                    "talent": talent_obj.get("id"),
                    "trial": enemy.get("id"),
                    "build": build,
                    "max_depth": max_depth,
                    "seed": int(seed),
                    "dt": float(dt),
                }
                st.caption(f"snapshot_hash: `{stable_hash(preview)}`")

            btns = st.columns([1, 1, 1])
            def make_snapshot() -> Dict[str, Any]:
                return {
                    "model_id": model_obj.get("id"),
                    "talent_id": talent_obj.get("id"),
                    "enemy": copy.deepcopy(enemy),
                    "build": copy.deepcopy(build),
                    "max_depth": int(max_depth),
                    "seed": int(seed),
                    "dt": float(dt),
                }

            def run_build(snapshot: Dict[str, Any]) -> Dict[str, Any]:
                model_id = snapshot["model_id"]
                talent_id = snapshot.get("talent_id")

                model_obj2 = next(m for m in data.get("models", []) if m.get("id") == model_id)
                talent_obj2 = next((t for t in data.get("talents", []) if t.get("id") == talent_id), None) if talent_id else None

                build2 = snapshot["build"]
                enemy2 = snapshot["enemy"]
                seed2 = int(snapshot.get("seed", 0))
                dt2 = float(snapshot.get("dt", 0.1))
                max_depth2 = int(snapshot.get("max_depth", 1))

                root = build_node(build2["main_skill"], build2["main_mods"])
                for t in build2["triggers"]:
                    if not t.get("enabled"):
                        continue
                    child = build_node(t["skill"], t.get("mods") or [])
                    child.triggers = []
                    root.triggers.append({"condition": t["condition"], "node": child})

                eng = DiabloEngine(data)
                eng.build_hero(model_obj2, talent_obj2)

                result = eng.simulate_mvp_fight(
                    root,
                    enemy_hp=float(enemy2.get("enemy_hp", 3000)),
                    init_enemy_hp=float(enemy2.get("enemy_hp", 3000)),
                    enemy_dps=float(enemy2.get("enemy_dps", 20)),
                    max_time=float(enemy2.get("max_time", 20)),
                    dt=dt2,
                    seed=seed2,
                    boss_crit_interval=float(enemy2.get("boss_crit_interval", 4.0)),
                    boss_crit_mult=float(enemy2.get("boss_crit_mult", 2.5)),
                    max_depth=max_depth2,
                )

                header = {
                    "trial_id": enemy2.get("id"),
                    "seed": seed2,
                    "dt": dt2,
                    "max_depth": max_depth2,
                    "build_hash": stable_hash(snapshot),
                    "engine_version": getattr(eng, "version", lambda: "unknown")(),
                }
                return {"header": header, "result": result}

            if btns[0].button("🚀 Run", type="primary", use_container_width=True):
                snap = make_snapshot()
                out = run_build(snap)
                st.session_state.mvp_last_snapshot = snap
                st.session_state.mvp_last_out = out
                st.session_state.mvp_last_primary_hash = out["result"].get("result_hash")
                # 清理旧 replay，避免误判
                st.session_state.pop("mvp_last_replay_out", None)
                st.session_state.pop("mvp_last_replay_hash", None)
                st.rerun()

            replay_disabled = "mvp_last_snapshot" not in st.session_state
            if btns[1].button("🔁 Replay", use_container_width=True, disabled=replay_disabled):
                snap = st.session_state.mvp_last_snapshot
                out = run_build(snap)
                st.session_state.mvp_last_replay_out = out
                st.session_state.mvp_last_replay_hash = out["result"].get("result_hash")
                st.rerun()

            if btns[2].button("🧹 清空结果", use_container_width=True):
                for k in ["mvp_last_snapshot", "mvp_last_out", "mvp_last_primary_hash", "mvp_last_replay_out", "mvp_last_replay_hash"]:
                    st.session_state.pop(k, None)
                st.rerun()

            # 确定性提示
            if "mvp_last_out" in st.session_state:
                h_run = st.session_state.get("mvp_last_primary_hash")
                h_rep = st.session_state.get("mvp_last_replay_hash")
                if h_rep is None:
                    st.info(f"Run result_hash: `{h_run}`（点 Replay 做确定性校验）")
                else:
                    if h_run == h_rep:
                        st.success(f"✅ 确定性通过：Run={h_run} Replay={h_rep}")
                    else:
                        st.error(f"❌ 非确定性：Run={h_run} Replay={h_rep}")

            with st.expander("🧾 Run Header / Result Hash", expanded=False):
                if "mvp_last_out" in st.session_state:
                    out = st.session_state.mvp_last_out
                    st.json({"header": out["header"], "result_hash": out["result"].get("result_hash")})
                else:
                    st.caption("先 Run 一次。")

        # ---- 报告区（Tabs）----
        st.markdown("#### 3) 战斗报告")
        if "mvp_last_out" not in st.session_state:
            st.info("先点击 Run 开始一次试炼。")
        else:
            out = st.session_state.mvp_last_out
            res = out["result"]
            tabs = st.tabs(["总览", "走势", "战斗日志", "技能DPS"])
            # ===== 总览 =====
            with tabs[0]:
                r = res.get("result")
                reason = res.get("reason")
                t_cost = res.get("time")
                seed_r = res.get("seed")
                dt_r = res.get("dt")

                m1, m2, m3 = st.columns(3)
                if r == "WIN":
                    m1.metric("结果", "WIN 🏆")
                elif r == "TIMEOUT":
                    m1.metric("结果", "TIMEOUT ⏳")
                else:
                    m1.metric("结果", "LOSE ☠️")
                m2.metric("耗时(s)", float(t_cost))
                m3.metric("原因", str(reason))

                st.caption(f"seed={seed_r}  dt={dt_r}  boss_crit_interval={res.get('boss_crit_interval')}  boss_crit_mult={res.get('boss_crit_mult')}")

                # 关键指标：剩余HP
                tl = res.get("timeline") or []
                if tl:
                    hero_end = tl[-1].get("hero_hp")
                    enemy_end = tl[-1].get("enemy_hp")
                    c = st.columns(2)
                    c[0].metric("英雄剩余HP", hero_end)
                    c[1].metric("敌人剩余HP", enemy_end)

            # ===== 走势 =====
            with tabs[1]:
                tl = res.get("timeline") or []
                if not tl:
                    st.info("无 timeline 数据。")
                else:
                    import altair as alt
                    df = pd.DataFrame(tl)
                    df_m = df.melt(id_vars=["time", "is_crit"], value_vars=["hero_hp", "enemy_hp"], var_name="who", value_name="hp")
                    df_m["who"] = df_m["who"].map({"hero_hp": "Hero", "enemy_hp": "Enemy"})
                    base = alt.Chart(df_m).mark_line().encode(
                        x=alt.X("time:Q", title="时间(s)"),
                        y=alt.Y("hp:Q", title="HP"),
                        color=alt.Color("who:N", title="对象"),
                        tooltip=["time:Q", "who:N", "hp:Q"]
                    ).properties(height=260)

                    crit_df = df[df["is_crit"] == True]
                    if len(crit_df) > 0:
                        rules = alt.Chart(crit_df).mark_rule(strokeDash=[4,4]).encode(
                            x="time:Q",
                            tooltip=[alt.Tooltip("time:Q", title="重击时间(s)")]
                        )
                        chart = base + rules
                    else:
                        chart = base

                    st.altair_chart(chart, use_container_width=True)

                    if len(crit_df) > 0:
                        st.caption("虚线为 BOSS 重击时刻（spike）。")

            # ===== 日志 =====
            with tabs[2]:
                logs = res.get("combat_log") or []
                if not logs:
                    st.info("无关键战斗事件。")
                else:
                    st.text_area("Combat Log", value="\n".join(logs), height=260)

            # ===== 技能DPS =====
            with tabs[3]:
                dps_logs = res.get("logs") or []
                if not dps_logs:
                    st.info("无技能构成数据。")
                else:
                    df = pd.DataFrame(dps_logs)
                    # 尝试更友好一点
                    show_cols = [c for c in ["skill", "role", "dps", "aps", "info"] if c in df.columns]
                    st.dataframe(df[show_cols], use_container_width=True, height=260, hide_index=True)

        # ---- 把 build 保存回 session ----
        st.session_state.mvp_build = build
# ==================================================================

# ==================================================================
# PAGE 3: 可视化编辑器
# ==================================================================
elif page_mode == "🎨 可视化编辑器":
    st.title("🎨 游戏内容编辑器")
    tab1, tab2, tab3, tab4 = st.tabs(["🗡️ 技能", "💍 物品/Buff", "👤 角色", "🌟 天赋"])

    with tab1:
        mode = st.radio("模式", ["🆕 新增", "✏️ 编辑"], horizontal=True, key="sk_mode")
        curr_data = {}
        idx = -1
        if mode == "✏️ 编辑":
            if not data['skills']: st.warning("无数据"); st.stop()
            sid = st.selectbox("选择技能", [s['id'] for s in data['skills']], format_func=lambda x: next(s['name'] for s in data['skills'] if s['id']==x))
            idx = get_index_by_id(data['skills'], sid)
            curr_data = data['skills'][idx]

        with st.form("sk_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("名称", value=curr_data.get("name", ""))
            sid_val = c2.text_input("ID", value=curr_data.get("id", ""), disabled=(mode=="✏️ 编辑"))
            desc = st.text_area("描述", value=curr_data.get("desc", ""))
            my_tags = curr_data.get("tags", [])
            all_tags = list(set(["attack", "spell", "projectile", "melee", "aoe", "physical", "fire"] + my_tags))
            tags = st.multiselect("标签", all_tags, default=my_tags)

            st.markdown("**伤害组件**")
            comps = curr_data.get("damage_components", [{}])
            comp0 = comps[0] if comps else {}
            dtypes = ["physical", "fire", "cold", "lightning", "chaos"]
            ctype = comp0.get("type", "physical")
            if ctype not in dtypes: dtypes.append(ctype)
            dtype = st.selectbox("类型", dtypes, index=dtypes.index(ctype))
            dc1, dc2 = st.columns(2)
            dmin = dc1.number_input("最小伤", value=float(comp0.get("min", 10)))
            dmax = dc2.number_input("最大伤", value=float(comp0.get("max", 20)))
            dsrc = st.selectbox("加成源", ["base_atk", "str", "int", "agi"], index=0)
            dcoef = st.number_input("系数", value=float(comp0.get("scaling_coef", 1.0)))

            if st.form_submit_button("💾 保存"):
                new_obj = {
                    "id": sid_val, "name": name, "desc": desc, "tags": tags,
                    "damage_components": [{"type": dtype, "min": dmin, "max": dmax, "scaling_source": dsrc, "scaling_coef": dcoef}]
                }
                if mode == "🆕 新增":
                    if get_index_by_id(data['skills'], sid_val) != -1: st.error("ID已存在")
                    else: data['skills'].append(new_obj); save_yaml(data); st.success("已添加")
                else:
                    data['skills'][idx] = new_obj; save_yaml(data); st.success("已更新")

    with tab2:
        mmode = st.radio("模式", ["🆕 新增", "✏️ 编辑"], horizontal=True, key="it_mode")
        curr_mod = {}
        midx = -1
        if mmode == "✏️ 编辑":
            if not data['modifiers']: st.warning("无数据"); st.stop()
            mid_sel = st.selectbox("选择物品", [m['id'] for m in data['modifiers']], format_func=lambda x: next(m['name'] for m in data['modifiers'] if m['id']==x))
            midx = get_index_by_id(data['modifiers'], mid_sel)
            curr_mod = data['modifiers'][midx]
            if 'curr_edit_mod_id' not in st.session_state or st.session_state.curr_edit_mod_id != mid_sel:
                st.session_state.temp_stats = curr_mod.get("stats", {}).copy()
                st.session_state.curr_edit_mod_id = mid_sel
                st.rerun()
        else:
            if 'curr_edit_mod_id' in st.session_state and st.session_state.curr_edit_mod_id is not None:
                st.session_state.temp_stats = {}
                st.session_state.curr_edit_mod_id = None
                st.rerun()
            if 'temp_stats' not in st.session_state: st.session_state.temp_stats = {}

        c1, c2 = st.columns(2)
        mname = c1.text_input("物品名称", value=curr_mod.get("name", ""))
        mid_val = c2.text_input("物品ID", value=curr_mod.get("id", ""), disabled=(mmode=="✏️ 编辑"))

        st.markdown("##### 🛒 属性列表")
        ac1, ac2, ac3 = st.columns([2, 1, 1])
        ak = ac1.selectbox("属性", KNOWN_STATS)
        av = ac2.number_input("数值", value=0.0)
        if ac3.button("➕ 添加"):
            st.session_state.temp_stats[ak] = av
            st.rerun()

        if st.session_state.temp_stats:
            st.write("已配置属性 (点击删除):")
            cols = st.columns(4)
            del_k = None
            for i, (k, v) in enumerate(st.session_state.temp_stats.items()):
                if cols[i%4].button(f"🗑️ {k}: {v}", key=f"del_{k}"): del_k = k
            if del_k:
                del st.session_state.temp_stats[del_k]
                st.rerun()

        if st.button("💾 保存物品", type="primary"):
            if not mname or not mid_val: st.error("信息不全")
            else:
                new_mod = {"id": mid_val, "name": mname, "stats": st.session_state.temp_stats.copy()}
                if mmode == "🆕 新增":
                    if get_index_by_id(data['modifiers'], mid_val) != -1: st.error("ID重复")
                    else: data['modifiers'].append(new_mod); save_yaml(data); st.success("保存成功")
                else:
                    data['modifiers'][midx] = new_mod; save_yaml(data); st.success("更新成功")

    with tab3: st.info("角色编辑请直接使用 YAML 管理页")
    with tab4: st.info("天赋编辑请直接使用 YAML 管理页")

# ==================================================================
# PAGE 4: YAML & 时光机
# ==================================================================
elif page_mode == "📄 原始 YAML / 时光机":
    st.title("📄 高级数据管理")
    yt1, yt2 = st.tabs(["📝 源码编辑", "🕰️ 时光机 (备份)"])

    with yt1:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            txt = st.text_area("编辑器", f.read(), height=600)
        if st.button("💾 覆盖保存"):
            try:
                obj = yaml.safe_load(txt)
                if save_yaml(obj):
                    st.session_state.data_cache = obj
                    st.success("保存成功")
                    st.rerun()
            except Exception as e: st.error(f"格式错误: {e}")

    with yt2:
        st.caption("最近 50 次保存记录")
        with st.expander("📸 创建手动快照"):
            tag = st.text_input("标签名")
            if st.button("创建快照"):
                save_yaml(data, manual_tag=tag if tag else "Manual")
                st.success("已创建")
                st.rerun()

        files = glob.glob(os.path.join(BACKUP_DIR, "data_*.yaml"))
        files.sort(key=os.path.getmtime, reverse=True)
        if not files: st.info("无备份")
        else:
            for f in files:
                fname = os.path.basename(f)
                ftime = datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M:%S")
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.code(fname)
                c2.write(ftime)
                if c3.button("♻️ 还原", key=f"res_{fname}"):
                    if restore_backup(fname):
                        st.session_state.data_cache = load_yaml()
                        st.success(f"已还原至 {fname}")
                        st.rerun()

# ==================================================================
# PAGE 5: 在线白皮书
# ==================================================================
elif page_mode == "📖 在线白皮书":
    st.title("📖 实时设计文档")
    try:
        html = generate_doc.get_html_content()
        components.html(html, height=1000, scrolling=True)
    except Exception as e:
        st.error(f"文档生成错误: {e}")