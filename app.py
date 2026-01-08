import streamlit as st
import yaml
import pandas as pd
import os
import shutil
import datetime
import streamlit.components.v1 as components
from engine import DiabloEngine
# 引入文档生成模块 (请确保 generate_doc.py 在同级目录)
import generate_doc

st.set_page_config(page_title="RPG Build CMS", layout="wide", page_icon="⚔️")

# ==========================================
# 1. 核心工具函数：数据读写与备份增强
# ==========================================
import glob # 新增这个库用于查找文件

DATA_FILE = "data.yaml"
BACKUP_DIR = "backup"
MAX_BACKUPS = 50  # 最多保留50个历史版本

def load_yaml():
    if not os.path.exists(DATA_FILE):
        return {"models": [], "talents": [], "skills": [], "modifiers": [], "rules": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def manage_backups():
    """清理旧备份，只保留最新的 MAX_BACKUPS 个"""
    try:
        # 获取所有备份文件
        files = glob.glob(os.path.join(BACKUP_DIR, "data_*.yaml"))
        # 按修改时间排序（最旧的在前面）
        files.sort(key=os.path.getmtime)

        # 如果数量超过限制，删除最旧的
        if len(files) > MAX_BACKUPS:
            files_to_delete = files[:len(files) - MAX_BACKUPS]
            for f in files_to_delete:
                os.remove(f)
            # print(f"已清理 {len(files_to_delete)} 个旧备份")
    except Exception as e:
        print(f"备份清理失败: {e}")

def save_yaml(data, manual_tag=None):
    """
    保存并备份
    :param manual_tag: 如果有值，则备份文件名会带上这个标签
    """
    try:
        # 1. 确保目录存在
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)

        # 2. 执行备份
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(DATA_FILE):
            if manual_tag:
                # 手动快照: data_20260108_140000_PatchV1.yaml
                backup_name = f"data_{timestamp}_{manual_tag}.yaml"
            else:
                # 自动备份: data_20260108_140000.yaml
                backup_name = f"data_{timestamp}.yaml"

            shutil.copy(DATA_FILE, os.path.join(BACKUP_DIR, backup_name))

        # 3. 写入新数据
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

        # 4. 触发清理（仅针对自动备份清理，建议手动快照不清理，这里为了简单统一清理）
        manage_backups()

        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False

def restore_backup(filename):
    """从备份文件恢复"""
    try:
        src = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(src):
            # 恢复前，给当前的再做一个“撤销用”的备份
            save_yaml(load_yaml(), manual_tag="BeforeRestore")

            # 覆盖主文件
            shutil.copy(src, DATA_FILE)
            return True
        return False
    except Exception as e:
        st.error(f"恢复失败: {e}")
        return False

# 初始化数据
if 'data_cache' not in st.session_state:
    st.session_state.data_cache = load_yaml()
data = st.session_state.data_cache

# ==========================================
# 2. 辅助 UI 函数
# ==========================================
KNOWN_STATS = [
    "max_hp", "base_atk", "crit_rate", "crit_dmg", "atk_spd",
    "str", "agi", "int",
    "flat_physical", "flat_fire", "flat_cold", "flat_lightning",
    "inc_physical", "inc_fire", "inc_cold", "inc_lightning", "inc_elemental", "inc_spell", "inc_all",
    "more_damage", "more_fire", "more_physical",
    "penetration_fire", "penetration_physical",
    "trigger" # 预留给触发器配置
]

def render_stat_adder(key_prefix):
    """渲染一个属性添加器，返回 (key, value) 或 None"""
    c1, c2 = st.columns([2, 1])
    with c1:
        # 允许选择预设，也允许手动输入新词条
        stat_key = st.selectbox("选择属性", [""] + KNOWN_STATS, key=f"{key_prefix}_key")
        # 如果是高级用户，允许手动输入
        manual_key = st.text_input("或手动输入属性Key", key=f"{key_prefix}_manual", placeholder="例如: life_leech")
    with c2:
        stat_val = st.number_input("数值", value=0.0, step=0.1, format="%.2f", key=f"{key_prefix}_val")

    final_key = manual_key if manual_key else stat_key
    return final_key, stat_val

