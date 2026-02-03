const dom = {
  container: document.getElementById('canvas-container'),
  steps: Array.from(document.querySelectorAll('#steps-bar .step')),
  realmSelect: document.getElementById('realm-select'),
  linggenSelect: document.getElementById('linggen-select'),
  stoneSelect: document.getElementById('stone-select'),
  clearSlot: document.getElementById('clear-slot'),
  hudPower: document.getElementById('hud-power'),
  hudBandwidth: document.getElementById('hud-bandwidth'),
  hudCounts: document.getElementById('hud-counts'),
  hudBonus: document.getElementById('hud-bonus'),
  hudRealmBonus: document.getElementById('hud-realm-bonus'),
  toggleContrast: document.getElementById('toggle-contrast'),
  toggleBroken: document.getElementById('toggle-broken'),
  clearLit: document.getElementById('clear-lit'),
  cfgHash: document.getElementById('cfg-hash'),
  cfgVersion: document.getElementById('cfg-version'),
  cfgMtime: document.getElementById('cfg-mtime'),
  simulateBtn: document.getElementById('simulate-btn'),
  openLog: document.getElementById('open-log'),
  detail: {
    name: document.getElementById('detail-name'),
    element: document.getElementById('detail-element'),
    type: document.getElementById('detail-type'),
    trigram: document.getElementById('detail-trigram'),
    component: document.getElementById('detail-component'),
    effect: document.getElementById('detail-effect'),
    power: document.getElementById('detail-power'),
    reason: document.getElementById('detail-reason'),
  },
  sim: {
    dps: document.getElementById('sim-dps'),
    ehp: document.getElementById('sim-ehp'),
    sustain: document.getElementById('sim-sustain'),
    stability: document.getElementById('sim-stability'),
    win: document.getElementById('sim-win'),
    ttk: document.getElementById('sim-ttk'),
    survive: document.getElementById('sim-survive'),
    logs: document.getElementById('sim-logs'),
  },
  toggleSwitch: document.getElementById('toggle-switch'),
  stats: {
    atk: document.getElementById('stat-atk'),
    crit: document.getElementById('stat-crit'),
    hp: document.getElementById('stat-hp'),
    shield: document.getElementById('stat-shield'),
    mana: document.getElementById('stat-mana'),
    regen: document.getElementById('stat-regen'),
  },
  lineMode: document.getElementById('line-mode'),
  lineElement: document.getElementById('line-element'),
  resetZoom: document.getElementById('reset-zoom'),
  reconfig: {
    panel: document.getElementById('reconfig-panel'),
    node: document.getElementById('reconfig-node'),
    slot: document.getElementById('reconfig-slot'),
    apply: document.getElementById('reconfig-apply'),
  },
  devToggle: document.getElementById('dev-toggle'),
  devDrawer: document.getElementById('dev-drawer'),
  toggleSectors: document.getElementById('toggle-sectors'),
  toggleRings: document.getElementById('toggle-rings'),
  toggleDebug: document.getElementById('toggle-debug'),
  channelCount: document.getElementById('channel-count'),
  contactThreshold: document.getElementById('contact-threshold'),
  glowStrength: document.getElementById('glow-strength'),
  edgeStrength: document.getElementById('edge-strength'),
  sectorOpacity: document.getElementById('sector-opacity'),
  ringStrength: document.getElementById('ring-strength'),
  scale: document.getElementById('scale'),
  panel: {
    edges: document.getElementById('toggle-edges'),
    labels: document.getElementById('toggle-labels'),
    reload: document.getElementById('reload-config'),
    export: document.getElementById('export-current'),
    reset: document.getElementById('reset-session'),
    presetSelect: document.getElementById('preset-select'),
    presetLoad: document.getElementById('load-preset'),
  },
  tooltip: document.getElementById('tooltip'),
  debugOverlay: document.getElementById('debug-overlay'),
};

let boardData = null;
let cfgData = null;
let cfgHash = '-';
let cfgMtime = '-';
let boardState = null;
let nodeReason = new Map();
let presetFiles = [];
const runtime = {
  flash: null,
  lastActiveEdges: new Set(),
  needsRender: true,
  needsConnectivityUpdate: true,
  lastRender: 0,
  hoveredNodeId: null,
  selectedNodeId: null,
  fps: 0,
  frames: 0,
  lastFpsTime: performance.now(),
  debugLastUpdate: 0,
  lastConnectivityUpdate: 0,
  lastRingOptionsKey: '',
  lastDynamicEdges: new Set(),
  feedbackTimer: null,
  rejectedNodeId: null,
  rejectUntil: 0,
  evalResult: null,
  selectedStoneId: null,
  pathEdges: null,
  panning: false,
  panStart: null,
};

const TRIGRAM_SECTORS = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
const TRIGRAMS = TRIGRAM_SECTORS;
const DEFAULT_REALM = '金丹';
const WUXING_COLORS = {
  金: '#E6E6E6',
  木: '#39D98A',
  水: '#3AA0FF',
  火: '#FF4D4D',
  土: '#FFD166',
};
const TRIGRAM_SYMBOLS = {
  乾: '☰',
  兑: '☱',
  离: '☲',
  震: '☳',
  巽: '☴',
  坎: '☵',
  艮: '☶',
  坤: '☷',
};
const TRIGRAM_COLORS = {
  乾: 'rgba(120, 190, 255, 0.08)',
  兑: 'rgba(180, 200, 255, 0.08)',
  离: 'rgba(255, 140, 120, 0.08)',
  震: 'rgba(160, 255, 170, 0.08)',
  巽: 'rgba(120, 220, 190, 0.08)',
  坎: 'rgba(110, 160, 255, 0.08)',
  艮: 'rgba(210, 210, 230, 0.08)',
  坤: 'rgba(255, 220, 140, 0.08)',
};
const VISUAL_CFG = {
  line: {
    baseAlpha: 0.16,
    glowAlpha: 0.85,
    baseWidth: 5.2,
    pathWidth: 7,
    glowWidth: 7,
    dashedWidth: 2,
  },
  inject: {
    width: 2.6,
    glowWidth: 7,
    inset: 8,
  },
  labels: {
    trigramSymbol: 16,
    trigramName: 13,
    watermark: 46,
  },
  slot: {
    outline: 6,
    text: 10,
  },
};
const SLOT_STYLE = {
  skill: { stroke: '#7fe9ff', fill: 0.08, width: 2.6, text: '技' },
  mod: { stroke: '#ff8bd1', fill: 0.08, width: 2.6, text: '改' },
  stat: { stroke: '#ffd166', fill: 0.06, width: 2.2, text: '属' },
  normal: { stroke: '#c2cbd6', fill: 0.03, width: 1.6, text: '' },
  core: { stroke: '#ffc46b', fill: 0.08, width: 2.8, text: '核' },
};

const QI_CFG = {
  k_gen: 0.06,
  k_ke: 0.08,
  k_turb: 0.12,
  turbulence_dash: 0.45,
  iterations: 18,
};
const SLOT_TYPES = {
  normal: 'normal',
  skill: 'skill',
  stat: 'stat',
  mod: 'mod',
  core_adjacent: 'core_adjacent',
  core: 'core',
};
const STONE_CATEGORIES = {
  SKILL: 'SKILL',
  STAT: 'STAT',
  MOD: 'MOD',
  CORE: 'CORE',
};
const STONES = [
  { id: 'stat_metal', name: '金属性石', element: '金', category: STONE_CATEGORIES.STAT, effects: { dps: 4, crit: 2 } },
  { id: 'stat_wood', name: '木属性石', element: '木', category: STONE_CATEGORIES.STAT, effects: { sustain: 3, regen: 2 } },
  { id: 'stat_water', name: '水属性石', element: '水', category: STONE_CATEGORIES.STAT, effects: { sustain: 4, mana: 3 } },
  { id: 'stat_fire', name: '火属性石', element: '火', category: STONE_CATEGORIES.STAT, effects: { dps: 6, stability: -1 } },
  { id: 'stat_earth', name: '土属性石', element: '土', category: STONE_CATEGORIES.STAT, effects: { ehp: 6, stability: 2 } },
  { id: 'skill_fire', name: '火诀石', element: '火', category: STONE_CATEGORIES.SKILL, effects: { dps: 5, crit: 1 } },
  { id: 'skill_water', name: '水诀石', element: '水', category: STONE_CATEGORIES.SKILL, effects: { sustain: 5, mana: 2 } },
  { id: 'skill_metal', name: '金诀石', element: '金', category: STONE_CATEGORIES.SKILL, effects: { dps: 4, crit: 2 } },
  { id: 'skill_wood', name: '木诀石', element: '木', category: STONE_CATEGORIES.SKILL, effects: { sustain: 4, ehp: 2 } },
  { id: 'skill_earth', name: '土诀石', element: '土', category: STONE_CATEGORIES.SKILL, effects: { ehp: 5, stability: 2 } },
  { id: 'mod_amp', name: '增幅石', element: '金', category: STONE_CATEGORIES.MOD, effects: { dps: 3, stability: -1 } },
  { id: 'mod_guard', name: '护持石', element: '土', category: STONE_CATEGORIES.MOD, effects: { ehp: 3, stability: 2 } },
  { id: 'mod_flow', name: '回流石', element: '水', category: STONE_CATEGORIES.MOD, effects: { sustain: 4, mana: 1 } },
  { id: 'mod_burst', name: '爆燃石', element: '火', category: STONE_CATEGORIES.MOD, effects: { dps: 4, stability: -2 } },
  { id: 'mod_spread', name: '蔓延石', element: '木', category: STONE_CATEGORIES.MOD, effects: { sustain: 2, ehp: 2 } },
  { id: 'core_lonely', name: '独自升级', element: '土', category: STONE_CATEGORIES.CORE, effects: {} },
  { id: 'core_five_color', name: '五色俱全', element: '金', category: STONE_CATEGORIES.CORE, effects: {} },
  { id: 'core_resonance', name: '灵脉共鸣', element: '水', category: STONE_CATEGORIES.CORE, effects: {} },
];
const LINGGEN_PROFILES = [
  {
    id: 'four_color',
    name: '四色灵根',
    sources: [
      { element: '金', capacity: 6, regen: 1, stability: 1 },
      { element: '木', capacity: 6, regen: 1, stability: 1 },
      { element: '水', capacity: 6, regen: 1, stability: 1 },
      { element: '火', capacity: 6, regen: 1, stability: 1 },
      { element: '土', capacity: 6, regen: 1, stability: 1 },
    ],
  },
  {
    id: 'pure_water',
    name: '先天水灵根',
    sources: [
      { element: '水', capacity: 10, regen: 2, stability: 2 },
      { element: '水', capacity: 8, regen: 2, stability: 2 },
      { element: '水', capacity: 6, regen: 1, stability: 1 },
      { element: '水', capacity: 5, regen: 1, stability: 1 },
      { element: '水', capacity: 4, regen: 1, stability: 1 },
    ],
  },
];
const TRIGRAM_MODS = {
  乾: { dps: 0.1, stability: -0.05 },
  兑: { crit: 0.1 },
  离: { dps: 0.15, stability: -0.1 },
  震: { dps: 0.12, sustain: -0.05 },
  巽: { sustain: 0.12 },
  坎: { sustain: 0.18 },
  艮: { ehp: 0.18, stability: 0.1 },
  坤: { ehp: 0.12, sustain: 0.05 },
};
const ELEMENT_MAP = {
  金: 'metal',
  木: 'wood',
  水: 'water',
  火: 'fire',
  土: 'earth',
};
const ELEMENT_LABEL = {
  metal: '金',
  wood: '木',
  water: '水',
  fire: '火',
  earth: '土',
};
const EDGE_COMPONENT_MAP = {
  WIRE: 'wire',
  RESISTOR: 'resistor',
  CAPACITOR: 'capacitor',
  DIODE: 'diode',
  AMPLIFIER: 'amplifier',
  SWITCH: 'switch',
};
const NODE_STYLE = {
  baseFill: 0.52,
  stroke: 0.95,
  glow: 0.18,
  hitPadding: 6,
  radius: {
    core: 10,
    major: 8,
    normal: 6,
    disabled: 4.5,
  },
};
const COMPONENT_TYPES = ['RESISTOR', 'CAPACITOR', 'DIODE', 'SWITCH', 'AMPLIFIER', 'SOURCE'];
const COMPONENT_DESC = {
  RESISTOR: '电阻：节点功耗 +1',
  CAPACITOR: '电容：带宽缓冲 +2',
  DIODE: '二极管：只允许向外环导通',
  SWITCH: '开关：可切换导通',
  AMPLIFIER: '放大器：带宽 +1（消耗电力）',
  SOURCE: '电源：提供额外电力 +2',
};
const NEIGHBOR_RULES = {
  crossCount: 2,
  coreInnerMax: 'all',
};
const TRIGRAM_BITS = {
  '乾': [1, 1, 1],
  '兑': [0, 1, 1],
  '离': [1, 0, 1],
  '震': [0, 0, 1],
  '巽': [1, 1, 0],
  '坎': [0, 1, 0],
  '艮': [1, 0, 0],
  '坤': [0, 0, 0],
};
const BITS_TRIGRAM = Object.fromEntries(
  Object.entries(TRIGRAM_BITS).map(([name, bits]) => [bits.join(''), name]),
);
const HEX_MOD_DEFAULTS = {
  qi_cap_mul: 1,
  qi_cap_add: 0,
  bandwidth_cap_mul: 1,
  bandwidth_cap_add: 0,
  link_cost_mul: 1,
  power_loss_per_edge: 0,
  max_link_range_steps: 1,
  crossCount: NEIGHBOR_RULES.crossCount,
  contactThresholdDegAdd: 0,
  rotate_disconnect_grace: 0,
  overload_soft_cap: 0,
  noise_flip_chance: 0,
};
const UPPER_TRIGRAM_MODS = {
  '乾': { max_link_range_steps: 2, rotate_disconnect_grace: 1 },
  '兑': { crossCount: 3, link_cost_mul: 0.9 },
  '离': { qi_cap_mul: 1.15, power_loss_per_edge: 0.05 },
  '震': { rotate_disconnect_grace: 1 },
  '巽': { link_cost_mul: 0.85, power_loss_per_edge: -0.02 },
  '坎': { overload_soft_cap: 1, qi_cap_mul: 0.95 },
  '艮': { max_link_range_steps: 1, power_loss_per_edge: -0.05, force_link_range: true },
  '坤': { qi_cap_mul: 1.2, link_cost_mul: 1.1 },
};
const LOWER_TRIGRAM_MODS = {
  '乾': { qi_cap_mul: 1.1 },
  '兑': { link_cost_mul: 0.9 },
  '离': { power_loss_per_edge: 0.05 },
  '震': { link_cost_mul: 0.8 },
  '巽': { power_loss_per_edge: -0.03 },
  '坎': { overload_soft_cap: 1 },
  '艮': { rotate_disconnect_grace: 1 },
  '坤': { link_cost_mul: 1.05, qi_cap_mul: 1.15 },
};

