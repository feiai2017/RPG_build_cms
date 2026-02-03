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
  detail: {
    name: document.getElementById('detail-name'),
    element: document.getElementById('detail-element'),
    type: document.getElementById('detail-type'),
    trigram: document.getElementById('detail-trigram'),
    component: document.getElementById('detail-component'),
    effect: document.getElementById('detail-effect'),
  },
  metrics: {
    casts: document.getElementById('metric-casts'),
    reactions: document.getElementById('metric-reactions'),
    downtime: document.getElementById('metric-downtime'),
    sustain: document.getElementById('metric-sustain'),
  },
  devLog: document.getElementById('dev-log-text'),
};

const GUA_ORDER = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
const GUA_INFO = {
  '乾': { element: '金', verb: '贯', symbol: '☰' },
  '兑': { element: '金', verb: '回', symbol: '☱' },
  '离': { element: '火', verb: '燃', symbol: '☲' },
  '震': { element: '木', verb: '连', symbol: '☳' },
  '巽': { element: '木', verb: '散', symbol: '☴' },
  '坎': { element: '水', verb: '控', symbol: '☵' },
  '艮': { element: '土', verb: '镇', symbol: '☶' },
  '坤': { element: '土', verb: '护', symbol: '☷' },
};
const WUXING_COLORS = {
  金: '#E6E6E6',
  木: '#39D98A',
  水: '#3AA0FF',
  火: '#FF4D4D',
  土: '#FFD166',
};
const EDGE_ENABLED_CAP = 3;
const PER_SKILL_EDGE_CAP = 2;

const SLOT_KIND = {
  SKILL: 'skill',
  FORM: 'form',
  LOOP: 'loop',
  EDGE: 'edge',
};

const ITEM_CATEGORY = {
  SKILL: 'SKILL',
  FORM: 'FORM',
  LOOP: 'LOOP',
  EDGE: 'EDGE',
};

const SKILLS = [
  { id: 'skill_qian_pierce', name: '贯金斩', gua: '乾', kind: 'output', element: '金', desc: '单体穿透' },
  { id: 'skill_dui_echo', name: '回音刃', gua: '兑', kind: 'output', element: '金', desc: '连击回荡' },
  { id: 'skill_li_flare', name: '燃光爆', gua: '离', kind: 'output', element: '火', desc: '爆发焰击' },
  { id: 'skill_zhen_chain', name: '连木冲', gua: '震', kind: 'output', element: '木', desc: '连锁突刺' },
  { id: 'skill_kan_tide', name: '控水潮', gua: '坎', kind: 'output', element: '水', desc: '水势压制' },
  { id: 'skill_xun_guard', name: '散影护', gua: '巽', kind: 'support', element: '木', desc: '护盾辅助' },
  { id: 'skill_gen_shell', name: '镇岳盾', gua: '艮', kind: 'support', element: '土', desc: '高护持' },
  { id: 'skill_kun_reforge', name: '护体阵', gua: '坤', kind: 'support', element: '土', desc: '持续守护' },
];

const FORM_RUNES = [
  { id: 'spread', name: '散射', desc: '多发散射' },
  { id: 'aoe', name: '范围', desc: '范围冲击' },
  { id: 'chain', name: '弹射', desc: '弹射连击' },
  { id: 'channel', name: '持续', desc: '持续施放' },
  { id: 'melee', name: '近战', desc: '高倍率近战' },
  { id: 'mark', name: '印记', desc: '强化印记' },
];

const LOOP_RUNES = [
  { id: 'cd_down', name: '降冷', desc: '缩短冷却' },
  { id: 'charge', name: '充能', desc: '额外充能' },
  { id: 'auto_recast', name: '复诵', desc: '延迟复施' },
  { id: 'cond_accel', name: '条件加速', desc: '印记加速' },
  { id: 'hit_energy', name: '命中回能', desc: '命中回能' },
  { id: 'crit_energy', name: '暴击回能', desc: '暴击回能' },
];

const EDGE_RUNES = [
  { id: 'RELAY', name: '接力', desc: '延迟接力施放' },
  { id: 'CD_ROUTER', name: '减冷路由', desc: '命中减冷' },
  { id: 'REACT_DETONATOR', name: '反应引爆', desc: '强制反应' },
  { id: 'SUSTAIN_LINK', name: '续航纽带', desc: '伤害转续航' },
];

