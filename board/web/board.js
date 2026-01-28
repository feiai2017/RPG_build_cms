const app = new PIXI.Application({
  resizeTo: window,
  backgroundAlpha: 0,
  antialias: true,
});

document.getElementById('canvas-container').appendChild(app.view);

const panel = {
  sectors: document.getElementById('toggle-sectors'),
  rings: document.getElementById('toggle-rings'),
  edges: document.getElementById('toggle-edges'),
  glow: document.getElementById('glow-strength'),
  edgeStrength: document.getElementById('edge-strength'),
  sectorOpacity: document.getElementById('sector-opacity'),
  ringStrength: document.getElementById('ring-strength'),
  scale: document.getElementById('scale'),
  search: document.getElementById('search'),
  searchResult: document.getElementById('search-result'),
};

const tooltip = document.getElementById('tooltip');

const TYPE_SIZES = {
  small: 10,
  medium: 12,
  keystone: 16,
  socket: 14,
  bridge: 12,
  convert: 12,
  core: 22,
};

const world = new PIXI.Container();
app.stage.addChild(world);

const layers = {
  vignette: new PIXI.Container(),
  sectors: new PIXI.Container(),
  rings: new PIXI.Container(),
  edges: new PIXI.Container(),
  nodesGlow: new PIXI.Container(),
  nodes: new PIXI.Container(),
  labels: new PIXI.Container(),
  highlight: new PIXI.Container(),
};

Object.values(layers).forEach((layer) => world.addChild(layer));

let boardData = null;
let nodeGraphics = new Map();
let edgeGraphics = [];
let highlightedNodeId = null;
let hoverNodeId = null;

const state = {
  drag: false,
  dragStart: { x: 0, y: 0 },
  worldStart: { x: 0, y: 0 },
  zoom: 1,
};

function hexToInt(hex) {
  return parseInt(hex.replace('#', '0x'), 16);
}

function getElementColor(element) {
  return boardData.meta.colors[element] || '#7aa5c7';
}

function clearLayer(layer) {
  layer.removeChildren();
}

function drawVignette(radius) {
  clearLayer(layers.vignette);
  for (let i = 0; i < 4; i++) {
    const ring = new PIXI.Graphics();
    const alpha = 0.08 + i * 0.04;
    ring.beginFill(0x000000, alpha);
    ring.drawCircle(0, 0, radius * (1.2 + i * 0.1));
    ring.endFill();
    layers.vignette.addChild(ring);
  }
}

function drawSectors(radius) {
  clearLayer(layers.sectors);
  if (!panel.sectors.checked) return;
  const elements = boardData.meta.elements;
  const span = (Math.PI * 2) / elements.length;
  elements.forEach((element, idx) => {
    const g = new PIXI.Graphics();
    const start = idx * span;
    const end = start + span;
    const steps = 32;
    g.beginFill(hexToInt(getElementColor(element)), parseFloat(panel.sectorOpacity.value));
    g.moveTo(0, 0);
    for (let i = 0; i <= steps; i++) {
      const t = start + (end - start) * (i / steps);
      g.lineTo(Math.cos(t) * radius, Math.sin(t) * radius);
    }
    g.lineTo(0, 0);
    g.endFill();
    layers.sectors.addChild(g);
  });
}

function drawRings() {
  clearLayer(layers.rings);
  if (!panel.rings.checked) return;
  const alpha = parseFloat(panel.ringStrength.value);
  boardData.rings.forEach((ring) => {
    if (ring.id === 'core') return;
    const g = new PIXI.Graphics();
    g.lineStyle(1.2, 0x2a3440, 0.35 * alpha);
    g.drawCircle(0, 0, ring.radius);
    layers.rings.addChild(g);
  });
}

