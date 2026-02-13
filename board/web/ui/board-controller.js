(function () {
  const Model = window.TiandaoModel;
  const Render = window.TiandaoRender;
  const GodotExport = window.TiandaoGodotExport;

  const dom = {
    container: document.getElementById('canvas-container'),
    steps: Array.from(document.querySelectorAll('#steps-bar .step')),
    itemSelect: document.getElementById('stone-select'),
    clearSlot: document.getElementById('clear-slot'),
    presetSelect: document.getElementById('preset-select'),
    presetLoad: document.getElementById('load-preset'),
    simulateBtn: document.getElementById('simulate-btn'),
    openLog: document.getElementById('open-log'),
    buildIssues: document.getElementById('build-issues'),
    buildStatus: document.getElementById('build-status'),
    exportBoard: document.getElementById('export-board'),
    bossList: document.getElementById('boss-list'),
    bossDetail: document.getElementById('boss-detail'),
    detail: {
      name: document.getElementById('detail-name'),
      element: document.getElementById('detail-element'),
      id: document.getElementById('detail-id'),
      type: document.getElementById('detail-type'),
      trigram: document.getElementById('detail-trigram'),
      component: document.getElementById('detail-component'),
      effect: document.getElementById('detail-effect'),
      runes: document.getElementById('detail-runes'),
      links: document.getElementById('detail-links'),
    },
    metrics: {
      casts: document.getElementById('metric-casts'),
      reactions: document.getElementById('metric-reactions'),
      downtime: document.getElementById('metric-downtime'),
      sustain: document.getElementById('metric-sustain'),
    },
    devLog: document.getElementById('dev-log-text'),
    copyButtons: Array.from(document.querySelectorAll('[data-copy-target]')),
    detailVerbose: document.getElementById('detail-verbose'),
    compareMode: document.getElementById('compare-mode'),
    compareHint: document.getElementById('compare-hint'),
  };

  let boardState = null;
  let presetFiles = [];
  let selectedSlotId = null;
  let issues = [];
  let focusId = null;
  let bossProfiles = [];
  let selectedBossId = null;
  let compareEnabled = false;
  let compareSkillId = null;
  let compareSkillGua = null;
  let compareTooltip = null;
  let lastCompareSlotId = null;

  function updateIssuePanel() {
    if (!dom.buildIssues) return;
    dom.buildIssues.innerHTML = '';
    if (!issues.length) {
      dom.buildIssues.innerHTML = '<li class="ok">构筑合法</li>';
      if (dom.buildStatus) dom.buildStatus.textContent = 'OK';
    } else {
      issues.forEach((issue) => {
        const li = document.createElement('li');
        li.textContent = issue.message;
        dom.buildIssues.appendChild(li);
      });
      if (dom.buildStatus) dom.buildStatus.textContent = `ERR(${issues.length})`;
    }
    if (dom.simulateBtn) dom.simulateBtn.disabled = issues.length > 0;
  }

  function refreshBoard() {
    if (!dom.container || !boardState) return;
    const compareState = { enabled: compareEnabled, skillId: compareSkillId };
    dom.container.innerHTML = Render.renderBoard(boardState, selectedSlotId, focusId, compareState);
    GodotExport.persistPayload(boardState);
  }

  function updateItemSelect(slot) {
    if (!dom.itemSelect || !slot) return;
    const accepts = Model.SLOT_ACCEPTS[slot.kind] || [];
    const options = Model.ITEMS.filter((it) => accepts.includes(it.category));
    dom.itemSelect.innerHTML = options.map((it) => `<option value="${it.id}">${it.name}</option>`).join('');
    dom.itemSelect.value = slot.item_id || options[0]?.id || '';
  }

  function updateDetail(slot) {
    if (!slot || !dom.detail) return;
    const verbose = dom.detailVerbose?.checked;
    Render.updateDetail(dom, boardState, slot, verbose);
  }

  function ensureCompareTooltip() {
    if (compareTooltip) return compareTooltip;
    compareTooltip = document.createElement('div');
    compareTooltip.id = 'compare-tooltip';
    document.body.appendChild(compareTooltip);
    return compareTooltip;
  }

  function showCompareTooltip(html, evt) {
    const tip = ensureCompareTooltip();
    tip.innerHTML = html;
    tip.style.display = 'block';
    const padding = 12;
    const maxX = window.innerWidth - tip.offsetWidth - padding;
    const maxY = window.innerHeight - tip.offsetHeight - padding;
    const x = Math.min(maxX, evt.clientX + 14);
    const y = Math.min(maxY, evt.clientY + 16);
    tip.style.left = `${Math.max(padding, x)}px`;
    tip.style.top = `${Math.max(padding, y)}px`;
  }

  function hideCompareTooltip() {
    if (!compareTooltip) return;
    compareTooltip.style.display = 'none';
  }

  function describeEdgeRune(edgeId) {
    const edge = Model.EDGE_RUNES_LIB?.[edgeId] || {};
    const name = edge?.name || edgeId || '未知';
    if (edgeId === 'RELAY') return `${name}（${edgeId}）：延迟${edge.delay}tick再施放，倍率${edge.mul}`;
    if (edgeId === 'CD_ROUTER') return `${name}（${edgeId}）：命中后减少目标冷却约${Math.round(edge.ratio * 100)}%`;
    if (edgeId === 'REACT_DETONATOR') return `${name}（${edgeId}）：引爆窗口${edge.window}tick`;
    if (edgeId === 'SUSTAIN_LINK') return `${name}（${edgeId}）：伤害${Math.round(edge.ratio * 100)}%转续航`;
    return `${name}（${edgeId}）`;
  }

  function compareSummary(skillId, targetGua) {
    const skill = Model.SKILL_LIBRARY?.[skillId];
    if (!skill) return '<div class="compare-line">未找到技能</div>';
    const runes = boardState.build.private_runes?.[targetGua] || {};
    const form = Model.FORM_RUNES_LIB?.[runes.form] || null;
    const loop = Model.LOOP_RUNES_LIB?.[runes.loop] || null;
    const trait = Model.GUA_TRAITS?.[targetGua];
    const baseCd = Math.max(1, (skill.baseCd || 0) + (form?.cdAdd || 0) + (loop?.cdDelta || 0));
    const hits = form?.hits || 1;
    const mult = form?.mult || 1;
    const markBonus = form?.markBonus || 0;
    const perHit = (skill.baseDamage || 0) * mult;
    const total = perHit * hits;
    const sustain = (skill.sustain || 0) * mult;

    const formLine = form
      ? `Form：${form.name}（${form.id}）| 倍率${mult} | 命中${hits}${form.cdAdd ? ` | 冷却+${form.cdAdd}` : ''}${markBonus ? ` | 印记+${markBonus}` : ''}`
      : 'Form：无';
    const loopLine = loop
      ? `Loop：${loop.name}（${loop.id}）${loop.cdDelta ? ` | 冷却${loop.cdDelta}` : ''}${loop.charges ? ` | 充能${loop.charges}` : ''}${loop.recastDelay ? ` | 复诵${loop.recastDelay}tick` : ''}${loop.accelOnMark ? ` | 条件加速${loop.accelOnMark}` : ''}${loop.sustainOnHit ? ` | 回能+${loop.sustainOnHit}` : ''}${loop.sustainOnCrit ? ` | 暴击回能+${loop.sustainOnCrit}` : ''}`
      : 'Loop：无';

    const prev = Model.GUA_ORDER[(Model.GUA_ORDER.indexOf(targetGua) - 1 + Model.GUA_ORDER.length) % Model.GUA_ORDER.length];
    const next = Model.nextGua(targetGua);
    const edgePrev = boardState.build.edge_runes?.[Model.canonicalEdgeKey(prev, targetGua)];
    const edgeNext = boardState.build.edge_runes?.[Model.canonicalEdgeKey(targetGua, next)];
    const edges = [edgePrev, edgeNext].filter(Boolean).map(describeEdgeRune);
    const edgeLine = edges.length ? `联结：${edges.join('；')}` : '联结：无';

    const baseLine = `基础：${skill.element} / ${skill.kind === 'support' ? '辅助' : '输出'}，D/C ${skill.baseDamage || 0}/${skill.baseCd || 0}`;
    const effectLine = skill.kind === 'support'
      ? `估算：护持${sustain.toFixed(1)}，冷却${baseCd}tick(${(baseCd * Model.TICK_SECONDS).toFixed(1)}s)`
      : `估算：每段${perHit.toFixed(1)} ×${hits} = ${total.toFixed(1)}，冷却${baseCd}tick(${(baseCd * Model.TICK_SECONDS).toFixed(1)}s)`;

    const compareFrom = compareSkillGua;
    const diffParts = [];
    if (compareFrom) {
      const baseRunes = boardState.build.private_runes?.[compareFrom] || {};
      if (baseRunes.form !== runes.form) diffParts.push(`Form ${baseRunes.form || '无'} → ${runes.form || '无'}`);
      if (baseRunes.loop !== runes.loop) diffParts.push(`Loop ${baseRunes.loop || '无'} → ${runes.loop || '无'}`);
      const baseTrait = Model.GUA_TRAITS?.[compareFrom];
      if (baseTrait?.id !== trait?.id) diffParts.push(`卦位特性 ${baseTrait?.name || '无'} → ${trait?.name || '无'}`);
      const basePrev = Model.GUA_ORDER[(Model.GUA_ORDER.indexOf(compareFrom) - 1 + Model.GUA_ORDER.length) % Model.GUA_ORDER.length];
      const baseNext = Model.nextGua(compareFrom);
      const baseEdgePrev = boardState.build.edge_runes?.[Model.canonicalEdgeKey(basePrev, compareFrom)];
      const baseEdgeNext = boardState.build.edge_runes?.[Model.canonicalEdgeKey(compareFrom, baseNext)];
      if (baseEdgePrev !== edgePrev || baseEdgeNext !== edgeNext) diffParts.push('联结不同');
      if (compareFrom !== targetGua) diffParts.push(`卦序位置 ${compareFrom} → ${targetGua}`);
    }
    const diffLine = diffParts.length
      ? `差异：${diffParts.join('，')}`
      : '差异：无（符文/联结相同）';

    return `
      <div class="compare-title">技能：${skill.name} → 卦位 ${targetGua}</div>
      <div class="compare-line">${baseLine}</div>
      <div class="compare-line">卦位特性：${trait ? `${trait.name}（${trait.desc}）` : '无'}</div>
      <div class="compare-line">${formLine}</div>
      <div class="compare-line">${loopLine}</div>
      <div class="compare-line">${edgeLine}</div>
      <div class="compare-line">${effectLine}</div>
      <div class="compare-line">${diffLine}</div>
      <div class="compare-line">提示：卦位差异来自符文/联结/施放顺序。</div>
    `;
  }

  function applyItem(slotId, itemId) {
    const slot = Model.applyItem(boardState, slotId, itemId);
    if (!slot) return;
    issues = Model.validateBuild(boardState);
    updateIssuePanel();
    refreshBoard();
    updateDetail(slot);
  }

  function clearSlot(slotId) {
    const slot = Model.clearSlot(boardState, slotId);
    if (!slot) return;
    issues = Model.validateBuild(boardState);
    updateIssuePanel();
    refreshBoard();
    updateDetail(slot);
  }

  function formatBossSummary(boss, fight) {
    if (!boss) return '请选择一个 Boss';
    const parts = [`${boss.name} · HP ${boss.hp} · DPS ${boss.dps}`];
    if (boss.spike) parts.push(`爆发 ${boss.spike}/${boss.spikeInterval}s`);
    if (fight?.time_to_kill != null) {
      parts.push(`TTK ${fight.time_to_kill}s / 生存 ${fight.time_survived}s`);
    }
    return parts.join(' | ');
  }

  function runSimulation() {
    if (issues.length) return;
    const boss = bossProfiles.find((b) => b.id === selectedBossId) || bossProfiles[0] || null;
    const result = Model.simulateBuild(boardState, {
      maxTicks: 20,
      tickSeconds: Model.TICK_SECONDS,
      targetName: boss?.name,
      targetId: boss?.id,
      target: boss || undefined,
    });
    if (!result) return;
    if (boss?.name && Array.isArray(result.events)) {
      result.events = result.events.map((evt) => {
        if (!evt || evt.kind === 'BOSS') return evt;
        if (evt.target === '玩家') return evt;
        return { ...evt, target: boss.name };
      });
    }
    const metrics = result.metrics || {};
    dom.metrics.casts.textContent = Render.formatCasts(metrics.casts_per_skill || {});
    dom.metrics.reactions.textContent = Render.formatReactions(metrics.reaction_counts || {});
    dom.metrics.downtime.textContent = metrics.downtime_ticks ?? '-';
    dom.metrics.sustain.textContent = metrics.sustain_total ?? '-';
    if (dom.devLog) dom.devLog.textContent = result.logs?.join('\n') || '';

    const fight = Model.simulateBoss(result, boss);
    if (dom.bossDetail) dom.bossDetail.textContent = formatBossSummary(boss, fight);
    const bossEvents = Array.isArray(fight?.events) ? fight.events : [];
    const mergedEvents = (result.events || [])
      .concat(bossEvents)
      .map((evt, idx) => ({ ...evt, __order: idx }))
      .sort((a, b) => {
        const at = typeof a.time === 'number' ? a.time : Number.POSITIVE_INFINITY;
        const bt = typeof b.time === 'number' ? b.time : Number.POSITIVE_INFINITY;
        if (at !== bt) return at - bt;
        const aTick = typeof a.tick === 'number' ? a.tick : Number.POSITIVE_INFINITY;
        const bTick = typeof b.tick === 'number' ? b.tick : Number.POSITIVE_INFINITY;
        if (aTick !== bTick) return aTick - bTick;
        return a.__order - b.__order;
      })
      .map(({ __order, ...evt }) => evt);

    const payload = {
      bd: {
        name: boardState.build.name || 'custom',
        skills: boardState.build.skills_by_gua,
        runes: boardState.build.private_runes,
        edges: boardState.build.edge_runes,
      },
      boss: boss || null,
      catalog: {
        skills: Model.SKILL_LIBRARY,
        form_runes: Model.FORM_RUNES_LIB,
        loop_runes: Model.LOOP_RUNES_LIB,
        edge_runes: Model.EDGE_RUNES_LIB,
        reactions: Model.REACTIONS,
      },
      result: {
        totals: result.totals,
        metrics: result.metrics,
      },
      fight: {
        events: mergedEvents,
        summary: fight,
      },
    };
    localStorage.setItem('battle_log', JSON.stringify(payload));
  }

  function exportBoard() {
    const payload = GodotExport.buildMinimalPayload(boardState);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tiandao_board.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function loadPreset(name) {
    const res = await fetch(`./configs/${name}.json?t=${Date.now()}`);
    const data = await res.json();
    boardState = Model.buildBoardState(data);
    issues = Model.validateBuild(boardState);
    updateIssuePanel();
    refreshBoard();
    selectedSlotId = boardState.slots[0]?.id || null;
    updateItemSelect(Model.getSlot(boardState, selectedSlotId));
    updateDetail(Model.getSlot(boardState, selectedSlotId));
  }

  function renderBossCards() {
    if (!dom.bossList) return;
    dom.bossList.innerHTML = '';
    bossProfiles.forEach((boss) => {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = `boss-card${boss.id === selectedBossId ? ' active' : ''}`;
      card.dataset.bossId = boss.id;
      card.innerHTML = `<strong>${boss.name}</strong><br>${boss.desc || ''}`;
      card.addEventListener('click', () => {
        selectedBossId = boss.id;
        renderBossCards();
        if (dom.bossDetail) dom.bossDetail.textContent = formatBossSummary(boss);
      });
      dom.bossList.appendChild(card);
    });
    const current = bossProfiles.find((b) => b.id === selectedBossId) || bossProfiles[0];
    if (current && dom.bossDetail) dom.bossDetail.textContent = formatBossSummary(current);
  }

  async function loadBosses() {
    try {
      const res = await fetch('./configs/tiandao_bosses.json?t=' + Date.now());
      const data = await res.json();
      bossProfiles = Array.isArray(data.bosses) ? data.bosses : [];
    } catch (err) {
      bossProfiles = Model.BOSS_PROFILES || [];
    }
    if (!bossProfiles.length) {
      bossProfiles = [{ id: 'dummy', name: '木桩', hp: 1200, dps: 0, spike: 0, spikeInterval: 10, desc: '基准对照' }];
    }
    selectedBossId = bossProfiles[0].id;
    renderBossCards();
  }

  function attachEvents() {
    dom.container.addEventListener('click', (evt) => {
      const slotEl = evt.target.closest('[data-slot-id]');
      if (!slotEl) {
        focusId = null;
        refreshBoard();
        return;
      }
      selectedSlotId = slotEl.getAttribute('data-slot-id');
      focusId = selectedSlotId;
      const slot = Model.getSlot(boardState, selectedSlotId);
      if (compareEnabled && slot?.kind === Model.SLOT_KIND.SKILL) {
        compareSkillId = slot.item_id;
        compareSkillGua = slot.gua;
        if (dom.compareHint) {
          dom.compareHint.textContent = compareSkillId
            ? `对比模式：当前技能「${Model.SKILL_LIBRARY?.[compareSkillId]?.name || compareSkillId}」，悬停各卦位查看效果。`
            : '对比模式：该槽位未配置技能。';
        }
      }
      updateItemSelect(slot);
      updateDetail(slot);
      refreshBoard();
    });

    dom.itemSelect?.addEventListener('change', () => {
      const slot = Model.getSlot(boardState, selectedSlotId);
      if (!slot) return;
      applyItem(slot.id, dom.itemSelect.value);
    });

    dom.clearSlot?.addEventListener('click', () => {
      const slot = Model.getSlot(boardState, selectedSlotId);
      if (!slot) return;
      clearSlot(slot.id);
    });

    dom.simulateBtn?.addEventListener('click', () => {
      runSimulation();
    });

    dom.openLog?.addEventListener('click', () => {
      if (!localStorage.getItem('battle_log')) {
        runSimulation();
      }
      window.open('battle_log.html', '_blank');
    });

    dom.presetLoad?.addEventListener('click', () => {
      const name = dom.presetSelect.value;
      if (name) loadPreset(name);
    });

    dom.exportBoard?.addEventListener('click', exportBoard);

    dom.copyButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const targetId = btn.getAttribute('data-copy-target');
        const target = document.getElementById(targetId);
        if (!target) return;
        navigator.clipboard?.writeText(target.textContent || '');
        btn.textContent = '已复制';
        setTimeout(() => { btn.textContent = '复制ID'; }, 1000);
      });
    });

    dom.detailVerbose?.addEventListener('change', () => {
      updateDetail(Model.getSlot(boardState, selectedSlotId));
    });

    dom.compareMode?.addEventListener('change', () => {
      compareEnabled = !!dom.compareMode.checked;
      compareSkillId = compareEnabled ? compareSkillId : null;
      compareSkillGua = compareEnabled ? compareSkillGua : null;
      if (dom.compareHint) {
        dom.compareHint.classList.toggle('hidden', !compareEnabled);
        dom.compareHint.textContent = compareEnabled
          ? '对比模式：点击任意技能槽后，悬停其它卦位即可查看该技能在不同卦位的效果。'
          : '';
      }
      hideCompareTooltip();
      refreshBoard();
    });

    dom.container.addEventListener('mousemove', (evt) => {
      if (!compareEnabled || !compareSkillId) {
        hideCompareTooltip();
        lastCompareSlotId = null;
        return;
      }
      const slotEl = evt.target.closest('[data-slot-id]');
      if (!slotEl) {
        hideCompareTooltip();
        lastCompareSlotId = null;
        return;
      }
      const slotId = slotEl.getAttribute('data-slot-id');
      const slot = Model.getSlot(boardState, slotId);
      if (!slot || slot.kind !== Model.SLOT_KIND.SKILL) {
        hideCompareTooltip();
        lastCompareSlotId = null;
        return;
      }
      if (slotId !== lastCompareSlotId) {
        lastCompareSlotId = slotId;
      }
      const html = compareSummary(compareSkillId, slot.gua);
      showCompareTooltip(html, evt);
    });

    dom.container.addEventListener('mouseleave', () => {
      hideCompareTooltip();
      lastCompareSlotId = null;
    });

    window.addEventListener('keydown', (evt) => {
      if (evt.key === 'Escape') {
        focusId = null;
        refreshBoard();
      }
    });
  }

  function initPresets() {
    presetFiles = ['preset_1_reaction_loop', 'preset_2_relay_chain', 'preset_3_sustain_steady'];
    if (dom.presetSelect) {
      dom.presetSelect.innerHTML = presetFiles.map((p) => `<option value="${p}">${p}</option>`).join('');
    }
  }

  async function init() {
    if (window.SkillLoader?.loadCatalog) {
      try {
        await window.SkillLoader.loadCatalog();
      } catch (err) {
        console.warn('技能库加载失败，将使用现有配置。', err);
      }
    }
    boardState = Model.buildBoardState(Model.buildDefaultConfig());
    issues = Model.validateBuild(boardState);
    updateIssuePanel();
    refreshBoard();
    selectedSlotId = boardState.slots[0]?.id || null;
    updateItemSelect(Model.getSlot(boardState, selectedSlotId));
    updateDetail(Model.getSlot(boardState, selectedSlotId));
    initPresets();
    await loadBosses();
    attachEvents();
    if (dom.compareHint) dom.compareHint.classList.add('hidden');
  }

  init();
})();