function normDeg(deg) {
  let v = deg % 360;
  if (v < 0) v += 360;
  return v;
}

function angleDiff(a, b) {
  const diff = Math.abs(normDeg(a) - normDeg(b));
  return Math.min(diff, 360 - diff);
}

function deltaAngleDeg(fromDeg, toDeg) {
  let diff = normDeg(toDeg) - normDeg(fromDeg);
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;
  return diff;
}

function trigramByAngle(theta) {
  const idx = Math.floor(normDeg(theta) / 45) % TRIGRAMS.length;
  return TRIGRAMS[idx];
}

function coreSourceIndex(theta) {
  const step = 360 / 5;
  return Math.floor(normDeg(theta) / step) % 5;
}

function bits3ToTrigramName(bits3) {
  const key = bits3.join('');
  return BITS_TRIGRAM[key] || '坤';
}

function trigramNameToBits3(name) {
  return TRIGRAM_BITS[name] ? [...TRIGRAM_BITS[name]] : [0, 0, 0];
}

function bits6ToHexId(bits6) {
  return bits6.reduce((sum, bit, idx) => sum + ((bit ? 1 : 0) << idx), 0);
}

function hexIdToBits6(hexId) {
  const bits = [];
  for (let i = 0; i < 6; i += 1) {
    bits.push((hexId >> i) & 1);
  }
  return bits;
}

function describeHex(upper, lower) {
  return `${upper}上${lower}下`;
}

function hexToRgb(hex) {
  const raw = hex.replace('#', '');
  if (raw.length !== 6) return { r: 200, g: 200, b: 200 };
  return {
    r: parseInt(raw.slice(0, 2), 16),
    g: parseInt(raw.slice(2, 4), 16),
    b: parseInt(raw.slice(4, 6), 16),
  };
}

function rgba(hex, alpha) {
  const { r, g, b } = hexToRgb(hex);
  return `rgba(${r},${g},${b},${alpha})`;
}

function mixColorFromRatio(ratio) {
  const base = { r: 0, g: 0, b: 0 };
  const keys = Object.keys(WUXING_COLORS);
  let total = 0;
  keys.forEach((k) => {
    const v = ratio?.[k] ?? 0;
    total += v;
  });
  const norm = total > 0 ? total : 1;
  keys.forEach((k) => {
    const weight = (ratio?.[k] ?? 0) / norm;
    const { r, g, b } = hexToRgb(WUXING_COLORS[k]);
    base.r += r * weight;
    base.g += g * weight;
    base.b += b * weight;
  });
  return `rgba(${Math.round(base.r)},${Math.round(base.g)},${Math.round(base.b)},1)`;
}

function hashId(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) >>> 0;
  }
  return hash;
}

function assignComponent(node) {
  if (node.id === 'core') {
    node.componentType = 'SOURCE';
    node.switchOn = true;
    return;
  }
  const idx = hashId(node.id) % COMPONENT_TYPES.length;
  node.componentType = COMPONENT_TYPES[idx];
  if (node.componentType === 'SWITCH') node.switchOn = true;
  if (node.componentType === 'CAPACITOR') node.capBuffer = 2;
}

function pickPortSlots(nSlots, k = 3, phase = 0) {
  if (!nSlots || nSlots <= 0) return [];
  const slots = [];
  for (let i = 0; i < k; i += 1) {
    const idx = Math.floor((i * nSlots) / k + phase) % nSlots;
    slots.push(idx);
  }
  return Array.from(new Set(slots));
}

function mergeMods(base, add) {
  const merged = { ...base };
  Object.keys(add || {}).forEach((key) => {
    if (key.endsWith('_mul')) {
      merged[key] *= add[key];
    } else if (key === 'max_link_range_steps') {
      merged[key] = Math.max(1, add[key]);
    } else if (key === 'crossCount') {
      merged[key] = add[key];
    } else if (key === 'force_link_range') {
      merged.force_link_range = true;
    } else {
      merged[key] += add[key];
    }
  });
  return merged;
}

function combineMods(upper, lower) {
  let mods = { ...HEX_MOD_DEFAULTS };
  const upperMods = UPPER_TRIGRAM_MODS[upper] || {};
  const lowerMods = LOWER_TRIGRAM_MODS[lower] || {};
  mods = mergeMods(mods, upperMods);
  mods = mergeMods(mods, lowerMods);
  if (upperMods.force_link_range) {
    mods.max_link_range_steps = 1;
  }
  return {
    mods,
    effects: [
      {
        id: `upper-${upper}`,
        title: `${upper}上卦`,
        desc: JSON.stringify(upperMods),
        mods: upperMods,
      },
      {
        id: `lower-${lower}`,
        title: `${lower}下卦`,
        desc: JSON.stringify(lowerMods),
        mods: lowerMods,
      },
      {
        id: 'combo',
        title: '组合增益',
        desc: `带宽倍率×${mods.bandwidth_cap_mul.toFixed(2)} | 电力倍率×${mods.qi_cap_mul.toFixed(2)}`,
        mods,
      },
    ],
  };
}

async function hashText(text) {
  if (!crypto?.subtle) return String(text.length);
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest('SHA-256', data);
  const bytes = Array.from(new Uint8Array(hash));
  return bytes.map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 10);
}

async function fetchJson(url) {
  const res = await fetch(`${url}?t=${Date.now()}`);
  const text = await res.text();
  const data = JSON.parse(text);
  const mtime = res.headers.get('last-modified') || '-';
  return { data, text, mtime };
}

async function loadConfig() {
  const { data, text, mtime } = await fetchJson('./board_config.json');
  cfgData = data;
  cfgHash = await hashText(text);
  cfgMtime = mtime;
}

async function loadBoard() {
  const { data } = await fetchJson('./board.json');
  boardData = data;
}

function buildBoardState(preset) {
  const nodes = [];
  const ringMap = cfgData.ring_map;
  const ringBuckets = { inner: [], mid: [], outer: [] };
  const slotStones = preset?.slots || {};

  const assignSlotTypes = (ring, list) => {
    const groups = {};
    list.forEach((node) => {
      if (!groups[node.trigram]) groups[node.trigram] = [];
      groups[node.trigram].push(node);
    });
    Object.values(groups).forEach((group) => {
      group.sort((a, b) => a.slot_idx - b.slot_idx);
      group.forEach((node, idx) => {
        if (ring === 'inner') {
          if (idx === 0) node.slot_type = SLOT_TYPES.skill;
          else if (idx === 1) node.slot_type = SLOT_TYPES.mod;
          else node.slot_type = SLOT_TYPES.stat;
        } else if (ring === 'mid') {
          if (idx === 0) node.slot_type = SLOT_TYPES.mod;
          else node.slot_type = SLOT_TYPES.stat;
        } else if (ring === 'outer') {
          node.slot_type = idx % 2 === 0 ? SLOT_TYPES.stat : SLOT_TYPES.normal;
        }
      });
    });
  };

  boardData.nodes.forEach((raw) => {
    if (raw.id === 'core' || raw.ring === 'core') return;
    const ring = ringMap[raw.ring] || raw.ring;
    const baseTheta = (raw.angle != null ? raw.angle : Math.atan2(raw.y, raw.x)) * (180 / Math.PI);
    const radius = raw.radius != null ? raw.radius : Math.hypot(raw.x, raw.y);
    ringBuckets[ring].push({
      id: raw.id,
      name: raw.label || raw.id,
      elem: raw.element,
      ring,
      slot_idx: 0,
      base_theta: baseTheta,
      r: radius,
      size: raw.type === 'keystone' ? 'major' : 'small',
      trigram: trigramByAngle(baseTheta),
      slot_type: SLOT_TYPES.normal,
      stone_id: null,
      powered: false,
    });
  });

  Object.keys(ringBuckets).forEach((ring) => {
    ringBuckets[ring].sort((a, b) => normDeg(a.base_theta) - normDeg(b.base_theta));
    ringBuckets[ring].forEach((node, idx) => {
      node.slot_idx = idx;
      node.id = `${ring}_${idx}`;
      node.core_adjacent = false;
      node.core_source_idx = null;
      if (ring === 'inner') {
        node.core_adjacent = true;
        node.core_source_idx = coreSourceIndex(node.base_theta);
      }
      node.stone_id = slotStones[node.id] || null;
      node.lit = !!node.stone_id;
      nodes.push(node);
    });
    assignSlotTypes(ring, ringBuckets[ring]);
  });

  if (cfgData.inner_core) {
    const slots = cfgData.inner_core.slots;
    const radius = cfgData.inner_core.radius;
    for (let i = 0; i < slots; i += 1) {
      const theta = (360 / slots) * i;
      nodes.push({
        id: `inner_core_${i}`,
        name: `内核-${i}`,
        elem: '土',
        ring: 'inner_core',
        slot_idx: i,
        base_theta: theta,
        r: radius,
        size: 'major',
        trigram: trigramByAngle(theta),
        slot_type: SLOT_TYPES.core,
        core_adjacent: false,
        core_source_idx: null,
        stone_id: slotStones[`inner_core_${i}`] || null,
        lit: !!slotStones[`inner_core_${i}`],
        powered: false,
      });
    }
  }

  const realm = preset?.realm || DEFAULT_REALM;
  const linggenId = preset?.linggen || LINGGEN_PROFILES[0].id;
  const linggenProfile = LINGGEN_PROFILES.find((p) => p.id === linggenId) || LINGGEN_PROFILES[0];
  const realmRule = cfgData.realm_rules?.[realm] || {};
  const baseQi = linggenProfile.sources.reduce((sum, s) => sum + s.capacity, 0);
  const qiCap = Math.min(baseQi, realmRule.qi_cap || baseQi);
  const bandwidthCap = Math.round(qiCap * (realmRule.bandwidth_mul ?? 0.8));

  boardState = {
    bd_name: preset?.name || null,
    realm,
    realm_rule: realmRule,
    enabled_rings: realmRule.rings || ['inner', 'mid', 'outer'],
    linggen_id: linggenProfile.id,
    linggen_profile: linggenProfile,
    core_sources: linggenProfile.sources,
    qi_cap: qiCap,
    qi_used: 0,
    bandwidth_cap: bandwidthCap,
    bandwidth_used: 0,
    nodes,
    edges: [],
    neighborMap: new Map(),
    ruleset_version: cfgData.ruleset_version || 'v2',
    cfg_hash: cfgHash,
    ui: {},
  };
  window.boardState = boardState;
}

