(function (global) {
  const DEFAULT_OPTIONS = {
    enforceBudgets: true,
    computeStructureMetrics: false,
    traverseLitOnly: true,
  };

  function normDeg(deg) {
    let v = deg % 360;
    if (v < 0) v += 360;
    return v;
  }

  function inSector(deg, sector) {
    const start = normDeg(sector.startDeg);
    const end = normDeg(sector.endDeg);
    if (start <= end) return deg >= start && deg < end;
    return deg >= start || deg < end;
  }

  function resolveMainElement(board) {
    const sectors = board.pointerRule?.sectors || [];
    const effectiveDeg = normDeg(0 - (board.rotationDeg || 0));
    for (const sector of sectors) {
      if (inSector(effectiveDeg, sector)) return sector.element;
    }
    return sectors[0]?.element || 'FIRE';
  }

  function aggregateStats(stats, payload, scale) {
    const key = payload.statKey;
    if (!stats.add[key]) stats.add[key] = 0;
    if (!stats.mul[key]) stats.mul[key] = 0;
    const value = payload.value * scale;
    if (payload.op === 'ADD') {
      stats.add[key] += value;
    } else {
      stats.mul[key] += value;
    }
    if (payload.cap != null) {
      stats.meta.cappedStats.add(key);
    }
  }

  function applyScaling(effect, node, mainElement) {
    let scale = 1;
    const scaling = effect.scaling || {};
    if (scaling.ringMultiplier && scaling.ringMultiplier[node.ring]) {
      scale *= scaling.ringMultiplier[node.ring];
    }
    if (scaling.mainElementMultiplier && node.element === mainElement) {
      scale *= scaling.mainElementMultiplier;
    }
    return scale;
  }

  function sortByRingAndId(a, b) {
    const order = { OUTER: 3, MIDDLE: 2, INNER: 1, CORE: 0 };
    const diff = (order[b.ring] || 0) - (order[a.ring] || 0);
    if (diff !== 0) return diff;
    return a.id.localeCompare(b.id);
  }

  function EvaluateBoard(board, catalog, options = {}) {
    const cfg = { ...DEFAULT_OPTIONS, ...options };
    const violations = [];
    const stats = { add: {}, mul: {}, meta: { cappedStats: new Set() } };
    const skillMods = [];
    const triggers = [];
    const nodeStates = {};
    const edgeStates = {};

    const mainElement = resolveMainElement(board);
    const powerCostPerNode = catalog.constants?.POWER_COST_PER_LIT_NODE ?? 1;

    const powerUsed = board.nodes.filter((n) => n.isLit).length * powerCostPerNode;
    let bandwidthUsed = 0;
    board.edges.forEach((edge) => {
      if (edge.state !== 'ENABLED') return;
      let cost = edge.baseCost ?? 1;
      if (edge.componentSlot?.type === 'RESISTOR') cost += 1;
      bandwidthUsed += cost;
    });

    let isValid = powerUsed <= board.budgets.powerCap && bandwidthUsed <= board.budgets.bandwidthCap;
    if (powerUsed > board.budgets.powerCap) {
      violations.push({ type: 'POWER_OVER', message: '点亮超出预算' });
    }
    if (bandwidthUsed > board.budgets.bandwidthCap) {
      violations.push({ type: 'BANDWIDTH_OVER', message: '连线超出预算' });
    }

    const adjacency = new Map();
    const addEdge = (from, to, edge) => {
      if (!adjacency.has(from)) adjacency.set(from, []);
      adjacency.get(from).push({ to, edge });
    };

    board.edges.forEach((edge) => {
      if (edge.state !== 'ENABLED') {
        edgeStates[edge.id] = 'DISABLED';
        return;
      }
      let directed = false;
      if (edge.componentSlot?.type === 'DIODE') directed = true;
      const from = edge.from;
      const to = edge.to;
      if (directed) {
        addEdge(from, to, edge);
      } else {
        addEdge(from, to, edge);
        addEdge(to, from, edge);
      }
      edgeStates[edge.id] = 'ENABLED';
    });

    const sources = board.nodes.filter(
      (n) => n.componentSlot?.type === 'SOURCE' || (n.visualType === 'CORE' && n.isLit),
    );
    if (!sources.length) {
      violations.push({ type: 'NO_SOURCE', message: '没有电源节点' });
      isValid = false;
    }

    const energizedNodes = new Set();
    const energizedEdges = new Set();
    if (sources.length) {
      const queue = sources.map((n) => n.id);
      const visited = new Set(queue);
      queue.forEach((id) => energizedNodes.add(id));
      while (queue.length) {
        const current = queue.shift();
        const neighbors = adjacency.get(current) || [];
        neighbors.forEach(({ to, edge }) => {
          const node = board.nodes.find((n) => n.id === to);
          if (!node) return;
          if (cfg.traverseLitOnly && !node.isLit && node.visualType !== 'CORE') return;
          if (!visited.has(to)) {
            visited.add(to);
            queue.push(to);
          }
          energizedEdges.add(edge.id);
          if (node.isLit) energizedNodes.add(to);
        });
      }
    }

    board.nodes.forEach((node) => {
      if (!node.isLit) {
        nodeStates[node.id] = 'OFF';
      } else if (!energizedNodes.has(node.id)) {
        nodeStates[node.id] = 'LIT_ONLY';
      } else {
        nodeStates[node.id] = 'ENERGIZED';
      }
    });

    if (!isValid && cfg.enforceBudgets) {
      Object.keys(nodeStates).forEach((id) => {
        if (nodeStates[id] !== 'OFF') nodeStates[id] = 'OVER_BUDGET';
      });
    }

    const energizedList = board.nodes
      .filter((n) => energizedNodes.has(n.id))
      .sort(sortByRingAndId);

    energizedList.forEach((node) => {
      if (!node.effectId) return;
      const effect = catalog.nodeEffects[node.effectId];
      if (!effect) {
        violations.push({ type: 'UNKNOWN_EFFECT', message: `未知效果 ${node.effectId}`, relatedIds: [node.id] });
        return;
      }
      const constraints = effect.constraints || { requireEnergized: true };
      if (constraints.requireEnergized && !energizedNodes.has(node.id)) return;
      if (constraints.requireElement && constraints.requireElement !== node.element) return;
      if (constraints.requireRing && constraints.requireRing !== node.ring) return;
      const scale = applyScaling(effect, node, mainElement);
      if (effect.category === 'STAT') {
        aggregateStats(stats, effect.payload, scale);
      } else if (effect.category === 'SKILL_MOD') {
        skillMods.push({ ...effect.payload, _source: node.id, _scale: scale, ring: node.ring });
      } else if (effect.category === 'TRIGGER') {
        triggers.push({ ...effect.payload, _source: node.id, _scale: scale, ring: node.ring });
      }
    });

    stats.meta.cappedStats = Array.from(stats.meta.cappedStats);

    const summaryLines = [
      `主元素：${mainElement}`,
      `Power: ${powerUsed}/${board.budgets.powerCap}`,
      `Bandwidth: ${bandwidthUsed}/${board.budgets.bandwidthCap}`,
      `通电节点：${energizedNodes.size}`,
    ];

    return {
      isValid,
      violations,
      costs: { powerUsed, bandwidthUsed },
      derived: {
        mainElement,
        sources: sources.map((n) => n.id),
        energizedNodes,
        energizedEdges,
      },
      combatOutput: {
        stats,
        skillMods,
        triggers,
        active: isValid || !cfg.enforceBudgets,
      },
      preview: {
        summaryLines,
        nodeStates,
        edgeStates,
      },
    };
  }

  global.BDEvaluator = { EvaluateBoard };
})(window);
