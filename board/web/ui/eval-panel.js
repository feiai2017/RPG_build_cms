(function () {
  const dom = {
    buildSelect: document.getElementById('eval-build'),
    suiteSelect: document.getElementById('eval-suite'),
    seedsInput: document.getElementById('eval-seeds'),
    runBtn: document.getElementById('eval-run'),
    exportBtn: document.getElementById('eval-export'),
    status: document.getElementById('eval-status'),
    summary: document.getElementById('eval-summary'),
    buildDetail: document.getElementById('eval-build-detail'),
    systemDetail: document.getElementById('eval-system-detail'),
    flowDetail: document.getElementById('eval-flow-detail'),
    skillOverview: document.getElementById('eval-skill-overview'),
    runeOverview: document.getElementById('eval-rune-overview'),
    tableBody: document.getElementById('eval-table-body'),
  };

  const state = {
    builds: [],
    bossSuites: [],
    nerfProfiles: [],
    latestResult: null,
  };

  function setStatus(text) {
    if (dom.status) dom.status.textContent = text;
  }

  function parseSeeds(text) {
    if (!text) return [101, 102, 103];
    const seeds = text
      .split(/[，,\s]+/)
      .map((v) => Number(v.trim()))
      .filter((v) => Number.isFinite(v));
    return seeds.length ? seeds : [101, 102, 103];
  }

  function fillSelect(select, options, valueKey, labelKey) {
    if (!select) return;
    select.innerHTML = options
      .map((opt) => `<option value="${opt[valueKey]}">${opt[labelKey]}</option>`)
      .join('');
  }

  async function fetchJson(url) {
    const res = await fetch(url + '?t=' + Date.now());
    if (!res.ok) throw new Error(`Failed to load ${url}`);
    return res.json();
  }

  async function loadConfigs() {
    setStatus('加载评测配置...');
    if (window.SkillLoader?.loadCatalog) {
      try {
        await window.SkillLoader.loadCatalog();
      } catch (err) {
        console.warn('技能库加载失败，将使用现有配置。', err);
      }
    }
    const [buildsCfg, bossesCfg, nerfCfg] = await Promise.all([
      fetchJson('./configs/eval_builds.json'),
      fetchJson('./configs/eval_bosses.json'),
      fetchJson('./configs/eval_nerf_profiles.json'),
    ]);

    const builds = buildsCfg.builds || [];
    for (const build of builds) {
      if (build.preset) {
        const preset = await fetchJson(`./configs/${build.preset}.json`);
        build.build_data = preset;
      }
    }

    state.builds = builds;
    state.bossSuites = bossesCfg.boss_suites || [];
    state.nerfProfiles = nerfCfg.profiles || [];

    fillSelect(dom.buildSelect, builds, 'build_id', 'name');
    const suiteOptions = [
      { suite_id: 'all', name: '全部套件' },
      ...state.bossSuites,
    ];
    fillSelect(dom.suiteSelect, suiteOptions, 'suite_id', 'name');
    renderBuildDetail(builds[0]);
    renderSystemDetail();
    renderFlowDetail();
    renderSkillOverview();
    renderRuneOverview();
    setStatus('配置就绪');
  }

  function formatSkillLine(gua, skillId, formId, loopId, libs) {
    const skill = libs.skills?.[skillId];
    const form = libs.forms?.[formId];
    const loop = libs.loops?.[loopId];
    const skillName = skill?.name || skillId || '-';
    const skillLabel = skillId ? `${skillName}（${skillId}）` : skillName;
    const element = skill?.element || '-';
    const kindRaw = skill?.kind || '-';
    const kind = kindRaw === 'output' ? '输出（output）' : kindRaw === 'support' ? '辅助（support）' : kindRaw;
    const base = skill ? `${skill.baseDamage || 0}/${skill.baseCd || 0}` : '-';
    const desc = skill?.desc || '-';
    const formName = form ? `${form.name}（${form.id}）` : formId ? `未知（${formId}）` : '无';
    const loopName = loop ? `${loop.name}（${loop.id}）` : loopId ? `未知（${loopId}）` : '无';
    const formNote = form
      ? `x${form.hits || 1} · ${form.mult || 1}${form.cdAdd ? ` · cd+${form.cdAdd}` : ''}${form.markBonus ? ` · mark+${form.markBonus}` : ''}`
      : '';
    const loopNote = loop
      ? `${loop.cdDelta ? `cd${loop.cdDelta}` : ''}${loop.charges ? ` · 充能${loop.charges}` : ''}${loop.recastDelay ? ` · 复诵${loop.recastDelay}` : ''}${loop.sustainOnHit ? ` · 回能${loop.sustainOnHit}` : ''}${loop.sustainOnCrit ? ` · 暴击回能${loop.sustainOnCrit}` : ''}${loop.accelOnMark ? ` · 印记加速${loop.accelOnMark}` : ''}`
      : '';
    return `
      <tr>
        <td>${gua}</td>
        <td>${skillLabel}</td>
        <td>${element} / ${kind}</td>
        <td>${base}</td>
        <td>${desc}</td>
        <td>${formName} ${formNote ? `<div class="stat-sub">${formNote}</div>` : ''}</td>
        <td>${loopName} ${loopNote ? `<div class="stat-sub">${loopNote}</div>` : ''}</td>
      </tr>
    `;
  }

  function renderBuildDetail(build) {
    if (!dom.buildDetail) return;
    if (!build) {
      dom.buildDetail.innerHTML = '<div class="eval-detail-card">未选择 Build</div>';
      return;
    }
    try {
      const solver = window.BaguaSolver || {};
      const model = window.TiandaoModel || {};
      const skillsFromModel = model.SKILLS || [];
      const skillMap = new Map(skillsFromModel.map((s) => [s.id, s]));
      const libs = {
        skills: Object.assign({}, solver.SKILL_LIBRARY || {}, Object.fromEntries(skillMap)),
        forms: solver.FORM_RUNES || {},
        loops: solver.LOOP_RUNES || {},
        edges: solver.EDGE_RUNES || {},
      };
      const buildData = build.build_data || {};
      const skillsByGua = buildData.skills_by_gua || {};
      const privateRunes = buildData.private_runes || {};
      const edgeRunes = buildData.edge_runes || {};
      const guaOrder = solver.GUA_ORDER || ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];

      const mechanismTags = (build.key_mechanisms || []).map((m) => `<span class="eval-chip">${m}</span>`).join('');
      const flagEntries = Object.entries(build.feature_flags_default || {});
      const flagText = flagEntries.length
        ? flagEntries.map(([k, v]) => `${k}:${v ? 'on' : 'off'}`).join(' · ')
        : '未配置';
      const highlightList = (build.highlights || []).map((h) => `<li>${h}</li>`).join('');

      const skillLines = guaOrder
        .map((gua) => {
          const runes = privateRunes[gua] || {};
          return formatSkillLine(gua, skillsByGua[gua], runes.form, runes.loop, libs);
        })
        .join('');

      const edgeLines = Object.entries(edgeRunes).length
        ? Object.entries(edgeRunes)
            .map(([key, edgeId]) => {
              const edge = libs.edges?.[edgeId];
              const note = edge ? `${edge.name} (${edge.id})` : edgeId;
              const extra = edge?.ratio != null ? ` · ratio ${edge.ratio}` : edge?.delay ? ` · delay ${edge.delay}` : edge?.window ? ` · window ${edge.window}` : '';
              return `<li><span>${key}</span>${note}${extra}</li>`;
            })
            .join('')
        : '<li>无联结</li>';

      const buildDataWarning = build.build_data ? '' : '<div class="stat-sub">注意：build_data 未加载，技能细节可能为空。</div>';
      const loopSet = new Set(Object.values(privateRunes).map((r) => r?.loop).filter(Boolean));
      const edgeSet = new Set(Object.values(edgeRunes));
      const loopHints = Array.from(loopSet)
        .map((id) => libs.loops?.[id]?.name || id)
        .map((name) => `<li>循环符文：${name}</li>`)
        .join('');
      const edgeHints = Array.from(edgeSet)
        .map((id) => libs.edges?.[id]?.name || id)
        .map((name) => `<li>联结效果：${name}</li>`)
        .join('');
      const cycleHints = `
        <li>按卦序选择可施放技能，冷却结束立即施放。</li>
        ${loopHints || ''}
        ${edgeHints || ''}
        <li>命中会施加印记并触发元素反应（若有）。</li>
        <li>续航来源：技能护持 + 回能/暴击回能 + 续航纽带。</li>
      `;

      dom.buildDetail.innerHTML = `
        ${buildDataWarning}
        <div class="eval-detail-grid">
          <div class="eval-detail-card">
            <h3>概览</h3>
            <div>名称：${build.name}</div>
            <div>预设：${build.preset || '-'}</div>
            <div>机制：${mechanismTags || '无'}</div>
            <div>默认开关：${flagText}</div>
          </div>
          <div class="eval-detail-card">
            <h3>特殊点</h3>
            ${highlightList ? `<ul class="eval-note-list">${highlightList}</ul>` : '未配置'}
          </div>
        </div>
        <div class="eval-detail-card">
          <h3>联结</h3>
          <ul class="eval-detail-list">${edgeLines}</ul>
        </div>
        <div class="eval-detail-card">
          <h3>循环说明</h3>
          <ul class="eval-note-list">${cycleHints}</ul>
        </div>
        <div class="eval-detail-card">
          <h3>技能 / 符文</h3>
          <div class="eval-table-wrap">
            <table class="eval-detail-table">
              <thead>
                <tr>
                  <th>卦位</th>
                  <th>技能</th>
                  <th>元素/类型</th>
                  <th>基础(D/C)</th>
                  <th>说明</th>
                  <th>Form</th>
                  <th>Loop</th>
                </tr>
              </thead>
              <tbody>${skillLines}</tbody>
            </table>
          </div>
        </div>
      `;
    } catch (err) {
      console.error(err);
      dom.buildDetail.innerHTML = `<div class="eval-detail-card">BD 详情渲染失败：${err?.message || err}</div>`;
      setStatus('BD 详情渲染失败，请刷新页面');
    }
  }

  function renderSystemDetail() {
    if (!dom.systemDetail) return;
    const tickSeconds = window.TiandaoModel?.TICK_SECONDS ?? 0.5;
    const traits = Object.values(window.TiandaoModel?.GUA_TRAITS || {});
    const traitLines = traits.length
      ? traits.map((t) => `<li><span class="eval-term">卦位特性</span>：${t.name}（${t.desc}）</li>`).join('')
      : '<li><span class="eval-term">卦位特性</span>：未配置</li>';
    dom.systemDetail.innerHTML = `
      <ul class="eval-note-list">
        <li><span class="eval-term">Boss HP</span>：用于计算 <span class="eval-term">TTK（击杀时间）</span>。</li>
        <li><span class="eval-term">EHP（有效生命）</span>：<span class="eval-term">base_ehp</span> + <span class="eval-term">ehp</span>，用于计算存活时间。</li>
        <li><span class="eval-term">SUSTAIN（续航）</span>：护持/回能/暴击回能/续航纽带的合计。</li>
        <li><span class="eval-term">CD（冷却）</span>：技能冷却按 tick 递减（${tickSeconds}s/ tick）。</li>
        <li><span class="eval-term">印记（MARK）</span>：命中附加元素印记，用于触发元素反应。</li>
        <li><span class="eval-term">联结（EDGE）</span>：接力/减冷/引爆/续航等触发。</li>
        ${traitLines}
      </ul>
      <div class="stat-sub">说明：这是当前 Web 模拟的简化模型，不包含真实蓝量/能量条与复杂承伤。</div>
    `;
  }

  function renderFlowDetail() {
    if (!dom.flowDetail) return;
    dom.flowDetail.innerHTML = `
      <pre class="eval-flow">
Tick 开始
  -> 冷却递减 / 处理接力队列
  -> 选择可施放技能（按卦序）
  -> 施放（可能触发复诵/接力）
  -> 命中造成伤害 + 施加印记
  -> 触发反应 / 联结 / 回能
  -> 统计 DPS / 续航 / 空窗
      </pre>
    `;
  }

  function renderSkillOverview() {
    if (!dom.skillOverview) return;
    const model = window.TiandaoModel || {};
    const skills = model.SKILLS || [];
    if (!skills.length) {
      dom.skillOverview.innerHTML = '<div class="stat-sub">未加载技能库。</div>';
      return;
    }
    const rows = skills
      .map((skill) => {
        const kind = skill.kind === 'output' ? '输出（output）' : skill.kind === 'support' ? '辅助（support）' : skill.kind;
        const label = `${skill.name}（${skill.id}）`;
        const base = `${skill.baseDamage || 0}/${skill.baseCd || 0}`;
        const desc = skill.desc || '-';
        const extra = skill.sustain ? `护持 ${skill.sustain}` : '-';
        return `
          <tr>
            <td>${label}</td>
            <td>${skill.element}</td>
            <td>${kind}</td>
            <td>${base}</td>
            <td>${desc}</td>
            <td>${extra}</td>
          </tr>
        `;
      })
      .join('');
    dom.skillOverview.innerHTML = `
      <div class="eval-table-wrap">
        <table class="eval-detail-table">
          <thead>
            <tr>
              <th>技能</th>
              <th>元素</th>
              <th>类型</th>
              <th>基础(D/C)</th>
              <th>说明</th>
              <th>额外效果</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    `;
  }

  function summarizeFormRune(rune) {
    if (!rune) return '';
    const parts = [`${rune.name}（${rune.id}）`];
    if (rune.mult != null) parts.push(`倍率 ${rune.mult}`);
    if (rune.hits != null) parts.push(`命中次数 ${rune.hits}`);
    if (rune.cdAdd) parts.push(`冷却 +${rune.cdAdd}`);
    if (rune.markBonus) parts.push(`印记 +${rune.markBonus}`);
    return parts.join(' · ');
  }

  function summarizeLoopRune(rune) {
    if (!rune) return '';
    const parts = [`${rune.name}（${rune.id}）`];
    if (rune.cdDelta) parts.push(`基础冷却 ${rune.cdDelta}`);
    if (rune.charges) parts.push(`充能 ${rune.charges}`);
    if (rune.recastDelay) parts.push(`复诵延迟 ${rune.recastDelay} tick`);
    if (rune.recastMul) parts.push(`复诵倍率 ${rune.recastMul}`);
    if (rune.accelOnMark) parts.push(`条件加速 ${rune.accelOnMark}`);
    if (rune.sustainOnHit) parts.push(`回能 ${rune.sustainOnHit}`);
    if (rune.sustainOnCrit) parts.push(`暴击回能 ${rune.sustainOnCrit}`);
    return parts.join(' · ');
  }

  function summarizeEdgeRune(rune) {
    if (!rune) return '';
    const parts = [`${rune.name}（${rune.id}）`];
    if (rune.delay) parts.push(`接力延迟 ${rune.delay} tick`);
    if (rune.mul) parts.push(`接力倍率 ${rune.mul}`);
    if (rune.ratio) parts.push(`比例 ${rune.ratio}`);
    if (rune.window) parts.push(`引爆窗口 ${rune.window}`);
    return parts.join(' · ');
  }

  function renderRuneOverview() {
    if (!dom.runeOverview) return;
    const solver = window.BaguaSolver || {};
    const forms = Object.values(solver.FORM_RUNES || {}).map(summarizeFormRune);
    const loops = Object.values(solver.LOOP_RUNES || {}).map(summarizeLoopRune);
    const edges = Object.values(solver.EDGE_RUNES || {}).map(summarizeEdgeRune);
    dom.runeOverview.innerHTML = `
      <div class="eval-detail-grid">
        <div class="eval-detail-card">
          <h3>Form 符文（形态）</h3>
          <ul class="eval-detail-list">${forms.map((s) => `<li>${s}</li>`).join('')}</ul>
        </div>
        <div class="eval-detail-card">
          <h3>Loop 符文（循环）</h3>
          <ul class="eval-detail-list">${loops.map((s) => `<li>${s}</li>`).join('')}</ul>
        </div>
      </div>
      <div class="eval-detail-card">
        <h3>Edge 联结（联动）</h3>
        <ul class="eval-detail-list">${edges.map((s) => `<li>${s}</li>`).join('')}</ul>
      </div>
    `;
  }

  function renderSummary(summary) {
    if (!dom.summary) return;
    if (!summary || summary.error) {
      dom.summary.innerHTML = '<div class="eval-card">暂无汇总</div>';
      return;
    }
    dom.summary.innerHTML = [
      `<div class="eval-card"><div class="eval-card-title">鲁棒通过率</div><div class="eval-card-value">${summary.robust_pass_rate}</div></div>`,
      `<div class="eval-card"><div class="eval-card-title">机制差异 TTK</div><div class="eval-card-value">${summary.mechanism_delta_ttk}</div></div>`,
      `<div class="eval-card"><div class="eval-card-title">机制差异生存</div><div class="eval-card-value">${summary.mechanism_delta_survival}</div></div>`,
      `<div class="eval-card"><div class="eval-card-title">专精评分</div><div class="eval-card-value">${summary.specialization_score}</div></div>`,
      `<div class="eval-card"><div class="eval-card-title">敏感度斜率</div><div class="eval-card-value">${summary.sensitivity_ttk_damage}</div></div>`,
      `<div class="eval-card"><div class="eval-card-title">最终判定</div><div class="eval-card-value">${summary.final_label}</div></div>`,
    ].join('');
  }

  function renderTable(rows) {
    if (!dom.tableBody) return;
    if (!rows?.length) {
      dom.tableBody.innerHTML = '<tr><td colspan="8" class="eval-empty">暂无数据</td></tr>';
      return;
    }
    dom.tableBody.innerHTML = rows
      .map((row) => {
        const passClass = row.pass_flag ? 'eval-pass' : 'eval-fail';
        const passLabel = row.pass_flag ? 'PASS' : 'FAIL';
        return `
          <tr>
            <td>${row.suite_name}</td>
            <td>${row.boss_name}</td>
            <td>${row.nerf_label}</td>
            <td>${row.mechanism_label}</td>
            <td>${row.ttk}</td>
            <td>${row.survival_margin}</td>
            <td>${row.effective_dps}</td>
            <td class="${passClass}">${passLabel}</td>
          </tr>
        `;
      })
      .join('');
  }

  function toCsv(rows) {
    const header = ['suite', 'boss', 'nerf', 'mode', 'ttk', 'survival_margin', 'effective_dps', 'pass_flag'];
    const lines = [header.join(',')];
    rows.forEach((row) => {
      lines.push([
        row.suite_name,
        row.boss_name,
        row.nerf_label,
        row.mechanism_label,
        row.ttk,
        row.survival_margin,
        row.effective_dps,
        row.pass_flag ? 'PASS' : 'FAIL',
      ].join(','));
    });
    return lines.join('\n');
  }

  function downloadText(content, filename) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function exportResults() {
    if (!state.latestResult) {
      setStatus('请先运行评测');
      return;
    }
    const exportedAt = new Date().toISOString();
    const payload = {
      exported_at: exportedAt,
      summary: state.latestResult.summary,
      rows: state.latestResult.rows,
    };
    const csv = '\ufeff' + toCsv(state.latestResult.rows);
    const json = '\ufeff' + JSON.stringify(payload, null, 2);
    downloadText(csv, 'bd_eval_report.csv');
    downloadText(json, 'bd_eval_report.json');
    setStatus('已导出 CSV/JSON');
  }

  function runEvaluation() {
    const buildId = dom.buildSelect?.value;
    const suiteId = dom.suiteSelect?.value;
    const build = state.builds.find((b) => b.build_id === buildId);
    if (!build) {
      setStatus('未找到 Build');
      return;
    }
    const bossSuites = suiteId === 'all'
      ? state.bossSuites
      : state.bossSuites.filter((s) => s.suite_id === suiteId);
    const seeds = parseSeeds(dom.seedsInput?.value);

    setStatus('评测运行中...');
    const result = window.BDEval.runEvaluation({
      build,
      bossSuites,
      nerfProfiles: state.nerfProfiles,
      mechanismModes: window.BDEval.DEFAULT_MECHANISM_MODES,
      seeds,
      maxTicks: 120,
      tickSeconds: 0.5,
      baseEhp: 100,
    });

    state.latestResult = result;
    renderSummary(result.summary);
    renderTable(result.rows);
    setStatus(`完成：${result.rows.length} 条组合`);
  }

  function attachEvents() {
    dom.runBtn?.addEventListener('click', runEvaluation);
    dom.exportBtn?.addEventListener('click', exportResults);
    dom.buildSelect?.addEventListener('change', () => {
      const buildId = dom.buildSelect?.value;
      const build = state.builds.find((b) => b.build_id === buildId);
      renderBuildDetail(build);
    });
  }

  if (dom.buildSelect && dom.suiteSelect) {
    loadConfigs().then(attachEvents).catch((err) => {
      setStatus('配置加载失败');
      console.error(err);
    });
  }

})();