const ITEMS = [
  ...SKILLS.map((s) => ({ ...s, category: ITEM_CATEGORY.SKILL })),
  ...FORM_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.FORM })),
  ...LOOP_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.LOOP })),
  ...EDGE_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.EDGE })),
];

const SLOT_ACCEPTS = {
  [SLOT_KIND.SKILL]: [ITEM_CATEGORY.SKILL],
  [SLOT_KIND.FORM]: [ITEM_CATEGORY.FORM],
  [SLOT_KIND.LOOP]: [ITEM_CATEGORY.LOOP],
  [SLOT_KIND.EDGE]: [ITEM_CATEGORY.EDGE],
};

const VISUAL = {
  size: 880,
  skillR: 190,
  runeR: 140,
  edgeR: 240,
  outerLabelR: 320,
};

let boardState = null;
let presetFiles = [];
let selectedSlotId = null;
let issues = [];

function canonicalEdgeKey(a, b) {
  const ai = GUA_ORDER.indexOf(a);
  const bi = GUA_ORDER.indexOf(b);
  return ai <= bi ? `${a}|${b}` : `${b}|${a}`;
}

function nextGua(gua) {
  const idx = GUA_ORDER.indexOf(gua);
  return GUA_ORDER[(idx + 1) % GUA_ORDER.length];
}

function buildDefaultConfig() {
  const skills_by_gua = {};
  SKILLS.forEach((skill) => {
    skills_by_gua[skill.gua] = skill.id;
  });
  const private_runes = {};
  GUA_ORDER.forEach((gua) => {
    private_runes[gua] = { form: null, loop: null };
  });
  return { name: 'default', skills_by_gua, private_runes, edge_runes: {} };
}

function buildBoardState(preset) {
  const cfg = preset || buildDefaultConfig();
  const slots = [];
  const cx = VISUAL.size / 2;
  const cy = VISUAL.size / 2;

  GUA_ORDER.forEach((gua, idx) => {
    const theta = (idx / GUA_ORDER.length) * Math.PI * 2 - Math.PI / 2;
    const info = GUA_INFO[gua];

    const skillSlot = {
      id: `skill_${gua}`,
      kind: SLOT_KIND.SKILL,
      gua,
      angle: theta,
      r: VISUAL.skillR,
      x: cx + Math.cos(theta) * VISUAL.skillR,
      y: cy + Math.sin(theta) * VISUAL.skillR,
      item_id: cfg.skills_by_gua?.[gua] || null,
      element: info.element,
    };
    slots.push(skillSlot);

    const formTheta = theta - Math.PI / 10;
    const loopTheta = theta + Math.PI / 10;
    slots.push({
      id: `form_${gua}`,
      kind: SLOT_KIND.FORM,
      gua,
      angle: formTheta,
      r: VISUAL.runeR,
      x: cx + Math.cos(formTheta) * VISUAL.runeR,
      y: cy + Math.sin(formTheta) * VISUAL.runeR,
      item_id: cfg.private_runes?.[gua]?.form || null,
      element: info.element,
    });
    slots.push({
      id: `loop_${gua}`,
      kind: SLOT_KIND.LOOP,
      gua,
      angle: loopTheta,
      r: VISUAL.runeR,
      x: cx + Math.cos(loopTheta) * VISUAL.runeR,
      y: cy + Math.sin(loopTheta) * VISUAL.runeR,
      item_id: cfg.private_runes?.[gua]?.loop || null,
      element: info.element,
    });

    const edgeGua = nextGua(gua);
    const edgeKey = canonicalEdgeKey(gua, edgeGua);
    const midTheta = (theta + ((idx + 1) / GUA_ORDER.length) * Math.PI * 2 - Math.PI / 2) / 2;
    slots.push({
      id: `edge_${edgeKey}`,
      kind: SLOT_KIND.EDGE,
      gua: edgeKey,
      angle: midTheta,
      r: VISUAL.edgeR,
      x: cx + Math.cos(midTheta) * VISUAL.edgeR,
      y: cy + Math.sin(midTheta) * VISUAL.edgeR,
      item_id: cfg.edge_runes?.[edgeKey] || null,
      element: info.element,
    });
  });

  boardState = {
    build: JSON.parse(JSON.stringify(cfg)),
    slots,
  };
}