def get_index_by_id(data_list, target_id):
    """辅助函数：通过ID查找列表索引"""
    for i, item in enumerate(data_list):
        if item['id'] == target_id: return i
    return -1

# ==========================================
# 3. 页面布局结构
# ==========================================
st.sidebar.title("🎛️ RPG 工具箱")
page_mode = st.sidebar.radio("选择模式", ["⚔️ 战斗模拟器", "🎨 可视化编辑器", "📄 原始 YAML 管理", "📖 在线白皮书"])

# ------------------------------------------------------------------
# PAGE 1: 战斗模拟器
# ------------------------------------------------------------------
if page_mode == "⚔️ 战斗模拟器":
    st.title("🛡️ 战斗数值验证台")

    models = {m['id']: m for m in data.get('models', [])}
    talents = {t['id']: t for t in data.get('talents', [])}
    skills = {s['id']: s for s in data.get('skills', [])}
    mods = {m['id']: m for m in data.get('modifiers', [])}

    if not models or not skills:
        st.warning("⚠️ 数据库为空，请先去【可视化编辑器】添加数据！")
        st.stop()

    # 1. 基础配置
    c1, c2 = st.columns(2)
    with c1:
        mid = st.selectbox("素体", list(models.keys()), format_func=lambda x: models[x]['name'])
    with c2:
        tid = st.selectbox("天赋", list(talents.keys()), format_func=lambda x: talents[x]['name'])

    # 2. 技能选择
    sid = st.selectbox("主技能", list(skills.keys()), format_func=lambda x: skills[x]['name'])
    s_data = skills[sid]
    with st.container():
        st.markdown(f"""
        <div style="background:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:10px; border-left:4px solid #ff4b4b">
            <strong>{s_data['name']}</strong>: {s_data.get('desc', '无描述')} <br>
            <small>标签: {', '.join(s_data.get('tags', []))}</small>
        </div>
        """, unsafe_allow_html=True)

    # 3. 装备Buff
    selected_mod_ids = st.multiselect("添加装备/Buff", list(mods.keys()), format_func=lambda x: mods[x]['name'])

    hp_pct = st.slider("当前血量 %", 0.0, 1.0, 1.0)

    # 4. 计算
    if st.button("🚀 开始计算"):
        eng = DiabloEngine(data)
        eng.set_simulation_state(hp_percent=hp_pct)
        eng.build_hero(models[mid], talents[tid])
        for m_id in selected_mod_ids:
            eng.apply_modifier(mods[m_id])

        res = eng.calculate_skill_damage(skills[sid])

        # 结果展示
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("DPS", int(res['DPS']))
        k2.metric("单发伤害", int(res['Avg_Hit']))
        k3.metric("暴击率", f"{res['Crit_Info']['rate']*100:.1f}%")
        k4.metric("攻速", f"{res['Crit_Info']['aps']:.2f}/s")

        # 触发器展示
        if res.get('Trigger_Info'):
            st.divider()
            st.markdown("### ⛓️ 触发链详情")
            for t in res['Trigger_Info']:
                st.info(f"⚡ **{t['source']}** 触发了 **{t['skill']}** (DPS贡献: {int(t['total'])})")

        with st.expander("查看详细计算过程"):
            st.write(res)

