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
  };

  let boardState = null;
  let presetFiles = [];
  let selectedSlotId = null;
  let issues = [];
  let focusId = null;
  let bossProfiles = [];
  let selectedBossId = null;

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
    dom.container.innerHTML = Render.renderBoard(boardState, selectedSlotId, focusId);
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
    const result = Model.simulateBuild(boardState, { maxTicks: 20, tickSeconds: Model.TICK_SECONDS });
    if (!result) return;
    const metrics = result.metrics || {};
    dom.metrics.casts.textContent = Render.formatCasts(metrics.casts_per_skill || {});
    dom.metrics.reactions.textContent = Render.formatReactions(metrics.reaction_counts || {});
    dom.metrics.downtime.textContent = metrics.downtime_ticks ?? '-';
    dom.metrics.sustain.textContent = metrics.sustain_total ?? '-';
    if (dom.devLog) dom.devLog.textContent = result.logs?.join('\n') || '';

    const boss = bossProfiles.find((b) => b.id === selectedBossId) || bossProfiles[0] || null;
    const fight = Model.simulateBoss(result, boss);
    if (dom.bossDetail) dom.bossDetail.textContent = formatBossSummary(boss, fight);

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
        events: result.events,
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
    const res = await fetch(`./configs/tiandao/${name}.json?t=${Date.now()}`);
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
      const res = await fetch('./configs/tiandao/bosses.json?t=' + Date.now());
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
  }

  init();
})();
