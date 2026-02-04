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
const SOLVER_CATALOG = window.BaguaSolver || {};
const SKILL_LIBRARY = SOLVER_CATALOG.SKILL_LIBRARY || {};
const FORM_RUNES_LIB = SOLVER_CATALOG.FORM_RUNES || {};
const LOOP_RUNES_LIB = SOLVER_CATALOG.LOOP_RUNES || {};
const EDGE_RUNES_LIB = SOLVER_CATALOG.EDGE_RUNES || {};
const TICK_SECONDS = 0.5;
const WUXING_COLORS = {
  金: '#E6E6E6',
  木: '#39D98A',
  水: '#3AA0FF',
  火: '#FF4D4D',
  土: '#FFD166',
};
const EDGE_ENABLED_CAP = 3;
const PER_SKILL_EDGE_CAP = 2;
const SLOT_FILL = 'rgba(255,255,255,0.06)';
const SLOT_VISUAL = {
  skill: { size: 20, stroke: 2.8, label: 14 },
  form: { size: 10, stroke: 2.0, label: 9 },
  loop: { size: 11, stroke: 2.0, label: 9 },
  edge: { size: 14, stroke: 2.6, label: 10 },
  edgeEmpty: { size: 12, stroke: 1.6, label: 9 },
};
const SECTOR_ANGLE = (Math.PI * 2) / GUA_ORDER.length;
const START_ANGLE = -Math.PI / 2;
const CENTER_OFFSET = SECTOR_ANGLE / 2;

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

const SKILL_DESC = {
  skill_qian_pierce: '单体穿透',
  skill_dui_echo: '连击回荡',
  skill_li_flare: '爆发焰击',
  skill_zhen_chain: '连锁突刺',
  skill_kan_tide: '水势压制',
  skill_xun_guard: '护盾辅助',
  skill_gen_shell: '高护持',
  skill_kun_reforge: '持续守护',
};
const SKILLS = Object.values(SKILL_LIBRARY).map((skill) => ({
  ...skill,
  desc: SKILL_DESC[skill.id] || '',
}));

const TERM_GLOSSARY = {
  火印记: '火系印记。再次被非火元素命中时触发元素反应并消耗印记。',
  水印记: '水系印记。再次被非水元素命中时触发元素反应并消耗印记。',
  木印记: '木系印记。再次被非木元素命中时触发元素反应并消耗印记。',
  金印记: '金系印记。再次被非金元素命中时触发元素反应并消耗印记。',
  土印记: '土系印记。再次被非土元素命中时触发元素反应并消耗印记。',
};

const FORM_RUNES = Object.values(FORM_RUNES_LIB).map((r) => ({
  ...r,
  desc: r.desc || r.name,
}));

const LOOP_RUNES = Object.values(LOOP_RUNES_LIB).map((r) => ({
  ...r,
  desc: r.desc || r.name,
}));