# ------------------------------------------------------------------
# PAGE 2: 可视化编辑器 (支持新增 + 编辑)
# ------------------------------------------------------------------
elif page_mode == "🎨 可视化编辑器":
    st.title("🎨 游戏内容编辑器")
    st.caption("支持新增内容，或修改现有内容。修改后立即生效。")

    editor_tab1, editor_tab2, editor_tab3, editor_tab4 = st.tabs(["🗡️ 技能管理", "💍 物品/Buff管理", "👤 角色素体", "🌟 天赋系统"])

    # === TAB 1: 技能管理 (新增 + 编辑) ===
    # === TAB 1: 技能管理 (修复版：自动兼容未知标签) ===
    with editor_tab1:
        skill_mode = st.radio("操作模式", ["🆕 新增技能", "✏️ 编辑现有技能"], horizontal=True, key="skill_mode_radio")

        current_skill_data = {}
        target_index = -1

        if skill_mode == "✏️ 编辑现有技能":
            if not data['skills']:
                st.warning("暂无技能可编辑")
            else:
                skill_ids = [s['id'] for s in data['skills']]
                # 这里的 format_func 增加容错，防止有的技能没名字报错
                selected_s_id = st.selectbox("选择要修改的技能", skill_ids, format_func=lambda x: f"{x} ({next((s.get('name', '未命名') for s in data['skills'] if s['id']==x), 'Unknown')})")
                target_index = get_index_by_id(data['skills'], selected_s_id)
                current_skill_data = data['skills'][target_index]

        st.markdown("---")

        with st.form("skill_editor_form"):
            c1, c2 = st.columns(2)
            s_name = c1.text_input("技能名称", value=current_skill_data.get("name", ""))
            s_id_val = current_skill_data.get("id", "")
            s_id = c2.text_input("技能ID (英文)", value=s_id_val, disabled=(skill_mode=="✏️ 编辑现有技能"))
            s_desc = st.text_area("描述", value=current_skill_data.get("desc", ""))

            # 【修复重点 1】标签处理
            # 获取当前技能的标签
            default_tags = current_skill_data.get("tags", [])
            # 定义基础选项
            base_options = ["attack", "spell", "projectile", "melee", "aoe", "physical", "fire", "lightning", "cold"]
            # 关键步骤：把 default_tags 里有的，但 base_options 里没有的，加进去！
            # 这样就能保证 default 一定在 options 里
            all_tag_options = list(set(base_options + default_tags))

            s_tags = st.multiselect("标签", all_tag_options, default=default_tags)

            st.markdown("**核心伤害组件 (Primary Component)**")
            old_comps = current_skill_data.get("damage_components", [{}])
            comp0 = old_comps[0] if old_comps else {}

            # 【修复重点 2】伤害类型处理 (同样的逻辑，防止报错)
            base_types = ["physical", "fire", "cold", "lightning", "chaos"]
            curr_type = comp0.get("type", "physical")
            if curr_type not in base_types:
                base_types.append(curr_type)

            d_type = st.selectbox("伤害类型", base_types, index=base_types.index(curr_type))

            dc1, dc2 = st.columns(2)
            d_min = dc1.number_input("最小基伤", value=float(comp0.get("min", 10)))
            d_max = dc2.number_input("最大基伤", value=float(comp0.get("max", 20)))

            scale_opts = ["base_atk", "str", "int", "agi"]
            curr_scale = comp0.get("scaling_source", "base_atk")
            # 防止 scaling_source 是其他奇怪的值导致 index 报错
            idx_scale = scale_opts.index(curr_scale) if curr_scale in scale_opts else 0

            d_scale_src = st.selectbox("加成属性来源", scale_opts, index=idx_scale)
            d_scale_coef = st.number_input("加成系数", value=float(comp0.get("scaling_coef", 1.0)))

            submitted = st.form_submit_button("💾 保存提交")

            if submitted:
                if not s_name or not s_id:
                    st.error("名称和ID必填")
                else:
                    new_obj = {
                        "id": s_id,
                        "name": s_name,
                        "desc": s_desc,
                        "tags": s_tags,
                        "damage_components": [{
                            "type": d_type,
                            "min": d_min,
                            "max": d_max,
                            "scaling_source": d_scale_src,
                            "scaling_coef": d_scale_coef
                        }]
                    }
                    if skill_mode == "🆕 新增技能":
                        if get_index_by_id(data['skills'], s_id) != -1:
                            st.error(f"ID {s_id} 已存在！")
                        else:
                            data['skills'].append(new_obj)
                            save_yaml(data)
                            st.success(f"技能 {s_name} 新增成功！")
                    else:
                        data['skills'][target_index] = new_obj
                        save_yaml(data)
                        st.success(f"技能 {s_name} 更新成功！")

    # === TAB 2: 物品/Buff 管理 (新增 + 编辑) ===
    with editor_tab2:
        mod_mode = st.radio("操作模式", ["🆕 新增物品", "✏️ 编辑现有物品"], horizontal=True, key="mod_mode_radio")

        current_mod_data = {}
        target_mod_index = -1

        if mod_mode == "✏️ 编辑现有物品":
            if not data['modifiers']:
                st.warning("暂无物品可编辑")
            else:
                mod_ids = [m['id'] for m in data['modifiers']]
                selected_m_id = st.selectbox("选择要修改的物品", mod_ids, format_func=lambda x: f"{x} ({next(m['name'] for m in data['modifiers'] if m['id']==x)})")
                target_mod_index = get_index_by_id(data['modifiers'], selected_m_id)
                current_mod_data = data['modifiers'][target_mod_index]

                # 加载旧数据到 Session
                if 'current_editing_mod' not in st.session_state or st.session_state.current_editing_mod != selected_m_id:
                    st.session_state.temp_stats = current_mod_data.get("stats", {}).copy()
                    st.session_state.current_editing_mod = selected_m_id
                    st.rerun()
        else:
            if 'current_editing_mod' in st.session_state and st.session_state.current_editing_mod is not None:
                st.session_state.temp_stats = {}
                st.session_state.current_editing_mod = None
                st.rerun()
            if 'temp_stats' not in st.session_state:
                st.session_state.temp_stats = {}

        st.markdown("---")
        c1, c2 = st.columns(2)
        m_name_input = c1.text_input("物品名称", value=current_mod_data.get("name", ""))
        m_id_input = c2.text_input("物品ID", value=current_mod_data.get("id", ""), disabled=(mod_mode=="✏️ 编辑现有物品"))

        st.markdown("##### ⚙️ 属性配置")
        col_input1, col_input2, col_btn = st.columns([2, 1, 1])
        with col_input1:
            add_k = st.selectbox("属性Key", KNOWN_STATS, key="mod_k_editor")
        with col_input2:
            add_v = st.number_input("数值", value=0.0, key="mod_v_editor")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("➕ 添加/修改属性"):
                if add_k:
                    st.session_state.temp_stats[add_k] = add_v
                    st.rerun()

        if st.session_state.temp_stats:
            st.write("当前属性列表 (点击删除):")
            cols = st.columns(4)
            keys_to_del = []
            for i, (k, v) in enumerate(st.session_state.temp_stats.items()):
                with cols[i % 4]:
                    if st.button(f"🗑️ {k}: {v}", key=f"del_{k}"):
                        keys_to_del.append(k)
            if keys_to_del:
                for k in keys_to_del: del st.session_state.temp_stats[k]
                st.rerun()
        else:
            st.info("暂无属性")

        st.markdown("---")
        if st.button("💾 保存物品/Buff", type="primary"):
            if m_name_input and m_id_input:
                new_mod_obj = {
                    "id": m_id_input,
                    "name": m_name_input,
                    "stats": st.session_state.temp_stats.copy()
                }
                # 触发器等复杂字段这里暂时保留旧的以免丢失，或者如果你想支持触发器编辑，需增加更多表单
                if mod_mode == "✏️ 编辑现有物品":
                    if 'trigger' in current_mod_data:
                        new_mod_obj['trigger'] = current_mod_data['trigger']

                if mod_mode == "🆕 新增物品":
                    if get_index_by_id(data['modifiers'], m_id_input) != -1:
                        st.error("ID 已存在")
                    else:
                        data['modifiers'].append(new_mod_obj)
                        save_yaml(data)
                        st.success("新增成功！")
                else:
                    data['modifiers'][target_mod_index] = new_mod_obj
                    save_yaml(data)
                    st.success("更新成功！")
            else:
                st.error("名称和ID不能为空")

    with editor_tab3:
        st.info("角色编辑功能逻辑与技能/物品类似，请在YAML页面直接修改更快捷。")
    with editor_tab4:
        st.info("天赋包含复杂Python表达式，请在YAML页面修改。")