function validateBuild() {
  const issuesOut = [];
  const edgeRunes = boardState.build.edge_runes || {};
  const enabledEdges = Object.entries(edgeRunes).filter(([, v]) => v);
  if (enabledEdges.length > EDGE_ENABLED_CAP) {
    issuesOut.push({ id: 'edge_cap', message: `联结槽启用超过上限（${enabledEdges.length}/${EDGE_ENABLED_CAP}）` });
  }
  const perSkillEdges = {};
  enabledEdges.forEach(([key]) => {
    const [a, b] = key.split('|');
    perSkillEdges[a] = (perSkillEdges[a] || 0) + 1;
    perSkillEdges[b] = (perSkillEdges[b] || 0) + 1;
    if (!boardState.build.skills_by_gua?.[a] || !boardState.build.skills_by_gua?.[b]) {
      issuesOut.push({ id: `edge_skill_${key}`, message: `联结 ${key} 需要两侧技能` });
    }
  });
  Object.entries(perSkillEdges).forEach(([gua, count]) => {
    if (count > PER_SKILL_EDGE_CAP) {
      issuesOut.push({ id: `skill_edge_${gua}`, message: `${gua} 参与联结超过上限（${count}/${PER_SKILL_EDGE_CAP}）` });
    }
  });
  issues = issuesOut;
  return issuesOut;
}

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

