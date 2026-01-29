const dom = {
  container: document.getElementById('canvas-container'),
  steps: Array.from(document.querySelectorAll('#steps-bar .step')),
  realmSelect: document.getElementById('realm-select'),
  hudPower: document.getElementById('hud-power'),
  hudBandwidth: document.getElementById('hud-bandwidth'),
  hudCounts: document.getElementById('hud-counts'),
  hudBonus: document.getElementById('hud-bonus'),
  toggleContrast: document.getElementById('toggle-contrast'),
  toggleBroken: document.getElementById('toggle-broken'),
  togglePorts: document.getElementById('toggle-ports'),
  toggleSnap: document.getElementById('toggle-snap'),
  modeToggle: document.getElementById('mode-toggle'),
  clearLit: document.getElementById('clear-lit'),
  toggleAutoEdges: document.getElementById('toggle-autoedges'),
  toggleNeighborHints: document.getElementById('toggle-neighbors'),
  ringSelect: document.getElementById('ring-select'),
  rotateContinuous: document.getElementById('rotate-continuous'),
  rotateLeft: document.getElementById('rotate-left'),
  rotateRight: document.getElementById('rotate-right'),
  rotateKnob: document.getElementById('rotate-knob'),
  hudRot: document.getElementById('hud-rot'),
  cfgHash: document.getElementById('cfg-hash'),
  cfgVersion: document.getElementById('cfg-version'),
  cfgRot: document.getElementById('cfg-rot'),
  cfgMtime: document.getElementById('cfg-mtime'),
  hex: {
    bits: document.getElementById('hex-bits'),
    trigrams: document.getElementById('hex-trigrams'),
    name: document.getElementById('hex-name'),
    id: document.getElementById('hex-id'),
    mods: document.getElementById('hex-mods'),
  },
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
  bd: {
    atk: document.getElementById('bd-atk'),
    crit: document.getElementById('bd-crit'),
    hp: document.getElementById('bd-hp'),
    fire: document.getElementById('bd-fire'),
    mana: document.getElementById('bd-mana'),
    energy: document.getElementById('bd-energy'),
    active: document.getElementById('bd-active'),
    main: document.getElementById('bd-main'),
    skillMods: document.getElementById('bd-skillmods'),
    triggers: document.getElementById('bd-triggers'),
    summary: document.getElementById('bd-summary'),
    changes: document.getElementById('bd-changes'),
    violations: document.getElementById('bd-violations'),
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
  anim: null,
  flash: null,
  lastActiveEdges: new Set(),
  needsRender: true,
  needsConnectivityUpdate: true,
  sparks: true,
  lastRender: 0,
  hoveredNodeId: null,
  selectedNodeId: 'core',
  drag: null,
  inertia: null,
  suppressClickUntil: 0,
  lastDragTime: 0,
  fps: 0,
  frames: 0,
  lastFpsTime: performance.now(),
  debugLastUpdate: 0,
  lastConnectivityUpdate: 0,
  lastRingOptionsKey: '',
  lastDynamicEdges: new Set(),
  feedbackTimer: null,
  wireStartId: null,
  wireDragActive: false,
  showNeighborHints: false,
  rejectedNodeId: null,
  rejectUntil: 0,
  evalResult: null,
};

const TRIGRAMS = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
const DEFAULT_REALM = '金丹';
const WUXING_COLORS = {
  金: '#E6E6E6',
  木: '#39D98A',
  水: '#3AA0FF',
  火: '#FF4D4D',
  土: '#FFD166',
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

  boardData.nodes.forEach((raw) => {
    if (raw.id === 'core' || raw.ring === 'core') return;
    const ring = ringMap[raw.ring] || raw.ring;
    const baseTheta = (raw.angle != null ? raw.angle : Math.atan2(raw.y, raw.x)) * (180 / Math.PI);
    const radius = raw.radius != null ? raw.radius : Math.hypot(raw.x, raw.y);
    ringBuckets[ring].push({
      id: raw.id,
      name: raw.label || raw.id,
      elem: raw.element,
      type: raw.type || 'normal',
      ring,
      slot_idx: 0,
      base_theta: baseTheta,
      r: radius,
      size: raw.type === 'keystone' || raw.type === 'core' ? 'major' : 'small',
      trigram: trigramByAngle(baseTheta),
      effects: raw.effects || {},
      lit: false,
      powered: false,
    });
  });

  Object.keys(ringBuckets).forEach((ring) => {
    ringBuckets[ring].sort((a, b) => normDeg(a.base_theta) - normDeg(b.base_theta));
    if (ring === 'outer') {
      const byElem = {};
      ringBuckets[ring].forEach((node) => {
        if (!byElem[node.elem]) byElem[node.elem] = [];
        byElem[node.elem].push(node);
      });
      Object.values(byElem).forEach((list) => {
        list.slice(0, 2).forEach((node) => {
          if (node.type === 'keystone') return;
          node.type = 'major';
          node.size = 'major';
        });
      });
    }
    ringBuckets[ring].forEach((node, idx) => {
      node.slot_idx = idx;
      node.id = `${ring}_${idx}`;
      assignComponent(node);
      nodes.push(node);
    });
  });

  nodes.push({
    id: 'core',
    name: '核心',
    elem: '土',
    type: 'core',
    ring: 'inner',
    slot_idx: -1,
    base_theta: 0,
    r: 0,
    size: 'major',
    trigram: '坤',
    effects: { core: 1 },
    lit: true,
    powered: true,
  });
  assignComponent(nodes[nodes.length - 1]);

  if (cfgData.inner_core) {
    const slots = cfgData.inner_core.slots;
    const radius = cfgData.inner_core.radius;
    for (let i = 0; i < slots; i += 1) {
      const theta = (360 / slots) * i;
      nodes.push({
        id: `inner_core_${i}`,
        name: `内核-${i}`,
        elem: '土',
        type: 'major',
        ring: 'inner_core',
        slot_idx: i,
        base_theta: theta,
        r: radius,
        size: 'major',
        trigram: trigramByAngle(theta),
        effects: { inner_core: 1 },
        lit: false,
        powered: false,
      });
      assignComponent(nodes[nodes.length - 1]);
    }
  }

  const ringRot = { inner: 0, mid: 0, outer: 0, inner_core: 0 };
  if (preset && preset.rot_deg) {
    Object.keys(preset.rot_deg).forEach((key) => {
      ringRot[key] = preset.rot_deg[key];
    });
  }

  const realm = preset?.realm || DEFAULT_REALM;
  const litSet = new Set(preset?.invested || []);
  nodes.forEach((node) => {
    if (litSet.has(node.id)) {
      node.lit = true;
    }
  });
  const qiCap = cfgData.realm_rules[realm]?.qi_cap || 10;
  const baseBandwidth = cfgData.bandwidth_cap || 12;
  const baseStability = 10;
  const presetResources = preset?.resources || {};
  const baseQiCap = presetResources.power ?? qiCap;
  const baseBandwidthCap = presetResources.bandwidth ?? baseBandwidth;
  const baseStabilityCap = presetResources.stability ?? baseStability;

  boardState = {
    realm,
    base_qi_cap: baseQiCap,
    qi_cap: baseQiCap,
    qi_used: 0,
    ring_rot_deg: ringRot,
    nodes,
    edges: [],
    wires: new Map(),
    neighborMap: new Map(),
    lit: litSet,
    base_bandwidth_cap: baseBandwidthCap,
    bandwidth_cap: baseBandwidthCap,
    stability_cap: baseStabilityCap,
    hex_bits: [0, 0, 0, 0, 0, 0],
    hex_id: 0,
    trigram_lower: '坤',
    trigram_upper: '坤',
    hex_name: '坤上坤下',
    hex_effects: [],
    hex_mods: { ...HEX_MOD_DEFAULTS },
    ruleset_version: cfgData.ruleset_version || 'v1',
    cfg_hash: cfgHash,
    ui: {},
  };
  window.boardState = boardState;

  if (Array.isArray(preset?.wires)) {
    preset.wires.forEach((edge) => {
      if (!edge?.a || !edge?.b) return;
      const key = wireKey(edge.a, edge.b);
      boardState.wires.set(key, {
        a: edge.a,
        b: edge.b,
        enabled: edge.enabled !== false,
        component: edge.component || 'wire',
        directed: edge.directed || false,
        bandwidthCost: edge.bandwidthCost ?? edgeBandwidthCost(edge.component || 'wire'),
      });
    });
  }
}

function initUIState() {
  boardState.ui = {
    selectedRing: dom.ringSelect?.value || 'mid',
    highContrast: dom.toggleContrast?.checked ?? false,
    showBroken: dom.toggleBroken?.checked ?? false,
    showEdges: dom.panel.edges?.checked ?? true,
    showLabels: dom.panel.labels?.checked ?? false,
    showSectors: dom.toggleSectors?.checked ?? true,
    showRings: dom.toggleRings?.checked ?? true,
    debug: dom.toggleDebug?.checked ?? false,
    snap: dom.toggleSnap?.checked ?? true,
    edgeStrength: parseFloat(dom.edgeStrength?.value ?? 0.6),
    glowStrength: parseFloat(dom.glowStrength?.value ?? 0.18),
    sectorOpacity: parseFloat(dom.sectorOpacity?.value ?? 0.05),
    ringStrength: parseFloat(dom.ringStrength?.value ?? 0.55),
    scale: parseFloat(dom.scale?.value ?? 0.7),
    contactThreshold: parseFloat(dom.contactThreshold?.value ?? cfgData.bridge_threshold_deg ?? 12),
    channelCount: parseInt(dom.channelCount?.value ?? 3, 10),
    mode: 'power',
    allowAutoEdges: false,
    showNeighborHints: dom.toggleNeighborHints?.checked ?? false,
  };
  runtime.selectedNodeId = 'core';
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
  return cfgData.realm_rules[boardState.realm]?.rings || ['inner', 'mid', 'outer'];
}

function ringIndex() {
  const map = {};
  boardState.nodes.forEach((node) => {
    if (!map[node.ring]) map[node.ring] = [];
    map[node.ring].push(node);
  });
  Object.keys(map).forEach((ring) => {
    map[ring].sort((a, b) => a.slot_idx - b.slot_idx);
  });
  return map;
}

function ringOrder() {
  const order = ['inner_core', 'inner', 'mid', 'outer'];
  const available = new Set(Object.keys(ringIndex()));
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
  return normDeg(node.base_theta + (boardState.ring_rot_deg[node.ring] || 0));
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

function buildNeighborMap() {
  const ringMap = ringIndex();
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

  const order = ringOrder();
  const core = boardState.nodes.find((n) => n.id === 'core');
  if (core) {
    const innerNodes = (ringMap.inner || []).filter((n) => n.id !== 'core');
    const maxCore = NEIGHBOR_RULES.coreInnerMax;
    const list = maxCore === 'all' ? innerNodes : innerNodes
      .map((node) => ({ node, diff: angleDiff(nodeAngleDeg(node), 0) }))
      .sort((a, b) => a.diff - b.diff)
      .slice(0, Math.min(maxCore || 6, innerNodes.length))
      .map((entry) => entry.node);
    list.forEach((node) => addNeighbor(core, node));
  }

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

  boardState.neighborMap = map;
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

function computePowerState(litSet) {
  const nodeMap = new Map(boardState.nodes.map((n) => [n.id, n]));
  const enabled = new Set(enabledRings());
  const adjacency = new Map();
  boardState.wires.forEach((edge) => {
    if (!edge.enabled) return;
    if (!adjacency.has(edge.a)) adjacency.set(edge.a, []);
    if (!adjacency.has(edge.b)) adjacency.set(edge.b, []);
    adjacency.get(edge.a).push(edge.b);
    adjacency.get(edge.b).push(edge.a);
  });

  const parent = new Map();
  const visited = new Set(['core']);
  const queue = ['core'];
  while (queue.length) {
    const current = queue.shift();
    const neighbors = adjacency.get(current) || [];
    neighbors.forEach((next) => {
      if (visited.has(next)) return;
      const curNode = nodeMap.get(current);
      const nextNode = nodeMap.get(next);
      if (!curNode || !nextNode) return;
      if (!enabled.has(nextNode.ring)) return;
      if (!isConductive(nextNode)) return;
      if (!diodeAllows(curNode, nextNode)) return;
      visited.add(next);
      parent.set(next, current);
      queue.push(next);
    });
  }

  const reachableLit = new Set([...litSet].filter((id) => visited.has(id)));
  const activeSet = new Set();
  reachableLit.forEach((id) => {
    let cur = id;
    while (cur && cur !== 'core') {
      const p = parent.get(cur);
      if (!p) break;
      activeSet.add(wireKey(cur, p));
      cur = p;
    }
  });

  let powerBudget = boardState.qi_cap;
  let bandwidthBudget = boardState.bandwidth_cap;
  reachableLit.forEach((id) => {
    const node = nodeMap.get(id);
    if (!node) return;
    if (node.componentType === 'SOURCE') powerBudget += 2;
    if (node.componentType === 'CAPACITOR') bandwidthBudget += 2;
    if (node.componentType === 'AMPLIFIER') bandwidthBudget += 1;
  });

  let powerUsed = 0;
  reachableLit.forEach((id) => {
    const node = nodeMap.get(id);
    if (node) powerUsed += nodePowerCost(node);
  });

  let bandwidthUsed = 0;
  activeSet.forEach((key) => {
    const edge = boardState.wires.get(key);
    bandwidthUsed += edge?.bandwidthCost ?? 1;
  });

  return { reachableLit, activeSet, powerUsed, powerBudget, bandwidthUsed, bandwidthBudget, visited };
}

function recomputeConnectivity(cause = '') {
  const enabled = new Set(enabledRings());
  nodeReason = new Map();
  const neighborMap = buildNeighborMap();
  const removed = validateWires(neighborMap);
  if (removed.length) {
    runtime.flash = {
      broken: removed.map((edge) => wireKey(edge.a, edge.b)),
      gained: [],
      start: performance.now(),
      duration: 180,
    };
    showFeedback(`断线：${removed.length}`);
  }

  const result = computePowerState(boardState.lit);
  const unreachable = [...boardState.lit].filter((id) => !result.reachableLit.has(id));
  if (unreachable.length) {
    unreachable.forEach((id) => boardState.lit.delete(id));
    showFeedback(`断线断电：${unreachable.length}`);
  }

  boardState.nodes.forEach((node) => {
    node.lit = node.id === 'core' || boardState.lit.has(node.id);
    node.powered = node.id === 'core' || (node.lit && result.reachableLit.has(node.id));
    if (node.lit && !node.powered) {
      nodeReason.set(node.id, '未连通或开关关闭');
    }
  });

  const edges = [];
  const connectionCount = new Map();
  boardState.wires.forEach((edge, key) => {
    const active = result.activeSet.has(key);
    edges.push({
      ...edge,
      active,
      kind: 'wire',
    });
    connectionCount.set(edge.a, (connectionCount.get(edge.a) || 0) + 1);
    connectionCount.set(edge.b, (connectionCount.get(edge.b) || 0) + 1);
  });

  boardState.nodes.forEach((node) => {
    if (!enabled.has(node.ring)) return;
    node.connected = (connectionCount.get(node.id) || 0) > 0;
    node.connectionCount = connectionCount.get(node.id) || 0;
  });

  boardState.power_used = Math.round(result.powerUsed * 10) / 10;
  boardState.bandwidth_used = Math.round(result.bandwidthUsed * 10) / 10;
  boardState.edges = edges;

  const activeSet = new Set(edges.filter((e) => e.active).map(edgeKey));
  runtime.lastActiveEdges = activeSet;

  runBoardEvaluation();
}

function nodePosition(node) {
  const rot = boardState.ring_rot_deg[node.ring] || 0;
  const theta = (node.base_theta + rot) * (Math.PI / 180);
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
  const selectedRing = ui.selectedRing;

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
  svg += `<g id="board-root" transform="translate(${cx} ${cy}) scale(${scale}) translate(${-cx} ${-cy})">`;

  if (showSectors) {
    const elements = boardData.meta.elements || Object.keys(colors);
    const step = 360 / elements.length;
    elements.forEach((elem, idx) => {
      const start = idx * step;
      const end = start + step;
      const path = sectorPath(cx, cy, innerR, maxR + 30, start, end);
      const fill = rgba(colors[elem] || WUXING_COLORS[elem] || '#4fe6ff', Math.min(0.18, Math.max(0.08, sectorOpacity)));
      const stroke = rgba(colors[elem] || WUXING_COLORS[elem] || '#4fe6ff', 0.16);
      svg += `<path d="${path}" fill="${fill}" stroke="${stroke}" stroke-width="1" />`;
    });
  }

  if (showRings) {
    boardData.rings.forEach((ring) => {
      const ringName = cfgData.ring_map[ring.id] || ring.id;
      if (!enabled.has(ringName)) return;
      const isSelected = ringName === selectedRing;
      const strokeAlpha = isSelected ? 0.8 : 0.25;
      const stroke = `rgba(120,170,200,${strokeAlpha * ringStrength})`;
      const width = isSelected ? 2.6 : 1.2;
      if (isSelected) {
        svg += `<circle cx="${cx}" cy="${cy}" r="${ring.radius}" fill="none" stroke="rgba(120,220,255,${0.12 * ringStrength})" stroke-width="${width + 6}" />`;
      }
      svg += `<circle cx="${cx}" cy="${cy}" r="${ring.radius}" fill="none" stroke="${stroke}" stroke-width="${width}" />`;
    });
    if (cfgData.inner_core && enabled.has('inner_core')) {
      const isSelected = selectedRing === 'inner_core';
      const strokeAlpha = isSelected ? 0.8 : 0.25;
      const stroke = `rgba(120,170,200,${strokeAlpha * ringStrength})`;
      const width = isSelected ? 2.6 : 1.2;
      if (isSelected) {
        svg += `<circle cx="${cx}" cy="${cy}" r="${cfgData.inner_core.radius}" fill="none" stroke="rgba(120,220,255,${0.12 * ringStrength})" stroke-width="${width + 6}" />`;
      }
      svg += `<circle cx="${cx}" cy="${cy}" r="${cfgData.inner_core.radius}" fill="none" stroke="${stroke}" stroke-width="${width}" />`;
    }

    Object.entries(ringMap).forEach(([ringName, nodes]) => {
      if (!enabled.has(ringName)) return;
      const ringRadius = nodes[0]?.r;
      if (!ringRadius) return;
      const rot = boardState.ring_rot_deg[ringName] || 0;
      const tickStep = 10;
      const isSelected = ringName === selectedRing;
      for (let angle = 0; angle < 360; angle += tickStep) {
        const major = angle % 30 === 0;
        const length = major ? 10 : 6;
        const tickAngle = angle + rot;
        const start = polarPoint(cx, cy, ringRadius - 6, tickAngle);
        const end = polarPoint(cx, cy, ringRadius - 6 - length, tickAngle);
        const alpha = isSelected ? 0.75 : 0.32;
        svg += `<line x1="${start.x}" y1="${start.y}" x2="${end.x}" y2="${end.y}" stroke="rgba(180,220,255,${alpha})" stroke-width="${major ? 1.6 : 1}" />`;
      }
    });
  }

  if (showEdges) {
    const dashOffset = -((now * 0.05) % 24);
    if (boardState.ui?.allowAutoEdges && boardState.neighborMap?.size) {
      boardState.neighborMap.forEach((neighbors, id) => {
        const a = boardState.nodes.find((n) => n.id === id);
        if (!a) return;
        neighbors.forEach((nid) => {
          if (id > nid) return;
          const b = boardState.nodes.find((n) => n.id === nid);
          if (!b) return;
          const pa = nodePosition(a);
          const pb = nodePosition(b);
          svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,140,160,0.15)" stroke-width="1" stroke-dasharray="2 6" />`;
        });
      });
    }

    if (runtime.showNeighborHints && runtime.hoveredNodeId && boardState.neighborMap?.size) {
      const neighbors = boardState.neighborMap.get(runtime.hoveredNodeId);
      const a = boardState.nodes.find((n) => n.id === runtime.hoveredNodeId);
      if (a && neighbors) {
        neighbors.forEach((nid) => {
          const key = wireKey(a.id, nid);
          if (boardState.wires.has(key)) return;
          const b = boardState.nodes.find((n) => n.id === nid);
          if (!b) return;
          const pa = nodePosition(a);
          const pb = nodePosition(b);
          svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(180,200,220,0.45)" stroke-width="1.4" stroke-dasharray="3 6" />`;
        });
      }
    }

    boardState.edges.forEach((edge) => {
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      if (!a || !b) return;
      if (!enabled.has(a.ring) || !enabled.has(b.ring)) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      const powered = edge.active && a.powered && b.powered;
      if (edge.active) {
        const base = powered ? 0.14 : 0.06;
        const lineAlpha = powered ? 0.95 : 0.35;
        const width = powered ? 8 : 2.4;
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,220,255,${base * edgeStrength})" stroke-width="${width}" />`;
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,220,255,${lineAlpha * edgeStrength})" stroke-width="${powered ? 3.2 : 1.6}" stroke-linecap="round" stroke-dasharray="${powered ? '8 10' : '0'}" stroke-dashoffset="${dashOffset}" />`;
      } else {
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(160,170,180,${0.35 * edgeStrength})" stroke-width="1.2" />`;
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
    const elemColor = colors[node.elem] || WUXING_COLORS[node.elem] || '#4fe6ff';
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

    if (node.connected && !node.powered) {
      svg += `<circle class="node-connected" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 6}" fill="none" stroke="rgba(120,200,255,0.35)" stroke-width="1.4" />`;
    }

    if (selected) {
      svg += `<circle class="node-selected" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 7}" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.8" />`;
      svg += `<circle class="node-selected" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 10}" fill="none" stroke="rgba(120,220,255,0.7)" stroke-width="1.2" />`;
    }
    if (runtime.wireStartId === node.id) {
      svg += `<circle cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 12}" fill="none" stroke="rgba(255,230,140,0.85)" stroke-width="2" stroke-dasharray="4 6" />`;
    }
    if (runtime.rejectedNodeId === node.id && now < runtime.rejectUntil) {
      svg += `<circle cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseRadius + 10}" fill="none" stroke="rgba(255,90,90,0.9)" stroke-width="2.2" />`;
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
  const ringOptions = [
    { value: 'inner', label: '内环' },
    { value: 'mid', label: '中环' },
    { value: 'outer', label: '外环' },
    { value: 'inner_core', label: '内核' },
  ];
  const enabled = new Set(enabledRings());
  const optionsKey = ringOptions
    .filter((r) => enabled.has(r.value))
    .map((r) => r.value)
    .join('|');
  if (optionsKey && optionsKey !== runtime.lastRingOptionsKey) {
    const optionsHtml = ringOptions
      .filter((r) => enabled.has(r.value))
      .map((r) => `<option value="${r.value}">${r.label}</option>`)
      .join('');
    dom.ringSelect.innerHTML = optionsHtml;
    runtime.lastRingOptionsKey = optionsKey;
  }
  if (!enabled.has(boardState.ui?.selectedRing)) {
    boardState.ui.selectedRing = dom.ringSelect.value;
  }
  if (boardState.ui?.selectedRing) {
    dom.ringSelect.value = boardState.ui.selectedRing;
  }
  dom.hudPower.textContent = `${boardState.power_used || 0} / ${boardState.qi_cap}`;
  dom.hudBandwidth.textContent = `${boardState.bandwidth_used || 0} / ${boardState.bandwidth_cap}`;
  const lit = boardState.nodes.filter((n) => n.lit).length - 1;
  const powered = boardState.nodes.filter((n) => n.powered).length - 1;
  dom.hudCounts.textContent = `${Math.max(lit, 0)} / ${Math.max(powered, 0)}`;
  if (runtime.evalResult?.derived?.mainElement) {
    dom.hudBonus.textContent = `主元素: ${runtime.evalResult.derived.mainElement}`;
  } else {
    dom.hudBonus.textContent = boardState.ui?.mode === 'wire' ? '连线模式' : '通电模式';
  }
  if (dom.modeToggle) {
    dom.modeToggle.textContent = boardState.ui?.mode === 'wire' ? '连线模式' : '通电模式';
  }
  dom.rotateKnob.textContent = `旋转${dom.ringSelect.selectedOptions[0]?.textContent || '中环'}`;
  if (dom.hudRot) {
    const ring = boardState.ui?.selectedRing || dom.ringSelect.value;
    const angle = boardState.ring_rot_deg[ring] || 0;
    dom.hudRot.textContent = `${angle.toFixed(1)}°`;
  }
  dom.cfgHash.textContent = cfgHash;
  dom.cfgVersion.textContent = cfgData.ruleset_version || '-';
  dom.cfgRot.textContent = JSON.stringify(boardState.ring_rot_deg);
  dom.cfgMtime.textContent = cfgMtime;
}

function updateDetail(nodeId) {
  const node = boardState.nodes.find((n) => n.id === nodeId) || boardState.nodes.find((n) => n.id === 'core');
  if (!node) return;
  dom.detail.name.textContent = node.id;
  dom.detail.element.textContent = node.elem;
  dom.detail.type.textContent = node.size;
  dom.detail.trigram.textContent = node.trigram;
  dom.detail.component.textContent = node.componentType || '-';
  const effectId = assignEffectId(node);
  if (effectId && window.BD_CATALOG?.nodeEffects?.[effectId]) {
    const effect = window.BD_CATALOG.nodeEffects[effectId];
    dom.detail.effect.textContent = `${effect.category}: ${effect.id}`;
  } else {
    dom.detail.effect.textContent = COMPONENT_DESC[node.componentType] || '-';
  }
  dom.detail.power.textContent = node.powered ? '通电' : node.lit ? '已点亮' : '未点亮';
  dom.detail.reason.textContent = nodeReason.get(node.id) || (node.componentType === 'SWITCH' && !node.switchOn ? '开关关闭' : '-');
  if (dom.toggleSwitch) {
    dom.toggleSwitch.classList.toggle('hidden', node.componentType !== 'SWITCH');
  }

  dom.stats.atk.textContent = Math.round(10 + poweredStat('atk'));
  dom.stats.crit.textContent = Math.round(4 + poweredStat('crit'));
  dom.stats.hp.textContent = Math.round(18 + poweredStat('hp'));
  dom.stats.shield.textContent = Math.round(6 + poweredStat('shield'));
  dom.stats.mana.textContent = Math.round(6 + poweredStat('mana'));
  dom.stats.regen.textContent = Math.round(3 + poweredStat('regen'));
}

function currentTrigramDeg() {
  return boardState.ring_rot_deg?.mid ?? 0;
}

function mapRing(ring) {
  if (ring === 'inner_core') return 'CORE';
  if (ring === 'inner') return 'INNER';
  if (ring === 'mid') return 'MIDDLE';
  if (ring === 'outer') return 'OUTER';
  return 'INNER';
}

function assignEffectId(node) {
  if (node.type === 'core') return null;
  const isMajor = node.size === 'major' || node.type === 'major' || node.type === 'keystone';
  if (isMajor) {
    if (node.elem === '火') return 'TRG_ONHIT_BURN_15';
    if (node.elem === '金') return 'SKM_CONVERT_MAIN_TO_METAL';
    if (node.elem === '水') return 'SKM_ADD_TAG_WATER';
  }
  switch (node.elem) {
    case '火':
      return 'STAT_FIRE_DMG_3';
    case '土':
      return 'STAT_EARTH_HP_5';
    case '金':
      return 'STAT_METAL_CRIT_2';
    case '水':
      return 'STAT_WATER_MANA_3';
    case '木':
      return 'STAT_WOOD_REGEN_2';
    default:
      return null;
  }
}

function buildBoardEvalState() {
  const sectors = [
    { element: 'FIRE', startDeg: 0, endDeg: 72 },
    { element: 'EARTH', startDeg: 72, endDeg: 144 },
    { element: 'METAL', startDeg: 144, endDeg: 216 },
    { element: 'WATER', startDeg: 216, endDeg: 288 },
    { element: 'WOOD', startDeg: 288, endDeg: 360 },
  ];

  const nodes = boardState.nodes.map((node) => ({
    id: node.id,
    ring: mapRing(node.ring),
    element: (ELEMENT_MAP[node.elem] || 'earth').toUpperCase(),
    visualType: node.type === 'core' ? 'CORE' : node.size === 'major' ? 'MAJOR' : 'NORMAL',
    isLit: node.lit,
    effectId: assignEffectId(node),
    componentSlot: {
      type: node.type === 'core' ? 'SOURCE' : (node.componentType || 'NONE'),
      params: { isOn: node.switchOn !== false },
    },
    tags: [],
  }));

  const edges = [];
  boardState.wires.forEach((edge, key) => {
    edges.push({
      id: key,
      from: edge.a,
      to: edge.b,
      baseCost: edge.bandwidthCost ?? 1,
      state: edge.enabled === false ? 'DISABLED' : 'ENABLED',
      componentSlot: {
        type: edge.component ? edge.component.toUpperCase() : 'NONE',
        params: { isOn: edge.enabled !== false },
      },
    });
  });

  return {
    boardId: 'wuxing_board',
    rotationDeg: currentTrigramDeg(),
    budgets: {
      powerCap: boardState.qi_cap,
      bandwidthCap: boardState.bandwidth_cap,
    },
    nodes,
    edges,
    pointerRule: { sectors },
  };
}

function updateBdOutput(evalResult) {
  if (!evalResult || !dom.bd?.atk) return;
  const stats = evalResult.combatOutput.stats;
  const add = stats.add;
  const mul = stats.mul;
  dom.bd.atk.textContent = `${Math.round((mul.ATK_PCT || 0) * 100)}%`;
  dom.bd.crit.textContent = `${Math.round(((add.CRIT_RATE || 0) + (mul.CRIT_RATE || 0)) * 100)}%`;
  dom.bd.hp.textContent = `${Math.round((mul.HP_PCT || 0) * 100)}%`;
  dom.bd.fire.textContent = `${Math.round((mul.FIRE_DMG_PCT || 0) * 100)}%`;
  dom.bd.mana.textContent = Math.round(add.MANA_REGEN || 0);
  dom.bd.energy.textContent = Math.round(add.ENERGY_REGEN || 0);
  dom.bd.active.textContent = evalResult.combatOutput.active ? '激活' : '未生效';
  dom.bd.main.textContent = evalResult.derived.mainElement || '-';

  dom.bd.skillMods.innerHTML = evalResult.combatOutput.skillMods.length
    ? evalResult.combatOutput.skillMods.map((mod) => {
      if (mod.modType === 'CONVERT_ELEMENT') {
        return `<div>转元素 → ${mod.params?.element || ''}</div>`;
      }
      if (mod.modType === 'ADD_TAG') {
        return `<div>附加标签 → ${mod.params?.tag || ''}</div>`;
      }
      return `<div>${mod.modType}</div>`;
    }).join('')
    : '<div>—</div>';
  dom.bd.triggers.innerHTML = evalResult.combatOutput.triggers.length
    ? evalResult.combatOutput.triggers.map((trg) => {
      const status = trg.effect?.applyStatus?.status || '';
      const chance = trg.effect?.chance ? ` ${(trg.effect.chance * 100).toFixed(0)}%` : '';
      return `<div>${trg.event} ${status}${chance}</div>`;
    }).join('')
    : '<div>—</div>';
  dom.bd.summary.innerHTML = evalResult.preview.summaryLines.map((line) => `<div>${line}</div>`).join('');
  if (!evalResult.combatOutput.active) {
    dom.bd.summary.innerHTML += '<div class="neg">⚠ 预算超限，输出未生效</div>';
  }
  dom.bd.violations.innerHTML = evalResult.violations.length
    ? evalResult.violations.map((v) => `<div>${v.type}: ${v.message}</div>`).join('')
    : '<div>—</div>';
}

function runBoardEvaluation() {
  if (!window.BDEvaluator?.EvaluateBoard || !window.BD_CATALOG) return;
  const evalState = buildBoardEvalState();
  const evalResult = window.BDEvaluator.EvaluateBoard(evalState, window.BD_CATALOG, {
    enforceBudgets: true,
    computeStructureMetrics: false,
  });
  const prev = runtime.evalResult;
  runtime.evalResult = evalResult;
  updateBdOutput(evalResult);
  if (dom.bd?.changes) {
    const changes = [];
    if (prev) {
      const prevStats = prev.combatOutput.stats;
      const nextStats = evalResult.combatOutput.stats;
      const diff = (key) => ((nextStats.mul[key] || 0) - (prevStats.mul[key] || 0)) * 100;
      const diffAdd = (key) => (nextStats.add[key] || 0) - (prevStats.add[key] || 0);
      const fireDiff = diff('FIRE_DMG_PCT');
      if (fireDiff) changes.push(`<div class="${fireDiff > 0 ? 'pos' : 'neg'}">火伤 ${fireDiff > 0 ? '+' : ''}${fireDiff.toFixed(0)}%</div>`);
      const hpDiff = diff('HP_PCT');
      if (hpDiff) changes.push(`<div class="${hpDiff > 0 ? 'pos' : 'neg'}">生命 ${hpDiff > 0 ? '+' : ''}${hpDiff.toFixed(0)}%</div>`);
      const critDiff = diffAdd('CRIT_RATE');
      if (critDiff) changes.push(`<div class="${critDiff > 0 ? 'pos' : 'neg'}">暴击 ${critDiff > 0 ? '+' : ''}${(critDiff * 100).toFixed(0)}%</div>`);
      const manaDiff = diffAdd('MANA_REGEN');
      if (manaDiff) changes.push(`<div class="${manaDiff > 0 ? 'pos' : 'neg'}">回蓝 ${manaDiff > 0 ? '+' : ''}${manaDiff.toFixed(0)}</div>`);
    }
    if (!changes.length) changes.push('<div>—</div>');
    dom.bd.changes.innerHTML = changes.join('');
    if (!prev) {
      dom.bd.changes.innerHTML = '<div>—</div>';
    }
  }
}

function poweredStat(key) {
  let total = 0;
  boardState.nodes.forEach((node) => {
    if (!node.powered) return;
    if (node.elem === '火' && key === 'atk') total += 2;
    if (node.elem === '金' && key === 'crit') total += 1.5;
    if (node.elem === '土' && key === 'hp') total += 2;
    if (node.elem === '水' && key === 'mana') total += 1.5;
    if (node.elem === '木' && key === 'regen') total += 1.2;
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
  const ringInfo = Object.entries(boardState.ring_rot_deg)
    .map(([ring, deg]) => `${ring}:${deg.toFixed(1)}°`)
    .join('  ');
  const activeEdges = boardState.edges.filter((e) => e.active).length;
  const nodeLines = boardState.nodes
    .map((node) => {
      const pos = nodePosition(node);
      return `${node.id} (${pos.x.toFixed(1)}, ${pos.y.toFixed(1)}) c:${node.connectionCount || 0}`;
    })
    .join('\n');
  dom.debugOverlay.textContent = `FPS: ${runtime.fps.toFixed(1)}\nEdges: ${activeEdges}/${boardState.edges.length}\nRings: ${ringInfo}\nNodes:\n${nodeLines}`;
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

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function startRotationAnim(ring, deltaDeg, opts = {}) {
  const now = performance.now();
  const startDeg = boardState.ring_rot_deg[ring] || 0;
  const continuous = opts.continuous || false;
  const step = continuous ? (deltaDeg > 0 ? 1 : -1) : 0;
  runtime.anim = {
    ring,
    startDeg,
    endDeg: startDeg + (continuous ? step : deltaDeg),
    startTime: now,
    duration: opts.duration ?? (continuous ? 50 : 350),
    repeat: opts.repeat ?? (continuous ? 29 : 0),
    stepDeg: opts.stepDeg ?? step,
    ease: opts.ease ?? !continuous,
    cause: opts.cause || 'rotation',
  };
}

function rotateRing(deltaDeg) {
  const ring = boardState.ui?.selectedRing || dom.ringSelect.value;
  if (!boardState.ring_rot_deg.hasOwnProperty(ring)) return;
  runtime.inertia = null;
  startRotationAnim(ring, deltaDeg, { continuous: dom.rotateContinuous.checked, cause: 'rotation' });
  runtime.needsRender = true;
}

function applyRotationDelta(ring, deltaDeg, cause = 'rotation') {
  if (!boardState.ring_rot_deg.hasOwnProperty(ring)) return;
  boardState.ring_rot_deg[ring] = normDeg((boardState.ring_rot_deg[ring] || 0) + deltaDeg);
  scheduleUpdate({ recompute: true, cause });
}

function getRingStep(ring) {
  const nodes = ringIndex()[ring] || [];
  if (!nodes.length) return null;
  return 360 / nodes.length;
}

function snapRing(ring) {
  if (!boardState.ui?.snap) return;
  const step = getRingStep(ring);
  if (!step) return;
  const current = boardState.ring_rot_deg[ring] || 0;
  const target = Math.round(current / step) * step;
  const delta = target - current;
  if (Math.abs(delta) < 0.05) return;
  startRotationAnim(ring, delta, { duration: 220, ease: true, cause: 'rotation' });
}

function setMode(mode) {
  boardState.ui.mode = mode;
  dom.modeToggle.textContent = mode === 'wire' ? '连线模式' : '通电模式';
  scheduleUpdate({ recompute: true, cause: 'mode' });
}

function toggleWire(aId, bId) {
  const neighborSet = boardState.neighborMap.get(aId);
  console.log('[toggleWire]', { aId, bId, neighbors: neighborSet ? [...neighborSet] : [] });
  if (!neighborSet || !neighborSet.has(bId)) {
    showFeedback('仅允许相邻连接');
    return;
  }
  const key = wireKey(aId, bId);
  if (boardState.wires.has(key)) {
    boardState.wires.delete(key);
    runtime.flash = { broken: [key], gained: [], start: performance.now(), duration: 160 };
  } else {
    boardState.wires.set(key, {
      a: aId,
      b: bId,
      enabled: true,
      component: 'wire',
      directed: false,
      bandwidthCost: edgeBandwidthCost('wire'),
    });
  }
  recomputeConnectivity('wire');
  runtime.needsRender = true;
}

function tryToggleLit(node) {
  if (node.id === 'core') {
    runtime.selectedNodeId = node.id;
    rerender(node.id);
    return;
  }
  if (!enabledRings().includes(node.ring)) {
    showFeedback('当前境界未解锁该环');
    return;
  }
  if (node.componentType === 'SWITCH' && !node.switchOn) {
    showFeedback('开关关闭');
    runtime.rejectedNodeId = node.id;
    runtime.rejectUntil = performance.now() + 300;
    return;
  }
  const litSet = new Set(boardState.lit);
  if (litSet.has(node.id)) {
    litSet.delete(node.id);
    boardState.lit = litSet;
    recomputeConnectivity('power');
    runtime.needsRender = true;
    return;
  }
  litSet.add(node.id);
  const result = computePowerState(litSet);
  if (!result.reachableLit.has(node.id)) {
    showFeedback('未连通：请先布线');
    runtime.rejectedNodeId = node.id;
    runtime.rejectUntil = performance.now() + 300;
    return;
  }
  if (result.powerUsed > result.powerBudget || result.bandwidthUsed > result.bandwidthBudget) {
    const powerGap = Math.max(0, result.powerUsed - result.powerBudget);
    const bandGap = Math.max(0, result.bandwidthUsed - result.bandwidthBudget);
    showFeedback(`资源不足：电力-${powerGap} / 带宽-${bandGap}`);
    runtime.rejectedNodeId = node.id;
    runtime.rejectUntil = performance.now() + 300;
    return;
  }
  boardState.lit = litSet;
  recomputeConnectivity('power');
  runtime.needsRender = true;
}

function attachEvents() {
  console.log('[attachEvents] binding listeners');
  dom.realmSelect.addEventListener('change', () => {
    boardState.realm = dom.realmSelect.value;
    boardState.qi_cap = cfgData.realm_rules[boardState.realm]?.qi_cap || boardState.qi_cap;
    scheduleUpdate({ recompute: true, cause: 'realm' });
    rerender();
  });
  dom.toggleContrast.addEventListener('change', () => {
    setUIState({ highContrast: dom.toggleContrast.checked }, { log: true });
  });
  dom.toggleBroken.addEventListener('change', () => {
    setUIState({ showBroken: dom.toggleBroken.checked }, { log: true });
  });
  dom.toggleSnap.addEventListener('change', () => {
    setUIState({ snap: dom.toggleSnap.checked }, { log: true });
  });
  dom.ringSelect.addEventListener('change', () => {
    setUIState({ selectedRing: dom.ringSelect.value }, { log: true });
    updateHud();
  });
  dom.modeToggle.addEventListener('click', () => {
    setMode(boardState.ui.mode === 'wire' ? 'power' : 'wire');
  });
  dom.clearLit.addEventListener('click', () => {
    boardState.lit.clear();
    recomputeConnectivity('power');
    runtime.needsRender = true;
  });
  dom.rotateLeft.addEventListener('click', () => rotateRing(-15));
  dom.rotateRight.addEventListener('click', () => rotateRing(15));
  dom.rotateKnob.addEventListener('click', () => rotateRing(15));

  dom.container.addEventListener('click', (event) => {
    if (performance.now() - runtime.lastDragTime < 180) return;
    if (performance.now() < runtime.suppressClickUntil) return;
    console.log('[click]', {
      x: event.clientX,
      y: event.clientY,
      mode: boardState.ui.mode,
      wireStart: runtime.wireStartId,
      shift: event.shiftKey,
    });
    const node = hitTestNode(event);
    console.log('[hitTest]', node ? { id: node.id, ring: node.ring, slot: node.slot_idx } : null);
    if (!node) return;
    console.log('hit', node.id, node.name, node.type);
    if (!enabledRings().includes(node.ring)) return;
    runtime.selectedNodeId = node.id;

    if (boardState.ui.mode === 'wire' || event.shiftKey) {
      if (!runtime.wireStartId) {
        runtime.wireStartId = node.id;
        runtime.needsRender = true;
        return;
      }
      if (runtime.wireStartId === node.id) {
        runtime.wireStartId = null;
        runtime.needsRender = true;
        return;
      }
      toggleWire(runtime.wireStartId, node.id);
      runtime.wireStartId = null;
      runtime.needsRender = true;
      return;
    }

    tryToggleLit(node);
  });

  document.body.addEventListener('click', (event) => {
    console.log('[body click]', { x: event.clientX, y: event.clientY, target: event.target?.id || event.target?.tagName });
  }, { capture: true });

  dom.container.addEventListener('pointermove', (event) => {
    if (runtime.drag && runtime.drag.pointerId === event.pointerId) {
      const dx = event.clientX - runtime.drag.startX;
      const dy = event.clientY - runtime.drag.startY;
      const dist = Math.hypot(dx, dy);
      if (dist > 4 && !runtime.drag.dragging) {
        runtime.drag.dragging = true;
        runtime.drag.hitNodeId = null;
      }
      const rect = dom.container.getBoundingClientRect();
      const center = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
      const angle = Math.atan2(event.clientY - center.y, event.clientX - center.x) * (180 / Math.PI);
      const delta = deltaAngleDeg(runtime.drag.lastAngle, angle);
      const now = performance.now();
      const dt = Math.max(8, now - runtime.drag.lastTime);
      if (runtime.drag.dragging && Math.abs(delta) > 0.02) {
        applyRotationDelta(runtime.drag.ring, delta, 'rotation');
        const velocity = delta / dt;
        runtime.drag.velocity = runtime.drag.velocity * 0.6 + velocity * 0.4;
        runtime.drag.moved = runtime.drag.moved || Math.abs(delta) > 0.4;
      }
      runtime.drag.lastAngle = angle;
      runtime.drag.lastTime = now;
      runtime.needsRender = true;
    }
    const node = hitTestNode(event);
    if (!node) {
      runtime.hoveredNodeId = null;
      dom.tooltip.style.opacity = 0;
    } else {
      runtime.hoveredNodeId = node.id;
      dom.tooltip.style.opacity = 1;
      dom.tooltip.style.left = `${event.clientX}px`;
      dom.tooltip.style.top = `${event.clientY}px`;
      const switchState = node.componentType === 'SWITCH' ? (node.switchOn ? '开' : '关') : '';
      const effectId = assignEffectId(node);
      const effect = effectId ? window.BD_CATALOG?.nodeEffects?.[effectId] : null;
      const effectText = effect ? `${effect.category}:${effect.id}` : '无效果';
      const powerState = node.powered ? '通电' : node.lit ? '已点亮' : '未点亮';
      dom.tooltip.textContent = `${node.name || node.id} | ${powerState} | ${node.componentType || node.type}${switchState ? `(${switchState})` : ''} | ${effectText}`;
    }
    runtime.showNeighborHints = event.shiftKey || boardState.ui.mode === 'wire' || boardState.ui.showNeighborHints;
    runtime.needsRender = true;
  });

  dom.container.addEventListener('pointerleave', () => {
    dom.tooltip.style.opacity = 0;
    runtime.hoveredNodeId = null;
    runtime.showNeighborHints = false;
    runtime.needsRender = true;
  });

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
  dom.toggleAutoEdges.addEventListener('change', () => {
    setUIState({ allowAutoEdges: dom.toggleAutoEdges.checked }, { log: true, recompute: true, cause: 'ui' });
  });
  dom.toggleNeighborHints.addEventListener('change', () => {
    setUIState({ showNeighborHints: dom.toggleNeighborHints.checked }, { log: true });
  });
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

  // BD 输出采用自动评估，无需手动触发

  dom.panel.reload.addEventListener('click', async () => {
    await loadConfig();
    await loadBoard();
    const keep = {
      realm: boardState.realm,
      rot_deg: { ...boardState.ring_rot_deg },
      invested: [...boardState.lit],
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

  dom.container.addEventListener('wheel', (event) => {
    if (event.ctrlKey) return;
    event.preventDefault();
    const ring = boardState.ui?.selectedRing || dom.ringSelect.value;
    const delta = event.deltaY > 0 ? 2 : -2;
    runtime.anim = null;
    runtime.inertia = null;
    applyRotationDelta(ring, delta, 'rotation');
  }, { passive: false });

  window.addEventListener('keydown', (event) => {
    const tag = document.activeElement?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'select' || tag === 'textarea') return;
    if (event.key === 'Escape') {
      boardState.lit.clear();
      runtime.wireStartId = null;
      runtime.selectedNodeId = 'core';
      rerender('core');
      return;
    }
    if (event.key === 'l' || event.key === 'L') {
      setMode(boardState.ui.mode === 'wire' ? 'power' : 'wire');
      return;
    }
    if (event.key === 'q' || event.key === 'Q' || event.key === 'a' || event.key === 'A') {
      rotateRing(-15);
    }
    if (event.key === 'e' || event.key === 'E' || event.key === 'd' || event.key === 'D') {
      rotateRing(15);
    }
  });

  dom.container.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) return;
    console.log('[pointerdown]', { x: event.clientX, y: event.clientY, shift: event.shiftKey });
    if (event.shiftKey) {
      const node = hitTestNode(event);
      if (node) {
        runtime.wireDragActive = true;
        runtime.wireStartId = node.id;
        return;
      }
    }
    const rect = dom.container.getBoundingClientRect();
    const center = { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    const angle = Math.atan2(event.clientY - center.y, event.clientX - center.x) * (180 / Math.PI);
    const hitNode = hitTestNode(event);
    runtime.drag = {
      ring: boardState.ui?.selectedRing || dom.ringSelect.value,
      lastAngle: angle,
      lastTime: performance.now(),
      velocity: 0,
      moved: false,
      dragging: false,
      startX: event.clientX,
      startY: event.clientY,
      hitNodeId: hitNode?.id || null,
      pointerId: event.pointerId,
    };
    runtime.anim = null;
    runtime.inertia = null;
    dom.container.setPointerCapture(event.pointerId);
  });

  dom.container.addEventListener('pointerup', (event) => {
    console.log('[pointerup]', { x: event.clientX, y: event.clientY, shift: event.shiftKey });
    if (runtime.wireDragActive) {
      const node = hitTestNode(event);
      if (node && runtime.wireStartId && node.id !== runtime.wireStartId) {
        toggleWire(runtime.wireStartId, node.id);
      } else if (!node) {
        showFeedback('仅允许相邻连接');
      }
      runtime.wireDragActive = false;
      runtime.wireStartId = null;
      return;
    }
    if (!runtime.drag || runtime.drag.pointerId !== event.pointerId) return;
    dom.container.releasePointerCapture(event.pointerId);
    const { ring, velocity, moved, hitNodeId } = runtime.drag;
    runtime.drag = null;
    if (moved && Math.abs(velocity) > 0.01) {
      const clamped = Math.max(-0.35, Math.min(0.35, velocity));
      runtime.inertia = {
        ring,
        velocity: clamped,
        lastTime: performance.now(),
      };
    } else {
      snapRing(ring);
    }
    if (moved) runtime.suppressClickUntil = performance.now() + 200;
    if (moved) runtime.lastDragTime = performance.now();
    if (!moved && performance.now() >= runtime.suppressClickUntil) {
      const node = hitNodeId ? boardState.nodes.find((n) => n.id === hitNodeId) : hitTestNode(event);
      console.log('[pointerup hit]', node ? node.id : null);
      if (!node) return;
      runtime.selectedNodeId = node.id;
      if (boardState.ui.mode === 'wire' || event.shiftKey) {
        if (!runtime.wireStartId) {
          runtime.wireStartId = node.id;
          runtime.needsRender = true;
          return;
        }
        if (runtime.wireStartId === node.id) {
          runtime.wireStartId = null;
          runtime.needsRender = true;
          return;
        }
        toggleWire(runtime.wireStartId, node.id);
        runtime.wireStartId = null;
        runtime.needsRender = true;
        return;
      }
      tryToggleLit(node);
    }
  });

  dom.container.addEventListener('pointercancel', () => {
    runtime.drag = null;
  });
}

function tick(now) {
  runtime.frames += 1;
  if (now - runtime.lastFpsTime >= 500) {
    runtime.fps = (runtime.frames * 1000) / (now - runtime.lastFpsTime);
    runtime.frames = 0;
    runtime.lastFpsTime = now;
  }

  let rotating = false;
  if (runtime.anim) {
    const anim = runtime.anim;
    const progress = Math.min((now - anim.startTime) / anim.duration, 1);
    const eased = anim.ease ? easeInOutCubic(progress) : progress;
    const current = anim.startDeg + (anim.endDeg - anim.startDeg) * eased;
    boardState.ring_rot_deg[anim.ring] = normDeg(current);
    runtime.needsConnectivityUpdate = true;
    runtime.updateCause = anim.cause || 'rotation';
    rotating = true;
    if (progress >= 1) {
      if (anim.repeat > 0) {
        anim.repeat -= 1;
        anim.startDeg = anim.endDeg;
        anim.endDeg = anim.endDeg + anim.stepDeg;
        anim.startTime = now;
      } else {
        boardState.ring_rot_deg[anim.ring] = normDeg(anim.endDeg);
        runtime.anim = null;
      }
    }
  }

  if (runtime.inertia) {
    const inertia = runtime.inertia;
    const dt = Math.max(8, now - inertia.lastTime);
    const delta = inertia.velocity * dt;
    applyRotationDelta(inertia.ring, delta, 'rotation');
    const damping = Math.pow(0.96, dt / 16);
    inertia.velocity *= damping;
    inertia.lastTime = now;
    rotating = true;
    if (Math.abs(inertia.velocity) < 0.002) {
      runtime.inertia = null;
      snapRing(inertia.ring);
    }
  }

  if (runtime.needsConnectivityUpdate && now - runtime.lastConnectivityUpdate > 30) {
    recomputeConnectivity(runtime.updateCause || 'rotation');
    runtime.needsConnectivityUpdate = false;
    runtime.lastConnectivityUpdate = now;
  }

  if (rotating || runtime.needsRender || runtime.flash || runtime.sparks) {
    if (rotating || now - runtime.lastRender > 33) {
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
  setMode('power');
  attachEvents();
  rerender();
  requestAnimationFrame(tick);
}

init();
