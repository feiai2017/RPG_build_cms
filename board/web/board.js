const dom = {
  container: document.getElementById('canvas-container'),
  steps: Array.from(document.querySelectorAll('#steps-bar .step')),
  realmSelect: document.getElementById('realm-select'),
  hudQi: document.getElementById('hud-qi'),
  hudCounts: document.getElementById('hud-counts'),
  hudBonus: document.getElementById('hud-bonus'),
  toggleContrast: document.getElementById('toggle-contrast'),
  toggleBroken: document.getElementById('toggle-broken'),
  ringSelect: document.getElementById('ring-select'),
  rotateContinuous: document.getElementById('rotate-continuous'),
  rotateLeft: document.getElementById('rotate-left'),
  rotateRight: document.getElementById('rotate-right'),
  rotateKnob: document.getElementById('rotate-knob'),
  cfgHash: document.getElementById('cfg-hash'),
  cfgVersion: document.getElementById('cfg-version'),
  cfgRot: document.getElementById('cfg-rot'),
  cfgMtime: document.getElementById('cfg-mtime'),
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
  sparks: true,
  lastRender: 0,
};

const TRIGRAMS = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
const DEFAULT_REALM = '金丹';

function normDeg(deg) {
  let v = deg % 360;
  if (v < 0) v += 360;
  return v;
}

function angleDiff(a, b) {
  const diff = Math.abs(normDeg(a) - normDeg(b));
  return Math.min(diff, 360 - diff);
}

function trigramByAngle(theta) {
  const idx = Math.floor(normDeg(theta) / 45) % TRIGRAMS.length;
  return TRIGRAMS[idx];
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
      elem: raw.element,
      ring,
      slot_idx: 0,
      base_theta: baseTheta,
      r: radius,
      size: raw.type === 'keystone' || raw.type === 'core' ? 'major' : 'small',
      trigram: trigramByAngle(baseTheta),
      effects: raw.effects || {},
      invested: false,
      powered: false,
    });
  });

  Object.keys(ringBuckets).forEach((ring) => {
    ringBuckets[ring].sort((a, b) => normDeg(a.base_theta) - normDeg(b.base_theta));
    ringBuckets[ring].forEach((node, idx) => {
      node.slot_idx = idx;
      node.id = `${ring}_${idx}`;
      nodes.push(node);
    });
  });

  nodes.push({
    id: 'core',
    elem: '土',
    ring: 'inner',
    slot_idx: -1,
    base_theta: 0,
    r: 0,
    size: 'major',
    trigram: '坤',
    effects: { core: 1 },
    invested: true,
    powered: true,
  });

  if (cfgData.inner_core) {
    const slots = cfgData.inner_core.slots;
    const radius = cfgData.inner_core.radius;
    for (let i = 0; i < slots; i += 1) {
      const theta = (360 / slots) * i;
      nodes.push({
        id: `inner_core_${i}`,
        elem: '土',
        ring: 'inner_core',
        slot_idx: i,
        base_theta: theta,
        r: radius,
        size: 'major',
        trigram: trigramByAngle(theta),
        effects: { inner_core: 1 },
        invested: false,
        powered: false,
      });
    }
  }

  const ringRot = { inner: 0, mid: 0, outer: 0, inner_core: 0 };
  if (preset && preset.rot_deg) {
    Object.keys(preset.rot_deg).forEach((key) => {
      ringRot[key] = preset.rot_deg[key];
    });
  }

  const realm = preset?.realm || DEFAULT_REALM;
  const invested = new Set(preset?.invested || []);
  nodes.forEach((node) => {
    if (invested.has(node.id)) node.invested = true;
  });
  const qiCap = cfgData.realm_rules[realm]?.qi_cap || 10;

  boardState = {
    realm,
    qi_cap: qiCap,
    qi_used: 0,
    ring_rot_deg: ringRot,
    nodes,
    edges: [],
    ruleset_version: cfgData.ruleset_version || 'v1',
    cfg_hash: cfgHash,
  };
  window.boardState = boardState;
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