function renderBoard() {
  const size = VISUAL.size;
  const cx = size / 2;
  const cy = size / 2;

  let svg = `<svg class="board" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">`;
  svg += '<defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur" /><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>';

  // sectors
  const sectorAngle = (Math.PI * 2) / GUA_ORDER.length;
  GUA_ORDER.forEach((gua, idx) => {
    const start = idx * sectorAngle - Math.PI / 2;
    const end = start + sectorAngle;
    const r = 300;
    const x1 = cx + Math.cos(start) * r;
    const y1 = cy + Math.sin(start) * r;
    const x2 = cx + Math.cos(end) * r;
    const y2 = cy + Math.sin(end) * r;
    const large = sectorAngle > Math.PI ? 1 : 0;
    svg += `<path d="M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z" fill="rgba(120,140,160,0.08)" stroke="rgba(140,170,200,0.35)" stroke-width="1" />`;
  });

  // outer labels
  GUA_ORDER.forEach((gua, idx) => {
    const theta = (idx / GUA_ORDER.length) * Math.PI * 2 - Math.PI / 2;
    const x = cx + Math.cos(theta) * VISUAL.outerLabelR;
    const y = cy + Math.sin(theta) * VISUAL.outerLabelR;
    const info = GUA_INFO[gua];
    svg += `<text x="${x}" y="${y - 6}" text-anchor="middle" font-size="18" fill="rgba(230,240,250,0.95)" stroke="rgba(6,8,12,0.7)" stroke-width="3" paint-order="stroke">${info.symbol}</text>`;
    svg += `<text x="${x}" y="${y + 12}" text-anchor="middle" font-size="13" fill="rgba(220,232,244,0.9)" stroke="rgba(6,8,12,0.7)" stroke-width="3" paint-order="stroke">${gua}</text>`;
  });

  // edge lines
  const edgeRunes = boardState.build.edge_runes || {};
  Object.entries(edgeRunes).forEach(([key, rune]) => {
    if (!rune) return;
    const [a, b] = key.split('|');
    const slotA = boardState.slots.find((s) => s.kind === SLOT_KIND.SKILL && s.gua === a);
    const slotB = boardState.slots.find((s) => s.kind === SLOT_KIND.SKILL && s.gua === b);
    if (!slotA || !slotB) return;
    svg += `<line x1="${slotA.x}" y1="${slotA.y}" x2="${slotB.x}" y2="${slotB.y}" stroke="rgba(120,200,255,0.65)" stroke-width="3" />`;
  });

  // slots
  boardState.slots.forEach((slot) => {
    const fillColor = slot.item_id ? WUXING_COLORS[slot.element] : 'rgba(20,26,32,0.5)';
    const stroke = slot.kind === SLOT_KIND.SKILL ? 'rgba(180,220,255,0.9)' : 'rgba(200,200,210,0.7)';
    const size = slot.kind === SLOT_KIND.SKILL ? 14 : slot.kind === SLOT_KIND.EDGE ? 8 : 10;

    if (slot.kind === SLOT_KIND.SKILL) {
      const r = size;
      const points = [];
      for (let i = 0; i < 6; i += 1) {
        const angle = Math.PI / 3 * i + Math.PI / 6;
        points.push(`${slot.x + Math.cos(angle) * r},${slot.y + Math.sin(angle) * r}`);
      }
      svg += `<polygon data-slot-id="${slot.id}" points="${points.join(' ')}" fill="${fillColor}" stroke="${stroke}" stroke-width="2" />`;
    } else if (slot.kind === SLOT_KIND.EDGE) {
      const side = size * 1.4;
      svg += `<rect data-slot-id="${slot.id}" x="${slot.x - side / 2}" y="${slot.y - side / 2}" width="${side}" height="${side}" rx="4" fill="${fillColor}" stroke="${stroke}" stroke-width="1.6" />`;
    } else if (slot.kind === SLOT_KIND.LOOP) {
      const r = size;
      const points = `${slot.x},${slot.y - r} ${slot.x + r},${slot.y} ${slot.x},${slot.y + r} ${slot.x - r},${slot.y}`;
      svg += `<polygon data-slot-id="${slot.id}" points="${points}" fill="${fillColor}" stroke="${stroke}" stroke-width="1.6" />`;
    } else {
      svg += `<circle data-slot-id="${slot.id}" cx="${slot.x}" cy="${slot.y}" r="${size}" fill="${fillColor}" stroke="${stroke}" stroke-width="1.6" />`;
    }

    const label = slot.kind === SLOT_KIND.SKILL ? GUA_INFO[slot.gua].verb : slot.kind === SLOT_KIND.FORM ? 'F' : slot.kind === SLOT_KIND.LOOP ? 'L' : '联';
    svg += `<text x="${slot.x}" y="${slot.y + 4}" text-anchor="middle" font-size="10" fill="rgba(240,244,250,0.9)" font-weight="600">${label}</text>`;

    if (slot.id === selectedSlotId) {
      svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 8}" fill="none" stroke="rgba(255,255,255,0.8)" stroke-width="1.5" />`;
    }
  });

  svg += '</svg>';
  dom.container.innerHTML = svg;
}

function getSlot(slotId) {
  return boardState.slots.find((s) => s.id === slotId);
}

function updateItemSelect(slot) {
  if (!dom.itemSelect || !slot) return;
  const accepts = SLOT_ACCEPTS[slot.kind] || [];
  const options = ITEMS.filter((it) => accepts.includes(it.category));
  dom.itemSelect.innerHTML = options.map((it) => `<option value="${it.id}">${it.name}</option>`).join('');
  dom.itemSelect.value = slot.item_id || options[0]?.id || '';
}

function updateDetail(slot) {
  if (!slot) return;
  const info = GUA_INFO[slot.gua] || { element: '-', verb: '-' };
  const item = ITEMS.find((it) => it.id === slot.item_id);
  dom.detail.name.textContent = item?.name || slot.id;
  dom.detail.element.textContent = info.element;
  dom.detail.type.textContent = slot.kind;
  dom.detail.trigram.textContent = `${slot.gua} · ${info.verb}`;
  dom.detail.component.textContent = item?.category || '-';
  dom.detail.effect.textContent = item?.desc || '空槽位';
}

