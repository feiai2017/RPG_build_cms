(function (global) {
  function solveBoard(boardState, options = {}) {
    const logs = [];
    const stones = options.stones || [];
    const trigramMods = options.trigramMods || {};
    const stoneMap = new Map(stones.map((s) => [s.id, s]));

    const slots = boardState.nodes;
    const sourceElements = new Map();
    boardState.core_sources.forEach((s) => {
      sourceElements.set(s.element, (sourceElements.get(s.element) || 0) + s.capacity);
    });

    const connectedEdges = boardState.edges.filter((e) => e.connected);
    const adjacency = new Map();
    connectedEdges.forEach((edge) => {
      if (!adjacency.has(edge.a)) adjacency.set(edge.a, []);
      if (!adjacency.has(edge.b)) adjacency.set(edge.b, []);
      adjacency.get(edge.a).push(edge.b);
      adjacency.get(edge.b).push(edge.a);
    });

    const energized = new Set();
    const queue = [];
    slots.forEach((slot) => {
      if (!slot.stone_id) return;
      if (slot.ring === 'inner' && sourceElements.has(slot.elem)) {
        energized.add(slot.id);
        queue.push(slot.id);
      }
    });

    while (queue.length) {
      const cur = queue.shift();
      const neighbors = adjacency.get(cur) || [];
      neighbors.forEach((nid) => {
        if (energized.has(nid)) return;
        energized.add(nid);
        queue.push(nid);
      });
    }

    const totals = { dps: 0, ehp: 0, sustain: 0, stability: 0 };
    const slotEffects = {};
    const component = new Set();

    const componentSlots = slots.filter((s) => energized.has(s.id));
    const elementCounts = new Map();
    componentSlots.forEach((slot) => {
      const stone = stoneMap.get(slot.stone_id);
      if (!stone) return;
      elementCounts.set(stone.element, (elementCounts.get(stone.element) || 0) + 1);
    });
    const dominantElement = [...elementCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || '土';

    componentSlots.forEach((slot) => {
      const stone = stoneMap.get(slot.stone_id);
      if (!stone) return;
      const base = { ...stone.effects };
      const trigram = slot.trigram;
      const mod = trigramMods[trigram] || {};
      const scale = slot.slot_type === 'skill' ? 1.2 : 1;
      const effect = {
        dps: (base.dps || 0) * (1 + (mod.dps || 0)) * scale,
        ehp: (base.ehp || 0) * (1 + (mod.ehp || 0)) * scale,
        sustain: (base.sustain || 0) * (1 + (mod.sustain || 0)) * scale,
        stability: (base.stability || 0) * (1 + (mod.stability || 0)) * scale,
      };
      totals.dps += effect.dps;
      totals.ehp += effect.ehp;
      totals.sustain += effect.sustain;
      totals.stability += effect.stability;
      slotEffects[slot.id] = { effect, trigram, slot_type: slot.slot_type, stone: stone.name };
    });

    const skillSlots = componentSlots.filter((s) => s.slot_type === 'skill');
    const skillMorphs = [];
    skillSlots.forEach((slot) => {
      if (dominantElement === '水') {
        totals.sustain += 6;
        skillMorphs.push(`${slot.id} 技能变形：回流 (sustain +6)`);
      } else if (dominantElement === '火') {
        totals.dps += 8;
        totals.stability -= 2;
        skillMorphs.push(`${slot.id} 技能变形：爆发 (dps +8, stability -2)`);
      } else if (dominantElement === '土') {
        totals.ehp += 10;
        skillMorphs.push(`${slot.id} 技能变形：守御 (ehp +10)`);
      } else if (dominantElement === '金') {
        totals.dps += 4;
        totals.stability += 1;
        skillMorphs.push(`${slot.id} 技能变形：锋锐 (dps +4)`);
      } else if (dominantElement === '木') {
        totals.sustain += 3;
        totals.ehp += 4;
        skillMorphs.push(`${slot.id} 技能变形：生息 (sustain +3, ehp +4)`);
      }
    });

    logs.push(`主导灵力元素：${dominantElement}`);
    logs.push(`通气槽位：${energized.size}`);
    skillMorphs.forEach((line) => logs.push(line));

    return {
      totals,
      dominantElement,
      energizedSlots: energized,
      slotEffects,
      logs,
    };
  }

  function simulateBoss(result, bossProfile) {
    const boss = bossProfile || { name: '镇岳傀儡', hp: 1200, dps: 25, burst: 80, burstInterval: 12 };
    const dps = Math.max(1, result.totals.dps);
    const ehp = Math.max(1, result.totals.ehp + 50);
    const sustain = Math.max(0, result.totals.sustain);
    const timeToKill = boss.hp / dps;
    const netIncoming = Math.max(1, boss.dps - sustain);
    const timeSurvive = ehp / netIncoming;
    const win = timeToKill <= timeSurvive;
    const logs = [
      `Boss ${boss.name} HP ${boss.hp}`,
      `击杀 ${timeToKill.toFixed(1)}s | 存活 ${timeSurvive.toFixed(1)}s`,
    ];
    return { win, timeToKill, timeSurvive, logs };
  }

  global.BaguaSolver = { solveBoard, simulateBoss };
})(window);