function edgeKey(edge) {
  return edge.a < edge.b ? `${edge.a}|${edge.b}` : `${edge.b}|${edge.a}`;
}

function recomputeConnectivity(cause = '') {
  const ringMap = ringIndex();
  const edges = [];
  const enabled = new Set(enabledRings());
  nodeReason = new Map();

  Object.values(ringMap).forEach((nodes) => {
    if (nodes.length < 2) return;
    for (let i = 0; i < nodes.length; i += 1) {
      const a = nodes[i];
      const b = nodes[(i + 1) % nodes.length];
      edges.push({ a: a.id, b: b.id, kind: 'link', active: true, reason: '' });
    }
  });

  const threshold = cfgData.bridge_threshold_deg || 12;
  const bridgeSlots = cfgData.bridge_slots || {};
  const pairs = cfgData.bridge_pairs || [];

  pairs.forEach(([ra, rb]) => {
    const aNodes = (ringMap[ra] || []).filter((n) => (bridgeSlots[ra] || []).includes(n.slot_idx));
    const bNodes = (ringMap[rb] || []).filter((n) => (bridgeSlots[rb] || []).includes(n.slot_idx));
    aNodes.forEach((a) => {
      let best = null;
      let bestDiff = 999;
      const aTheta = normDeg(a.base_theta + (boardState.ring_rot_deg[a.ring] || 0));
      bNodes.forEach((b) => {
        const bTheta = normDeg(b.base_theta + (boardState.ring_rot_deg[b.ring] || 0));
        const diff = angleDiff(aTheta, bTheta);
        if (diff < bestDiff) {
          bestDiff = diff;
          best = b;
        }
      });
      if (!best) return;
      const active = bestDiff <= threshold;
      edges.push({
        a: a.id,
        b: best.id,
        kind: 'power',
        active,
        reason: active ? '' : '旋转后不相邻断线',
      });
    });
  });

  boardState.nodes.forEach((node) => {
    node.powered = false;
  });

  let qiUsed = 0;
  const queue = ['core'];
  const powered = new Set(['core']);
  const nodeMap = new Map(boardState.nodes.map((n) => [n.id, n]));

  while (queue.length) {
    const current = queue.shift();
    edges.forEach((edge) => {
      if (!edge.active) return;
      const a = nodeMap.get(edge.a);
      const b = nodeMap.get(edge.b);
      if (!a || !b) return;
      if (!enabled.has(a.ring) || !enabled.has(b.ring)) {
        edge.active = false;
        edge.reason = '境界未解锁';
        return;
      }
      const next = edge.a === current ? edge.b : edge.b === current ? edge.a : null;
      if (!next) return;
      if (powered.has(next)) return;
      const node = nodeMap.get(next);
      if (!node.invested) return;
      const cost = cfgData.qi_cost[node.size] || 1;
      if (qiUsed + cost > boardState.qi_cap) {
        nodeReason.set(node.id, '带宽不足');
        return;
      }
      qiUsed += cost;
      powered.add(next);
      queue.push(next);
    });
  }

  boardState.nodes.forEach((node) => {
    if (!enabled.has(node.ring)) return;
    if (powered.has(node.id)) {
      node.powered = true;
    } else if (node.invested && !nodeReason.has(node.id)) {
      nodeReason.set(node.id, '断电：连接断开');
    }
  });

  boardState.qi_used = Math.round(qiUsed * 10) / 10;
  boardState.edges = edges;

  const activeSet = new Set(edges.filter((e) => e.active).map(edgeKey));
  if (cause === 'rotation') {
    const broken = [...runtime.lastActiveEdges].filter((k) => !activeSet.has(k));
    const gained = [...activeSet].filter((k) => !runtime.lastActiveEdges.has(k));
    if (broken.length || gained.length) {
      runtime.flash = {
        broken,
        gained,
        start: performance.now(),
        duration: 600,
      };
    }
  }
  runtime.lastActiveEdges = activeSet;
}

function nodePosition(node) {
  const rot = boardState.ring_rot_deg[node.ring] || 0;
  const theta = (node.base_theta + rot) * (Math.PI / 180);
  return {
    x: Math.cos(theta) * node.r,
    y: Math.sin(theta) * node.r,
  };
}