function initUIState() {
  boardState.ui = {
    highContrast: dom.toggleContrast?.checked ?? false,
    showBroken: dom.toggleBroken?.checked ?? false,
    showEdges: dom.panel.edges?.checked ?? true,
    showLabels: dom.panel.labels?.checked ?? false,
    showSectors: dom.toggleSectors?.checked ?? true,
    showRings: dom.toggleRings?.checked ?? true,
    debug: dom.toggleDebug?.checked ?? false,
    edgeStrength: parseFloat(dom.edgeStrength?.value ?? 0.6),
    glowStrength: parseFloat(dom.glowStrength?.value ?? 0.18),
    sectorOpacity: parseFloat(dom.sectorOpacity?.value ?? 0.05),
    ringStrength: parseFloat(dom.ringStrength?.value ?? 0.55),
    scale: parseFloat(dom.scale?.value ?? 0.7),
    contactThreshold: parseFloat(dom.contactThreshold?.value ?? cfgData.bridge_threshold_deg ?? 12),
    channelCount: parseInt(dom.channelCount?.value ?? 3, 10),
    allowAutoEdges: false,
    lineMode: dom.lineMode?.value || 'all',
    lineElement: dom.lineElement?.value || '水',
    panX: 0,
    panY: 0,
  };
  runtime.selectedNodeId = boardState.nodes[0]?.id || null;
}

function debugLog(message) {
  if (boardState?.ui?.debug) {
    console.log(`[board] ${message}`);
  }
}

function scheduleUpdate(opts = {}) {
  runtime.needsRender = true;
  if (opts.recompute) {
    runtime.needsConnectivityUpdate = true;
    runtime.updateCause = opts.cause || '';
  }
}

function setUIState(patch, opts = {}) {
  Object.assign(boardState.ui, patch);
  if (opts.log) {
    const entries = Object.entries(patch)
      .map(([k, v]) => `${k}:${v}`)
      .join(', ');
    debugLog(`ui ${entries}`);
  }
  if (boardState.ui.debug) {
    dom.debugOverlay?.classList.remove('hidden');
  } else {
    dom.debugOverlay?.classList.add('hidden');
  }
  scheduleUpdate({ recompute: opts.recompute, cause: opts.cause });
}

function enabledRings() {
  return boardState.enabled_rings || cfgData.realm_rules[boardState.realm]?.rings || ['inner', 'mid', 'outer'];
}

function ringIndex(nodes = boardState.nodes) {
  const map = {};
  nodes.forEach((node) => {
    if (!map[node.ring]) map[node.ring] = [];
    map[node.ring].push(node);
  });
  Object.keys(map).forEach((ring) => {
    map[ring].sort((a, b) => a.slot_idx - b.slot_idx);
  });
  return map;
}

function ringOrder(nodes = boardState.nodes) {
  const order = ['inner_core', 'inner', 'mid', 'outer'];
  const available = new Set(Object.keys(ringIndex(nodes)));
  return order.filter((r) => available.has(r));
}

function ringDistance(aRing, bRing) {
  const order = ringOrder();
  const ai = order.indexOf(aRing);
  const bi = order.indexOf(bRing);
  if (ai === -1 || bi === -1) return 99;
  return Math.abs(ai - bi);
}

function nodeAngleDeg(node) {
  return normDeg(node.base_theta);
}

