# generate_doc.py

def get_html_content():
	# 注意：这里保留 r""" 以防止 LaTeX 转义错误
	return r"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Roguelike ARPG 数值体系架构说明书</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; line-height: 1.6; color: #333; max-width: 950px; margin: 0 auto; padding: 40px; background-color: #fcfcfc; }
        h1 { text-align: center; border-bottom: 3px solid #2c3e50; padding-bottom: 15px; margin-bottom: 40px; color: #2c3e50; }
        h2 { color: #2980b9; border-left: 6px solid #e74c3c; padding-left: 15px; margin-top: 50px; background: #ecf0f1; padding: 10px 15px; }
        h3 { color: #e67e22; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
        h4 { color: #34495e; margin-top: 20px; font-weight: bold; }
        
        code { background-color: #f1f2f6; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; color: #c0392b; font-weight: bold; }
        pre { background-color: #2d3436; color: #dfe6e9; padding: 15px; border-radius: 8px; overflow-x: auto; font-family: Consolas, monospace; }
        
        .box { background-color: #e8f4f8; border-left: 5px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .warn-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .example-box { background-color: #e9f7ef; border: 1px solid #2ecc71; padding: 20px; margin: 20px 0; border-radius: 8px; }
        
        .math-block { background-color: #fff; padding: 15px; text-align: center; font-size: 1.2em; border: 1px solid #eee; margin: 15px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        
        table { border-collapse: collapse; width: 100%; margin: 20px 0; font-size: 0.95em; }
        th, td { border: 1px solid #bdc3c7; padding: 12px; text-align: left; }
        th { background-color: #34495e; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        
        .tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; color: white; margin-right: 5px; }
        .tag-inc { background-color: #3498db; }
        .tag-more { background-color: #e74c3c; }
        .tag-flat { background-color: #9b59b6; }

        @media print {
            body { max-width: 100%; padding: 0; background-color: white; }
            .no-print { display: none; }
            h2 { background: none; border-left: none; border-bottom: 2px solid #ccc; padding: 0; }
            button { display: none; }
        }
    </style>
</head>
<body>

    <h1>Roguelike ARPG 数值体系架构说明书</h1>
    <p style="text-align: center; color: #7f8c8d;">Version: 2.0 | Codename: The Pipeline</p>

    <div class="box">
        <strong>核心摘要：</strong> 本文档详细定义了基于 YAML 配置驱动的伤害计算管线。体系区分了 <strong>基础点伤 (Flat)</strong>、<strong>加算池 (Inc)</strong> 和 <strong>独立乘区 (More)</strong>，确保 BD 构建既有广度（堆属性）也有深度（找机制）。
    </div>

    <h2>1. 伤害公式全景 (The Formula)</h2>
    <p>所有伤害计算严格遵循以下 5 阶段管线：</p>
    
    <div class="math-block">
        $$DPS = \underbrace{(\text{Base} + \text{Flat})}_{\text{Stage 1}} \times \underbrace{(1 + \sum \text{Inc})}_{\text{Stage 3}} \times \underbrace{\prod (1 + \text{More})}_{\text{Stage 4}} \times \underbrace{(\text{Crit} \times \text{Speed})}_{\text{Stage 5}}$$
    </div>

    <p><em>注：Stage 2 为伤害转化 (Conversion)，发生在计算加成之前。</em></p>

    <h2>2. 详解：三大伤害维度</h2>
    <p>为了数值平衡，必须严格区分以下三类属性在 YAML 中的定义。</p>

    <h3>维度 A：基础点伤 (Base Flat Damage)</h3>
    <p><span class="tag tag-flat">Flat</span> <strong>地位：地基。</strong>所有倍率放大的基础。</p>
    <table>
        <tr>
            <th>YAML Key 示例</th>
            <th>中文名</th>
            <th>说明</th>
        </tr>
        <tr>
            <td><code>flat_physical</code></td>
            <td>物理点伤</td>
            <td>直接加到基础伤害池。例如铁戒指 (+10)。</td>
        </tr>
        <tr>
            <td><code>flat_fire</code></td>
            <td>火焰点伤</td>
            <td>直接加到火焰伤害池。法术和攻击均可享受。</td>
        </tr>
        <tr>
            <td><code>flat_chaos</code></td>
            <td>混沌点伤</td>
            <td>稀有的点伤类型，穿透护盾。</td>
        </tr>
    </table>

    <h3>维度 B：加算池 (Additive / Inc)</h3>
    <p><span class="tag tag-inc">Inc</span> <strong>地位：最常见的增伤手段。</strong>边际收益递减。</p>
    <div class="math-block">
        $$Multiplier_{Inc} = 1 + (\text{Global} + \text{Type} + \text{Tag})$$
    </div>
    <table>
        <tr>
            <th>YAML Key 示例</th>
            <th>中文名</th>
            <th>说明</th>
        </tr>
        <tr>
            <td><code>inc_all</code></td>
            <td>全局增伤</td>
            <td>通用性最强，数值通常较低。</td>
        </tr>
        <tr>
            <td><code>inc_physical</code></td>
            <td>物理增伤</td>
            <td>仅对 Physical 标签生效。</td>
        </tr>
        <tr>
            <td><code>inc_elemental</code></td>
            <td>元素增伤</td>
            <td>同时加成 Fire / Cold / Lightning。</td>
        </tr>
        <tr>
            <td><code>inc_spell</code></td>
            <td>法术增伤</td>
            <td>仅对 Spell 标签技能生效。</td>
        </tr>
    </table>

    <h3>维度 C：独立乘区 (Multiplicative / More)</h3>
    <p><span class="tag tag-more">More</span> <strong>地位：稀有且强力。</strong>通常来自天赋大点或传奇装备。</p>
    <div class="math-block">
        $$Multiplier_{More} = (1 + \text{More}_1) \times (1 + \text{More}_2) \times ...$$
    </div>
    <table>
        <tr>
            <th>YAML Key 示例</th>
            <th>中文名</th>
            <th>说明</th>
        </tr>
        <tr>
            <td><code>more_damage</code></td>
            <td>全局独立增伤</td>
            <td>极其珍贵。例如：处决巨斧 (20% More)。</td>
        </tr>
        <tr>
            <td><code>more_fire</code></td>
            <td>火焰独立增伤</td>
            <td>例如：献祭 Buff (20% More Fire)。</td>
        </tr>
    </table>

    <h2>3. 实例演算 (Calculation Example)</h2>
    <p>为了理解不同词条的收益差距，假设技能<strong>基础伤害为 100 火伤</strong>。</p>

    <div class="example-box">
        <h4>场景 A：全是加算 (Inc) —— 收益最低</h4>
        <ul>
            <li>装备1: <code>inc_fire: 0.5</code> (+50%)</li>
            <li>装备2: <code>inc_spell: 0.5</code> (+50%)</li>
        </ul>
        <p><strong>计算：</strong> $$100 \times (1 + 0.5 + 0.5) = 100 \times 2.0 = \mathbf{200}$$</p>
    </div>

    <div class="example-box" style="border-color: #e74c3c; background-color: #fdedec;">
        <h4>场景 B：全是乘算 (More) —— 收益爆炸</h4>
        <ul>
            <li>装备1: <code>more_damage: 0.5</code> (+50% More)</li>
            <li>装备2: <code>more_fire: 0.5</code> (+50% More)</li>
        </ul>
        <p><strong>计算：</strong> $$100 \times (1 + 0.5) \times (1 + 0.5) = 100 \times 1.5 \times 1.5 = \mathbf{225}$$</p>
    </div>

    <div class="example-box" style="border-color: #9b59b6; background-color: #f4ecf7;">
        <h4>场景 C：点伤 + 加算 —— 前期最强</h4>
        <ul>
            <li>装备1: <code>flat_fire: 50</code> (+50 点伤)</li>
            <li>装备2: <code>inc_fire: 0.5</code> (+50%)</li>
        </ul>
        <p><strong>计算：</strong> $$(100 + 50) \times (1 + 0.5) = 150 \times 1.5 = \mathbf{225}$$</p>
    </div>

    <h2>4. 属性转化与机制 (Conversion & Mechanics)</h2>
    <p>这是构建复杂 BD 的关键。</p>
    
    <h3>伤害转化 (Conversion)</h3>
    <p>在 YAML 中使用 <code>conversions</code> 列表定义。</p>
    <div class="warn-box">
        <strong>规则：</strong> 转化发生在 <strong>Stage 2</strong>（基础点伤之后，加成计算之前）。
        <br>例如：物理转火。被转化的物理伤害将<strong>不再享受物理加成</strong>（简化模型），而是享受火焰加成。
    </div>

    <h3>动态机制 (Dynamic Stats)</h3>
    <p>允许使用 Python 表达式引用运行时状态。</p>
    <pre>
# 示例：血量转攻速机制
dynamic_stats:
  atk_spd: "stats['current_hp'] / 100"
    </pre>

    <hr>
    <p style="text-align: center;" class="no-print">
        <button onclick="window.print()" style="padding: 12px 24px; font-size: 16px; cursor: pointer; background: #2c3e50; color: white; border: none; border-radius: 5px; font-weight: bold;">🖨️ 保存为 PDF (Ctrl + P)</button>
    </p>

</body>
</html>
"""