function applyItem(slot, itemId) {
  const item = ITEMS.find((it) => it.id === itemId);
  if (!slot || !item) return;
  if (!SLOT_ACCEPTS[slot.kind]?.includes(item.category)) return;
  slot.item_id = item.id;
  const gua = slot.gua;
  if (slot.kind === SLOT_KIND.SKILL) {
    boardState.build.skills_by_gua[gua] = item.id;
  } else if (slot.kind === SLOT_KIND.FORM) {
    boardState.build.private_runes[gua] = boardState.build.private_runes[gua] || { form: null, loop: null };
    boardState.build.private_runes[gua].form = item.id;
  } else if (slot.kind === SLOT_KIND.LOOP) {
    boardState.build.private_runes[gua] = boardState.build.private_runes[gua] || { form: null, loop: null };
    boardState.build.private_runes[gua].loop = item.id;
  } else if (slot.kind === SLOT_KIND.EDGE) {
    boardState.build.edge_runes[slot.gua] = item.id;
  }
  validateBuild();
  updateIssuePanel();
  renderBoard();
  updateDetail(slot);
}

function clearSlot(slot) {
  if (!slot) return;
  if (slot.kind === SLOT_KIND.SKILL) {
    boardState.build.skills_by_gua[slot.gua] = null;
  } else if (slot.kind === SLOT_KIND.FORM) {
    boardState.build.private_runes[slot.gua].form = null;
  } else if (slot.kind === SLOT_KIND.LOOP) {
    boardState.build.private_runes[slot.gua].loop = null;
  } else if (slot.kind === SLOT_KIND.EDGE) {
    delete boardState.build.edge_runes[slot.gua];
  }
  slot.item_id = null;
  validateBuild();
  updateIssuePanel();
  renderBoard();
  updateDetail(slot);
}

function runSimulation() {
  if (issues.length) return;
  const result = window.BaguaSolver.simulateBuild(boardState.build, { maxTicks: 20, tickSeconds: 0.5 });
  const metrics = result.metrics || {};
  dom.metrics.casts.textContent = JSON.stringify(metrics.casts_per_skill || {});
  dom.metrics.reactions.textContent = JSON.stringify(metrics.reaction_counts || {});
  dom.metrics.downtime.textContent = metrics.downtime_ticks ?? '-';
  dom.metrics.sustain.textContent = metrics.sustain_total ?? '-';
  if (dom.devLog) dom.devLog.textContent = result.logs?.join('\n') || '';

  const payload = {
    bd: {
      name: boardState.build.name || 'custom',
      skills: boardState.build.skills_by_gua,
      runes: boardState.build.private_runes,
      edges: boardState.build.edge_runes,
    },
    result: {
      totals: result.totals,
      metrics: result.metrics,
    },
    fight: {
      events: result.events,
    },
  };
  localStorage.setItem('battle_log', JSON.stringify(payload));
}

async function loadPreset(name) {
  const res = await fetch(`./configs/tiandao/${name}.json?t=${Date.now()}`);
  const data = await res.json();
  buildBoardState(data);
  validateBuild();
  updateIssuePanel();
  renderBoard();
  selectedSlotId = boardState.slots[0]?.id || null;
  updateItemSelect(getSlot(selectedSlotId));
  updateDetail(getSlot(selectedSlotId));
}

function attachEvents() {
  dom.container.addEventListener('click', (evt) => {
    const slotEl = evt.target.closest('[data-slot-id]');
    if (!slotEl) return;
    selectedSlotId = slotEl.getAttribute('data-slot-id');
    const slot = getSlot(selectedSlotId);
    updateItemSelect(slot);
    updateDetail(slot);
    renderBoard();
  });

  dom.itemSelect?.addEventListener('change', () => {
    const slot = getSlot(selectedSlotId);
    if (!slot) return;
    applyItem(slot, dom.itemSelect.value);
  });

  dom.clearSlot?.addEventListener('click', () => {
    const slot = getSlot(selectedSlotId);
    clearSlot(slot);
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
}

function initPresets() {
  presetFiles = ['preset_1_reaction_loop', 'preset_2_relay_chain', 'preset_3_sustain_steady'];
  if (dom.presetSelect) {
    dom.presetSelect.innerHTML = presetFiles.map((p) => `<option value="${p}">${p}</option>`).join('');
  }
}

function init() {
  buildBoardState(buildDefaultConfig());
  validateBuild();
  updateIssuePanel();
  renderBoard();
  selectedSlotId = boardState.slots[0]?.id || null;
  updateItemSelect(getSlot(selectedSlotId));
  updateDetail(getSlot(selectedSlotId));
  initPresets();
  attachEvents();
}

init();
