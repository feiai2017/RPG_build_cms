import streamlit as st
import yaml
import pandas as pd
from engine import DiabloEngine
# 【新增】引入文档生成模块
import generate_doc

st.set_page_config(page_title="RPG Build 验证台", layout="wide")

# ==========================================
# 工具函数
# ==========================================
def get_tag_from_stat_key(key):
    if key in ['str', 'agi', 'int', 'all_attributes']: return "Attributes"
    if key in ['inc_physical', 'more_physical', 'inc_melee', 'dr_physical']: return "Physical"
    if key in ['inc_fire', 'more_fire', 'dr_fire']: return "Fire"
    if key in ['inc_cold', 'more_cold']: return "Cold"
    if key in ['inc_lightning', 'more_lightning']: return "Lightning"
    if key in ['inc_chaos', 'inc_dark', 'inc_poison', 'more_poison']: return "Chaos/Dark"
    if key in ['inc_elemental', 'more_elemental']: return "Elemental(General)"
    if key in ['atk_spd', 'cast_spd']: return "Speed"
    if key in ['crit_rate', 'crit_dmg']: return "Crit"
    if key in ['inc_spell', 'more_spell']: return "Spell"
    if key in ['inc_projectile']: return "Projectile"
    if key in ['more_damage', 'inc_damage', 'inc_all']: return "Global Dmg"
    if key in ['max_hp', 'armor', 'evasion']: return "Defense"
    if key.startswith('flat_'): return "Flat Dmg(点伤)" # 新增点伤标签
    return None

def analyze_mod_effects(mod_data):
    tags = set()
    if 'stats' in mod_data:
        for k in mod_data['stats'].keys():
            tag = get_tag_from_stat_key(k)
            if tag: tags.add(tag)
    if 'dynamic_stats' in mod_data:
        tags.add("Mechanic(动态)")
        for k in mod_data['dynamic_stats'].keys():
            tag = get_tag_from_stat_key(k)
            if tag: tags.add(tag)
    if 'conversions' in mod_data:
        tags.add("Conversion")
        for conv in mod_data['conversions']:
            to_type = conv.get('to')
            if to_type == 'fire': tags.add("Fire")
            elif to_type == 'cold': tags.add("Cold")
            elif to_type == 'lightning': tags.add("Lightning")
    return list(tags)

def render_tags_html(tags):
    html = ""
    for tag in sorted(tags):
        c_map = {
            "Fire": ("#ffebee", "#c62828"),
            "Cold": ("#e3f2fd", "#1565c0"),
            "Lightning": ("#fffde7", "#f9a825"),
            "Physical": ("#eceff1", "#455a64"),
            "Chaos/Dark": ("#f3e5f5", "#6a1b9a"),
            "Crit": ("#e0f2f1", "#00695c"),
            "Speed": ("#e8f5e9", "#2e7d32"),
            "Attributes": ("#f5f5f5", "#616161"),
            "Global Dmg": ("#fff3e0", "#e65100"),
            "Conversion": ("#f3e5f5", "#8e24aa"),
            "Mechanic(动态)": ("#e0f7fa", "#006064"),
            "Flat Dmg(点伤)": ("#f3e5f5", "#4a148c")
        }
        bg, fg = c_map.get(tag, ("#eee", "#333"))
        html += f"<span style='background:{bg}; color:{fg}; padding:2px 8px; border-radius:10px; font-size:0.75rem; margin-right:4px; border:1px solid {fg}20'>{tag}</span>"
    return html

