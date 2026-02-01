const dom = {
  reloadSnapshot: document.getElementById('reload-snapshot'),
  snapshotMeta: document.getElementById('snapshot-meta'),
  charMain: document.getElementById('char-main'),
  charBreakdown: document.getElementById('char-breakdown'),
  slotDetailList: document.getElementById('slot-detail-list'),
  bossSelect: document.getElementById('boss-select'),
  bossDesc: document.getElementById('boss-desc'),
  simulateBtn: document.getElementById('simulate-btn'),
  bossSuiteBtn: document.getElementById('boss-suite-btn'),
  bossSuiteReport: document.getElementById('boss-suite-report'),
  simWin: document.getElementById('sim-win'),
  simTtk: document.getElementById('sim-ttk'),
  simSurvive: document.getElementById('sim-survive'),
  logTimeline: document.getElementById('log-timeline'),
  logEvents: document.getElementById('log-events'),
  logLevel: document.getElementById('log-level'),
  logLimit: document.getElementById('log-limit'),
  bdGuide: document.getElementById('bd-guide'),
  realmGuide: document.getElementById('realm-guide'),
  realmEffects: document.getElementById('realm-effects'),
};

let snapshot = null;
let evalResult = null;
let bossProfiles = [];

function readSnapshot() {
  try {
    const raw = localStorage.getItem('bd_snapshot');
    if (raw) snapshot = JSON.parse(raw);
    const evalRaw = localStorage.getItem('bd_eval');
    if (evalRaw) evalResult = JSON.parse(evalRaw);
  } catch (err) {
    console.warn('[combat] snapshot parse failed', err);
  }
}

function renderSnapshotMeta() {
  if (!dom.snapshotMeta) return;
  if (!snapshot || !evalResult) {
    dom.snapshotMeta.textContent = '未加载，请在棋盘页面点击 Open Combat Panel。';
    return;
  }
  const time = snapshot.saved_at || '-';
  dom.snapshotMeta.textContent = `境界 ${snapshot.realm} · 灵根 ${snapshot.linggen} · 保存 ${time}`;
}

function renderCharacterPanel() {
  if (!evalResult) return;
  const totals = evalResult.totals || {};
  const domElem = evalResult.dominantElement || '-';
  const energized = Array.isArray(evalResult.energizedSlots) ? evalResult.energizedSlots.length : 0;

  if (dom.charMain) {
    dom.charMain.innerHTML = [
      `DPS <span>${Math.round(totals.dps || 0)}</span>`,
      `EHP <span>${Math.round(totals.ehp || 0)}</span>`,
      `续航 <span>${Math.round(totals.sustain || 0)}</span>`,
      `稳定 <span>${Math.round(totals.stability || 0)}</span>`,
      `主导元素 <span>${domElem}</span>`,
      `通气槽位 <span>${energized}</span>`,
    ].map((line) => `<div>${line}</div>`).join('');
  }

  if (dom.charBreakdown) {
    const byType = { skill: { dps: 0, ehp: 0, sustain: 0, stability: 0, count: 0 }, mod: { dps: 0, ehp: 0, sustain: 0, stability: 0, count: 0 }, stat: { dps: 0, ehp: 0, sustain: 0, stability: 0, count: 0 }, normal: { dps: 0, ehp: 0, sustain: 0, stability: 0, count: 0 } };
    const slotEffects = evalResult.slotEffects || {};
    Object.values(slotEffects).forEach((info) => {
      const type = info.slot_type || 'normal';
      const eff = info.effect || {};
      if (!byType[type]) byType[type] = { dps: 0, ehp: 0, sustain: 0, stability: 0, count: 0 };
      byType[type].dps += eff.dps || 0;
      byType[type].ehp += eff.ehp || 0;
      byType[type].sustain += eff.sustain || 0;
      byType[type].stability += eff.stability || 0;
      byType[type].count += 1;
    });
    const base = snapshot?.char || {};
    const baseLines = [
      `基础属性：atk ${base.atk ?? '-'} def ${base.def ?? '-'} hp ${base.hp ?? '-'} regen ${base.regen ?? '-'}`,
      `派生上限：并行回路 ${base.max_parallel_loops ?? '-'} | 边负载 ${base.max_edge_load ?? '-'} | 反噬抗性 ${base.backlash_resist ?? '-'}`,
    ];
    dom.charBreakdown.innerHTML = baseLines.concat(Object.entries(byType).map(([k, v]) => (
      `${k.toUpperCase()}(${v.count}) · DPS ${v.dps.toFixed(1)} / EHP ${v.ehp.toFixed(1)} / 续航 ${v.sustain.toFixed(1)} / 稳定 ${v.stability.toFixed(1)}`
    ))).map((line) => `<div>${line}</div>`).join('');
  }

  if (dom.slotDetailList) {
    const lines = [];
    const slotEffects = evalResult.slotEffects || {};
    Object.entries(slotEffects).forEach(([slotId, info]) => {
      const eff = info.effect || {};
      lines.push(`${slotId} | ${info.stone || '-'} | ${info.slot_type || '-'} | ${info.trigram || '-'} | dps ${eff.dps || 0} ehp ${eff.ehp || 0} sustain ${eff.sustain || 0} stability ${eff.stability || 0}`);
    });
    dom.slotDetailList.textContent = lines.join('\n');
  }
}