function drawEdges() {
  clearLayer(layers.edges);
  clearLayer(layers.highlight);
  if (!panel.edges.checked) return;
  const strength = parseFloat(panel.edgeStrength.value);
  edgeGraphics = [];
  const kindAlpha = {
    ring: 0.18,
    radial: 0.26,
    special: 0.38,
  };

  boardData.edges.forEach((edge) => {
    const a = boardData.nodeMap.get(edge.a);
    const b = boardData.nodeMap.get(edge.b);
    if (!a || !b) return;
    const g = new PIXI.Graphics();
    g.lineStyle(1.1, 0x8fa5b8, kindAlpha[edge.kind] * strength);
    g.moveTo(a.x, a.y);
    g.lineTo(b.x, b.y);
    layers.edges.addChild(g);
    edgeGraphics.push({ edge, g });
  });
}

function drawLabels(radius) {
  clearLayer(layers.labels);
  const elements = boardData.meta.elements;
  const span = (Math.PI * 2) / elements.length;
  elements.forEach((element, idx) => {
    const angle = idx * span + span / 2;
    const x = Math.cos(angle) * (radius + 22);
    const y = Math.sin(angle) * (radius + 22);
    const text = new PIXI.Text(element, {
      fontFamily: 'Microsoft YaHei, Noto Sans CJK SC, sans-serif',
      fontSize: 20,
      fill: '#DFE8F2',
    });
    text.anchor.set(0.5);
    text.position.set(x, y);
    layers.labels.addChild(text);
  });
}

function drawNodeShape(g, node, size, fillColor, strokeColor) {
  const c = hexToInt(strokeColor);
  g.lineStyle(1.4, c, 0.9);
  if (node.type === 'small') {
    g.drawCircle(0, 0, size * 0.5);
  } else if (node.type === 'medium') {
    g.beginFill(hexToInt(fillColor), 0.55);
    g.drawCircle(0, 0, size * 0.55);
    g.endFill();
  } else if (node.type === 'keystone') {
    const r = size * 0.6;
    g.drawPolygon([
      -r, 0,
      -r / 2, -r * 0.86,
      r / 2, -r * 0.86,
      r, 0,
      r / 2, r * 0.86,
      -r / 2, r * 0.86,
    ]);
  } else if (node.type === 'socket') {
    g.drawCircle(0, 0, size * 0.55);
    g.beginFill(hexToInt(fillColor), 0.9);
    g.drawCircle(0, 0, size * 0.18);
    g.endFill();
  } else if (node.type === 'bridge') {
    const s = size * 0.6;
    g.drawRect(-s / 2, -s / 2, s, s);
  } else if (node.type === 'convert') {
    const r = size * 0.55;
    g.drawPolygon([0, -r, r, 0, 0, r, -r, 0]);
  } else if (node.type === 'core') {
    g.lineStyle(2.2, c, 1);
    g.beginFill(hexToInt(fillColor), 0.7);
    g.drawCircle(0, 0, size * 0.7);
    g.endFill();
  }
}

function drawNodes() {
  clearLayer(layers.nodesGlow);
  clearLayer(layers.nodes);
  nodeGraphics.clear();

  const glowStrength = parseFloat(panel.glow.value);

  boardData.nodes.forEach((node) => {
    const color = node.type === 'core' ? '#9FE6FF' : getElementColor(node.element);
    const baseSize = TYPE_SIZES[node.type] || 12;

    const glow = new PIXI.Graphics();
    glow.beginFill(hexToInt(color), glowStrength);
    glow.drawCircle(0, 0, baseSize);
    glow.endFill();
    glow.position.set(node.x, node.y);
    layers.nodesGlow.addChild(glow);

    const g = new PIXI.Graphics();
    drawNodeShape(g, node, baseSize, '#101821', color);
    g.position.set(node.x, node.y);
    g.eventMode = 'static';
    g.cursor = 'pointer';
    g.hitArea = new PIXI.Circle(0, 0, baseSize * 0.7);

    g.on('pointerover', () => {
      hoverNodeId = node.id;
      showTooltip(node);
      highlightNode(node.id, true);
    });
    g.on('pointerout', () => {
      hoverNodeId = null;
      hideTooltip();
      highlightNode(null, false);
    });

    layers.nodes.addChild(g);
    nodeGraphics.set(node.id, g);
  });
}