def format_option(option_key, data_map, type_label=""):
    item = data_map.get(option_key)
    if not item: return option_key
    name = item.get('name', option_key)

    if type_label == "skill":
        tags = item.get('tags', [])
        icon = "⚔️" if "attack" in tags else "🔮" if "spell" in tags else "⚪"
        dmg_info = []
        for c in item.get('damage_components', []):
            base = (c['min'] + c['max']) / 2
            extras = []
            if 'weapon_scale' in c: extras.append(f"{c['weapon_scale']*100:.0f}%武")
            if 'scaling_source' in c: extras.append(f"{c.get('scaling_coef',1)*100:.0f}%{c['scaling_source'][:3].upper()}")
            t_icon = {"fire":"🔥","cold":"❄️","lightning":"⚡","physical":"👊","chaos":"🟣","poison":"🧪","dark":"🌑"}.get(c['type'], "")
            val_str = f"{int(base)}"
            if extras: val_str += f"(+{'+'.join(extras)})"
            dmg_info.append(f"{t_icon}{val_str}")
        return f"{icon} {name} [{' | '.join(dmg_info)}]"

    if type_label == "mod":
        details = []
        if 'stats' in item:
            for k, v in item['stats'].items():
                val_fmt = f"{v}"
                k_fmt = k
                if any(x in k for x in ['inc', 'more', 'rate', 'dmg', 'spd']): val_fmt = f"{v*100:.0f}%"
                if k == 'str': k_fmt = "力"
                elif k == 'agi': k_fmt = "敏"
                elif k == 'int': k_fmt = "智"
                elif k == 'atk_spd': k_fmt = "攻速"
                elif k == 'crit_rate': k_fmt = "暴率"
                elif k == 'crit_dmg': k_fmt = "暴伤"
                elif k == 'max_hp': k_fmt = "HP"
                elif k.startswith('inc_'): k_fmt = k.replace('inc_', '').capitalize()
                elif k.startswith('more_'): k_fmt = f"MORE {k.replace('more_', '').capitalize()}"
                elif k.startswith('flat_'): k_fmt = f"点伤 {k.replace('flat_', '')}"
                sign = "+" if (isinstance(v, (int, float)) and v > 0) else ""
                details.append(f"{sign}{val_fmt} {k_fmt}")
        if 'conversions' in item:
            for c in item['conversions']:
                src = c['from'][:4].title()
                dst = c['to'][:4].title()
                details.append(f"♻️{c['ratio']*100:.0f}% {src}→{dst}")
        if 'dynamic_stats' in item:
            targets = [k.replace('inc_', '') for k in item['dynamic_stats'].keys()]
            details.append(f"⚙️动态:{','.join(targets)}")

        info_str = " | ".join(details)
        if len(info_str) > 50: info_str = info_str[:48] + "..."
        return f"{name} [{info_str}]" if details else name

    return name

# ==========================================
# 数据加载
# ==========================================
import os, sys
@st.cache_data
def load_data():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(__file__)
    yaml_path = os.path.join(base_dir, "data.yaml")

    if not os.path.exists(yaml_path):
        st.error(f"缺失文件: {yaml_path}")
        st.stop()
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

try:
    data = load_data()
except Exception as e:
    st.error(f"读取 YAML 失败: {e}")
    st.stop()

models = {m['id']: m for m in data['models']}
talents = {t['id']: t for t in data['talents']}
skills = {s['id']: s for s in data['skills']}
mods = {m['id']: m for m in data['modifiers']}

# ==========================================
# 界面布局
# ==========================================
st.sidebar.title("🎛️ 战斗环境")
hp_slider = st.sidebar.slider("当前血量 %", 0.0, 1.0, 1.0, 0.01)

# 【新增】文档下载按钮
st.sidebar.divider()
st.sidebar.subheader("📄 技术文档")
doc_html = generate_doc.get_html_content()
st.sidebar.download_button(
    label="📥 下载设计白皮书 (HTML)",
    data=doc_html,
    file_name="numerical_design_spec.html",
    mime="text/html",
    help="下载后用浏览器打开，按 Ctrl+P 可另存为 PDF"
)

st.title("🛡️ 严谨数值验证台")

# 1. 基础
c1, c2 = st.columns(2)
with c1:
    selected_model_id = st.selectbox("1. 素体", list(models.keys()), format_func=lambda x: models[x]['name'])
