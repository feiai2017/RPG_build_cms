from typing import List
import streamlit as st
import yaml
import pandas as pd
import os
import shutil
import datetime
import glob
import copy
import streamlit.components.v1 as components
from engine import DiabloEngine, SkillNode # 必须确保 engine.py 里有 SkillNode 类
import generate_doc

st.set_page_config(page_title="RPG Build CMS", layout="wide", page_icon="⚔️")

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
            total_dps, logs = eng.simulate_chain(root)

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
# PAGE 3: 可视化编辑器
# ==================================================================

# ==================================================================
# PAGE 2.5: MVP 验证 Demo（最小可验证：会赢/会输/会超时）
# ==================================================================
elif page_mode == "🧪 MVP 验证 Demo":
    st.title("🧪 MVP 验证 Demo")
    st.caption("目标：用最小内容验证“技能 + 触发 + 自动战斗（有生存）”是否成立。")

    mvp_rules = (data.get("rules", {}).get("mvp") or {})
    if not mvp_rules:
        st.warning("⚠️ data.yaml 未配置 rules.mvp。请更新 data.yaml 后再来。")
        st.stop()

    allowed_models = set(mvp_rules.get("allowed_models", []))
    allowed_talents = set(mvp_rules.get("allowed_talents", []))
    allowed_skills = set(mvp_rules.get("allowed_skills", []))
    allowed_mods = set(mvp_rules.get("allowed_modifiers", []))
    allowed_conditions = mvp_rules.get("allowed_conditions", ["on_hit", "on_crit", "fixed_chance_20", "hp_lt_30"])

    max_triggers = int(mvp_rules.get("max_triggers", 2))
    max_depth = int(mvp_rules.get("max_depth", 1))
    enemy_presets = mvp_rules.get("enemy_presets", [])

    # --- filtered dictionaries ---
    models = {m["id"]: m for m in data.get("models", []) if m.get("id") in allowed_models}
    talents = {t["id"]: t for t in data.get("talents", []) if t.get("id") in allowed_talents}
    skills = {s["id"]: s for s in data.get("skills", []) if s.get("id") in allowed_skills}
    mods = {m["id"]: m for m in data.get("modifiers", []) if m.get("id") in allowed_mods}

    if not models or not skills:
        st.warning("⚠️ MVP 白名单过滤后数据为空。请检查 data.yaml rules.mvp 的 allowed_* 配置。")
        st.stop()

    # --- session defaults ---
    if "mvp_model" not in st.session_state:
        st.session_state.mvp_model = list(models.keys())[0]
    if "mvp_talent" not in st.session_state:
        st.session_state.mvp_talent = list(talents.keys())[0] if talents else None
    if "mvp_main_skill" not in st.session_state:
        st.session_state.mvp_main_skill = list(skills.keys())[0]
    if "mvp_main_mods" not in st.session_state:
        st.session_state.mvp_main_mods = []

    st.subheader("① 角色 & 敌人")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state.mvp_model = st.selectbox("素体（MVP）", list(models.keys()), format_func=lambda x: models[x]["name"])
    with c2:
        if talents:
            st.session_state.mvp_talent = st.selectbox("天赋（MVP）", list(talents.keys()), format_func=lambda x: talents[x]["name"])
        else:
            st.session_state.mvp_talent = None
            st.info("本 MVP 未启用天赋白名单。")
    with c3:
        preset_ids = [p.get("id") for p in enemy_presets] if enemy_presets else []
        preset_map = {p.get("id"): p for p in enemy_presets} if enemy_presets else {}
        if preset_ids:
            preset_id = st.selectbox("敌人预设", preset_ids, format_func=lambda x: preset_map[x].get("name", x))
            preset = preset_map[preset_id]
        else:
            preset = {"enemy_hp": 3000, "enemy_dps": 30, "max_time": 20}

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        enemy_hp = st.number_input("敌人 HP", min_value=100.0, max_value=999999.0, value=float(preset.get("enemy_hp", 3000.0)), step=100.0)
    with ec2:
        enemy_dps = st.number_input("敌人 DPS（恒定）", min_value=1.0, max_value=99999.0, value=float(preset.get("enemy_dps", 30.0)), step=1.0)
    with ec3:
        max_time = st.number_input("最大战斗时间（秒）", min_value=5.0, max_value=300.0, value=float(preset.get("max_time", 20.0)), step=1.0)

    st.divider()

    st.subheader("② Build（主技能 + 触发链）")
    st.session_state.mvp_main_skill = st.selectbox("主技能", list(skills.keys()), format_func=lambda x: skills[x]["name"])

    # 主技能模组
    st.session_state.mvp_main_mods = st.multiselect(
        "主技能模组（MVP 白名单）",
        list(mods.keys()),
        default=[m for m in st.session_state.mvp_main_mods if m in mods],
        format_func=lambda x: mods[x]["name"]
    )

    st.markdown("#### 触发器（MVP：最多 {} 个，深度锁死为 {}）".format(max_triggers, max_depth))
    triggers_cfg = []
    for i in range(max_triggers):
        with st.container(border=True):
            tc1, tc2, tc3 = st.columns([1, 1, 2])
            with tc1:
                cond = st.selectbox(f"条件 #{i+1}", allowed_conditions, key=f"mvp_trig_cond_{i}")
            with tc2:
                child_skill = st.selectbox(f"子技能 #{i+1}", list(skills.keys()), format_func=lambda x: skills[x]["name"], key=f"mvp_trig_skill_{i}")
            with tc3:
                child_mods = st.multiselect(
                    f"子技能模组 #{i+1}",
                    list(mods.keys()),
                    default=[],
                    format_func=lambda x: mods[x]["name"],
                    key=f"mvp_trig_mods_{i}"
                )

            enabled = st.checkbox("启用该触发器", value=(i == 0), key=f"mvp_trig_enabled_{i}")
            if enabled:
                triggers_cfg.append({
                    "condition": cond,
                    "skill_id": child_skill,
                    "mod_ids": child_mods,
                })

    # 组装 SkillNode
    def build_node(skill_id: str, mod_ids: List[str]) -> SkillNode:
        return SkillNode(skills[skill_id], modifiers=[mods[mid] for mid in mod_ids if mid in mods], triggers=[])

    root = SkillNode(
        skills[st.session_state.mvp_main_skill],
        modifiers=[mods[mid] for mid in st.session_state.mvp_main_mods if mid in mods],
        triggers=[]
    )
    for tcfg in triggers_cfg:
        child = build_node(tcfg["skill_id"], tcfg["mod_ids"])
        root.triggers.append({"condition": tcfg["condition"], "node": child})

    st.divider()

    # ---- 运行 & A/B 对比 ----
    st.subheader("③ 运行 & 对比")
    run_col1, run_col2, run_col3 = st.columns([1, 1, 2])
    with run_col1:
        run_now = st.button("▶️ 运行 MVP 战斗", type="primary", use_container_width=True)
    with run_col2:
        save_a = st.button("💾 保存为 A", use_container_width=True)
        save_b = st.button("💾 保存为 B", use_container_width=True)
    with run_col3:
        compare = st.button("🆚 A/B 对比运行", use_container_width=True)

    # Serialize current build
    def serialize_current_build():
        return {
            "model_id": st.session_state.mvp_model,
            "talent_id": st.session_state.mvp_talent,
            "main_skill_id": st.session_state.mvp_main_skill,
            "main_mods": list(st.session_state.mvp_main_mods),
            "triggers": triggers_cfg,
            "enemy": {"enemy_hp": float(enemy_hp), "enemy_dps": float(enemy_dps), "max_time": float(max_time)},
        }

    def run_build(build_cfg: dict):
        eng = DiabloEngine(data)
        eng.build_hero(models[build_cfg["model_id"]], talents.get(build_cfg["talent_id"]) if build_cfg["talent_id"] else None)

        main_skill = build_cfg["main_skill_id"]
        main_mod_ids = build_cfg.get("main_mods", [])

        r = SkillNode(skills[main_skill], modifiers=[mods[mid] for mid in main_mod_ids if mid in mods], triggers=[])

        for tcfg in build_cfg.get("triggers", [])[:max_triggers]:
            if tcfg.get("skill_id") not in skills:
                continue
            child = SkillNode(
                skills[tcfg["skill_id"]],
                modifiers=[mods[mid] for mid in (tcfg.get("mod_ids") or []) if mid in mods],
                triggers=[]
            )
            r.triggers.append({"condition": tcfg.get("condition", "on_hit"), "node": child})

        e = build_cfg.get("enemy", {})
        return eng.simulate_mvp_fight(
            r,
            enemy_hp=float(e.get("enemy_hp", 3000.0)),
            enemy_dps=float(e.get("enemy_dps", 30.0)),
            max_time=float(e.get("max_time", 20.0)),
            dt=0.1,
            max_depth=max_depth,
        )

    if save_a:
        st.session_state.mvp_build_a = serialize_current_build()
        st.success("已保存为方案 A")
    if save_b:
        st.session_state.mvp_build_b = serialize_current_build()
        st.success("已保存为方案 B")

    def render_result(res: dict, title: str = "结果"):
        r = res.get("result")
        if r == "WIN":
            st.success(f"✅ {title}: WIN（{res.get('time')}s）")
        elif r == "LOSE":
            st.error(f"❌ {title}: LOSE（{res.get('time')}s）")
        else:
            st.warning(f"⏱️ {title}: TIMEOUT（{res.get('time')}s）")

        summ = res.get("summary") or {}
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("英雄最大HP", summ.get("hero_max_hp", "-"))
        s2.metric("英雄剩余HP", summ.get("hero_hp_left", "-"))
        s3.metric("敌人剩余HP", summ.get("enemy_hp_left", "-"))
        s4.metric("平均DPS", summ.get("avg_dps", "-"))

        s5, s6 = st.columns(2)
        s5.metric("总治疗量", summ.get("total_heal", "-"))
        s6.metric("总承伤量", summ.get("total_incoming", "-"))

        tl = res.get("timeline") or []
        if tl:
            df = pd.DataFrame(tl)
            st.markdown("**时间轴（截取最后 120 条）**")
            st.dataframe(df.tail(120), use_container_width=True)

    if run_now:
        build_cfg = serialize_current_build()
        res = run_build(build_cfg)
        render_result(res, "当前方案")

    if compare:
        a = st.session_state.get("mvp_build_a")
        b = st.session_state.get("mvp_build_b")
        if not a or not b:
            st.warning("请先分别保存方案 A / B。")
        else:
            ra = run_build(a)
            rb = run_build(b)

            st.markdown("### 🆚 A/B 结果对比")
            ca, cb = st.columns(2)
            with ca:
                render_result(ra, "方案 A")
            with cb:
                render_result(rb, "方案 B")

            def summarize(res):
                s = res.get("summary") or {}
                return {
                    "result": res.get("result"),
                    "time": res.get("time"),
                    "enemy_hp_left": s.get("enemy_hp_left"),
                    "hero_hp_left": s.get("hero_hp_left"),
                    "avg_dps": s.get("avg_dps"),
                    "total_heal": s.get("total_heal"),
                    "total_incoming": s.get("total_incoming"),
                }

            df = pd.DataFrame([summarize(ra), summarize(rb)], index=["A", "B"])
            st.dataframe(df, use_container_width=True)

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