function loadBossProfiles() {
  bossProfiles = window.BossProfiles || [];
  if (!dom.bossSelect) return;
  dom.bossSelect.innerHTML = bossProfiles.map((b) => `<option value="${b.id}">${b.name}</option>`).join('');
  updateBossDesc();
}

function selectedBossProfile() {
  if (!dom.bossSelect) return bossProfiles[0];
  const id = dom.bossSelect.value;
  return bossProfiles.find((b) => b.id === id) || bossProfiles[0];
}

function updateBossDesc() {
  if (!dom.bossDesc) return;
  const boss = selectedBossProfile();
  if (!boss) {
    dom.bossDesc.textContent = '-';
    return;
  }
  dom.bossDesc.textContent = `${boss.realm} · ${boss.element} · HP ${boss.hp} · DPS ${boss.dps} · 爆发 ${boss.spike}`;
}

function simulateCombat() {
  if (!window.CircuitCore?.simulateCombat) return;
  if (!evalResult) return;
  const boss = selectedBossProfile();
  const detailLevel = dom.logLevel?.value || 'events';
  const maxEventLines = parseInt(dom.logLimit?.value || '2000', 10);
  const result = window.CircuitCore.simulateCombat(evalResult, boss, {
    detailLevel,
    maxEventLines,
    slotEffects: evalResult.slotEffects,
    loopInfo: evalResult.circuits,
  });
  dom.simWin.textContent = result.win ? '胜' : '败';
  dom.simTtk.textContent = result.time_to_kill;
  dom.simSurvive.textContent = result.time_survived;
  dom.logTimeline.textContent = (result.timeline_logs || []).join('\n');
  const events = result.event_logs || [];
  if (!result.win && result.failure_reason) {
    events.unshift(`0.0s | 失败归因 | ${result.failure_reason}`);
  }
  dom.logEvents.textContent = events.join('\n');
}

function runBossSuite() {
  if (!window.CircuitCore?.simulateCombat) return;
  if (!evalResult) return;
  const lines = [];
  bossProfiles.forEach((boss) => {
    const result = window.CircuitCore.simulateCombat(evalResult, boss, { detailLevel: 'summary' });
    const winLabel = result.win ? '胜' : '败';
    lines.push(`${boss.name}(${boss.realm}) | ${winLabel} | 击杀 ${result.time_to_kill}s | 存活 ${result.time_survived}s`);
  });
  dom.bossSuiteReport.textContent = lines.join('\n');
}

async function loadGuides() {
  try {
    const res = await fetch(`bd_guide.json?t=${Date.now()}`);
    const data = await res.json();
    dom.bdGuide.innerHTML = (data.bds || []).map((bd) => (
      `<div><strong>${bd.name}</strong> (${bd.realm})<br/>思路：${bd.idea}<br/>功法：${bd.gongfa.join(' / ')}<br/>关键词：${bd.keys.join(', ')}<br/>备注：${bd.notes}</div>`
    )).join('<hr/>');
  } catch (err) {
    dom.bdGuide.textContent = 'BD说明加载失败。';
  }

  try {
    const res = await fetch(`realm_guide.json?t=${Date.now()}`);
    const data = await res.json();
    dom.realmGuide.innerHTML = (data.realms || []).map((r) => (
      `<div><strong>${r.name}</strong>：${r.diff}</div>`
    )).join('');
  } catch (err) {
    dom.realmGuide.textContent = '境界说明加载失败。';
  }

  try {
    const res = await fetch(`board_config.json?t=${Date.now()}`);
    const data = await res.json();
    const realm = snapshot?.realm;
    const features = data?.realm_rules?.[realm]?.features || {};
    dom.realmEffects.innerHTML = [
      `<div>境界：${realm || '-'}</div>`,
      `<div>跨环连接：${features.allow_cross_ring ? '允许' : '禁止'}</div>`,
      `<div>邻接通道：${features.cross_count ?? '-'}</div>`,
      `<div>并行回路上限：${features.max_parallel_loops ?? '-'}</div>`,
      `<div>反噬风险：${features.backlash_risk ?? 0}</div>`,
    ].join('');
  } catch (err) {
    if (dom.realmEffects) dom.realmEffects.textContent = '境界效果加载失败。';
  }
}

function bindEvents() {
  dom.reloadSnapshot?.addEventListener('click', () => {
    readSnapshot();
    renderSnapshotMeta();
    renderCharacterPanel();
  });
  dom.bossSelect?.addEventListener('change', () => {
    updateBossDesc();
  });
  dom.simulateBtn?.addEventListener('click', () => {
    simulateCombat();
  });
  dom.bossSuiteBtn?.addEventListener('click', () => {
    runBossSuite();
  });
}

function init() {
  readSnapshot();
  renderSnapshotMeta();
  renderCharacterPanel();
  loadBossProfiles();
  loadGuides();
  bindEvents();
}

init();