function wireKey(a, b) {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

function nodePowerCost(node) {
  if (node.id === 'core') return 0;
  const base = node.size === 'major' || node.type === 'major' || node.type === 'keystone' ? 2 : 1;
  return base + (node.componentType === 'RESISTOR' ? 1 : 0);
}

function edgeBandwidthCost(component) {
  switch (component) {
    case 'amplifier':
      return 1.2;
    case 'resistor':
      return 0.9;
    case 'capacitor':
      return 0.8;
    default:
      return 1;
  }
}

function isConductive(node) {
  if (node.id === 'core') return true;
  if (node.componentType === 'SWITCH' && !node.switchOn) return false;
  return true;
}

function diodeAllows(fromNode, toNode) {
  if (fromNode.componentType !== 'DIODE') return true;
  return ringLevel(toNode.ring) >= ringLevel(fromNode.ring);
}

function edgeKey(edge) {
  return edge.a < edge.b ? `${edge.a}|${edge.b}` : `${edge.b}|${edge.a}`;
}

function ringLevel(ring) {
  const order = ringOrder();
  const idx = order.indexOf(ring);
  return idx === -1 ? 0 : idx;
}

function buildNeighborMap(nodes = boardState.nodes) {
  const ringMap = ringIndex(nodes);
  const map = new Map();
  const addNeighbor = (a, b) => {
    if (!a || !b || a.id === b.id) return;
    if (!map.has(a.id)) map.set(a.id, new Set());
    if (!map.has(b.id)) map.set(b.id, new Set());
    map.get(a.id).add(b.id);
    map.get(b.id).add(a.id);
  };

  Object.entries(ringMap).forEach(([ring, nodes]) => {
    const ringNodes = nodes.filter((n) => n.id !== 'core' && n.slot_idx >= 0);
    if (ringNodes.length < 2) return;
    for (let i = 0; i < ringNodes.length; i += 1) {
      const a = ringNodes[i];
      const b = ringNodes[(i + 1) % ringNodes.length];
      addNeighbor(a, b);
    }
  });

  const order = ringOrder(nodes);
  order.forEach((ring) => {
    const nodes = (ringMap[ring] || []).filter((n) => n.id !== 'core');
    const ringIdx = order.indexOf(ring);
    [ringIdx - 1, ringIdx + 1].forEach((idx) => {
      const targetRing = order[idx];
      if (!targetRing) return;
      const targetNodes = (ringMap[targetRing] || []).filter((n) => n.id !== 'core');
      nodes.forEach((node) => {
        const candidates = targetNodes
          .map((t) => ({ node: t, diff: angleDiff(nodeAngleDeg(node), nodeAngleDeg(t)) }))
          .sort((a, b) => a.diff - b.diff)
          .slice(0, NEIGHBOR_RULES.crossCount);
        candidates.forEach((entry) => addNeighbor(node, entry.node));
      });
    });
  });

  return map;
}

function validateWires(neighborMap) {
  const removed = [];
  boardState.wires.forEach((edge, key) => {
    const neighbors = neighborMap.get(edge.a);
    if (!neighbors || !neighbors.has(edge.b)) {
      removed.push(edge);
      boardState.wires.delete(key);
    }
  });
  return removed;
}

function buildAutoEdges(nodes = boardState.nodes, enabledSet = null) {
  const neighborMap = buildNeighborMap(nodes);
  const edges = [];
  const seen = new Set();
  neighborMap.forEach((neighbors, id) => {
    neighbors.forEach((nid) => {
      const key = wireKey(id, nid);
      if (seen.has(key)) return;
      seen.add(key);
      const a = nodes.find((n) => n.id === id);
      const b = nodes.find((n) => n.id === nid);
      if (!a || !b) return;
      if (enabledSet && (!enabledSet.has(a.ring) || !enabledSet.has(b.ring))) {
        return;
      }
      const connected = !!a.stone_id && !!b.stone_id;
      edges.push({
        a: id,
        b: nid,
        active: false,
        connected,
        kind: 'auto',
      });
    });
  });
  return { edges, neighborMap };
}

const ELEMENT_PRIORITY = ['金', '木', '水', '火', '土'];
const SHENG = {
  木: '火',
  火: '土',
  土: '金',
  金: '水',
  水: '木',
};
const KE = {
  金: '木',
  木: '土',
  土: '水',
  水: '火',
  火: '金',
};

function computeQiFlow(edges, nodes = boardState.nodes, enabledSet = null) {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const adjacency = new Map();
  edges.forEach((edge) => {
    if (!edge.connected) return;
    if (!adjacency.has(edge.a)) adjacency.set(edge.a, []);
    if (!adjacency.has(edge.b)) adjacency.set(edge.b, []);
    adjacency.get(edge.a).push(edge.b);
    adjacency.get(edge.b).push(edge.a);
  });

  const coreSources = boardState.core_sources || [];
  nodes.forEach((node) => {
    if (!node.core_adjacent) return;
    const idx = node.core_source_idx ?? coreSourceIndex(node.base_theta);
    const src = coreSources[idx];
    node.core_source_element = src?.element || null;
  });

  const startNodes = nodes.filter((n) => {
    if (!n.core_adjacent || !n.stone_id) return false;
    if (enabledSet && !enabledSet.has(n.ring)) return false;
    const idx = n.core_source_idx ?? coreSourceIndex(n.base_theta);
    const src = coreSources[idx];
    if (!src) return false;
    return (src.capacity ?? 0) > 0;
  });
  startNodes.sort((a, b) => {
    const ea = a.core_source_element || '';
    const eb = b.core_source_element || '';
    const pa = ELEMENT_PRIORITY.indexOf(ea);
    const pb = ELEMENT_PRIORITY.indexOf(eb);
    if (pa !== pb) return pa - pb;
    return a.id.localeCompare(b.id);
  });
  const queue = startNodes.map((n) => n.id);
  const energized = new Set(queue);
  const parentMap = new Map();
  const sourceMap = new Map();
  startNodes.forEach((n) => {
    if (n.core_source_element) sourceMap.set(n.id, n.core_source_element);
  });

  while (queue.length) {
    const current = queue.shift();
    const neighbors = adjacency.get(current) || [];
    neighbors.forEach((next) => {
      if (energized.has(next)) return;
      if (enabledSet) {
        const nextNode = nodeMap.get(next);
        if (!nextNode || !enabledSet.has(nextNode.ring)) return;
      }
      energized.add(next);
      queue.push(next);
      parentMap.set(next, current);
      const src = sourceMap.get(current);
      if (src) sourceMap.set(next, src);
    });
  }

  const activeEdges = new Set();
  edges.forEach((edge) => {
    if (!edge.connected) return;
    if (energized.has(edge.a) && energized.has(edge.b)) {
      activeEdges.add(wireKey(edge.a, edge.b));
    }
  });

  return { energized, activeEdges, parentMap, sourceMap };
}

function zeroQi() {
  return { 金: 0, 木: 0, 水: 0, 火: 0, 土: 0 };
}

function addQi(a, b) {
  const out = zeroQi();
  Object.keys(out).forEach((k) => {
    out[k] = (a[k] || 0) + (b[k] || 0);
  });
  return out;
}

function scaleQi(q, s) {
  const out = zeroQi();
  Object.keys(out).forEach((k) => {
    out[k] = (q[k] || 0) * s;
  });
  return out;
}

function dominantElement(q) {
  let best = '金';
  let bestVal = -Infinity;
  Object.keys(q).forEach((k) => {
    if (q[k] > bestVal) {
      bestVal = q[k];
      best = k;
    }
  });
  return best;
}

function normalizeQi(q) {
  const total = Object.values(q).reduce((s, v) => s + v, 0) || 1;
  const out = {};
  Object.keys(q).forEach((k) => {
    out[k] = q[k] / total;
  });
  return out;
}

function trigramModifiers(trigram) {
  const mods = { k_gen: 1, k_ke: 1, k_turb: 1, sustain: 0 };
  if (trigram === '坎') {
    mods.k_turb *= 0.7;
    mods.sustain += 0.1;
  }
  if (trigram === '离') {
    mods.k_gen *= 1.35;
    mods.k_turb *= 1.2;
  }
  if (trigram === '艮') {
    mods.k_turb *= 0.55;
  }
  if (trigram === '巽') {
    mods.k_gen *= 1.1;
  }
  return mods;
}

function applyReactions(qIn, trigram, slotType) {
  const q = { ...qIn };
  let turbulence = 0;
  const residue = zeroQi();
  const triMod = trigramModifiers(trigram);
  let k_gen = QI_CFG.k_gen * triMod.k_gen;
  let k_ke = QI_CFG.k_ke * triMod.k_ke;
  let k_turb = QI_CFG.k_turb * triMod.k_turb;

  if (slotType === SLOT_TYPES.mod) {
    k_ke *= 0.85;
    k_turb *= 0.75;
  }

  Object.entries(KE).forEach(([a, b]) => {
    const n = k_ke * Math.min(q[a] || 0, q[b] || 0);
    if (n <= 0) return;
    q[a] -= n;
    q[b] -= n;
    turbulence += n;
    residue[b] += n;
  });

  Object.entries(SHENG).forEach(([a, b]) => {
    const g = k_gen * (q[a] || 0);
    if (g <= 0) return;
    q[b] += g;
  });

  const transmit = Math.exp(-k_turb * turbulence);
  return { qOut: scaleQi(q, transmit), turbulence, residue, transmit };
}

function computeQiNetwork(nodes, edges) {
  const energizedNodes = nodes.filter((n) => n.powered);
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const activeEdges = edges.filter((e) => e.active);
  const adjacency = new Map();
  activeEdges.forEach((edge) => {
    if (!adjacency.has(edge.a)) adjacency.set(edge.a, []);
    if (!adjacency.has(edge.b)) adjacency.set(edge.b, []);
    adjacency.get(edge.a).push(edge.b);
    adjacency.get(edge.b).push(edge.a);
  });

  const order = energizedNodes.map((n) => n.id).sort();
  let qiOutPrev = new Map(order.map((id) => [id, zeroQi()]));

  for (let iter = 0; iter < QI_CFG.iterations; iter += 1) {
    const qiOutNext = new Map();
    order.forEach((id) => {
      const node = nodeMap.get(id);
      if (!node) return;
      let qIn = zeroQi();
      const neighbors = adjacency.get(id) || [];
      if (neighbors.length) {
        neighbors.forEach((nid) => {
          qIn = addQi(qIn, qiOutPrev.get(nid) || zeroQi());
        });
        qIn = scaleQi(qIn, 1 / neighbors.length);
      }
      if (node.core_adjacent) {
        const idx = node.core_source_idx ?? coreSourceIndex(node.base_theta);
        const src = boardState.core_sources?.[idx];
        if (src?.element) {
          const inject = zeroQi();
          inject[src.element] = Math.max(0.5, src.capacity * 0.2);
          qIn = addQi(qIn, inject);
        }
      }
      const reaction = applyReactions(qIn, node.trigram, node.slot_type);
      qiOutNext.set(id, reaction.qOut);
      node.qi_out = reaction.qOut;
      node.qi_ratio = normalizeQi(reaction.qOut);
      node.turbulence = reaction.turbulence;
      node.residue = reaction.residue;
      node.dominant_element = dominantElement(reaction.qOut);
      node.transmit = reaction.transmit;
    });
    qiOutPrev = qiOutNext;
  }

  edges.forEach((edge) => {
    if (!edge.active) {
      edge.qi_comp = zeroQi();
      edge.turbulence = 0;
      return;
    }
    const a = nodeMap.get(edge.a);
    const b = nodeMap.get(edge.b);
    const qa = a?.qi_out || zeroQi();
    const qb = b?.qi_out || zeroQi();
    edge.qi_comp = addQi(qa, qb);
    edge.qi_ratio = normalizeQi(edge.qi_comp);
    edge.dominant_element = dominantElement(edge.qi_comp);
    edge.turbulence = ((a?.turbulence || 0) + (b?.turbulence || 0)) * 0.5;
  });
}

function computeConnectivitySnapshot(nodes) {
  const enabledSet = new Set(enabledRings());
  const { edges, neighborMap } = buildAutoEdges(nodes, enabledSet);
  const { energized, activeEdges, parentMap, sourceMap } = computeQiFlow(edges, nodes, enabledSet);
  const powerUsed = nodes.filter((n) => enabledSet.has(n.ring) && n.stone_id).length;
  const bandwidthUsed = activeEdges.size;
  const powerOk = powerUsed <= boardState.qi_cap;
  const bandwidthOk = bandwidthUsed <= boardState.bandwidth_cap;
  const nodeReasons = new Map();
  const nodePowered = new Map();

  nodes.forEach((node) => {
    const lit = !!node.stone_id;
    const powered = powerOk && bandwidthOk && energized.has(node.id);
    nodePowered.set(node.id, powered);
    if (lit && !powered) {
      if (!enabledSet.has(node.ring)) {
        nodeReasons.set(node.id, '境界未解锁');
      } else if (!powerOk || !bandwidthOk) {
        nodeReasons.set(node.id, '预算不足');
      } else if (node.core_adjacent) {
        const idx = node.core_source_idx ?? coreSourceIndex(node.base_theta);
        const src = boardState.core_sources?.[idx];
        nodeReasons.set(node.id, src && (src.capacity ?? 0) <= 0 ? '供能不足' : '未接入核心');
      } else {
        nodeReasons.set(node.id, '未接入核心');
      }
    }
  });

  return {
    edges,
    neighborMap,
    energized,
    activeEdges,
    parentMap,
    sourceMap,
    powerUsed,
    bandwidthUsed,
    powerOk,
    bandwidthOk,
    nodeReasons,
    nodePowered,
  };
}

function recomputeConnectivity(cause = '') {
  const enabled = new Set(enabledRings());
  nodeReason = new Map();
  const snapshot = computeConnectivitySnapshot(boardState.nodes);
  boardState.neighborMap = snapshot.neighborMap;
  boardState.qi_used = snapshot.powerUsed;
  boardState.bandwidth_used = snapshot.bandwidthUsed;

  boardState.nodes.forEach((node) => {
    node.lit = !!node.stone_id;
    node.powered = snapshot.powerOk && snapshot.bandwidthOk && snapshot.energized.has(node.id);
    node.source_element = snapshot.sourceMap.get(node.id) || null;
    node.parent = snapshot.parentMap.get(node.id) || null;
    const reason = snapshot.nodeReasons.get(node.id);
    if (reason) nodeReason.set(node.id, reason);
  });

  boardState.edges = snapshot.edges.map((edge) => {
    let src = snapshot.sourceMap.get(edge.a) || snapshot.sourceMap.get(edge.b) || null;
    if (snapshot.parentMap.get(edge.a) === edge.b) src = snapshot.sourceMap.get(edge.a) || src;
    if (snapshot.parentMap.get(edge.b) === edge.a) src = snapshot.sourceMap.get(edge.b) || src;
    return {
      ...edge,
      active: snapshot.powerOk && snapshot.bandwidthOk && snapshot.activeEdges.has(wireKey(edge.a, edge.b)),
      source_element: src,
    };
  });

  boardState.parentMap = snapshot.parentMap;
  boardState.sourceMap = snapshot.sourceMap;

  runtime.lastActiveEdges = new Set(boardState.edges.filter((e) => e.active).map(edgeKey));

  computeQiNetwork(boardState.nodes, boardState.edges);
  boardState.edges.forEach((edge) => {
    if (!edge.connected) {
      edge.state = 'NONE';
      return;
    }
    const reason = [];
    if (!snapshot.powerOk || !snapshot.bandwidthOk) reason.push('预算不足');
    if (!edge.active) reason.push('未接入核心');
    if (edge.turbulence > QI_CFG.turbulence_dash) reason.push('乱流过高');
    if (edge.active && edge.turbulence <= QI_CFG.turbulence_dash) {
      edge.state = 'ENERGIZED';
    } else {
      edge.state = 'CONNECTED_NO_QI';
      edge.reason = reason.join(' / ') || '无气';
    }
    edge.source_element = edge.dominant_element || edge.source_element;
  });

  runSolver();
}

function nodePosition(node) {
  const theta = node.base_theta * (Math.PI / 180);
  return {
    x: Math.cos(theta) * node.r,
    y: Math.sin(theta) * node.r,
  };
}

function nodeRadius(node) {
  if (!enabledRings().includes(node.ring)) return NODE_STYLE.radius.disabled;
  if (node.type === 'core') return NODE_STYLE.radius.core;
  if (node.size === 'major' || node.type === 'keystone' || node.type === 'major') return NODE_STYLE.radius.major;
  return NODE_STYLE.radius.normal;
}

function hitTestNode(event) {
  const svg = dom.container.querySelector('svg.board');
  const group = svg?.querySelector('#board-root');
  if (!svg || !group) return null;
  const ctm = group.getScreenCTM();
  if (!ctm) return null;
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const pt = point.matrixTransform(ctm.inverse());
  const size = 760;
  const cx = size / 2;
  const cy = size / 2;
  let best = null;
  let bestDist = Infinity;
  boardState.nodes.forEach((node) => {
    const pos = nodePosition(node);
    const nx = cx + pos.x;
    const ny = cy + pos.y;
    const r = nodeRadius(node) + NODE_STYLE.hitPadding;
    const dx = pt.x - nx;
    const dy = pt.y - ny;
    const dist = Math.hypot(dx, dy);
    if (dist <= r && dist < bestDist) {
      best = node;
      bestDist = dist;
    }
  });
  return best;
}

function hitTestEdge(event) {
  const svg = dom.container.querySelector('svg.board');
  const group = svg?.querySelector('#board-root');
  if (!svg || !group) return null;
  const ctm = group.getScreenCTM();
  if (!ctm) return null;
  const point = svg.createSVGPoint();
  point.x = event.clientX;
  point.y = event.clientY;
  const pt = point.matrixTransform(ctm.inverse());
  const size = 760;
  const cx = size / 2;
  const cy = size / 2;
  let best = null;
  let bestDist = Infinity;
  const edges = boardState.edges.filter((e) => e.connected && e.state !== 'NONE');
  edges.forEach((edge) => {
    const a = boardState.nodes.find((n) => n.id === edge.a);
    const b = boardState.nodes.find((n) => n.id === edge.b);
    if (!a || !b) return;
    const pa = nodePosition(a);
    const pb = nodePosition(b);
    const x1 = cx + pa.x;
    const y1 = cy + pa.y;
    const x2 = cx + pb.x;
    const y2 = cy + pb.y;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len2 = dx * dx + dy * dy || 1;
    let t = ((pt.x - x1) * dx + (pt.y - y1) * dy) / len2;
    t = Math.max(0, Math.min(1, t));
    const projX = x1 + t * dx;
    const projY = y1 + t * dy;
    const dist = Math.hypot(pt.x - projX, pt.y - projY);
    if (dist < 6 && dist < bestDist) {
      bestDist = dist;
      best = edge;
    }
  });
  return best;
}

function polarPoint(cx, cy, r, deg) {
  const rad = (deg - 90) * (Math.PI / 180);
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function sectorPath(cx, cy, innerR, outerR, startDeg, endDeg) {
  const startOuter = polarPoint(cx, cy, outerR, startDeg);
  const endOuter = polarPoint(cx, cy, outerR, endDeg);
  const startInner = polarPoint(cx, cy, innerR, endDeg);
  const endInner = polarPoint(cx, cy, innerR, startDeg);
  const largeArc = endDeg - startDeg <= 180 ? 0 : 1;
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 1 ${endOuter.x} ${endOuter.y}`,
    `L ${startInner.x} ${startInner.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 0 ${endInner.x} ${endInner.y}`,
    'Z',
  ].join(' ');
}

function renderComponentGlyph(node, x, y, r) {
  const s = r * 0.6;
  const stroke = 'rgba(20,25,30,0.8)';
  const strokeWide = 'rgba(240,245,250,0.8)';
  switch (node.componentType) {
    case 'RESISTOR':
      return `<path d="M ${x - s} ${y} l ${s * 0.3} ${-s * 0.3} l ${s * 0.3} ${s * 0.3} l ${s * 0.3} ${-s * 0.3} l ${s * 0.3} ${s * 0.3}" fill="none" stroke="${stroke}" stroke-width="1.4" />`;
    case 'CAPACITOR':
      return `<line x1="${x - s * 0.4}" y1="${y - s * 0.6}" x2="${x - s * 0.4}" y2="${y + s * 0.6}" stroke="${stroke}" stroke-width="1.6" />
        <line x1="${x + s * 0.4}" y1="${y - s * 0.6}" x2="${x + s * 0.4}" y2="${y + s * 0.6}" stroke="${stroke}" stroke-width="1.6" />`;
    case 'DIODE':
      return `<path d="M ${x - s * 0.6} ${y - s * 0.5} L ${x - s * 0.6} ${y + s * 0.5} L ${x + s * 0.4} ${y} Z" fill="${stroke}" />
        <line x1="${x + s * 0.5}" y1="${y - s * 0.6}" x2="${x + s * 0.5}" y2="${y + s * 0.6}" stroke="${stroke}" stroke-width="1.6" />`;
    case 'SWITCH':
      return `<line x1="${x - s * 0.7}" y1="${y}" x2="${x - s * 0.1}" y2="${y}" stroke="${stroke}" stroke-width="1.6" />
        <line x1="${x + s * 0.1}" y1="${y}" x2="${x + s * 0.7}" y2="${y}" stroke="${stroke}" stroke-width="1.6" />
        <circle cx="${x}" cy="${y - s * 0.3}" r="${s * 0.15}" fill="${stroke}" />`;
    case 'AMPLIFIER':
      return `<path d="M ${x - s * 0.6} ${y - s * 0.5} L ${x - s * 0.6} ${y + s * 0.5} L ${x + s * 0.6} ${y} Z" fill="${stroke}" />`;
    case 'SOURCE':
      return `<circle cx="${x}" cy="${y}" r="${s * 0.55}" fill="none" stroke="${strokeWide}" stroke-width="1.6" />
        <line x1="${x - s * 0.3}" y1="${y}" x2="${x + s * 0.3}" y2="${y}" stroke="${strokeWide}" stroke-width="1.6" />
        <line x1="${x}" y1="${y - s * 0.3}" x2="${x}" y2="${y + s * 0.3}" stroke="${strokeWide}" stroke-width="1.6" />`;
    default:
      return '';
  }
}

function renderBoard(now = performance.now()) {
  const size = 760;
  const cx = size / 2;
  const cy = size / 2;
  const enabled = new Set(enabledRings());
  const colors = boardData.meta.colors || WUXING_COLORS;
  const ui = boardState.ui || {};
  const showEdges = ui.showEdges;
  const showLabels = ui.showLabels;
  const highContrast = ui.highContrast;
  const showBroken = ui.showBroken;
  const showSectors = ui.showSectors;
  const showRings = ui.showRings;
  const edgeStrength = ui.edgeStrength ?? 0.6;
  const ringStrength = ui.ringStrength ?? 0.55;
  const glowStrength = ui.glowStrength ?? 0.18;
  const sectorOpacity = ui.sectorOpacity ?? 0.05;
  const scale = ui.scale ?? 1;
  const panX = ui.panX ?? 0;
  const panY = ui.panY ?? 0;
  const lineMode = ui.lineMode || 'all';
  const lineElement = ui.lineElement || '水';
  const pathEdges = runtime.pathEdges;
  const selectedRing = null;

  const ringMap = ringIndex();
  const ringRadii = boardData.rings.map((r) => r.radius);
  if (cfgData.inner_core) ringRadii.push(cfgData.inner_core.radius);
  const maxR = Math.max(...ringRadii, 0);
  const innerR = Math.max(60, Math.min(...ringRadii.filter((r) => r > 0)) || 60);

  let svg = `<svg class="board" viewBox="0 0 ${size} ${size}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<defs>
    <filter id="node-glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>`;
  svg += `<g id="board-root" transform="translate(${cx + panX} ${cy + panY}) scale(${scale}) translate(${-cx} ${-cy})">`;

  if (showSectors) {
    const step = 360 / TRIGRAMS.length;
    TRIGRAMS.forEach((tri, idx) => {
      const start = idx * step;
      const end = start + step;
      const path = sectorPath(cx, cy, innerR, maxR + 34, start, end);
      const fill = TRIGRAM_COLORS[tri] || `rgba(120,160,200,${sectorOpacity})`;
      const stroke = `rgba(120,170,200,${0.32})`;
      svg += `<path d="${path}" fill="${fill}" stroke="${stroke}" stroke-width="1.2" />`;
    });
    for (let i = 0; i < TRIGRAMS.length; i += 1) {
      const angle = i * step;
      const start = polarPoint(cx, cy, innerR, angle);
      const end = polarPoint(cx, cy, maxR + 34, angle);
      svg += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="rgba(140,180,210,0.45)" stroke-width="1.4" />`;
    }
    const watermarkR = innerR + (maxR - innerR) * 0.55;
    TRIGRAMS.forEach((tri, idx) => {
      const mid = idx * step + step / 2;
      const pos = polarPoint(cx, cy, watermarkR, mid);
      const symbol = TRIGRAM_SYMBOLS[tri] || '';
      svg += `<text x="${pos.x}" y="${pos.y + 12}" text-anchor="middle" font-size="${VISUAL_CFG.labels.watermark}" fill="rgba(160,190,210,0.08)" font-weight="700">${symbol}</text>`;
    });
  }

  const labelInner = maxR + 16;
  const labelOuter = maxR + 36;
  svg += `<circle cx="${cx}" cy="${cy}" r="${labelInner}" fill="none" stroke="rgba(120,160,190,0.35)" stroke-width="1.4" />`;
  svg += `<circle cx="${cx}" cy="${cy}" r="${labelOuter}" fill="none" stroke="rgba(120,160,190,0.2)" stroke-width="1" />`;
  const trigramLabelR = maxR + 28;
  TRIGRAMS.forEach((tri, idx) => {
    const step = 360 / TRIGRAMS.length;
    const mid = idx * step + step / 2;
    const pos = polarPoint(cx, cy, trigramLabelR, mid);
    const symbol = TRIGRAM_SYMBOLS[tri] || '';
    svg += `<text x="${pos.x}" y="${pos.y - 4}" text-anchor="middle" font-size="${VISUAL_CFG.labels.trigramSymbol}" fill="rgba(230,240,250,0.95)" font-weight="600" stroke="rgba(6,8,10,0.8)" stroke-width="3" paint-order="stroke">${symbol}</text>`;
    svg += `<text x="${pos.x}" y="${pos.y + 14}" text-anchor="middle" font-size="${VISUAL_CFG.labels.trigramName}" fill="rgba(220,232,244,0.9)" font-weight="600" stroke="rgba(6,8,10,0.75)" stroke-width="3" paint-order="stroke">${tri}</text>`;
  });

  const coreSources = boardState.core_sources || [];
  let coreVisual = null;
  if (coreSources.length > 0) {
    const coreStep = 360 / coreSources.length;
    const coreR = Math.max(52, Math.min(innerR - 14, 92));
    const coreInner = coreR * 0.25;
    coreVisual = { coreStep, coreR, coreInner };
    svg += `<text x="${cx}" y="${cy - coreR - 6}" text-anchor="middle" font-size="12" fill="rgba(210,224,238,0.8)">灵根</text>`;
    coreSources.forEach((src, idx) => {
      const start = idx * coreStep;
      const end = start + coreStep;
      const color = WUXING_COLORS[src.element] || '#9fd0ff';
      const fill = rgba(color, 0.45);
      const stroke = rgba(color, 0.8);
      const path = sectorPath(cx, cy, coreInner, coreR, start, end);
      svg += `<path d="${path}" fill="${fill}" stroke="${stroke}" stroke-width="1.4" />`;
      const mid = start + coreStep / 2;
      const pos = polarPoint(cx, cy, coreR * 0.62, mid);
      const label = `${src.element}`;
      const val = `${src.capacity ?? 0}/${src.regen ?? 0}`;
      const warn = src.capacity !== undefined && src.capacity <= 2;
      const textColor = warn ? 'rgba(255,190,150,0.95)' : 'rgba(240,245,250,0.95)';
      svg += `<text x="${pos.x}" y="${pos.y - 4}" text-anchor="middle" font-size="12" fill="${textColor}" font-weight="600">${label}</text>`;
      svg += `<text x="${pos.x}" y="${pos.y + 12}" text-anchor="middle" font-size="10" fill="rgba(210,220,230,0.85)">${val}</text>`;
      if (warn) {
        svg += `<text x="${pos.x}" y="${pos.y + 26}" text-anchor="middle" font-size="10" fill="rgba(255,160,120,0.9)">供能低</text>`;
      }
    });
    svg += `<circle cx="${cx}" cy="${cy}" r="${coreInner}" fill="rgba(6,10,14,0.9)" stroke="rgba(120,160,190,0.35)" stroke-width="1" />`;
  }

  if (showRings) {
    boardData.rings.forEach((ring) => {
      const ringName = cfgData.ring_map[ring.id] || ring.id;
      if (!enabled.has(ringName)) return;
      const strokeAlpha = 0.25;
      const stroke = `rgba(120,170,200,${strokeAlpha * ringStrength})`;
      const width = 1.2;
      svg += `<circle cx="${cx}" cy="${cy}" r="${ring.radius}" fill="none" stroke="${stroke}" stroke-width="${width}" />`;
    });
    if (cfgData.inner_core && enabled.has('inner_core')) {
      const strokeAlpha = 0.25;
      const stroke = `rgba(120,170,200,${strokeAlpha * ringStrength})`;
      const width = 1.2;
      svg += `<circle cx="${cx}" cy="${cy}" r="${cfgData.inner_core.radius}" fill="none" stroke="${stroke}" stroke-width="${width}" />`;
    }

    Object.entries(ringMap).forEach(([ringName, nodes]) => {
      if (!enabled.has(ringName)) return;
      const ringRadius = nodes[0]?.r;
      if (!ringRadius) return;
      const tickStep = 10;
      for (let angle = 0; angle < 360; angle += tickStep) {
        const major = angle % 30 === 0;
        const length = major ? 10 : 6;
        const tickAngle = angle;
        const start = polarPoint(cx, cy, ringRadius - 6, tickAngle);
        const end = polarPoint(cx, cy, ringRadius - 6 - length, tickAngle);
        const alpha = 0.32;
        svg += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="rgba(180,220,255,${alpha})" stroke-width="${major ? 1.6 : 1}" />`;
      }
    });
  }

  if (coreVisual) {
    const { coreR } = coreVisual;
    boardState.nodes.forEach((node) => {
      if (!node.core_adjacent || !node.stone_id || !node.powered) return;
      const idx = node.core_source_idx ?? coreSourceIndex(node.base_theta);
      const src = coreSources[idx];
      if (!src) return;
      const endPos = nodePosition(node);
      const len = Math.hypot(endPos.x, endPos.y) || 1;
      const dirX = endPos.x / len;
      const dirY = endPos.y / len;
      const start = { x: cx + dirX * coreR * 0.92, y: cy + dirY * coreR * 0.92 };
      const end = { x: cx + endPos.x - dirX * VISUAL_CFG.inject.inset, y: cy + endPos.y - dirY * VISUAL_CFG.inject.inset };
      const color = WUXING_COLORS[src.element] || '#9fd0ff';
      svg += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="${rgba(color, 0.65)}" stroke-width="${VISUAL_CFG.inject.width}" stroke-linecap="round" />`;
      svg += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="${rgba(color, 0.22)}" stroke-width="${VISUAL_CFG.inject.glowWidth}" stroke-linecap="round" />`;
    });
  }

  if (showEdges) {
    const dashOffset = -((now * 0.05) % 24);
    let edgesToDraw = boardState.edges.filter((edge) => edge.connected);
    if (lineMode === 'element') {
      edgesToDraw = edgesToDraw.filter((edge) => edge.dominant_element === lineElement || edge.source_element === lineElement);
    } else if (lineMode === 'path') {
      edgesToDraw = pathEdges ? edgesToDraw.filter((edge) => pathEdges.has(wireKey(edge.a, edge.b))) : [];
    }
    edgesToDraw.forEach((edge) => {
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      if (!a || !b) return;
      if (!enabled.has(a.ring) || !enabled.has(b.ring)) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      const dominant = edge.dominant_element || edge.source_element;
      const edgeColor = WUXING_COLORS[dominant] || 'rgba(120,220,255,0.9)';
      const pathBoost = pathEdges && pathEdges.has(wireKey(edge.a, edge.b));
      const baseAlpha = lineMode === 'all' && pathEdges ? (pathBoost ? 0.22 : 0.06) : VISUAL_CFG.line.baseAlpha;
      const lineAlpha = lineMode === 'all' && pathEdges ? (pathBoost ? 0.95 : 0.2) : VISUAL_CFG.line.glowAlpha;
      const width = pathBoost ? VISUAL_CFG.line.pathWidth : VISUAL_CFG.line.baseWidth;
      const solidAlpha = edge.active ? baseAlpha : baseAlpha * 0.45;
      svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="${rgba(edgeColor, solidAlpha * edgeStrength)}" stroke-width="${width}" />`;
      if (edge.active) {
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="${rgba(edgeColor, lineAlpha * edgeStrength)}" stroke-width="${pathBoost ? 3.3 : 2.2}" stroke-linecap="round" stroke-dasharray="8 10" stroke-dashoffset="${dashOffset}" />`;
      }
      if ((edge.turbulence || 0) > QI_CFG.turbulence_dash) {
        const ratioColor = mixColorFromRatio(edge.qi_ratio || normalizeQi(edge.qi_comp || zeroQi()));
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="${rgba(ratioColor, 0.8)}" stroke-width="${VISUAL_CFG.line.dashedWidth}" stroke-dasharray="4 6" />`;
      }
    });
  }

  if (runtime.flash) {
    const elapsed = now - runtime.flash.start;
    const t = Math.min(elapsed / runtime.flash.duration, 1);
    const alphaOut = Math.max(0, 1 - t);
    runtime.flash.broken.forEach((key) => {
      const [aId, bId] = key.split('|');
      const a = boardState.nodes.find((n) => n.id === aId);
      const b = boardState.nodes.find((n) => n.id === bId);
      if (!a || !b) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(255,90,90,${alphaOut})" stroke-width="6" />`;
      const midX = cx + (pa.x + pb.x) / 2;
      const midY = cy + (pa.y + pb.y) / 2;
      svg += `<circle cx="${midX}" cy="${midY}" r="${5 - t * 3}" fill="rgba(255,140,120,${alphaOut})" />`;
    });
    if (t >= 1) runtime.flash = null;
  }

  boardState.nodes.forEach((node) => {
    const isEnabled = enabled.has(node.ring);
    const pos = nodePosition(node);
    const stone = STONES.find((s) => s.id === node.stone_id);
    const displayElem = stone ? stone.element : node.elem;
    const elemColor = colors[displayElem] || WUXING_COLORS[displayElem] || '#4fe6ff';
    const strokeColor = rgba(elemColor, 0.9);
    const neutralFill = highContrast ? 'rgba(230,240,250,0.55)' : 'rgba(210,220,235,0.38)';
    const baseRadius = nodeRadius(node);
    const hoverBoost = runtime.hoveredNodeId === node.id ? 1.4 : 0;
    const selected = runtime.selectedNodeId === node.id;
    const breathe = 1 + Math.sin(now / 320) * 0.08;

    if (!isEnabled) {
      svg += `<circle class="node-dot disabled" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${NODE_STYLE.radius.disabled}" fill="rgba(120,130,140,0.18)" stroke="rgba(180,190,200,0.35)" stroke-width="1.5" />`;
      return;
    }

    if (!node.lit) {
      svg += `<circle class="node-glow" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 6}" fill="${rgba(elemColor, NODE_STYLE.glow * 0.4)}" filter="url(#node-glow)" opacity="${runtime.hoveredNodeId === node.id ? 0.9 : 0}" />`;
      svg += `<circle class="node-dot normal" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + hoverBoost}" fill="${neutralFill}" stroke="${strokeColor}" stroke-width="1.8" />`;
    } else if (node.lit && !node.powered) {
      const glowSize = baseRadius + 7 + Math.sin(now / 300) * 1.2;
      svg += `<circle class="node-glow" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${glowSize}" fill="${rgba(elemColor, glowStrength)}" filter="url(#node-glow)" />`;
      svg += `<circle class="node-dot lit" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${(baseRadius + hoverBoost + 1) * breathe}" fill="${neutralFill}" stroke="${strokeColor}" stroke-width="2.4" />`;
    } else {
      const glowSize = baseRadius + 10 + Math.sin(now / 260) * 1.6;
      svg += `<circle class="node-glow" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${glowSize}" fill="${rgba(elemColor, glowStrength)}" filter="url(#node-glow)" />`;
      svg += `<circle class="node-dot powered" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + hoverBoost + 1}" fill="${neutralFill}" stroke="${strokeColor}" stroke-width="2.8" />`;
    }

    if (selected) {
      svg += `<circle class="node-selected" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 7}" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.8" />`;
      svg += `<circle class="node-selected" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 10}" fill="none" stroke="rgba(120,220,255,0.7)" stroke-width="1.2" />`;
    }
    if (node.core_adjacent) {
      const idx = node.core_source_idx ?? coreSourceIndex(node.base_theta);
      const src = coreSources[idx];
      const haloColor = src ? WUXING_COLORS[src.element] : '#9fd0ff';
      const haloAlpha = node.stone_id ? 0.55 : 0.22;
      svg += `<circle cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 8}" fill="none" stroke="${rgba(haloColor, haloAlpha)}" stroke-width="1.6" />`;
    }
    {
      const typeKey = node.slot_type || SLOT_TYPES.normal;
      const style = SLOT_STYLE[typeKey] || SLOT_STYLE.normal;
      const outlineR = baseRadius + VISUAL_CFG.slot.outline + (typeKey === SLOT_TYPES.core ? 3 : 0);
      const alpha = node.stone_id ? 0.8 : 0.45;
      const fillAlpha = node.stone_id ? style.fill + 0.04 : style.fill;
      const stroke = rgba(style.stroke, alpha);
      const fill = rgba(style.stroke, fillAlpha);
      const x = cx + pos.x;
      const y = cy + pos.y;

      if (typeKey === SLOT_TYPES.core) {
        svg += `<circle cx="${x}" cy="${y}" r="${outlineR}" fill="${fill}" stroke="${stroke}" stroke-width="${style.width}" />`;
        svg += `<circle cx="${x}" cy="${y}" r="${outlineR + 5}" fill="none" stroke="${rgba(style.stroke, 0.35)}" stroke-width="1.6" />`;
      } else if (typeKey === SLOT_TYPES.skill) {
        const side = outlineR * 2;
        svg += `<rect x="${x - side / 2}" y="${y - side / 2}" width="${side}" height="${side}" rx="4" ry="4" fill="${fill}" stroke="${stroke}" stroke-width="${style.width}" />`;
      } else if (typeKey === SLOT_TYPES.mod) {
        const r = outlineR;
        svg += `<polygon points="${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}" fill="${fill}" stroke="${stroke}" stroke-width="${style.width}" />`;
        const r2 = r * 0.65;
        svg += `<polygon points="${x},${y - r2} ${x + r2},${y} ${x},${y + r2} ${x - r2},${y}" fill="none" stroke="${rgba(style.stroke, 0.4)}" stroke-width="1.2" />`;
      } else if (typeKey === SLOT_TYPES.stat) {
        svg += `<circle cx="${x}" cy="${y}" r="${outlineR}" fill="${fill}" stroke="${stroke}" stroke-width="${style.width}" stroke-dasharray="4 6" />`;
      } else {
        svg += `<circle cx="${x}" cy="${y}" r="${outlineR}" fill="none" stroke="${stroke}" stroke-width="${style.width}" />`;
      }

      if (style.text) {
        svg += `<text x="${x}" y="${y + 4}" text-anchor="middle" font-size="${VISUAL_CFG.slot.text + 1}" fill="${rgba(style.stroke, 0.95)}" font-weight="700">${style.text}</text>`;
      }
    }

    if (node.type === 'core') {
      svg += `<circle cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 12}" fill="none" stroke="rgba(255,215,140,0.65)" stroke-width="2" />`;
      svg += `<circle cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 16}" fill="none" stroke="rgba(255,215,140,0.28)" stroke-width="3" />`;
    }

    if (node.type === 'core' || node.size === 'major' || node.type === 'keystone' || node.type === 'major') {
      const mark = baseRadius * 0.55;
      const x = cx + pos.x;
      const y = cy + pos.y;
      svg += `<path d="M ${x} ${y - mark} L ${x + mark} ${y} L ${x} ${y + mark} L ${x - mark} ${y} Z" fill="rgba(10,10,14,0.55)" stroke="rgba(255,255,255,0.8)" stroke-width="1" />`;
    }

    svg += renderComponentGlyph(node, cx + pos.x, cy + pos.y, baseRadius);
    if (node.componentType === 'SWITCH' && !node.switchOn) {
      svg += `<line x1="${cx + pos.x - baseRadius * 0.8}" y1="${cy + pos.y - baseRadius * 0.8}" x2="${cx + pos.x + baseRadius * 0.8}" y2="${cy + pos.y + baseRadius * 0.8}" stroke="rgba(255,90,90,0.8)" stroke-width="1.4" />`;
    }

    if (showLabels) {
      svg += `<text x="${cx + pos.x}" y="${cy + pos.y - 12}" font-size="10" fill="#9fb4c8" text-anchor="middle">${node.slot_idx >= 0 ? node.slot_idx : '核'}</text>`;
    }
  });

  if (runtime.sparks) {
    const poweredEdges = boardState.edges.filter((edge) => {
      if (!edge.active) return false;
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      return a && b && a.powered && b.powered;
    });
    const density = Math.max(1, Math.min(5, ui.channelCount || 3));
    poweredEdges.forEach((edge, idx) => {
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      if (!a || !b) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      for (let i = 0; i < density; i += 1) {
        const speed = 0.0005 + i * 0.00008;
        const p = (now * speed + idx * 0.23 + i * 0.2) % 1;
        const x = pa.x * (1 - p) + pb.x * p;
        const y = pa.y * (1 - p) + pb.y * p;
        svg += `<circle cx="${cx + x}" cy="${cy + y}" r="${2.5 - i * 0.3}" fill="rgba(180,255,255,0.9)" />`;
      }
    });
  }

  svg += '</g></svg>';
  dom.container.innerHTML = svg;
}

function updateHud() {
  if (dom.realmSelect.options.length === 0) {
    const realms = Object.keys(cfgData.realm_rules || {});
    dom.realmSelect.innerHTML = realms.map((r) => `<option value="${r}">${r}</option>`).join('');
  }
  dom.realmSelect.value = boardState.realm;
  if (dom.linggenSelect && dom.linggenSelect.options.length === 0) {
    dom.linggenSelect.innerHTML = LINGGEN_PROFILES.map((p) => `<option value="${p.id}">${p.name}</option>`).join('');
  }
  if (dom.linggenSelect) dom.linggenSelect.value = boardState.linggen_id;
  if (dom.stoneSelect && dom.stoneSelect.options.length === 0) {
    dom.stoneSelect.innerHTML = STONES.map((s) => `<option value="${s.id}">[${stoneCategoryLabel(s.category)}] ${s.name}</option>`).join('');
    runtime.selectedStoneId = STONES[0]?.id || null;
  }
  dom.hudPower.textContent = `${boardState.qi_used || 0} / ${boardState.qi_cap}`;
  dom.hudBandwidth.textContent = `${boardState.bandwidth_used || 0} / ${boardState.bandwidth_cap}`;
  const lit = boardState.nodes.filter((n) => n.lit).length;
  const powered = boardState.nodes.filter((n) => n.powered).length;
  dom.hudCounts.textContent = `${lit} / ${powered}`;
  dom.hudBonus.textContent = boardState.main_element || '无';
  if (dom.hudRealmBonus) {
    const rule = boardState.realm_rule || cfgData.realm_rules?.[boardState.realm] || {};
    const skillMul = rule.skill_mul ?? 1;
    const bandMul = rule.bandwidth_mul ?? 0.8;
    const coreCap = rule.core_stone_cap ?? 0;
    dom.hudRealmBonus.textContent = `技能×${skillMul.toFixed(2)} / 带宽×${bandMul.toFixed(2)} / 核心上限${coreCap}`;
  }
  dom.cfgHash.textContent = cfgHash;
  dom.cfgVersion.textContent = cfgData.ruleset_version || '-';
  dom.cfgMtime.textContent = cfgMtime;
  if (dom.lineMode) dom.lineMode.value = boardState.ui?.lineMode || 'all';
  if (dom.lineElement) dom.lineElement.value = boardState.ui?.lineElement || '水';
  if (dom.lineElement) dom.lineElement.disabled = (boardState.ui?.lineMode || 'all') !== 'element';
}

function updateDetail(nodeId) {
  const node = boardState.nodes.find((n) => n.id === nodeId) || boardState.nodes.find((n) => n.id === 'core');
  if (!node) return;
  const stone = STONES.find((s) => s.id === node.stone_id);
  const slotText = slotTypeLabel(node);
  const trigramSymbol = TRIGRAM_SYMBOLS[node.trigram] || '';
  dom.detail.name.textContent = node.name || node.id;
  dom.detail.element.textContent = stone ? stone.element : (node.core_source_element || node.elem);
  dom.detail.type.textContent = slotText;
  dom.detail.trigram.textContent = `${trigramSymbol} ${node.trigram}`;
  dom.detail.component.textContent = '-';
  const effectText = stone ? `${stone.name} · ${stoneCategoryLabel(stone.category)}` : slotText;
  dom.detail.effect.textContent = effectText;
  dom.detail.power.textContent = node.powered ? '通气' : node.lit ? '已插石' : '未插石';
  dom.detail.reason.textContent = nodeReason.get(node.id) || '-';
  if (dom.toggleSwitch) {
    dom.toggleSwitch.classList.add('hidden');
  }

  dom.stats.atk.textContent = Math.round(10 + poweredStat('atk'));
  dom.stats.crit.textContent = Math.round(4 + poweredStat('crit'));
  dom.stats.hp.textContent = Math.round(18 + poweredStat('hp'));
  dom.stats.shield.textContent = Math.round(6 + poweredStat('shield'));
  dom.stats.mana.textContent = Math.round(6 + poweredStat('mana'));
  dom.stats.regen.textContent = Math.round(3 + poweredStat('regen'));
}

function mapRing(ring) {
  if (ring === 'inner_core') return 'CORE';
  if (ring === 'inner') return 'INNER';
  if (ring === 'mid') return 'MIDDLE';
  if (ring === 'outer') return 'OUTER';
  return 'INNER';
}

function slotTypeLabel(node) {
  let base = '普通槽';
  if (node.slot_type === SLOT_TYPES.skill) base = '技能槽';
  if (node.slot_type === SLOT_TYPES.mod) base = '改造槽';
  if (node.slot_type === SLOT_TYPES.stat) base = '属性槽';
  if (node.slot_type === SLOT_TYPES.core) base = '核心槽';
  if (node.core_adjacent) return `核心入口·${base}`;
  return base;
}

function stoneCategoryLabel(category) {
  if (category === STONE_CATEGORIES.SKILL) return '技能';
  if (category === STONE_CATEGORIES.MOD) return '改造';
  if (category === STONE_CATEGORIES.STAT) return '属性';
  if (category === STONE_CATEGORIES.CORE) return '核心';
  return '通用';
}

const SLOT_ACCEPTS = {
  [SLOT_TYPES.skill]: [STONE_CATEGORIES.SKILL],
  [SLOT_TYPES.stat]: [STONE_CATEGORIES.STAT],
  [SLOT_TYPES.mod]: [STONE_CATEGORIES.MOD],
  [SLOT_TYPES.normal]: [STONE_CATEGORIES.STAT],
  [SLOT_TYPES.core]: [STONE_CATEGORIES.CORE],
};

function canPlaceStone(node, stone) {
  if (!stone) return true;
  const allowed = SLOT_ACCEPTS[node.slot_type] || [];
  return allowed.includes(stone.category);
}

function coreStoneLimitOk(node, stone) {
  if (!stone || stone.category !== STONE_CATEGORIES.CORE) return true;
  const cap = boardState.realm_rule?.core_stone_cap ?? 0;
  if (cap <= 0) return false;
  const coreCount = boardState.nodes.filter((n) => {
    if (!n.stone_id) return false;
    const s = STONES.find((it) => it.id === n.stone_id);
    return s && s.category === STONE_CATEGORIES.CORE;
  }).length;
  if (node.stone_id) return true;
  return coreCount < cap;
}

function computePathEdges(nodeId) {
  const edges = new Set();
  if (!nodeId || !boardState.parentMap) return edges;
  let current = nodeId;
  while (boardState.parentMap.has(current)) {
    const parent = boardState.parentMap.get(current);
    edges.add(wireKey(current, parent));
    current = parent;
  }
  return edges;
}

function runSolver() {
  if (!window.BaguaSolver) {
    showFeedback('求解器未加载');
    return;
  }
  const result = window.BaguaSolver.solveBoard(boardState, {
    stones: STONES,
    trigramMods: TRIGRAM_MODS,
    realmRule: boardState.realm_rule,
  });
  runtime.evalResult = result;
  boardState.main_element = result.dominantElement;
  updateSolverUI(result);
}

function runSimulation() {
  runSolver();
  if (!runtime.evalResult || !window.BaguaSolver?.simulateBoss) {
    showFeedback('无法启动模拟');
    return;
  }
  const fight = window.BaguaSolver.simulateBoss(runtime.evalResult);
  dom.sim.win.textContent = fight.win ? '胜利' : '失败';
  const ttk = Number.isFinite(fight.timeToKill) ? `${fight.timeToKill.toFixed(1)}s` : '-';
  const survive = Number.isFinite(fight.timeSurvive) ? `${fight.timeSurvive.toFixed(1)}s` : '-';
  dom.sim.ttk.textContent = ttk;
  dom.sim.survive.textContent = survive;
  dom.sim.logs.textContent = fight.logs?.join('\n') || '';
  const payload = {
    timestamp: Date.now(),
    bd: buildBDInfo(),
    result: runtime.evalResult,
    fight,
  };
  localStorage.setItem('battle_log', JSON.stringify(payload));
}

function buildBDInfo() {
  const stoneMap = new Map(STONES.map((s) => [s.id, s]));
  const slots = boardState.nodes.filter((n) => n.stone_id);
  const byCategory = { SKILL: [], STAT: [], MOD: [], CORE: [] };
  const byElement = { 金: 0, 木: 0, 水: 0, 火: 0, 土: 0 };
  slots.forEach((node) => {
    const stone = stoneMap.get(node.stone_id);
    if (!stone) return;
    byElement[stone.element] = (byElement[stone.element] || 0) + 1;
    const cat = stone.category || 'STAT';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push({
      id: stone.id,
      name: stone.name,
      element: stone.element,
      slot: node.id,
      slotType: slotTypeLabel(node),
      trigram: node.trigram,
    });
  });
  return {
    name: boardState.bd_name || '自定义构筑',
    linggen: boardState.linggen_profile?.name || boardState.linggen_id,
    dominant: boardState.main_element,
    elementCounts: byElement,
    stones: byCategory,
  };
}

function updateSolverUI(result) {
  if (!dom.sim?.dps) return;
  dom.sim.dps.textContent = Math.round(result.totals.dps);
  dom.sim.ehp.textContent = Math.round(result.totals.ehp);
  dom.sim.sustain.textContent = Math.round(result.totals.sustain);
  dom.sim.stability.textContent = Math.round(result.totals.stability);
  dom.stats.atk.textContent = Math.round(result.totals.dps);
  dom.stats.crit.textContent = Math.round(result.totals.stability);
  dom.stats.hp.textContent = Math.round(result.totals.ehp);
  dom.stats.shield.textContent = Math.round(result.totals.stability);
  dom.stats.mana.textContent = Math.round(result.totals.sustain);
  dom.stats.regen.textContent = Math.round(result.totals.sustain);
}

function poweredStat(key) {
  let total = 0;
  boardState.nodes.forEach((node) => {
    if (!node.powered) return;
    const stone = STONES.find((s) => s.id === node.stone_id);
    const elem = stone ? stone.element : node.elem;
    if (elem === '火' && key === 'atk') total += 2;
    if (elem === '金' && key === 'crit') total += 1.5;
    if (elem === '土' && key === 'hp') total += 2;
    if (elem === '水' && key === 'mana') total += 1.5;
    if (elem === '木' && key === 'regen') total += 1.2;
  });
  return total;
}

function showFeedback(message) {
  const el = document.getElementById('feedback');
  if (!el) return;
  el.textContent = message;
  el.classList.remove('hidden');
  el.classList.add('show');
  clearTimeout(runtime.feedbackTimer);
  runtime.feedbackTimer = setTimeout(() => {
    el.classList.remove('show');
  }, 900);
}

function updateDebugOverlay(now) {
  if (!boardState.ui?.debug || !dom.debugOverlay) return;
  if (now - runtime.debugLastUpdate < 120) return;
  runtime.debugLastUpdate = now;
  const activeEdges = boardState.edges.filter((e) => e.active).length;
  const nodeLines = boardState.nodes
    .map((node) => {
      const pos = nodePosition(node);
      return `${node.id} (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}) c:${node.connectionCount || 0}`;
    })
    .join('\n');
  dom.debugOverlay.textContent = `FPS: ${runtime.fps.toFixed(1)}\nEdges: ${activeEdges}/${boardState.edges.length}\nNodes:\n${nodeLines}`;
}

function refreshReconfig() {
  const unlocked = cfgData.realm_rules[boardState.realm]?.unlock?.includes('reconfig');
  dom.reconfig.panel.classList.toggle('hidden', !unlocked);
  if (!unlocked) return;
  const outerNodes = boardState.nodes.filter((n) => n.ring === 'outer');
  dom.reconfig.node.innerHTML = outerNodes.map((n) => `<option value="${n.id}">${n.id}</option>`).join('');
  const slots = outerNodes.length;
  dom.reconfig.slot.innerHTML = Array.from({ length: slots }, (_, i) => `<option value="${i}">${i}</option>`).join('');
}

function rerender(selectedId, opts = {}) {
  if (opts.recompute !== false) {
    recomputeConnectivity(opts.cause || '');
    runtime.needsConnectivityUpdate = false;
  }
  if (selectedId) {
    runtime.selectedNodeId = selectedId;
  }
  renderBoard();
  updateHud();
  refreshReconfig();
  updateDetail(runtime.selectedNodeId || 'core');
  runtime.needsRender = false;
}

function applyStone(node, stoneId) {
  if (!node) return;
  if (!enabledRings().includes(node.ring)) {
    showFeedback('当前境界未解锁该环');
    return;
  }
  const stone = STONES.find((s) => s.id === stoneId);
  if (stoneId && !canPlaceStone(node, stone)) {
    showFeedback('槽位类型不匹配');
    return;
  }
  if (stoneId && !coreStoneLimitOk(node, stone)) {
    showFeedback('当前境界无法承载更多核心强化');
    return;
  }

  const nodesCopy = boardState.nodes.map((n) => ({ ...n }));
  const target = nodesCopy.find((n) => n.id === node.id);
  if (target) {
    target.stone_id = stoneId;
    target.lit = !!stoneId;
  }
  const preview = computeConnectivitySnapshot(nodesCopy);
  if (!preview.powerOk || !preview.bandwidthOk) {
    const parts = [];
    if (!preview.powerOk) {
      const need = preview.powerUsed - boardState.qi_cap;
      parts.push(`灵力不足(${need})`);
    }
    if (!preview.bandwidthOk) {
      const need = preview.bandwidthUsed - boardState.bandwidth_cap;
      parts.push(`通气不足(${need})`);
    }
    showFeedback(`资源不足，无法放置：${parts.join(' / ')}`);
    return;
  }

  node.stone_id = stoneId;
  node.lit = !!stoneId;
  recomputeConnectivity('stone');
  runtime.needsRender = true;
}

function attachEvents() {
  console.log('[attachEvents] binding listeners');
  dom.realmSelect.addEventListener('change', () => {
    boardState.realm = dom.realmSelect.value;
    const rule = cfgData.realm_rules?.[boardState.realm] || {};
    const baseQi = boardState.linggen_profile?.sources?.reduce((sum, s) => sum + s.capacity, 0) || boardState.qi_cap;
    boardState.realm_rule = rule;
    boardState.enabled_rings = rule.rings || ['inner', 'mid', 'outer'];
    boardState.qi_cap = Math.min(baseQi, rule.qi_cap || baseQi);
    boardState.bandwidth_cap = Math.round(boardState.qi_cap * (rule.bandwidth_mul ?? 0.8));
    scheduleUpdate({ recompute: true, cause: 'realm' });
    rerender();
  });
  dom.toggleContrast.addEventListener('change', () => {
    setUIState({ highContrast: dom.toggleContrast.checked }, { log: true });
  });
  dom.toggleBroken.addEventListener('change', () => {
    setUIState({ showBroken: dom.toggleBroken.checked }, { log: true });
  });
  dom.resetZoom?.addEventListener('click', () => {
    setUIState({ scale: 1, panX: 0, panY: 0 }, { log: true });
    runtime.needsRender = true;
  });
  if (dom.lineMode) {
    dom.lineMode.addEventListener('change', () => {
      const mode = dom.lineMode.value;
      setUIState({ lineMode: mode }, { log: true });
      if (dom.lineElement) {
        dom.lineElement.disabled = mode !== 'element';
      }
    });
  }
  if (dom.lineElement) {
    dom.lineElement.addEventListener('change', () => {
      setUIState({ lineElement: dom.lineElement.value }, { log: true });
    });
  }
  dom.resetZoom?.addEventListener('click', () => {
    setUIState({ scale: 1 }, { log: true });
    runtime.needsRender = true;
  });
  if (dom.lineMode) {
    dom.lineMode.addEventListener('change', () => {
      const mode = dom.lineMode.value;
      setUIState({ lineMode: mode }, { log: true });
      if (dom.lineElement) {
        dom.lineElement.disabled = mode !== 'element';
      }
    });
  }
  if (dom.lineElement) {
    dom.lineElement.addEventListener('change', () => {
      setUIState({ lineElement: dom.lineElement.value }, { log: true });
    });
  }
  dom.clearLit.addEventListener('click', () => {
    boardState.nodes.forEach((n) => { n.stone_id = null; n.lit = false; });
    recomputeConnectivity('stone');
    runtime.needsRender = true;
  });
  dom.linggenSelect?.addEventListener('change', () => {
    const next = LINGGEN_PROFILES.find((p) => p.id === dom.linggenSelect.value);
    if (next) {
      boardState.linggen_id = next.id;
      boardState.linggen_profile = next;
      boardState.core_sources = next.sources;
      const rule = cfgData.realm_rules?.[boardState.realm] || {};
      const baseQi = next.sources.reduce((sum, s) => sum + s.capacity, 0);
      boardState.qi_cap = Math.min(baseQi, rule.qi_cap || baseQi);
      boardState.bandwidth_cap = Math.round(boardState.qi_cap * (rule.bandwidth_mul ?? 0.8));
      recomputeConnectivity('linggen');
      runtime.needsRender = true;
    }
  });
  dom.stoneSelect?.addEventListener('change', () => {
    runtime.selectedStoneId = dom.stoneSelect.value;
  });
  dom.clearSlot?.addEventListener('click', () => {
    dom.clearSlot.dataset.active = dom.clearSlot.dataset.active === '1' ? '0' : '1';
    dom.clearSlot.textContent = dom.clearSlot.dataset.active === '1' ? '清空槽位(已激活)' : '清空槽位';
  });

  dom.container.addEventListener('pointermove', (event) => {
    if (runtime.panning && runtime.panStart) {
      const dx = event.clientX - runtime.panStart.x;
      const dy = event.clientY - runtime.panStart.y;
      const scale = boardState.ui.scale ?? 1;
      boardState.ui.panX = (boardState.ui.panX || 0) + dx / scale;
      boardState.ui.panY = (boardState.ui.panY || 0) + dy / scale;
      runtime.panStart = { x: event.clientX, y: event.clientY };
      runtime.needsRender = true;
      return;
    }
    const node = hitTestNode(event);
    if (!node) {
      runtime.hoveredNodeId = null;
      runtime.pathEdges = null;
      dom.tooltip.style.opacity = 0;
      const edge = hitTestEdge(event);
      if (edge) {
        const ratio = edge.qi_ratio || normalizeQi(edge.qi_comp || zeroQi());
        const ratioText = `金${(ratio['金'] * 100).toFixed(0)} 木${(ratio['木'] * 100).toFixed(0)} 水${(ratio['水'] * 100).toFixed(0)} 火${(ratio['火'] * 100).toFixed(0)} 土${(ratio['土'] * 100).toFixed(0)}`;
        const reason = edge.state === 'CONNECTED_NO_QI' ? edge.reason || '无气' : '通气中';
        dom.tooltip.style.opacity = 1;
        dom.tooltip.style.left = `${event.clientX}px`;
        dom.tooltip.style.top = `${event.clientY}px`;
        dom.tooltip.textContent = `气脉 ${edge.dominant_element || edge.source_element || '-'} | ${ratioText} | 乱流${(edge.turbulence || 0).toFixed(2)} | ${reason}`;
      }
    } else {
      runtime.hoveredNodeId = node.id;
      runtime.pathEdges = computePathEdges(node.id);
      dom.tooltip.style.opacity = 1;
      dom.tooltip.style.left = `${event.clientX}px`;
      dom.tooltip.style.top = `${event.clientY}px`;
      const stone = STONES.find((s) => s.id === node.stone_id);
      const effectText = stone ? `${stone.name}/${stoneCategoryLabel(stone.category)}` : '空槽';
      const powerState = node.powered ? '通气' : node.lit ? '已插石' : '未插石';
      const trigramText = `${TRIGRAM_SYMBOLS[node.trigram] || ''}${node.trigram}`;
      const slotText = slotTypeLabel(node);
      const sourceText = node.source_element ? `${node.source_element}脉` : '无源';
      const ratio = node.qi_ratio || normalizeQi(node.qi_out || zeroQi());
      const ratioText = `金${(ratio['金'] * 100).toFixed(0)} 木${(ratio['木'] * 100).toFixed(0)} 水${(ratio['水'] * 100).toFixed(0)} 火${(ratio['火'] * 100).toFixed(0)} 土${(ratio['土'] * 100).toFixed(0)}`;
      dom.tooltip.textContent = `${node.name || node.id} | ${powerState} | ${trigramText} | ${slotText} | ${sourceText} | ${ratioText} | 乱流${(node.turbulence || 0).toFixed(2)} | ${effectText}`;
    }
    runtime.needsRender = true;
  });

  dom.container.addEventListener('wheel', (event) => {
    event.preventDefault();
    const delta = Math.sign(event.deltaY);
    const current = boardState.ui.scale ?? 1;
    const next = Math.min(2.0, Math.max(0.6, current - delta * 0.06));
    setUIState({ scale: next }, { log: true });
  }, { passive: false });

  dom.container.addEventListener('pointerleave', () => {
    dom.tooltip.style.opacity = 0;
    runtime.hoveredNodeId = null;
    runtime.pathEdges = null;
    runtime.showNeighborHints = false;
    runtime.panning = false;
    runtime.panStart = null;
    runtime.needsRender = true;
  });

  dom.container.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    const node = hitTestNode(event);
    if (node) return;
    runtime.panning = true;
    runtime.panStart = { x: event.clientX, y: event.clientY };
    dom.container.setPointerCapture(event.pointerId);
  });

  dom.container.addEventListener('pointercancel', () => {
    runtime.panning = false;
    runtime.panStart = null;
  });

  dom.container.addEventListener('wheel', (event) => {
    event.preventDefault();
    const delta = Math.sign(event.deltaY);
    const current = boardState.ui.scale ?? 1;
    const next = Math.min(2.0, Math.max(0.6, current - delta * 0.06));
    setUIState({ scale: next }, { log: true });
  }, { passive: false });

  dom.devToggle.addEventListener('click', () => {
    dom.devDrawer.classList.toggle('hidden');
  });
  dom.toggleSectors.addEventListener('change', () => {
    setUIState({ showSectors: dom.toggleSectors.checked }, { log: true });
  });
  dom.toggleRings.addEventListener('change', () => {
    setUIState({ showRings: dom.toggleRings.checked }, { log: true });
  });
  dom.panel.edges.addEventListener('change', () => {
    setUIState({ showEdges: dom.panel.edges.checked }, { log: true });
  });
  dom.panel.labels.addEventListener('change', () => {
    setUIState({ showLabels: dom.panel.labels.checked }, { log: true });
  });
  if (dom.toggleAutoEdges) {
    dom.toggleAutoEdges.addEventListener('change', () => {
      setUIState({ allowAutoEdges: dom.toggleAutoEdges.checked }, { log: true, recompute: true, cause: 'ui' });
    });
  }
  if (dom.toggleNeighborHints) {
    dom.toggleNeighborHints.addEventListener('change', () => {
      setUIState({ showNeighborHints: dom.toggleNeighborHints.checked }, { log: true });
    });
  }
  dom.toggleDebug.addEventListener('change', () => {
    setUIState({ debug: dom.toggleDebug.checked }, { log: true });
    updateDebugOverlay(performance.now());
  });
  dom.channelCount.addEventListener('input', () => {
    setUIState({ channelCount: parseInt(dom.channelCount.value, 10) }, { log: true });
  });
  dom.contactThreshold.addEventListener('input', () => {
    setUIState({ contactThreshold: parseFloat(dom.contactThreshold.value) }, { log: true, recompute: true, cause: 'ui' });
  });
  dom.glowStrength.addEventListener('input', () => {
    setUIState({ glowStrength: parseFloat(dom.glowStrength.value) }, { log: true });
  });
  dom.edgeStrength.addEventListener('input', () => {
    setUIState({ edgeStrength: parseFloat(dom.edgeStrength.value) }, { log: true });
  });
  dom.sectorOpacity.addEventListener('input', () => {
    setUIState({ sectorOpacity: parseFloat(dom.sectorOpacity.value) }, { log: true });
  });
  dom.ringStrength.addEventListener('input', () => {
    setUIState({ ringStrength: parseFloat(dom.ringStrength.value) }, { log: true });
  });
  dom.scale.addEventListener('input', () => {
    setUIState({ scale: parseFloat(dom.scale.value) }, { log: true });
  });
  dom.toggleSwitch.addEventListener('click', () => {
    const node = boardState.nodes.find((n) => n.id === runtime.selectedNodeId);
    if (!node || node.componentType !== 'SWITCH') return;
    node.switchOn = !node.switchOn;
    recomputeConnectivity('switch');
    runtime.needsRender = true;
    updateDetail(node.id);
  });
  dom.simulateBtn?.addEventListener('click', () => {
    runSimulation();
    window.open('battle_log.html', '_blank');
  });
  dom.openLog?.addEventListener('click', () => {
    if (!localStorage.getItem('battle_log')) {
      runSimulation();
    }
    window.open('battle_log.html', '_blank');
  });

  // BD 输出采用自动评估，无需手动触发

  dom.panel.reload.addEventListener('click', async () => {
    await loadConfig();
    await loadBoard();
    const keep = {
      realm: boardState.realm,
      slots: boardState.slots,
      linggen_id: boardState.linggen_id,
    };
    buildBoardState(keep);
    initUIState();
    rerender();
  });

  dom.panel.export.addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(boardState, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'board_state.json';
    a.click();
    URL.revokeObjectURL(a.href);
  });

  dom.panel.reset.addEventListener('click', () => {
    buildBoardState();
    initUIState();
    rerender();
  });

  dom.panel.presetLoad.addEventListener('click', async () => {
    const name = dom.panel.presetSelect.value;
    if (!name) return;
    const { data } = await fetchJson(`./presets/${name}.json`);
    buildBoardState(data);
    initUIState();
    rerender();
  });

  dom.reconfig.apply.addEventListener('click', () => {
    const nodeId = dom.reconfig.node.value;
    const target = parseInt(dom.reconfig.slot.value, 10);
    const outerNodes = boardState.nodes.filter((n) => n.ring === 'outer');
    const node = outerNodes.find((n) => n.id === nodeId);
    const swap = outerNodes.find((n) => n.slot_idx === target);
    if (!node || !swap) return;
    const tempIdx = node.slot_idx;
    node.slot_idx = swap.slot_idx;
    swap.slot_idx = tempIdx;
    node.base_theta = (360 / outerNodes.length) * node.slot_idx;
    swap.base_theta = (360 / outerNodes.length) * swap.slot_idx;
    node.id = `outer_${node.slot_idx}`;
    swap.id = `outer_${swap.slot_idx}`;
    node.name = `外环-${node.slot_idx}`;
    swap.name = `外环-${swap.slot_idx}`;
    rerender(node.id);
  });

  window.addEventListener('keydown', (event) => {
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
    if (event.key === 'Escape') {
      boardState.nodes.forEach((n) => { n.stone_id = null; n.lit = false; });
      runtime.selectedNodeId = null;
      rerender();
    }
  });

  dom.container.addEventListener('pointerup', (event) => {
    if (event.button !== 0) return;
    if (runtime.panning) {
      runtime.panning = false;
      runtime.panStart = null;
      dom.container.releasePointerCapture(event.pointerId);
      return;
    }
    const node = hitTestNode(event);
    if (!node) return;
    runtime.selectedNodeId = node.id;
    if (dom.clearSlot?.dataset?.active === '1') {
      applyStone(node, null);
    } else if (node.stone_id) {
      applyStone(node, null);
    } else {
      applyStone(node, runtime.selectedStoneId);
    }
    updateDetail(node.id);
  });
}

