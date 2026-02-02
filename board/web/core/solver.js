(function (global) {
  const DAMAGE_TYPE = {
    金: '物理',
    木: '自然',
    水: '寒霜',
    火: '火焰',
    土: '震荡',
    无: '混合',
  };

  function clamp(v, min, max) {
    return Math.max(min, Math.min(max, v));
  }

  function solveBoard(boardState, options = {}) {
    const logs = [];
    const stones = options.stones || [];
    const trigramMods = options.trigramMods || {};
    const realmRule = options.realmRule || {};
    const stoneMap = new Map(stones.map((s) => [s.id, s]));
    const slots = boardState.nodes || [];
    const poweredSlots = slots.filter((s) => s.powered && s.stone_id);

    const totals = { dps: 0, ehp: 0, sustain: 0, stability: 0 };
    const slotEffects = {};
    const elementCounts = new Map();

    poweredSlots.forEach((slot) => {
      const stone = stoneMap.get(slot.stone_id);
      if (!stone) return;
      elementCounts.set(stone.element, (elementCounts.get(stone.element) || 0) + 1);
    });

    const dominantElement =
      [...elementCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || '无';

    const skillMul = realmRule.skill_mul ?? 1;
    let skillDps = 0;

    poweredSlots.forEach((slot) => {
      const stone = stoneMap.get(slot.stone_id);
      if (!stone) return;
      const trigram = slot.trigram;
      const mod = trigramMods[trigram] || {};
      const scale = slot.slot_type === 'skill' ? 1.2 * skillMul : 1;
      const base = stone.effects || {};
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
      if (slot.slot_type === 'skill') skillDps += effect.dps;
      slotEffects[slot.id] = {
        effect,
        trigram,
        slot_type: slot.slot_type,
        stone: stone.name,
        element: stone.element,
      };
    });

    const enabledRings = boardState.enabled_rings || [];
    const eligibleSlots = slots.filter((s) => enabledRings.includes(s.ring) && s.slot_type !== 'core');
    const emptySlots = eligibleSlots.filter((s) => !s.stone_id).length;
    const distinctElements = elementCounts.size;
    const coreSlots = poweredSlots.filter((s) => s.slot_type === 'core');
    const coreStoneIds = coreSlots.map((s) => stoneMap.get(s.stone_id)?.id).filter(Boolean);

    if (coreStoneIds.includes('core_lonely')) {
      const bonus = emptySlots * 0.8;
      totals.dps += bonus;
      logs.push(`核心石·独自升级：空槽${emptySlots} → dps +${bonus.toFixed(1)}`);
    }
    if (coreStoneIds.includes('core_five_color')) {
      const bonus = skillDps * (distinctElements * 0.05);
      if (bonus > 0) {
        totals.dps += bonus;
        logs.push(`核心石·五色俱全：元素${distinctElements} → 技能dps +${bonus.toFixed(1)}`);
      }
    }
    if (coreStoneIds.includes('core_resonance')) {
      const filled = eligibleSlots.length - emptySlots;
      const bonus = Math.floor(filled / 4) * 2;
      if (bonus > 0) {
        totals.sustain += bonus;
        logs.push(`核心石·灵脉共鸣：已插${filled} → sustain +${bonus}`);
      }
    }

    const skillSlots = poweredSlots.filter((s) => s.slot_type === 'skill');
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
        skillMorphs.push(`${slot.id} 技能变形：锋锐 (dps +4, stability +1)`);
      } else if (dominantElement === '木') {
        totals.sustain += 3;
        totals.ehp += 4;
        skillMorphs.push(`${slot.id} 技能变形：生息 (sustain +3, ehp +4)`);
      }
    });

    logs.push(`主导灵力元素：${dominantElement}`);
    logs.push(`通气槽位：${poweredSlots.length}`);
    if (skillMul !== 1) logs.push(`境界技能倍率：x${skillMul.toFixed(2)}`);
    skillMorphs.forEach((line) => logs.push(line));

    return {
      totals,
      dominantElement,
      energizedSlots: poweredSlots.map((s) => s.id),
      slotEffects,
      elementCounts: Object.fromEntries(elementCounts),
      logs,
    };
  }

  function simulateBoss(result, bossProfile, options = {}) {
    const boss = bossProfile || {
      name: '镇河魇王',
      hp: 1400,
      dps: 26,
      burst: 90,
      burstInterval: 8,
    };
    const dt = options.tickSeconds || 0.5;
    const maxTicks = options.maxTicks || 240;
    const basePlayerHp = 120;
    const dps = Math.max(1, result.totals.dps);
    const sustain = Math.max(0, result.totals.sustain);
    const stability = result.totals.stability || 0;
    const playerMaxHp = Math.max(1, basePlayerHp + result.totals.ehp);
    const bossMaxHp = boss.hp;

    let playerHp = playerMaxHp;
    let bossHp = bossMaxHp;
    let tick = 0;
    let timeToKill = Infinity;
    let timeSurvive = Infinity;
    let win = false;

    const events = [];
    const logs = [];

    const critChance = clamp(stability / 120, 0, 0.45);
    const critMult = 1.6;
    const dmgType = DAMAGE_TYPE[result.dominantElement || '无'] || '混合';
    const incomingMult = clamp(1 - stability / 180, 0.6, 1.05);

    const pushEvent = (evt) => {
      events.push(evt);
      const line = `[${evt.tick}] ${evt.time.toFixed(1)}s ${evt.source} → ${evt.target} ${evt.amount.toFixed(1)} (${evt.kind}) ${evt.type}`;
      logs.push(line);
    };

    for (tick = 0; tick < maxTicks; tick += 1) {
      const time = tick * dt;
      const critRoll = ((tick * 37) % 100) / 100;
      const isCrit = critRoll < critChance;
      const atkDamage = dps * dt * (isCrit ? critMult : 1);
      bossHp -= atkDamage;
      pushEvent({
        tick,
        time,
        source: '玩家',
        target: boss.name,
        amount: atkDamage,
        kind: isCrit ? 'CRIT' : 'HIT',
        type: dmgType,
        note: isCrit ? `暴击×${critMult.toFixed(1)}` : '',
        bossHp: Math.max(0, bossHp),
        playerHp,
      });

      if (bossHp <= 0) {
        timeToKill = time;
        win = true;
        break;
      }

      const baseIncoming = boss.dps * dt * incomingMult;
      playerHp -= baseIncoming;
      pushEvent({
        tick,
        time,
        source: boss.name,
        target: '玩家',
        amount: baseIncoming,
        kind: 'DAMAGE',
        type: '物理',
        note: '常规压力',
        bossHp,
        playerHp: Math.max(0, playerHp),
      });

      if (boss.burst && boss.burstInterval > 0 && time > 0 && time % boss.burstInterval < dt) {
        const burstDamage = boss.burst * incomingMult;
        playerHp -= burstDamage;
        pushEvent({
          tick,
          time,
          source: boss.name,
          target: '玩家',
          amount: burstDamage,
          kind: 'BURST',
          type: '法术',
          note: '爆发技',
          bossHp,
          playerHp: Math.max(0, playerHp),
        });
      }

      if (sustain > 0) {
        const heal = sustain * dt;
        playerHp = Math.min(playerMaxHp, playerHp + heal);
        pushEvent({
          tick,
          time,
          source: '玩家',
          target: '玩家',
          amount: heal,
          kind: 'HEAL',
          type: '回能',
          note: '续航回复',
          bossHp,
          playerHp,
        });
      }

      if (playerHp <= 0) {
        timeSurvive = time;
        win = false;
        break;
      }
    }

    if (!win && timeSurvive === Infinity) {
      timeSurvive = tick * dt;
    }
    if (win && timeToKill === Infinity) {
      timeToKill = tick * dt;
    }

    const summary = [
      `Boss ${boss.name} HP ${bossMaxHp}`,
      `击杀 ${timeToKill === Infinity ? '-' : timeToKill.toFixed(1)}s | 存活 ${timeSurvive === Infinity ? '-' : timeSurvive.toFixed(1)}s`,
    ];

    return {
      win,
      timeToKill,
      timeSurvive,
      boss,
      logs: summary.concat(logs.slice(0, 10)),
      events,
      summary,
    };
  }

  global.BaguaSolver = { solveBoard, simulateBoss };
})(window);