# ------------------------------------------------------------------
# PAGE 3: 原始 YAML 管理 & 备份回滚
# ------------------------------------------------------------------
elif page_mode == "📄 原始 YAML 管理":
    st.title("📄 高级管理")

    tab_edit, tab_backup = st.tabs(["📝 源码编辑", "🕰️ 时光机 (备份与回滚)"])

    # === TAB 1: 源码编辑 (保持原样) ===
    with tab_edit:
        st.warning("此模式适合批量修改。修改前建议先在隔壁标签页创建一个手动快照。")

        # 文档下载
        c_doc, c_null = st.columns([1, 4])
        with c_doc:
            doc_html = generate_doc.get_html_content()
            st.download_button("📥 下载白皮书", doc_html, "design_spec.html", "text/html")

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            current_content = f.read()

        new_content = st.text_area("YAML 编辑器", value=current_content, height=600)

        if st.button("💾 覆盖保存"):
            try:
                # 校验并转为对象
                new_data_obj = yaml.safe_load(new_content)
                # 调用新的 save_yaml，自动处理备份
                if save_yaml(new_data_obj):
                    st.session_state.data_cache = new_data_obj
                    st.success("✅ 保存成功！已自动创建备份。")
                    st.rerun()
            except yaml.YAMLError as e:
                st.error(f"YAML 格式错误: {e}")

    # === TAB 2: 时光机 (新增功能) ===
    with tab_backup:
        st.header("🕰️ 历史版本管理")
        st.caption("这里保留了最近 50 次修改记录。你可以随时回滚到任意状态。")

        # 1. 手动创建快照
        with st.expander("📸 创建手动快照", expanded=False):
            c1, c2 = st.columns([3, 1])
            tag_name = c1.text_input("快照标签 (可选)", placeholder="例如: 平衡性调整前")
            if c2.button("创建快照"):
                if save_yaml(data, manual_tag=tag_name if tag_name else "Manual"):
                    st.success("快照创建成功！")
                    st.rerun()

        # 2. 读取备份列表
        if not os.path.exists(BACKUP_DIR):
            st.info("暂无备份记录")
        else:
            files = glob.glob(os.path.join(BACKUP_DIR, "data_*.yaml"))
            # 按时间倒序排列（最新的在上面）
            files.sort(key=os.path.getmtime, reverse=True)

            if not files:
                st.info("暂无备份文件")
            else:
                # 3. 显示列表
                st.write(f"共找到 {len(files)} 个历史版本：")

                # 表头
                h1, h2, h3, h4 = st.columns([3, 2, 2, 2])
                h1.markdown("**文件名/标签**")
                h2.markdown("**备份时间**")
                h3.markdown("**文件大小**")
                h4.markdown("**操作**")

                for f_path in files:
                    f_name = os.path.basename(f_path)
                    # 获取文件信息
                    stats = os.stat(f_path)
                    f_time = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    f_size = f"{stats.st_size / 1024:.1f} KB"

                    # 提取标签显示
                    display_name = f_name
                    if "Manual" in f_name or "Patch" in f_name or "Before" in f_name:
                        display_name = f"🚩 {f_name}" # 给手动备份加个旗帜

                    # 渲染行
                    r1, r2, r3, r4 = st.columns([3, 2, 2, 2])
                    r1.code(display_name)
                    r2.write(f_time)
                    r3.write(f_size)

                    # 每一个备份文件都有一个独立的回滚按钮
                    if r4.button("♻️ 还原此版", key=f"restore_{f_name}"):
                        if restore_backup(f_name):
                            # 还原后，重载内存缓存
                            st.session_state.data_cache = load_yaml()
                            st.toast(f"已回滚至 {f_name}", icon="✅")
                            st.rerun()

# ------------------------------------------------------------------
# PAGE 4: 在线白皮书 (新增)
# ------------------------------------------------------------------
elif page_mode == "📖 在线白皮书":
    st.title("📖 实时设计白皮书")
    st.caption("本文档由当前 data.yaml 配置自动生成，实时同步最新数值。")

    # 1. 生成最新的 HTML 内容
    try:
        html_content = generate_doc.get_html_content()

        # 2. 使用 Components 组件将其渲染在 iframe 中
        # height 可以设置得很高，scrolling=True 允许内部滚动
        components.html(html_content, height=1000, scrolling=True)

    except Exception as e:
        st.error(f"文档生成失败: {e}")
        st.info("请检查 generate_doc.py 是否存在且逻辑正确。")