with c2:
    selected_talent_id = st.selectbox("2. 天赋", list(talents.keys()), format_func=lambda x: talents[x]['name'])
    st.caption(f"天赋效果: {talents[selected_talent_id]['desc']}")

st.divider()

# 2. 技能
selected_skill_id = st.selectbox("3. 主技能", list(skills.keys()), format_func=lambda x: format_option(x, skills, "skill"))
s_data = skills[selected_skill_id]
with st.container():
    st.markdown(f"""
    <div style="background:#fafafa; padding:15px; border-radius:8px; border-left:4px solid #ff5252">
        <h4 style="margin:0">{s_data['name']}</h4>
        <p style="margin:5px 0; color:#666">{s_data.get('desc', '无描述')}</p>
        <div style="margin-top:8px">
            {' '.join([f"<span style='background:#ddd; padding:2px 6px; border-radius:4px; font-size:0.8em'>{t}</span>" for t in s_data.get('tags', [])])}
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# 3. 筛选
st.subheader("4. 局内强化 (Modifiers)")
ALL_TAGS = ["Flat Dmg(点伤)", "Physical", "Fire", "Cold", "Lightning", "Chaos/Dark", "Elemental(General)", "Crit", "Speed", "Spell", "Projectile", "Global Dmg", "Attributes", "Defense", "Conversion", "Mechanic(动态)"]

col_filter, col_select = st.columns([1, 2])
with col_filter:
    st.markdown("##### 🕵️‍♀️ 按效果筛选")
    selected_tags = st.multiselect("勾选属性:", ALL_TAGS)
    filtered_ids = []
    if not selected_tags:
        filtered_ids = list(mods.keys())
    else:
        for mid, m_data in mods.items():
            item_effects = set(analyze_mod_effects(m_data))
            if not item_effects.isdisjoint(set(selected_tags)):
                filtered_ids.append(mid)
    st.info(f"匹配到 {len(filtered_ids)} 个组件")

with col_select:
    st.markdown("##### 📦 选择组件")
    if not filtered_ids:
        st.warning("无匹配")
        selected_mod_ids = []
    else:
        selected_mod_ids = st.multiselect("点击添加:", filtered_ids, format_func=lambda x: format_option(x, mods, "mod"))

if selected_mod_ids:
    st.write("已生效组件:")
    for mid in selected_mod_ids:
        tags = analyze_mod_effects(mods[mid])
        st.markdown(f"• **{mods[mid]['name']}**: {render_tags_html(tags)}", unsafe_allow_html=True)

# 计算
engine = DiabloEngine(data)
engine.set_simulation_state(hp_percent=hp_slider)
engine.build_hero(models[selected_model_id], talents[selected_talent_id])
for mid in selected_mod_ids:
    engine.apply_modifier(mods[mid])
result = engine.calculate_skill_damage(s_data)

st.divider()
st.title("📊 计算结果")

k1, k2, k3, k4 = st.columns(4)
k1.metric("DPS", int(result['DPS']))
k2.metric("单发", int(result['Avg_Hit']))
k3.metric("暴击", f"{result['Crit_Info']['rate']*100:.1f}%")
k4.metric("攻速", f"{result['Crit_Info']['aps']:.2f}")

df = pd.DataFrame(list(result['Packet'].items()), columns=['Type', 'Value'])
df = df[df['Value']>0]
if not df.empty:
    st.bar_chart(df.set_index('Type'), height=150, color="#FF4B4B")

with st.expander("🧮 详细公式"):
    st.markdown("**1. 基础点伤构建**")
    for e in result['Base_Explain']: st.code(e, language='text')
    st.markdown("**2. 乘区计算**")
    for p in result['Process']:
        st.latex(f"{p['type']}: {p['base']:.0f} \\times (1+{p['inc_sum']*100:.0f}\\% ) \\times {p['more_mult']:.2f} = \\mathbf{{{p['final']:.0f}}}")
        if p['matched_buffs']: st.caption(f"生效: {p['matched_buffs']}")

with st.expander("🛠️ 最终面板属性"):
    st.json(engine.stats)