function renderBoard(now = performance.now()) {
  const size = 760;
  const cx = size / 2;
  const cy = size / 2;
  const enabled = new Set(enabledRings());
  const colors = boardData.meta.colors || {};
  const showEdges = dom.panel.edges?.checked ?? true;
  const showLabels = dom.panel.labels?.checked ?? false;
  const highContrast = dom.toggleContrast?.checked ?? false;
  const showBroken = dom.toggleBroken?.checked ?? false;

  let svg = `<svg class="board" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">`;

  boardData.rings.forEach((ring) => {
    const ringName = cfgData.ring_map[ring.id] || ring.id;
    if (!enabled.has(ringName)) return;
    svg += `<circle cx="${cx}" cy="${cy}" r="${ring.radius}" fill="none" stroke="rgba(60,90,110,0.45)" stroke-width="1.2" />`;
  });
  if (cfgData.inner_core && enabled.has('inner_core')) {
    svg += `<circle cx="${cx}" cy="${cy}" r="${cfgData.inner_core.radius}" fill="none" stroke="rgba(60,90,110,0.45)" stroke-width="1.2" />`;
  }

  if (showEdges) {
    boardState.edges.forEach((edge) => {
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      if (!a || !b) return;
      if (!enabled.has(a.ring) || !enabled.has(b.ring)) return;
      if (!edge.active && !showBroken) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      const powered = edge.active && a.powered && b.powered;
      if (powered) {
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,220,255,0.12)" stroke-width="10" />`;
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,220,255,0.9)" stroke-width="3.5" />`;
      } else if (edge.active) {
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(200,200,200,0.25)" stroke-width="2" />`;
      } else {
        svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(255,120,120,0.18)" stroke-width="1" stroke-dasharray="4 4" opacity="0.4" />`;
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
      svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(255,80,80,${alphaOut})" stroke-width="6" />`;
    });
    runtime.flash.gained.forEach((key) => {
      const [aId, bId] = key.split('|');
      const a = boardState.nodes.find((n) => n.id === aId);
      const b = boardState.nodes.find((n) => n.id === bId);
      if (!a || !b) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      const alpha = Math.max(0.3, t);
      svg += `<line x1="${cx + pa.x}" y1="${cy + pa.y}" x2="${cx + pb.x}" y2="${cy + pb.y}" stroke="rgba(120,220,255,${alpha})" stroke-width="6" />`;
    });
    if (t >= 1) runtime.flash = null;
  }

  boardState.nodes.forEach((node) => {
    if (!enabled.has(node.ring)) return;
    const pos = nodePosition(node);
    const elemColor = colors[node.elem] || '#4fe6ff';
    const major = node.size === 'major';
    const unlitSize = 10;
    const litSize = major ? 18 : 14;
    const poweredSize = major ? 18 : 14;
    if (!node.invested) {
      const baseSize = highContrast ? unlitSize - 2 : unlitSize;
      svg += `<circle class="node-dot unlit" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${baseSize / 2}" fill="rgba(0,0,0,0)" stroke="rgba(255,255,255,0.15)" stroke-width="1" opacity="${highContrast ? 0.18 : 0.25}" />`;
    } else if (node.invested && !node.powered) {
      const fill = rgba(elemColor, highContrast ? 0.25 : 0.32);
      svg += `<circle class="node-dot lit" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${litSize / 2}" fill="${fill}" stroke="rgba(255,255,255,0.35)" stroke-width="2" />`;
    } else {
      const glowSize = poweredSize / 2 + (highContrast ? 8 : 6) + Math.sin(now / 300) * 1.5;
      svg += `<circle class="node-glow" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${glowSize}" fill="${rgba(elemColor, highContrast ? 0.14 : 0.1)}" />`;
      svg += `<circle class="node-dot powered" data-node-id="${node.id}" cx="${cx + pos.x}" cy="${cy + pos.y}" r="${poweredSize / 2}" fill="${rgba(elemColor, 0.95)}" stroke="rgba(255,255,255,0.9)" stroke-width="2.5" />`;
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
    poweredEdges.forEach((edge, idx) => {
      const a = boardState.nodes.find((n) => n.id === edge.a);
      const b = boardState.nodes.find((n) => n.id === edge.b);
      if (!a || !b) return;
      const pa = nodePosition(a);
      const pb = nodePosition(b);
      const speed = 0.0006;
      const p = (now * speed + idx * 0.23) % 1;
      const x = pa.x * (1 - p) + pb.x * p;
      const y = pa.y * (1 - p) + pb.y * p;
      svg += `<circle cx="${cx + x}" cy="${cy + y}" r="3" fill="rgba(180,255,255,0.9)" />`;
    });
  }

  svg += '</svg>';
  dom.container.innerHTML = svg;
}

function updateHud() {
  if (dom.realmSelect.options.length === 0) {
    const realms = Object.keys(cfgData.realm_rules || {});
    dom.realmSelect.innerHTML = realms.map((r) => `<option value="${r}">${r}</option>`).join('');
  }
  dom.realmSelect.value = boardState.realm;
  dom.hudQi.textContent = `${boardState.qi_used} / ${boardState.qi_cap}`;
  const invested = boardState.nodes.filter((n) => n.invested).length - 1;
  const powered = boardState.nodes.filter((n) => n.powered).length - 1;
  dom.hudCounts.textContent = `${Math.max(invested, 0)} / ${Math.max(powered, 0)}`;
  dom.hudBonus.textContent = '旋转改变连通';
  dom.rotateKnob.textContent = `旋转${dom.ringSelect.selectedOptions[0]?.textContent || '中环'}`;
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
  dom.detail.component.textContent = node.effects?.inner_core ? 'inner_core' : '-';
  dom.detail.effect.textContent = node.effects ? Object.keys(node.effects).join(', ') : '-';
  dom.detail.power.textContent = node.powered ? '通电' : node.invested ? '已点亮' : '未点亮';
  dom.detail.reason.textContent = nodeReason.get(node.id) || '-';

  dom.stats.atk.textContent = Math.round(10 + poweredStat('atk'));
  dom.stats.crit.textContent = Math.round(4 + poweredStat('crit'));
  dom.stats.hp.textContent = Math.round(18 + poweredStat('hp'));
  dom.stats.shield.textContent = Math.round(6 + poweredStat('shield'));
  dom.stats.mana.textContent = Math.round(6 + poweredStat('mana'));
  dom.stats.regen.textContent = Math.round(3 + poweredStat('regen'));
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
  }
  renderBoard();
  updateHud();
  refreshReconfig();
  updateDetail(selectedId || 'core');
  runtime.needsRender = false;
}