function highlightNode(nodeId, fromHover = false) {
  clearLayer(layers.highlight);
  if (!nodeId && !highlightedNodeId) return;
  const id = nodeId || highlightedNodeId;
  const node = boardData.nodeMap.get(id);
  if (!node) return;
  const ring = new PIXI.Graphics();
  ring.lineStyle(2, 0x9fe6ff, 0.9);
  ring.drawCircle(node.x, node.y, (TYPE_SIZES[node.type] || 12) + 8);
  layers.highlight.addChild(ring);

  boardData.edges.forEach((edge) => {
    if (edge.a !== id && edge.b !== id) return;
    const a = boardData.nodeMap.get(edge.a);
    const b = boardData.nodeMap.get(edge.b);
    if (!a || !b) return;
    const g = new PIXI.Graphics();
    g.lineStyle(2.2, 0x9fe6ff, 0.7);
    g.moveTo(a.x, a.y);
    g.lineTo(b.x, b.y);
    layers.highlight.addChild(g);
  });

  if (!fromHover) {
    centerOnNode(node);
  }
}

function showTooltip(node) {
  tooltip.style.opacity = '1';
  tooltip.innerHTML = `${node.id}<br>${node.element} | ${node.ring} | ${node.type}`;
}

function hideTooltip() {
  tooltip.style.opacity = '0';
}

function updateTooltipPosition(x, y) {
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
}

function centerOnNode(node) {
  const scale = parseFloat(panel.scale.value) * state.zoom;
  world.position.set(app.renderer.width / 2 - node.x * scale, app.renderer.height / 2 - node.y * scale);
}

function redrawAll() {
  if (!boardData) return;
  const maxRadius = Math.max(...boardData.rings.map((r) => r.radius));
  drawVignette(maxRadius);
  drawSectors(maxRadius);
  drawRings();
  drawEdges();
  drawNodes();
  drawLabels(maxRadius);
  const scale = parseFloat(panel.scale.value) * state.zoom;
  world.scale.set(scale);
  world.position.set(app.renderer.width / 2, app.renderer.height / 2);
}

function initControls() {
  const inputs = [
    panel.sectors,
    panel.rings,
    panel.edges,
    panel.glow,
    panel.edgeStrength,
    panel.sectorOpacity,
    panel.ringStrength,
    panel.scale,
  ];
  inputs.forEach((input) => input.addEventListener('input', redrawAll));

  panel.search.addEventListener('input', () => {
    const id = panel.search.value.trim();
    if (!id) {
      highlightedNodeId = null;
      panel.searchResult.textContent = '';
      redrawAll();
      return;
    }
    const node = boardData.nodeMap.get(id);
    if (node) {
      highlightedNodeId = node.id;
      panel.searchResult.textContent = `${node.id} (${node.element} / ${node.ring} / ${node.type})`;
      redrawAll();
      highlightNode(node.id, false);
    } else {
      panel.searchResult.textContent = '未找到';
    }
  });
}

function attachInteraction() {
  app.view.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = Math.sign(e.deltaY) * -0.05;
    state.zoom = Math.min(2.0, Math.max(0.5, state.zoom + delta));
    redrawAll();
  });

  app.view.addEventListener('pointerdown', (e) => {
    state.drag = true;
    state.dragStart = { x: e.clientX, y: e.clientY };
    state.worldStart = { x: world.position.x, y: world.position.y };
  });

  window.addEventListener('pointerup', () => {
    state.drag = false;
  });

  window.addEventListener('pointermove', (e) => {
    updateTooltipPosition(e.clientX, e.clientY);
    if (!state.drag) return;
    const dx = e.clientX - state.dragStart.x;
    const dy = e.clientY - state.dragStart.y;
    world.position.set(state.worldStart.x + dx, state.worldStart.y + dy);
  });
}

async function loadBoard() {
  const res = await fetch('./board.json');
  const data = await res.json();
  data.nodeMap = new Map();
  data.nodes.forEach((n) => data.nodeMap.set(n.id, n));
  boardData = data;
  redrawAll();
}

window.addEventListener('resize', () => redrawAll());

loadBoard().then(() => {
  initControls();
  attachInteraction();
});
