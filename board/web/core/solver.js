(function (global) {
  const GUA_ORDER = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
  const GUA_INFO = {
    '乾': { element: '金', verb: '贯' },
    '兑': { element: '金', verb: '回' },
    '离': { element: '火', verb: '燃' },
    '震': { element: '木', verb: '连' },
    '巽': { element: '木', verb: '散' },
    '坎': { element: '水', verb: '控' },
    '艮': { element: '土', verb: '镇' },
    '坤': { element: '土', verb: '护' },
  };

  const SKILL_LIBRARY = {
    skill_qian_pierce: { id: 'skill_qian_pierce', name: '贯金斩', gua: '乾', kind: 'output', element: '金', baseDamage: 26, baseCd: 5 },
    skill_dui_echo: { id: 'skill_dui_echo', name: '回音刃', gua: '兑', kind: 'output', element: '金', baseDamage: 22, baseCd: 4 },
    skill_li_flare: { id: 'skill_li_flare', name: '燃光爆', gua: '离', kind: 'output', element: '火', baseDamage: 30, baseCd: 6 },
    skill_zhen_chain: { id: 'skill_zhen_chain', name: '连木冲', gua: '震', kind: 'output', element: '木', baseDamage: 20, baseCd: 4 },
    skill_kan_tide: { id: 'skill_kan_tide', name: '控水潮', gua: '坎', kind: 'output', element: '水', baseDamage: 24, baseCd: 5 },
    skill_xun_guard: { id: 'skill_xun_guard', name: '散影护', gua: '巽', kind: 'support', element: '木', baseDamage: 0, baseCd: 5, sustain: 6 },
    skill_gen_shell: { id: 'skill_gen_shell', name: '镇岳盾', gua: '艮', kind: 'support', element: '土', baseDamage: 0, baseCd: 6, sustain: 8 },
    skill_kun_reforge: { id: 'skill_kun_reforge', name: '护体阵', gua: '坤', kind: 'support', element: '土', baseDamage: 0, baseCd: 4, sustain: 5 },
  };

  const FORM_RUNES = {
    spread: { id: 'spread', name: '散射', mult: 0.6, hits: 2 },
    aoe: { id: 'aoe', name: '范围', mult: 1.2, hits: 1 },
    chain: { id: 'chain', name: '弹射', mult: 0.55, hits: 2 },
    channel: { id: 'channel', name: '持续', mult: 0.4, hits: 3 },
    melee: { id: 'melee', name: '近战', mult: 1.5, hits: 1, cdAdd: 1 },
    mark: { id: 'mark', name: '印记', mult: 1, hits: 1, markBonus: 2 },
  };

  const LOOP_RUNES = {
    cd_down: { id: 'cd_down', name: '降冷', cdDelta: -1 },
    charge: { id: 'charge', name: '充能', charges: 2 },
    auto_recast: { id: 'auto_recast', name: '复诵', recastDelay: 2, recastMul: 0.55 },
    cond_accel: { id: 'cond_accel', name: '条件加速', accelOnMark: 1 },
    hit_energy: { id: 'hit_energy', name: '命中回能', sustainOnHit: 3 },
    crit_energy: { id: 'crit_energy', name: '暴击回能', sustainOnCrit: 5 },
  };

  const EDGE_RUNES = {
    RELAY: { id: 'RELAY', name: '接力', delay: 2, mul: 0.55 },
    CD_ROUTER: { id: 'CD_ROUTER', name: '减冷路由', ratio: 0.1 },
    REACT_DETONATOR: { id: 'REACT_DETONATOR', name: '反应引爆', window: 4 },
    SUSTAIN_LINK: { id: 'SUSTAIN_LINK', name: '续航纽带', ratio: 0.05 },
  };

  const REACTIONS = {
    '火|水': { type: 'STEAM', name: '蒸汽', bonus: 0.6 },
    '水|金': { type: 'FROST', name: '凝霜', bonus: 0.4 },
    '木|火': { type: 'BURN_SPREAD', name: '焚化', bonus: 0.5 },
    '木|土': { type: 'ROOT', name: '生根', bonus: 0.35 },
    '金|土': { type: 'SHATTER', name: '崩解', bonus: 0.45 },
    '火|土': { type: 'LAVA_FIELD', name: '熔域', bonus: 0.5 },
  };

  const BOSS_PROFILES = [
    { id: 'dummy', name: '木桩', hp: 1200, dps: 0, spike: 0, spikeInterval: 10, desc: '基准对照' },
    { id: 'burst', name: '玄铁巨兽', hp: 1800, dps: 20, spike: 120, spikeInterval: 8, desc: '爆发型' },
    { id: 'pressure', name: '玄水魅影', hp: 1600, dps: 45, spike: 60, spikeInterval: 12, desc: '持续压制' },
  ];

  function canonicalElementPair(a, b) {
    return [a, b].sort().join('|');
  }

  function pushEvent(events, evt) {
    events.push(evt);
  }

  function buildSkillState(skillId, formRune, loopRune) {
    const base = SKILL_LIBRARY[skillId];
    if (!base) return null;
    const form = formRune ? FORM_RUNES[formRune] : null;
    const loop = loopRune ? LOOP_RUNES[loopRune] : null;
    let baseCd = base.baseCd;
    if (form?.cdAdd) baseCd += form.cdAdd;
    if (loop?.cdDelta) baseCd = Math.max(1, baseCd + loop.cdDelta);
    const charges = loop?.charges || 1;
    return {
      ...base,
      formRune,
      loopRune,
      baseCd,
      charges,
      chargeMax: charges,
      cdLeft: 0,
    };
  }

  function applyCooldownReduction(skill, amount, reason, tick, events) {
    const before = skill.cdLeft;
    skill.cdLeft = Math.max(0, skill.cdLeft - amount);
    if (before !== skill.cdLeft) {
      pushEvent(events, {
        tick,
        time: tick * 0.5,
        source: '系统',
        target: skill.name,
        amount: before - skill.cdLeft,
        kind: 'COOLDOWN',
        type: '冷却',
        note: reason,
        extra: { event: 'COOLDOWN_CHANGED', skill_id: skill.id, before, after: skill.cdLeft, reason },
      });
    }
  }

  function simulateBuild(build, options = {}) {
    const tickSeconds = options.tickSeconds || 0.5;
    const maxTicks = options.maxTicks || 20;
    const guaOrder = GUA_ORDER;
    const skillsByGua = build.skills_by_gua || {};
    const privateRunes = build.private_runes || {};
    const edgeRunes = build.edge_runes || {};

    const skillStates = new Map();
    guaOrder.forEach((gua) => {
      const skillId = skillsByGua[gua];
      if (!skillId) return;
      const runes = privateRunes[gua] || {};
      const state = buildSkillState(skillId, runes.form, runes.loop);
      if (state) skillStates.set(gua, state);
    });

    const edgeMap = new Map();
    Object.entries(edgeRunes).forEach(([key, runeId]) => {
      if (!runeId) return;
      const parts = key.split('|');
      if (parts.length !== 2) return;
      const [a, b] = parts;
      if (!edgeMap.has(a)) edgeMap.set(a, []);
      if (!edgeMap.has(b)) edgeMap.set(b, []);
      edgeMap.get(a).push({ to: b, rune: runeId });
      edgeMap.get(b).push({ to: a, rune: runeId });
    });

    const events = [];
    const castsPerSkill = {};
    const reactionCounts = {};
    let downtimeTicks = 0;
    let sustainTotal = 0;
    let totalDamage = 0;

    const target = { id: 'dummy', name: '木桩', mark: null };
    const detonateWindows = new Map();
    const immediateQueue = [];

    for (let tick = 0; tick < maxTicks; tick += 1) {
      // cooldown tick
      skillStates.forEach((skill) => {
        if (skill.cdLeft > 0) skill.cdLeft -= 1;
      });

      // process delayed queue
      immediateQueue.forEach((item) => { item.delay -= 1; });

      let castItem = immediateQueue.find((item) => item.delay <= 0);
      if (castItem) {
        immediateQueue.splice(immediateQueue.indexOf(castItem), 1);
      } else {
        castItem = null;
      }

      let skillToCast = null;
      if (castItem) {
        skillToCast = skillStates.get(castItem.gua) || null;
      } else {
        for (const gua of guaOrder) {
          const skill = skillStates.get(gua);
          if (!skill) continue;
          if (skill.cdLeft <= 0) {
            skillToCast = skill;
            break;
          }
        }
      }

      if (!skillToCast) {
        downtimeTicks += 1;
        continue;
      }

      const isRelay = !!castItem;
      const gua = skillToCast.gua;
      const form = skillToCast.formRune ? FORM_RUNES[skillToCast.formRune] : null;
      const loop = skillToCast.loopRune ? LOOP_RUNES[skillToCast.loopRune] : null;
      const hits = form?.hits || 1;
      const baseMul = form?.mult || 1;
      const markBonus = form?.markBonus || 0;
      const relayMul = isRelay ? EDGE_RUNES.RELAY.mul : 1;
      const totalMul = baseMul * relayMul;

      skillToCast.cdLeft = skillToCast.baseCd;
      castsPerSkill[skillToCast.id] = (castsPerSkill[skillToCast.id] || 0) + 1;

      pushEvent(events, {
        tick,
        time: tick * tickSeconds,
        source: '玩家',
        target: target.name,
        amount: 0,
        kind: 'CAST',
        type: skillToCast.element,
        note: isRelay ? '接力施放' : '施放',
        extra: {
          event: 'SKILL_CAST',
          skill_id: skillToCast.id,
          gua,
          element: skillToCast.element,
          is_relay_cast: isRelay,
          runes_snapshot: { form: skillToCast.formRune, loop: skillToCast.loopRune },
        },
      });

      if (loop?.recastDelay && !isRelay) {
        immediateQueue.push({ gua, delay: loop.recastDelay, relay: true });
      }

      const edgeLinks = edgeMap.get(gua) || [];
      edgeLinks.forEach((link) => {
        if (link.rune === 'RELAY' && !isRelay) {
          immediateQueue.push({ gua: link.to, delay: EDGE_RUNES.RELAY.delay, relay: true, from: gua });
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: gua,
            target: link.to,
            amount: 0,
            kind: 'EDGE',
            type: 'RELAY',
            note: '接力触发',
            extra: { event: 'EDGE_RUNE_TRIGGERED', edge_type: 'RELAY', from_gua: gua, to_gua: link.to },
          });
        }
      });

      for (let h = 0; h < hits; h += 1) {
        if (skillToCast.kind === 'support') {
          const sustain = (skillToCast.sustain || 4) * totalMul;
          sustainTotal += sustain;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: '玩家',
            target: '玩家',
            amount: sustain,
            kind: 'SUSTAIN',
            type: '护持',
            note: skillToCast.name,
            extra: { event: 'SUSTAIN_GAINED', amount: sustain, kind: 'shield', source: skillToCast.id },
          });
          continue;
        }

        const damage = skillToCast.baseDamage * totalMul;
        totalDamage += damage;

        // reaction check
        let reaction = null;
        if (target.mark && target.mark.element !== skillToCast.element) {
          const key = canonicalElementPair(target.mark.element, skillToCast.element);
          reaction = REACTIONS[key] || null;
          target.mark = null;
        }

        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: skillToCast.name,
          target: target.name,
          amount: damage,
          kind: 'HIT',
          type: skillToCast.element,
          note: form?.name || '',
          extra: {
            event: 'HIT',
            skill_id: skillToCast.id,
            element: skillToCast.element,
            applied_mark: skillToCast.element,
          },
        });

        if (loop?.sustainOnHit) {
          sustainTotal += loop.sustainOnHit;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: skillToCast.name,
            target: '玩家',
            amount: loop.sustainOnHit,
            kind: 'SUSTAIN',
            type: '回能',
            note: loop.name,
            extra: { event: 'SUSTAIN_GAINED', amount: loop.sustainOnHit, kind: 'energy', source: skillToCast.id },
          });
        }

        if (loop?.sustainOnCrit) {
          const crit = ((tick + h + skillToCast.baseCd) % 5) === 0;
          if (crit) {
            sustainTotal += loop.sustainOnCrit;
            pushEvent(events, {
              tick,
              time: tick * tickSeconds,
              source: skillToCast.name,
              target: '玩家',
              amount: loop.sustainOnCrit,
              kind: 'SUSTAIN',
              type: '暴击回能',
              note: loop.name,
              extra: { event: 'SUSTAIN_GAINED', amount: loop.sustainOnCrit, kind: 'energy', source: skillToCast.id, crit: true },
            });
          }
        }

        edgeLinks.forEach((link) => {
          if (link.rune === 'CD_ROUTER') {
            const targetSkill = skillStates.get(link.to);
            if (targetSkill) {
              const reduce = Math.ceil(targetSkill.cdLeft * EDGE_RUNES.CD_ROUTER.ratio);
              applyCooldownReduction(targetSkill, reduce, '减冷路由', tick, events);
              pushEvent(events, {
                tick,
                time: tick * tickSeconds,
                source: gua,
                target: link.to,
                amount: reduce,
                kind: 'EDGE',
                type: 'CD_ROUTER',
                note: '减冷触发',
                extra: { event: 'EDGE_RUNE_TRIGGERED', edge_type: 'CD_ROUTER', from_gua: gua, to_gua: link.to },
              });
            }
          }
          if (link.rune === 'SUSTAIN_LINK') {
            const gain = damage * EDGE_RUNES.SUSTAIN_LINK.ratio;
            sustainTotal += gain;
            pushEvent(events, {
              tick,
              time: tick * tickSeconds,
              source: gua,
              target: link.to,
              amount: gain,
              kind: 'SUSTAIN',
              type: '续航纽带',
              note: '伤害转续航',
              extra: { event: 'EDGE_RUNE_TRIGGERED', edge_type: 'SUSTAIN_LINK', from_gua: gua, to_gua: link.to, payload: { gain } },
            });
          }
        });

        if (reaction) {
          const extra = damage * reaction.bonus;
          totalDamage += extra;
          reactionCounts[reaction.type] = (reactionCounts[reaction.type] || 0) + 1;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: '反应',
            target: target.name,
            amount: extra,
            kind: 'REACTION',
            type: reaction.type,
            note: reaction.name,
            extra: {
              event: 'REACTION_TRIGGERED',
              reaction_type: reaction.type,
              elements: [skillToCast.element],
              extra_effects: reaction.name,
            },
          });
        }

        // apply mark
        const markDuration = 4 + markBonus;
        target.mark = { element: skillToCast.element, expires: tick + markDuration };
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: skillToCast.name,
          target: target.name,
          amount: 0,
          kind: 'MARK',
          type: skillToCast.element,
          note: `持续${markDuration}`,
          extra: { event: 'MARK_APPLIED', element: skillToCast.element, expires_tick: tick + markDuration },
        });

        // REACT_DETONATOR window
        edgeLinks.forEach((link) => {
          if (link.rune === 'REACT_DETONATOR') {
            detonateWindows.set(link.to, { expires: tick + EDGE_RUNES.REACT_DETONATOR.window, markElement: skillToCast.element });
            pushEvent(events, {
              tick,
              time: tick * tickSeconds,
              source: gua,
              target: link.to,
              amount: 0,
              kind: 'EDGE',
              type: 'REACT_DETONATOR',
              note: '引爆窗口',
              extra: { event: 'EDGE_RUNE_TRIGGERED', edge_type: 'REACT_DETONATOR', from_gua: gua, to_gua: link.to },
            });
          }
        });
      }

      // conditional accel
      if (loop?.accelOnMark && target.mark) {
        applyCooldownReduction(skillToCast, loop.accelOnMark, '印记加速', tick, events);
      }
    }

    const dps = totalDamage / (maxTicks * tickSeconds);
    const result = {
      totals: { dps, sustain: sustainTotal, ehp: sustainTotal * 0.4, stability: 0 },
      metrics: {
        casts_per_skill: castsPerSkill,
        reaction_counts: reactionCounts,
        downtime_ticks: downtimeTicks,
        sustain_total: sustainTotal,
      },
      logs: [
        `10秒木桩：施放${Object.values(castsPerSkill).reduce((a, b) => a + b, 0)}次`,
        `反应次数：${Object.values(reactionCounts).reduce((a, b) => a + b, 0)}次`,
        `空窗：${downtimeTicks} tick`,
      ],
      events,
    };

    return result;
  }

  function simulateBoss(result, bossProfile) {
    const boss = bossProfile || BOSS_PROFILES[0];
    if (global.CircuitCore?.simulateCombat) {
      return global.CircuitCore.simulateCombat(result, boss);
    }
    return {
      win: null,
      time_to_kill: null,
      time_survived: null,
      boss: boss?.name || '木桩',
      logs: result.logs,
      events: result.events,
    };
  }

  global.BaguaSolver = {
    simulateBuild,
    solveBoard: simulateBuild,
    simulateBoss,
    SKILL_LIBRARY,
    FORM_RUNES,
    LOOP_RUNES,
    EDGE_RUNES,
    REACTIONS,
    BOSS_PROFILES,
    GUA_INFO,
  };
})(window);