function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function startRotationAnim(ring, deltaDeg, continuous) {
  const now = performance.now();
  const startDeg = boardState.ring_rot_deg[ring];
  if (continuous) {
    const step = deltaDeg > 0 ? 1 : -1;
    runtime.anim = {
      ring,
      startDeg,
      endDeg: startDeg + step,
      startTime: now,
      duration: 50,
      repeat: 29,
      stepDeg: step,
      ease: false,
    };
  } else {
    runtime.anim = {
      ring,
      startDeg,
      endDeg: startDeg + deltaDeg,
      startTime: now,
      duration: 350,
      repeat: 0,
      stepDeg: 0,
      ease: true,
    };
  }
}

function rotateRing(deltaDeg) {
  const ring = dom.ringSelect.value;
  if (!boardState.ring_rot_deg.hasOwnProperty(ring)) return;
  startRotationAnim(ring, deltaDeg, dom.rotateContinuous.checked);
  runtime.needsRender = true;
}

function attachEvents() {
  dom.realmSelect.addEventListener('change', () => {
    boardState.realm = dom.realmSelect.value;
    boardState.qi_cap = cfgData.realm_rules[boardState.realm]?.qi_cap || boardState.qi_cap;
    rerender();
  });
  dom.toggleContrast.addEventListener('change', () => {
    runtime.needsRender = true;
    renderBoard();
  });
  dom.toggleBroken.addEventListener('change', () => {
    runtime.needsRender = true;
    renderBoard();
  });
  dom.rotateLeft.addEventListener('click', () => rotateRing(-15));
  dom.rotateRight.addEventListener('click', () => rotateRing(15));
  dom.rotateKnob.addEventListener('click', () => rotateRing(15));

  dom.container.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof SVGElement)) return;
    const nodeId = target.getAttribute('data-node-id');
    if (!nodeId) return;
    const node = boardState.nodes.find((n) => n.id === nodeId);
    if (!node || node.id === 'core') {
      updateDetail(nodeId);
      return;
    }
    node.invested = !node.invested;
    rerender(nodeId);
  });

  dom.container.addEventListener('mousemove', (event) => {
    const target = event.target;
    if (!(target instanceof SVGElement)) return;
    const nodeId = target.getAttribute('data-node-id');
    if (!nodeId) {
      dom.tooltip.style.opacity = 0;
      return;
    }
    const node = boardState.nodes.find((n) => n.id === nodeId);
    if (!node) return;
    dom.tooltip.style.opacity = 1;
    dom.tooltip.style.left = `${event.clientX}px`;
    dom.tooltip.style.top = `${event.clientY}px`;
    dom.tooltip.textContent = `${node.id} | ${node.elem} | ${node.trigram} | ${node.powered ? '通电' : node.invested ? '点亮' : '未点亮'}`;
  });

  dom.container.addEventListener('mouseleave', () => {
    dom.tooltip.style.opacity = 0;
  });

  dom.devToggle.addEventListener('click', () => {
    dom.devDrawer.classList.toggle('hidden');
  });

  dom.panel.reload.addEventListener('click', async () => {
    await loadConfig();
    await loadBoard();
    const keep = {
      realm: boardState.realm,
      rot_deg: { ...boardState.ring_rot_deg },
      invested: boardState.nodes.filter((n) => n.invested).map((n) => n.id),
    };
    buildBoardState(keep);
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
    rerender();
  });

  dom.panel.presetLoad.addEventListener('click', async () => {
    const name = dom.panel.presetSelect.value;
    if (!name) return;
    const { data } = await fetchJson(`./presets/${name}.json`);
    buildBoardState(data);
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
    rerender(node.id);
  });
}