const EDGE_RUNES = Object.values(EDGE_RUNES_LIB).map((r) => ({
  ...r,
  desc: r.desc || r.name,
}));

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
let focusId = null;

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
    const theta = START_ANGLE + idx * SECTOR_ANGLE + CENTER_OFFSET;
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

    const formTheta = theta - SECTOR_ANGLE * 0.18;
    const loopTheta = theta + SECTOR_ANGLE * 0.18;
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
    const edgeTheta = START_ANGLE + (idx + 1) * SECTOR_ANGLE;
    slots.push({
      id: `edge_${edgeKey}`,
      kind: SLOT_KIND.EDGE,
      gua: edgeKey,
      gua_a: gua,
      gua_b: edgeGua,
      angle: edgeTheta,
      r: VISUAL.edgeR,
      x: cx + Math.cos(edgeTheta) * VISUAL.edgeR,
      y: cy + Math.sin(edgeTheta) * VISUAL.edgeR,
      item_id: cfg.edge_runes?.[edgeKey] || null,
      element: info.element,
    });
  });

  boardState = {
    build: JSON.parse(JSON.stringify(cfg)),
    slots,
    layout: {
      size: VISUAL.size,
      center: { x: cx, y: cy },
      skillR: VISUAL.skillR,
      runeR: VISUAL.runeR,
      edgeR: VISUAL.edgeR,
      outerLabelR: VISUAL.outerLabelR,
      sectorAngle: SECTOR_ANGLE,
      startAngle: START_ANGLE,
      centerOffset: CENTER_OFFSET,
    },
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

function buildGodotPayload() {
  return {
    version: 1,
    gua_order: [...GUA_ORDER],
    gua_info: { ...GUA_INFO },
    catalog: {
      skills: { ...SKILL_LIBRARY },
      form_runes: { ...FORM_RUNES_LIB },
      loop_runes: { ...LOOP_RUNES_LIB },
      edge_runes: { ...EDGE_RUNES_LIB },
      tick_seconds: TICK_SECONDS,
    },
    layout: boardState.layout,
    slots: boardState.slots.map((slot) => ({
      id: slot.id,
      kind: slot.kind,
      gua: slot.gua,
      gua_a: slot.gua_a || null,
      gua_b: slot.gua_b || null,
      element: slot.element,
      angle: slot.angle,
      r: slot.r,
      x: slot.x,
      y: slot.y,
      item_id: slot.item_id || null,
      label: slot.kind === SLOT_KIND.SKILL ? GUA_INFO[slot.gua].verb : slot.kind === SLOT_KIND.FORM ? 'F' : slot.kind === SLOT_KIND.LOOP ? 'L' : '⛓',
    })),
    build: boardState.build,
  };
}

function persistGodotPayload() {
  const payload = buildGodotPayload();
  localStorage.setItem('tiandao_board', JSON.stringify(payload));
}

function getItemById(itemId) {
  if (!itemId) return null;
  return ITEMS.find((it) => it.id === itemId) || null;
}

function formatRune(prefix, item) {
  if (!item) return `${prefix}: 空`;
  return `${prefix}: ${item.name}（${item.desc}）`;
}

function formatSkillKind(kind) {
  return kind === 'support' ? '辅助技能' : '输出技能';
}

function formatSkillEffect(item) {
  if (!item) return '空槽位';
  const parts = [];
  if (item.desc) parts.push(item.desc);
  if (item.effect) parts.push(item.effect);
  return parts.length ? parts.join('；') : '空槽位';
}

function formatSkillDetail(item) {
  if (!item) return '空槽位';
  const skill = SKILL_LIBRARY[item.id] || item;
  const lines = [];
  if (skill.baseDamage != null) lines.push(`基础伤害:${skill.baseDamage}`);
  if (skill.kind === 'support' && skill.sustain != null) lines.push(`护持:${skill.sustain}`);
  if (skill.element) lines.push(`印记:${skill.element}印记`);
  if (skill.baseCd != null) lines.push(`冷却:${skill.baseCd}tick(${(skill.baseCd * TICK_SECONDS).toFixed(1)}s)`);
  return lines.join('，');
}

function computeSkillDetailText(skill, form, loop) {
  if (!skill) return '空槽位';
  const lines = [];
  const baseCd = Math.max(1, (skill.baseCd || 0) + (form?.cdAdd || 0) + (loop?.cdDelta || 0));
  const markTerm = skill.element ? `${skill.element}印记` : null;
  if (skill.kind === 'support') {
    const mult = form?.mult || 1;
    const sustain = (skill.sustain || 0) * mult;
    if (skill.sustain != null) lines.push(`护持:${sustain.toFixed(1)}`);
    if (form?.mult) lines.push(`形态倍率:${mult.toFixed(2)}x`);
    if (loop?.charges) lines.push(`充能:${loop.charges}`);
    if (loop?.recastDelay) lines.push(`复施:${loop.recastDelay}tick`);
    if (loop?.sustainOnHit) lines.push(`命中回能:+${loop.sustainOnHit}`);
    if (loop?.sustainOnCrit) lines.push(`暴击回能:+${loop.sustainOnCrit}`);
  } else {
    const hits = form?.hits || 1;
    const mult = form?.mult || 1;
    const perHit = (skill.baseDamage || 0) * mult;
    const total = perHit * hits;
    if (skill.baseDamage != null) lines.push(`基础伤害:${skill.baseDamage}`);
    lines.push(`多段:${hits} 每段:${perHit.toFixed(1)} 总计:${total.toFixed(1)}`);
    if (form?.mult) lines.push(`形态倍率:${mult.toFixed(2)}x`);
    if (form?.markBonus) lines.push(`印记强化:+${form.markBonus}`);
    if (markTerm) lines.push(`印记:${markTerm}`);
    if (loop?.charges) lines.push(`充能:${loop.charges}`);
    if (loop?.recastDelay) lines.push(`复施:${loop.recastDelay}tick`);
    if (loop?.accelOnMark) lines.push(`印记加速:-${loop.accelOnMark}tick`);
    if (loop?.sustainOnHit) lines.push(`命中回能:+${loop.sustainOnHit}`);
    if (loop?.sustainOnCrit) lines.push(`暴击回能:+${loop.sustainOnCrit}`);
  }
  lines.push(`冷却:${baseCd}tick(${(baseCd * TICK_SECONDS).toFixed(1)}s)`);
  return lines.join('\n');
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderWithGlossary(text) {
  if (!text) return '-';
  let html = escapeHtml(text).replace(/\n/g, '<br>');
  Object.entries(TERM_GLOSSARY).forEach(([term, tip]) => {
    const safeTerm = escapeHtml(term);
    const safeTip = escapeHtml(tip);
    html = html.split(safeTerm).join(`<span class="term" data-tip="${safeTip}">${safeTerm}</span>`);
  });
  return html;
}

let termTooltip = null;

function ensureTermTooltip() {
  if (termTooltip) return termTooltip;
  termTooltip = document.createElement('div');
  termTooltip.id = 'term-tooltip';
  termTooltip.style.display = 'none';
  document.body.appendChild(termTooltip);
  return termTooltip;
}

function showTermTooltip(text, evt) {
  const tip = ensureTermTooltip();
  tip.textContent = text;
  tip.style.display = 'block';
  moveTermTooltip(evt);
}

function moveTermTooltip(evt) {
  if (!termTooltip) return;
  const padding = 12;
  const maxX = window.innerWidth - termTooltip.offsetWidth - padding;
  const maxY = window.innerHeight - termTooltip.offsetHeight - padding;
  const x = Math.min(maxX, evt.clientX + 14);
  const y = Math.min(maxY, evt.clientY + 16);
  termTooltip.style.left = `${Math.max(padding, x)}px`;
  termTooltip.style.top = `${Math.max(padding, y)}px`;
}

function hideTermTooltip() {
  if (!termTooltip) return;
  termTooltip.style.display = 'none';
}

function bindGlossaryTooltips(root) {
  if (!root) return;
  root.querySelectorAll('.term').forEach((node) => {
    node.addEventListener('mouseenter', (evt) => showTermTooltip(node.dataset.tip, evt));
    node.addEventListener('mousemove', moveTermTooltip);
    node.addEventListener('mouseleave', hideTermTooltip);
  });
}

function computeRelatedIds(targetId) {
  if (!targetId) return null;
  const slot = getSlot(targetId);
  if (!slot) return null;
  const related = new Set([slot.id]);
  if (slot.kind === SLOT_KIND.SKILL) {
    const gua = slot.gua;
    const form = getSlot(`form_${gua}`);
    const loop = getSlot(`loop_${gua}`);
    if (form) related.add(form.id);
    if (loop) related.add(loop.id);
    const prev = GUA_ORDER[(GUA_ORDER.indexOf(gua) - 1 + GUA_ORDER.length) % GUA_ORDER.length];
    const next = nextGua(gua);
    const edgePrev = getSlot(`edge_${canonicalEdgeKey(prev, gua)}`);
    const edgeNext = getSlot(`edge_${canonicalEdgeKey(gua, next)}`);
    if (edgePrev && edgePrev.item_id) related.add(edgePrev.id);
    if (edgeNext && edgeNext.item_id) related.add(edgeNext.id);
  }
  if (slot.kind === SLOT_KIND.EDGE) {
    const a = slot.gua_a;
    const b = slot.gua_b;
    const skillA = getSlot(`skill_${a}`);
    const skillB = getSlot(`skill_${b}`);
    const formA = getSlot(`form_${a}`);
    const loopA = getSlot(`loop_${a}`);
    const formB = getSlot(`form_${b}`);
    const loopB = getSlot(`loop_${b}`);
    [skillA, skillB, formA, loopA, formB, loopB].forEach((s) => s && related.add(s.id));
  }
  return related;
}

function dimOpacity(slotId, focusSet) {
  if (!focusSet) return 1;
  return focusSet.has(slotId) ? 1 : 0.15;
}

function renderEdgeSocket(slot, focusSet) {
  const isActive = !!slot.item_id;
  const isFocused = !focusSet || focusSet.has(slot.id);
  const opacity = isFocused ? 1 : 0.15;
  const sizeCfg = isActive ? SLOT_VISUAL.edge : SLOT_VISUAL.edgeEmpty;
  const size = sizeCfg.size;
  const strokeW = sizeCfg.stroke;
  const aColor = WUXING_COLORS[GUA_INFO[slot.gua_a]?.element || '金'];
  const bColor = WUXING_COLORS[GUA_INFO[slot.gua_b]?.element || '金'];
  const r = size;
  const rInner = size * 0.68;
  const outerPoints = `${slot.x},${slot.y - r} ${slot.x + r},${slot.y} ${slot.x},${slot.y + r} ${slot.x - r},${slot.y}`;
  const innerPoints = `${slot.x},${slot.y - rInner} ${slot.x + rInner},${slot.y} ${slot.x},${slot.y + rInner} ${slot.x - rInner},${slot.y}`;
  const edgeItem = getItemById(slot.item_id);
  const title = edgeItem ? `联结槽：${edgeItem.name} - ${edgeItem.desc}` : '联结槽：空';
  let svg = '';
  svg += `<g data-slot-id="${slot.id}">`;
  svg += `<title>${title}</title>`;
  svg += `<polygon points="${outerPoints}" fill="${SLOT_FILL}" stroke="${aColor}" stroke-width="${strokeW}" opacity="${opacity}" />`;
  svg += `<polygon points="${innerPoints}" fill="none" stroke="${bColor}" stroke-width="${strokeW - 0.6}" opacity="${opacity}" />`;
  if (isActive) {
    svg += `<polygon points="${outerPoints}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1.4" opacity="${opacity}" />`;
    svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 6}" fill="none" stroke="rgba(140,220,255,0.35)" stroke-width="1.2" opacity="${opacity}" />`;
  }
  svg += `<text x="${slot.x}" y="${slot.y + 4}" text-anchor="middle" font-size="${SLOT_VISUAL.edge.label}" fill="rgba(230,240,250,0.95)" opacity="${opacity}">⛓</text>`;
  svg += `<circle data-slot-id="${slot.id}" cx="${slot.x}" cy="${slot.y}" r="${size + 10}" fill="transparent" stroke="none" pointer-events="all" />`;
  svg += `</g>`;
  return svg;
}

function renderBoard() {
  const size = VISUAL.size;
  const cx = size / 2;
  const cy = size / 2;
  const focusSet = computeRelatedIds(focusId);

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

  // outer labels (centered in each gua sector)
  GUA_ORDER.forEach((gua, idx) => {
    const theta = START_ANGLE + idx * SECTOR_ANGLE + CENTER_OFFSET;
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
    const edgeSlot = boardState.slots.find((s) => s.kind === SLOT_KIND.EDGE && s.gua === key);
    if (!slotA || !slotB) return;
    const lineOpacity = focusSet ? (focusSet.has(edgeSlot?.id) ? 0.5 : 0.12) : 0.45;
    svg += `<line x1="${slotA.x}" y1="${slotA.y}" x2="${slotB.x}" y2="${slotB.y}" stroke="rgba(120,200,255,${lineOpacity})" stroke-width="1.3" />`;
  });

  // slots
  boardState.slots.forEach((slot) => {
    const opacity = dimOpacity(slot.id, focusSet);
    const stroke = WUXING_COLORS[slot.element] || '#dfe8f2';

    if (slot.kind === SLOT_KIND.EDGE) {
      svg += renderEdgeSocket(slot, focusSet);
      return;
    }

    const sizeCfg = slot.kind === SLOT_KIND.SKILL ? SLOT_VISUAL.skill : slot.kind === SLOT_KIND.LOOP ? SLOT_VISUAL.loop : SLOT_VISUAL.form;
    const size = sizeCfg.size;
    const strokeWidth = sizeCfg.stroke;
    const slotItem = getItemById(slot.item_id);
    let title = '空槽位';
    if (slot.kind === SLOT_KIND.SKILL) {
      if (slotItem) {
        const baseSkill = SKILL_LIBRARY[slotItem.id] || slotItem;
        const runes = boardState.build.private_runes?.[slot.gua] || {};
        const form = FORM_RUNES_LIB[runes.form];
        const loop = LOOP_RUNES_LIB[runes.loop];
        const detailText = computeSkillDetailText(baseSkill, form, loop).replace(/\n/g, ' | ');
        title = `技能：${slotItem.name} | ${formatSkillKind(baseSkill.kind)} | 元素:${baseSkill.element} | ${detailText}`;
      } else {
        title = '技能槽：空';
      }
    } else if (slot.kind === SLOT_KIND.FORM) {
      title = slotItem ? `Form：${slotItem.name} - ${slotItem.desc}` : 'Form 槽：空';
    } else if (slot.kind === SLOT_KIND.LOOP) {
      title = slotItem ? `Loop：${slotItem.name} - ${slotItem.desc}` : 'Loop 槽：空';
    }

    svg += `<g data-slot-id="${slot.id}"><title>${title}</title>`;

    if (slot.kind === SLOT_KIND.SKILL) {
      const r = size;
      const points = [];
      for (let i = 0; i < 6; i += 1) {
        const angle = Math.PI / 3 * i + Math.PI / 6;
        points.push(`${slot.x + Math.cos(angle) * r},${slot.y + Math.sin(angle) * r}`);
      }
      svg += `<polygon points="${points.join(' ')}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
    } else if (slot.kind === SLOT_KIND.LOOP) {
      const r = size;
      const points = `${slot.x},${slot.y - r} ${slot.x + r},${slot.y} ${slot.x},${slot.y + r} ${slot.x - r},${slot.y}`;
      svg += `<polygon points="${points}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
    } else {
      svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
    }

    const label = slot.kind === SLOT_KIND.SKILL ? GUA_INFO[slot.gua].verb : slot.kind === SLOT_KIND.FORM ? 'F' : 'L';
    const labelSize = slot.kind === SLOT_KIND.SKILL ? SLOT_VISUAL.skill.label : SLOT_VISUAL.form.label;
    svg += `<text x="${slot.x}" y="${slot.y + 5}" text-anchor="middle" font-size="${labelSize}" fill="rgba(240,244,250,0.95)" font-weight="700" opacity="${opacity}" pointer-events="none">${label}</text>`;

    if (slot.id === selectedSlotId) {
      svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 8}" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.6" />`;
      svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 12}" fill="none" stroke="rgba(120,220,255,0.55)" stroke-width="1.2" />`;
    }
    svg += `<circle data-slot-id="${slot.id}" cx="${slot.x}" cy="${slot.y}" r="${size + 10}" fill="transparent" stroke="none" pointer-events="all" />`;
    svg += `</g>`;
  });

  svg += '</svg>';
  dom.container.innerHTML = svg;
  persistGodotPayload();
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
  const verbose = dom.detailVerbose?.checked;
  const info = GUA_INFO[slot.gua] || { element: '-', verb: '-' };
  const item = getItemById(slot.item_id);
  const friendly = item?.name ? `${info.verb}·${item.name}` : `${info.verb}·空槽`;
  dom.detail.name.textContent = friendly;
  dom.detail.element.textContent = info.element;
  dom.detail.type.textContent = slot.kind;
  dom.detail.trigram.textContent = `${slot.gua} · ${info.verb}`;
  if (slot.kind === SLOT_KIND.SKILL && item) {
    const baseSkill = SKILL_LIBRARY[item.id] || item;
    const runes = boardState.build.private_runes?.[slot.gua] || {};
    const form = FORM_RUNES_LIB[runes.form];
    const loop = LOOP_RUNES_LIB[runes.loop];
    dom.detail.component.textContent = verbose ? `${item.category} · ${formatSkillKind(baseSkill.kind)} · 元素:${baseSkill.element}` : `${item.category} · ${formatSkillKind(baseSkill.kind)}`;
    const detailText = verbose ? `${computeSkillDetailText(baseSkill, form, loop)}\nID:${item.id}` : formatSkillEffect(item);
    dom.detail.effect.innerHTML = renderWithGlossary(detailText);
  } else {
    dom.detail.component.textContent = item?.category || '-';
    dom.detail.effect.textContent = item?.desc || '空槽位';
  }
  if (dom.detail.id) dom.detail.id.textContent = slot.id;
  if (dom.detail.runes) {
    if (slot.kind === SLOT_KIND.SKILL) {
      const runes = boardState.build.private_runes?.[slot.gua] || { form: null, loop: null };
      const formItem = FORM_RUNES_LIB[runes.form] || getItemById(runes.form);
      const loopItem = LOOP_RUNES_LIB[runes.loop] || getItemById(runes.loop);
      dom.detail.runes.textContent = `${formatRune('F', formItem)} / ${formatRune('L', loopItem)}`;
    } else if (slot.kind === SLOT_KIND.FORM) {
      dom.detail.runes.textContent = formatRune('F', item);
    } else if (slot.kind === SLOT_KIND.LOOP) {
      dom.detail.runes.textContent = formatRune('L', item);
    } else {
      dom.detail.runes.textContent = '-';
    }
  }
  if (dom.detail.effect) {
    bindGlossaryTooltips(dom.detail.effect);
  }

  if (dom.detail.links) {
    if (slot.kind === SLOT_KIND.EDGE) {
      const rune = boardState.build.edge_runes?.[slot.gua] || '空';
      dom.detail.links.textContent = `${slot.gua_a} ↔ ${slot.gua_b} · ${rune}`;
    } else if (slot.kind === SLOT_KIND.SKILL) {
      const prev = GUA_ORDER[(GUA_ORDER.indexOf(slot.gua) - 1 + GUA_ORDER.length) % GUA_ORDER.length];
      const next = nextGua(slot.gua);
      const edges = [];
      const edgePrev = boardState.build.edge_runes?.[canonicalEdgeKey(prev, slot.gua)];
      const edgeNext = boardState.build.edge_runes?.[canonicalEdgeKey(slot.gua, next)];
      if (edgePrev) edges.push(`${prev}↔${slot.gua}:${edgePrev}`);
      if (edgeNext) edges.push(`${slot.gua}↔${next}:${edgeNext}`);
      dom.detail.links.textContent = edges.length ? edges.join(' | ') : '无联结';
    } else {
      dom.detail.links.textContent = '-';
    }
  }
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

function exportBoard() {
  const payload = buildGodotPayload();
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
    if (!slotEl) {
      focusId = null;
      renderBoard();
      return;
    }
    selectedSlotId = slotEl.getAttribute('data-slot-id');
    focusId = selectedSlotId;
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
    updateDetail(getSlot(selectedSlotId));
  });

  window.addEventListener('keydown', (evt) => {
    if (evt.key === 'Escape') {
      focusId = null;
      renderBoard();
    }
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
