(function (global) {
  const { NodeState, EdgeComponent } = global.CircuitCore.types;
  const { get_trigram, apply_trigram_modifiers, TRIGRAM_LABELS } = global.CircuitCore.rules;

  const ELEMENT_REL = {
    wood: { sheng: 'fire', ke: 'earth' },
    fire: { sheng: 'earth', ke: 'metal' },
    earth: { sheng: 'metal', ke: 'water' },
    metal: { sheng: 'water', ke: 'wood' },
    water: { sheng: 'wood', ke: 'fire' },
  };

  function element_relation(a, b) {
    if (!a || !b) return 'none';
    if (a === b) return 'same';
    const map = ELEMENT_REL[a];
    if (!map) return 'none';
    if (map.sheng === b) return 'sheng';
    if (map.ke === b) return 'ke';
    return 'none';
  }

  function edgeKey(a, b) {
    return `${a}|${b}`;
  }

  function solveCircuit(state) {
    const logs = [];
    const trigram = get_trigram(state.rotation_deg || 0);
    const modifiers = {
      dpsMul: 1,
      sustainMul: 1,
      ehpMul: 1,
      overloadThresholdMul: 1,
      stabilityMul: 1,
      powerMul: 1,
      bandwidthMul: 1,
      lifesteal: 0,
      spread: 0,
      conditional: null,
    };

    const resources = {
      power: state.resources?.power ?? 10,
      bandwidth: state.resources?.bandwidth ?? 10,
      stability: state.resources?.stability ?? 10,
    };

    const context = { trigram, logs, modifiers, resources };
    apply_trigram_modifiers(context);

    resources.power *= modifiers.powerMul;
    resources.bandwidth *= modifiers.bandwidthMul;
    resources.stability *= modifiers.stabilityMul;

    const nodeMap = new Map(state.nodes.map((n) => [n.id, { ...n }]));
    const perNode = {};
    const adjacency = new Map();

    state.edges.forEach((edge) => {
      if (edge.enabled === false) return;
      if (!adjacency.has(edge.from)) adjacency.set(edge.from, []);
      if (!adjacency.has(edge.to)) adjacency.set(edge.to, []);
      adjacency.get(edge.from).push(edge);
      adjacency.get(edge.to).push(edge);
    });

    const reachable = new Set();
    const queue = ['core'];
    reachable.add('core');

    while (queue.length) {
      const current = queue.shift();
      const edges = adjacency.get(current) || [];
      edges.forEach((edge) => {
        const next = edge.from === current ? edge.to : edge.from;
        if (reachable.has(next)) return;
        if (edge.component === EdgeComponent.switch && edge.params?.enabled === false) return;
        if (edge.component === EdgeComponent.diode && edge.directed && edge.from !== current) return;
        reachable.add(next);
        queue.push(next);
      });
    }

    state.nodes.forEach((node) => {
      if (node.id === 'core') return;
      if (!node.invested) {
        perNode[node.id] = { state: NodeState.off };
        return;
      }
      if (!reachable.has(node.id)) {
        perNode[node.id] = { state: NodeState.charged, reason: '断线' };
      }
    });
    const disconnected = state.nodes.filter((n) => n.invested && !reachable.has(n.id)).map((n) => n.id);
    if (disconnected.length) {
      logs.push(`断线节点：${disconnected.slice(0, 6).join(', ')}${disconnected.length > 6 ? '...' : ''}`);
    }

    let powerBudget = resources.power;
    let bandwidthBudget = resources.bandwidth;
    let stabilityBudget = resources.stability;
    let powerUsed = 0;
    let bandwidthUsed = 0;

    const bfsOrder = Array.from(reachable).filter((id) => id !== 'core');
    bfsOrder.sort((a, b) => (nodeMap.get(a)?.ring || '').localeCompare(nodeMap.get(b)?.ring || ''));

    bfsOrder.forEach((id) => {
      const node = nodeMap.get(id);
      if (!node) return;
      if (!node.invested) {
        perNode[id] = { state: NodeState.off };
        return;
      }
      const powerCost = node.power_cost ?? 1;
      const bandwidthCost = node.bandwidth_cost ?? 1;
      const stabilityCost = node.stability_cost ?? 0.2;
      if (powerBudget - powerCost < 0 || bandwidthBudget - bandwidthCost < 0) {
        perNode[id] = { state: NodeState.charged, reason: '资源不足' };
        logs.push(`节点 ${id} 资源不足，保持charged`);
        return;
      }
      powerBudget -= powerCost;
      bandwidthBudget -= bandwidthCost;
      stabilityBudget -= stabilityCost;
      powerUsed += powerCost;
      bandwidthUsed += bandwidthCost;
      perNode[id] = { state: NodeState.active };
    });

    const activeNodes = new Set(
      Object.entries(perNode)
        .filter(([, info]) => info.state === NodeState.active)
        .map(([id]) => id),
    );
    activeNodes.add('core');

    state.edges.forEach((edge) => {
      if (edge.enabled === false) return;
      if (!activeNodes.has(edge.from) || !activeNodes.has(edge.to)) return;
      const cost = edge.bandwidth_cost ?? 0.5;
      bandwidthBudget -= cost;
      bandwidthUsed += cost;
    });

    const capBuffer = new Map();
    const tickSignals = [];
    let currentSignals = new Map([['core', 1]]);
    for (let tick = 0; tick < 2; tick += 1) {
      const nextSignals = new Map();
      currentSignals.forEach((signal, fromId) => {
        const fromNode = nodeMap.get(fromId);
        if (!fromNode) return;
        if (!activeNodes.has(fromId)) return;
        const edges = adjacency.get(fromId) || [];
        edges.forEach((edge) => {
          const toId = edge.from === fromId ? edge.to : edge.from;
          if (!activeNodes.has(toId)) return;
          if (edge.component === EdgeComponent.switch && edge.params?.enabled === false) return;
          if (edge.component === EdgeComponent.diode && edge.directed && edge.from !== fromId) return;

          let s = signal;
          if (edge.component === EdgeComponent.resistor) s *= 0.7;
          if (edge.component === EdgeComponent.amplifier) s *= 1.5;
          if (edge.component === EdgeComponent.capacitor) {
            const key = edgeKey(fromId, toId);
            if (tick === 0) {
              capBuffer.set(key, s);
              return;
            }
            s = (capBuffer.get(key) || s) * 1.3;
          }

          const rel = element_relation(fromNode.element, nodeMap.get(toId)?.element);
          if (rel === 'sheng') s *= 1.2;
          if (rel === 'ke') {
            s *= 1.4;
            stabilityBudget -= 1;
          }

          nextSignals.set(toId, (nextSignals.get(toId) || 0) + s);
        });
      });
      tickSignals.push(nextSignals);
      currentSignals = nextSignals;
    }

    const finalSignals = tickSignals[tickSignals.length - 1] || new Map();
    const overloadThreshold = 1.5 * modifiers.overloadThresholdMul;
    let overloadCount = 0;
    let burnedCount = 0;
    finalSignals.forEach((signal, id) => {
      const info = perNode[id] || { state: NodeState.off };
      if (info.state !== NodeState.active) return;
      info.in_signal = signal;
      info.out_signal = signal;
      if (signal > overloadThreshold) {
        overloadCount += 1;
        info.state = NodeState.overload;
        if (stabilityBudget <= 0) {
          info.state = NodeState.burned;
          burnedCount += 1;
        }
      }
      perNode[id] = info;
    });

    let activeCount = 0;
    nodeMap.forEach((node) => {
      const info = perNode[node.id];
      if (!info || info.state !== NodeState.active) return;
      activeCount += 1;
    });

    const elementWeights = {
      fire: { dps: 4 },
      metal: { dps: 2 },
      earth: { ehp: 10 },
      water: { sustain: 2, ehp: 4 },
      wood: { sustain: 1.5, dps: 1 },
    };

    let dps = 12;
    let ehp = 60;
    let sustain = 2;
    nodeMap.forEach((node) => {
      const stateInfo = perNode[node.id];
      if (!stateInfo || stateInfo.state !== NodeState.active) return;
      const weights = elementWeights[node.element] || {};
      dps += weights.dps || 0;
      ehp += weights.ehp || 0;
      sustain += weights.sustain || 0;
    });

    dps *= modifiers.dpsMul;
    sustain *= modifiers.sustainMul;
    ehp *= modifiers.ehpMul;

    if (modifiers.conditional && activeCount >= modifiers.conditional.minActive) {
      dps *= modifiers.conditional.dpsMul;
      logs.push(`兑：满足条件，输出提升 x${modifiers.conditional.dpsMul}`);
    }

    dps *= Math.max(0.2, 1 - overloadCount * 0.05 - burnedCount * 0.1);

    logs.push(`资源消耗：Power ${powerUsed.toFixed(1)} / ${resources.power.toFixed(1)}`);
    logs.push(`带宽消耗：Bandwidth ${bandwidthUsed.toFixed(1)} / ${resources.bandwidth.toFixed(1)}`);
    logs.push(`过载数：${overloadCount}，烧毁数：${burnedCount}`);

    return {
      trigram,
      trigramLabel: TRIGRAM_LABELS[trigram] || trigram,
      totals: {
        dps: Number(dps.toFixed(1)),
        ehp: Number(ehp.toFixed(1)),
        sustain: Number(sustain.toFixed(1)),
        overload_count: overloadCount,
        burned_count: burnedCount,
      },
      per_node: perNode,
      logs,
    };
  }

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.solveCircuit = solveCircuit;
  global.CircuitCore.element_relation = element_relation;
})(window);