function tick(now) {
  runtime.frames += 1;
  if (now - runtime.lastFpsTime >= 500) {
    runtime.fps = (runtime.frames * 1000) / (now - runtime.lastFpsTime);
    runtime.frames = 0;
    runtime.lastFpsTime = now;
  }

  if (runtime.needsConnectivityUpdate && now - runtime.lastConnectivityUpdate > 30) {
    recomputeConnectivity(runtime.updateCause || 'ui');
    runtime.needsConnectivityUpdate = false;
    runtime.lastConnectivityUpdate = now;
  }

  if (runtime.needsRender || runtime.flash || runtime.sparks) {
    if (now - runtime.lastRender > 33) {
      renderBoard(now);
      updateHud();
      runtime.lastRender = now;
      runtime.needsRender = false;
    }
  }

  updateDebugOverlay(now);
  requestAnimationFrame(tick);
}

async function loadPresets() {
  const presets = ['bd1_dot_core', 'bd2_shield_loop', 'bd3_crit_chain'];
  presetFiles = presets;
  dom.panel.presetSelect.innerHTML = presets.map((p) => `<option value="${p}">${p}</option>`).join('');
}

async function init() {
  console.log('[init] start');
  await loadConfig();
  await loadBoard();
  await loadPresets();
  buildBoardState();
  initUIState();
  attachEvents();
  rerender();
  requestAnimationFrame(tick);
}

init();