function tick(now) {
  let didRender = false;
  if (runtime.anim) {
    const anim = runtime.anim;
    const progress = Math.min((now - anim.startTime) / anim.duration, 1);
    const eased = anim.ease ? easeInOutCubic(progress) : progress;
    const current = anim.startDeg + (anim.endDeg - anim.startDeg) * eased;
    boardState.ring_rot_deg[anim.ring] = normDeg(current);
    renderBoard(now);
    didRender = true;
    if (progress >= 1) {
      if (anim.repeat > 0) {
        anim.repeat -= 1;
        anim.startDeg = anim.endDeg;
        anim.endDeg = anim.endDeg + anim.stepDeg;
        anim.startTime = now;
      } else {
        boardState.ring_rot_deg[anim.ring] = normDeg(anim.endDeg);
        runtime.anim = null;
        rerender(null, { cause: 'rotation' });
      }
    }
  } else if (runtime.needsRender || runtime.flash || runtime.sparks) {
    if (now - runtime.lastRender > 33) {
      renderBoard(now);
      runtime.lastRender = now;
      didRender = true;
    }
  }
  if (!didRender && runtime.needsRender) {
    renderBoard(now);
    runtime.needsRender = false;
  }
  requestAnimationFrame(tick);
}

async function loadPresets() {
  const presets = ['bd1_dot_core', 'bd2_shield_loop', 'bd3_crit_chain'];
  presetFiles = presets;
  dom.panel.presetSelect.innerHTML = presets.map((p) => `<option value="${p}">${p}</option>`).join('');
}

async function init() {
  await loadConfig();
  await loadBoard();
  await loadPresets();
  buildBoardState();
  attachEvents();
  rerender();
  requestAnimationFrame(tick);
}

init();
