(function (global) {
  let GUA_ORDER = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
  let GUA_INFO = {
    '乾': { element: '金', verb: '贯' },
    '兑': { element: '金', verb: '回' },
    '离': { element: '火', verb: '燃' },
    '震': { element: '木', verb: '连' },
    '巽': { element: '木', verb: '散' },
    '坎': { element: '水', verb: '控' },
    '艮': { element: '土', verb: '镇' },
    '坤': { element: '土', verb: '护' },
  };

  let SKILL_LIBRARY = {};

  function resolveSkillLibrary() {
    return global.BD_SKILLS || SKILL_LIBRARY;
  }

  function setSkillLibrary(library) {
    SKILL_LIBRARY = library || {};
    if (global.BaguaSolver) {
      global.BaguaSolver.SKILL_LIBRARY = SKILL_LIBRARY;
    }
    return SKILL_LIBRARY;
  }

  function setRuneLibrary(runes) {
    FORM_RUNES = runes?.form_runes || {};
    LOOP_RUNES = runes?.loop_runes || {};
    EDGE_RUNES = runes?.edge_runes || {};
    if (global.BaguaSolver) {
      global.BaguaSolver.FORM_RUNES = FORM_RUNES;
      global.BaguaSolver.LOOP_RUNES = LOOP_RUNES;
      global.BaguaSolver.EDGE_RUNES = EDGE_RUNES;
    }
    return { FORM_RUNES, LOOP_RUNES, EDGE_RUNES };
  }

  function setReactions(reactions) {
    REACTIONS = reactions || {};
    if (global.BaguaSolver) {
      global.BaguaSolver.REACTIONS = REACTIONS;
    }
    return REACTIONS;
  }

  function setGuaTraits(traits) {
    GUA_TRAITS = traits || {};
    if (global.BaguaSolver) {
      global.BaguaSolver.GUA_TRAITS = GUA_TRAITS;
    }
    return GUA_TRAITS;
  }

  function setBossProfiles(bosses) {
    BOSS_PROFILES = Array.isArray(bosses) ? bosses : [];
    if (global.BaguaSolver) {
      global.BaguaSolver.BOSS_PROFILES = BOSS_PROFILES;
    }
    return BOSS_PROFILES;
  }

  function setGuaConfig(config) {
    if (Array.isArray(config?.gua_order) && config.gua_order.length) {
      GUA_ORDER = config.gua_order.slice();
    }
    if (config?.gua_info) {
      GUA_INFO = Object.assign({}, config.gua_info);
    }
    if (global.BaguaSolver) {
      global.BaguaSolver.GUA_ORDER = GUA_ORDER;
      global.BaguaSolver.GUA_INFO = GUA_INFO;
    }
    return { GUA_ORDER, GUA_INFO };
  }

  let FORM_RUNES = {};
  let LOOP_RUNES = {};
  let EDGE_RUNES = {};
  let REACTIONS = {};

  let BOSS_PROFILES = [];

  let GUA_TRAITS = {};

  let DEFAULT_MECHANISM_FLAGS = {
    lifesteal_loop_enabled: true,
    overheal_to_shield_enabled: true,
    dot_refresh_enabled: true,
    dr_stacking_enabled: true,
  };

  function toNumber(value, fallback) {
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
  }

  function resolveMechanismFlags(flags) {
    return { ...DEFAULT_MECHANISM_FLAGS, ...(flags || {}) };
  }

  function setMechanismFlags(flags) {
    DEFAULT_MECHANISM_FLAGS = { ...DEFAULT_MECHANISM_FLAGS, ...(flags || {}) };
    if (global.BaguaSolver) {
      global.BaguaSolver.DEFAULT_MECHANISM_FLAGS = DEFAULT_MECHANISM_FLAGS;
    }
    return DEFAULT_MECHANISM_FLAGS;
  }

  function makeSeededRng(seed) {
    let state = (seed >>> 0) || 1;
    return function rng() {
      state = (state * 1664525 + 1013904223) >>> 0;
      return state / 0x100000000;
    };
  }

  function canonicalElementPair(a, b) {
    return [a, b].sort().join('|');
  }

  function pushEvent(events, evt) {
    events.push(evt);
  }

  function buildSkillState(skillId, formRune, loopRune, skillLibrary) {
    const base = skillLibrary?.[skillId];
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

  function normalizeDotConfig(dot) {
    if (!dot) return null;
    const tickDamage = toNumber(dot.tick_damage, null);
    if (!Number.isFinite(tickDamage)) return null;
    return {
      tick_damage: tickDamage,
      duration: Math.max(1, toNumber(dot.duration, 1)),
      tick_interval: Math.max(1, toNumber(dot.tick_interval, 1)),
      max_stacks: Math.max(1, toNumber(dot.max_stacks, 1)),
      refresh_mode: dot.refresh_mode || 'reset',
      snapshot: dot.snapshot === true,
    };
  }

  function normalizeFieldConfig(reaction) {
    if (!reaction) return null;
    if (reaction.type !== 'FIELD' && !reaction.field) return null;
    const field = reaction.field || {};
    const dot = field.dot || field;
    const tickDamage = toNumber(dot.tick_damage, null);
    if (!Number.isFinite(tickDamage)) return null;
    return {
      tick_damage: tickDamage,
      duration: Math.max(1, toNumber(dot.duration ?? field.duration, 1)),
      tick_interval: Math.max(1, toNumber(dot.tick_interval ?? field.tick_interval, 1)),
      amp_dot: toNumber(field.amp_dot, 0),
      amp_reaction: toNumber(field.amp_reaction, 0),
    };
  }

  function simulateBuild(build, options = {}) {
    const tickSeconds = options.tickSeconds || 0.5;
    const maxTicks = options.maxTicks || 20;
    const nerfProfile = options.nerfProfile || options.nerf_profile || null;
    const damageMul = toNumber(options.damageMul ?? options.damage_mul ?? nerfProfile?.damage_mul, 1);
    const healMul = toNumber(options.healMul ?? options.heal_mul ?? nerfProfile?.heal_mul, 1);
    const shieldMul = toNumber(options.shieldMul ?? options.shield_mul ?? nerfProfile?.shield_mul, 1);
    const mechanismFlags = resolveMechanismFlags(options.mechanismFlags || options.mechanism_flags);
    const dotRefreshEnabled = mechanismFlags.dot_refresh_enabled !== false;
    const lifestealEnabled = mechanismFlags.lifesteal_loop_enabled !== false;
    const overhealToShieldEnabled = mechanismFlags.overheal_to_shield_enabled !== false;
    const drStackingEnabled = mechanismFlags.dr_stacking_enabled !== false;
    const seedValue = options.seed;
    const seed = Number.isFinite(Number(seedValue)) ? Number(seedValue) : null;
    const rng = seed == null ? null : makeSeededRng(seed);
    const baseEhp = toNumber(options.baseEhp ?? options.base_ehp, 100);
    const guaOrder = GUA_ORDER;
    const skillsByGua = build.skills_by_gua || {};
    const privateRunes = build.private_runes || {};
    const edgeRunes = build.edge_runes || {};
    const skillLibrary = resolveSkillLibrary();

    const skillStates = new Map();
    guaOrder.forEach((gua) => {
      const skillId = skillsByGua[gua];
      if (!skillId) return;
      const runes = privateRunes[gua] || {};
      const state = buildSkillState(skillId, runes.form, runes.loop, skillLibrary);
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

    skillStates.forEach((skill) => {
      if (normalizeDotConfig(skill.dot)) {
        dotSkillList.push(`${skill.name}(${skill.id})`);
      }
    });

    const events = [];
    const castsPerSkill = {};
    const reactionCounts = {};
    let downtimeTicks = 0;
    let sustainRaw = 0;
    let totalDamage = 0;
    let hitDamage = 0;
    let dotDamage = 0;
    let fieldDamage = 0;
    let reactionBonusDamage = 0;
    let dotActiveTicks = 0;
    let dotStackSum = 0;
    let fieldActiveTicks = 0;

    const targetName = options.targetName || options.target?.name || '木桩';
    const targetId = options.targetId || options.target?.id || 'dummy';
    const target = { id: targetId, name: targetName, mark: null, activeDots: new Map(), activeFields: new Map() };
    const targetLabel = target.name || '木桩';
    const detonateWindows = new Map();
    const immediateQueue = [];
    const dotSkillList = [];

    function resolveActiveMark(gua, tick) {
      if (target.mark && Number.isFinite(target.mark.expires) && tick >= target.mark.expires) {
        target.mark = null;
      }
      detonateWindows.forEach((window, key) => {
        if (tick > window.expires) detonateWindows.delete(key);
      });
      if (target.mark) return { mark: target.mark, virtual: false };
      if (gua) {
        const window = detonateWindows.get(gua);
        if (window && tick <= window.expires) {
          return { mark: { element: window.markElement, stacks: 0, dot_amp_per_stack: 0 }, virtual: true };
        }
      }
      return { mark: null, virtual: false };
    }

    function applyMark(element, tick, duration, markConfig, sourceName) {
      const maxStacks = Math.max(1, toNumber(markConfig?.max_stacks, 1));
      const dotAmp = toNumber(markConfig?.dot_amp_per_stack, 0);
      let stacks = 1;
      if (target.mark && target.mark.element === element && dotRefreshEnabled) {
        stacks = Math.min(maxStacks, (target.mark.stacks || 1) + 1);
      }
      target.mark = {
        element,
        expires: tick + duration,
        stacks,
        dot_amp_per_stack: dotAmp,
        max_stacks: maxStacks,
      };
      pushEvent(events, {
        tick,
        time: tick * tickSeconds,
        source: sourceName || '系统',
        target: target.name,
        amount: 0,
        kind: 'MARK',
        type: element,
        note: `持续${duration}`,
        extra: {
          event: 'MARK_APPLIED',
          element,
          expires_tick: tick + duration,
          stacks,
          max_stacks: maxStacks,
          dot_amp_per_stack: dotAmp,
        },
      });
    }

    function applyDot(skill, tick) {
      const dotCfg = normalizeDotConfig(skill.dot);
      if (!dotCfg) return;
      const key = skill.id;
      const existing = target.activeDots.get(key);
      if (existing) {
        if (!dotRefreshEnabled) return;
        if (dotCfg.refresh_mode === 'stack') {
          existing.stacks = Math.min(dotCfg.max_stacks, (existing.stacks || 1) + 1);
          existing.expires = tick + dotCfg.duration;
        } else if (dotCfg.refresh_mode === 'extend') {
          const cap = tick + dotCfg.duration * dotCfg.max_stacks;
          existing.expires = Math.min(cap, existing.expires + dotCfg.duration);
        } else {
          existing.expires = tick + dotCfg.duration;
          existing.stacks = Math.min(dotCfg.max_stacks, existing.stacks || 1);
        }
        existing.tick_damage = dotCfg.tick_damage;
        existing.tick_interval = dotCfg.tick_interval;
        existing.refresh_mode = dotCfg.refresh_mode;
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: skill.name,
          target: target.name,
          amount: 0,
          kind: 'DOT',
          type: skill.element,
          note: 'DOT刷新',
          extra: {
            event: 'DOT_REFRESH',
            skill_id: skill.id,
            stacks: existing.stacks,
            expires_tick: existing.expires,
            refresh_mode: dotCfg.refresh_mode,
          },
        });
        return;
      }

      target.activeDots.set(key, {
        skill_id: skill.id,
        name: skill.name,
        element: skill.element,
        gua: skill.gua,
        tick_damage: dotCfg.tick_damage,
        tick_interval: dotCfg.tick_interval,
        refresh_mode: dotCfg.refresh_mode,
        stacks: 1,
        expires: tick + dotCfg.duration,
        next_tick_at: tick + dotCfg.tick_interval,
      });
      pushEvent(events, {
        tick,
        time: tick * tickSeconds,
        source: skill.name,
        target: target.name,
        amount: 0,
        kind: 'DOT',
        type: skill.element,
        note: 'DOT施加',
        extra: {
          event: 'DOT_APPLIED',
          skill_id: skill.id,
          stacks: 1,
          duration: dotCfg.duration,
          tick_interval: dotCfg.tick_interval,
          refresh_mode: dotCfg.refresh_mode,
        },
      });
    }

    function applyField(reaction, tick, sourceElement) {
      const fieldCfg = normalizeFieldConfig(reaction);
      if (!fieldCfg) return;
      const key = reaction.name || reaction.type || 'FIELD';
      const existing = target.activeFields.get(key);
      if (existing) {
        existing.expires = Math.max(existing.expires, tick + fieldCfg.duration);
        existing.tick_damage = fieldCfg.tick_damage;
        existing.tick_interval = fieldCfg.tick_interval;
        existing.amp_dot = fieldCfg.amp_dot;
      } else {
        target.activeFields.set(key, {
          id: key,
          name: reaction.name || key,
          element: sourceElement,
          tick_damage: fieldCfg.tick_damage,
          tick_interval: fieldCfg.tick_interval,
          amp_dot: fieldCfg.amp_dot,
          expires: tick + fieldCfg.duration,
          next_tick_at: tick + fieldCfg.tick_interval,
        });
      }
      pushEvent(events, {
        tick,
        time: tick * tickSeconds,
        source: '反应场',
        target: target.name,
        amount: 0,
        kind: 'FIELD',
        type: key,
        note: reaction.name || key,
        extra: {
          event: 'FIELD_APPLIED',
          reaction_type: reaction.type,
          duration: fieldCfg.duration,
          tick_interval: fieldCfg.tick_interval,
          amp_dot: fieldCfg.amp_dot,
        },
      });
    }

    function sumFieldAmpDot(tick) {
      let amp = 0;
      target.activeFields.forEach((field) => {
        if (field?.amp_dot && (field.expires == null || tick < field.expires)) amp += field.amp_dot;
      });
      return amp;
    }

    function handleReaction(element, damage, tick, trait, gua) {
      if (!dotRefreshEnabled) return;
      const markState = resolveActiveMark(gua, tick);
      const mark = markState.mark;
      if (!mark || mark.element === element) return;
      const key = canonicalElementPair(mark.element, element);
      const reaction = REACTIONS[key] || null;
      if (!reaction) return;
      const reactionType = reaction.type === 'FIELD' ? (reaction.name || 'FIELD') : (reaction.type || 'BONUS');
      reactionCounts[reactionType] = (reactionCounts[reactionType] || 0) + 1;
      if (markState.virtual && gua) {
        detonateWindows.delete(gua);
      }
      if (!trait?.noConsumeMark && !markState.virtual) target.mark = null;

      const isField = reaction.type === 'FIELD' || reaction.field;
      if (isField) {
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: '反应',
          target: target.name,
          amount: 0,
          kind: 'REACTION',
          type: reactionType,
          note: reaction.name,
          extra: {
            event: 'REACTION_TRIGGERED',
            reaction_type: reactionType,
            elements: [element],
            extra_effects: reaction.name,
            field: true,
          },
        });
        applyField(reaction, tick, element);
      } else {
        const extra = damage * reaction.bonus;
        totalDamage += extra;
        reactionBonusDamage += extra;
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: '反应',
          target: target.name,
          amount: extra,
          kind: 'REACTION',
          type: reactionType,
          note: reaction.name,
          extra: {
            event: 'REACTION_TRIGGERED',
            reaction_type: reactionType,
            elements: [element],
            extra_effects: reaction.name,
          },
        });
      }
      if (trait?.reactionCooldown) {
        const skill = skillStates.get(gua) || null;
        if (skill) {
          applyCooldownReduction(skill, trait.reactionCooldown, `卦位${gua}连动`, tick, events);
        }
      }
    }


    for (let tick = 0; tick < maxTicks; tick += 1) {
      // cooldown tick
      skillStates.forEach((skill) => {
        if (skill.cdLeft > 0) skill.cdLeft -= 1;
      });

      // process delayed queue
      immediateQueue.forEach((item) => { item.delay -= 1; });

      if (target.mark && Number.isFinite(target.mark.expires) && tick >= target.mark.expires) {
        target.mark = null;
      }

      let dotActiveThisTick = false;
      let dotStacksThisTick = 0;
      const fieldAmp = sumFieldAmpDot(tick);
      target.activeDots.forEach((dot, key) => {
        if (tick >= dot.expires) {
          target.activeDots.delete(key);
          return;
        }
        dotActiveThisTick = true;
        dotStacksThisTick += dot.stacks || 1;
        while (tick >= dot.next_tick_at && tick < dot.expires) {
          const markAmp = target.mark ? (target.mark.stacks || 1) * (target.mark.dot_amp_per_stack || 0) : 0;
          const amp = 1 + markAmp + fieldAmp;
          const baseTick = dot.tick_damage * (dot.stacks || 1);
          const dmg = baseTick * amp * damageMul;
          totalDamage += dmg;
          dotDamage += dmg;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: dot.name || 'DOT',
            target: target.name,
            amount: dmg,
            kind: 'DOT',
            type: dot.element,
            note: 'DOT跳伤',
            extra: {
              event: 'DOT_TICK',
              skill_id: dot.skill_id,
              stacks: dot.stacks || 1,
              mark_amp: markAmp,
              field_amp: fieldAmp,
            },
          });
          const dotTrait = dot.gua ? GUA_TRAITS[dot.gua] : null;
          handleReaction(dot.element, dmg, tick, dotTrait, dot.gua);
          dot.next_tick_at += dot.tick_interval;
        }
      });
      if (dotActiveThisTick) {
        dotActiveTicks += 1;
        dotStackSum += dotStacksThisTick;
      }

      let fieldActiveThisTick = false;
      target.activeFields.forEach((field, key) => {
        if (tick >= field.expires) {
          target.activeFields.delete(key);
          return;
        }
        fieldActiveThisTick = true;
        while (tick >= field.next_tick_at && tick < field.expires) {
          const dmg = field.tick_damage * damageMul;
          totalDamage += dmg;
          fieldDamage += dmg;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: field.name || '反应场',
            target: target.name,
            amount: dmg,
            kind: 'FIELD',
            type: field.id,
            note: '反应场跳伤',
            extra: {
              event: 'FIELD_TICK',
              field_id: field.id,
            },
          });
          field.next_tick_at += field.tick_interval;
        }
      });
      if (fieldActiveThisTick) fieldActiveTicks += 1;

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
      const isTraitEcho = castItem?.tag === 'ECHO';
      const gua = skillToCast.gua;
      const trait = GUA_TRAITS[gua];
      const form = skillToCast.formRune ? FORM_RUNES[skillToCast.formRune] : null;
      const loop = skillToCast.loopRune ? LOOP_RUNES[skillToCast.loopRune] : null;
      const hits = form?.hits || 1;
      const baseMul = form?.mult || 1;
      const markConfig = form?.mark || null;
      const markBonus = dotRefreshEnabled ? (form?.markBonus || 0) + (trait?.markBonus || 0) : 0;
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

      if (trait?.echoDelay && !isRelay && !isTraitEcho) {
        immediateQueue.push({ gua, delay: trait.echoDelay, relay: true, tag: 'ECHO' });
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

      let hadMarkBeforeAny = false;
      for (let h = 0; h < hits; h += 1) {
        if (skillToCast.kind === 'support') {
          const sustainBase = (skillToCast.sustain || 4) * totalMul;
          const sustain = sustainBase * shieldMul;
          sustainRaw += sustain;
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

        const baseDamage = skillToCast.baseDamage * totalMul;
        const damage = baseDamage * damageMul;
        totalDamage += damage;
        hitDamage += damage;

        const hadMarkBefore = !!target.mark;
        if (hadMarkBefore) hadMarkBeforeAny = true;

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

        if (h === 0) {
          applyDot(skillToCast, tick);
        }

        handleReaction(skillToCast.element, damage, tick, trait, gua);

        if (trait?.sustainFromDamageRatio && skillToCast.kind === 'output') {
          const gain = damage * trait.sustainFromDamageRatio * healMul;
          sustainRaw += gain;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: skillToCast.name,
            target: '玩家',
            amount: gain,
            kind: 'SUSTAIN',
            type: '护持',
            note: `卦位${gua}护持`,
            extra: { event: 'SUSTAIN_GAINED', amount: gain, kind: 'shield', source: skillToCast.id },
          });
        }

        if (loop?.sustainOnHit && lifestealEnabled) {
          const sustain = loop.sustainOnHit * healMul;
          sustainRaw += sustain;
          pushEvent(events, {
            tick,
            time: tick * tickSeconds,
            source: skillToCast.name,
            target: '玩家',
            amount: sustain,
            kind: 'SUSTAIN',
            type: '回能',
            note: loop.name,
            extra: { event: 'SUSTAIN_GAINED', amount: sustain, kind: 'energy', source: skillToCast.id },
          });
        }

        if (loop?.sustainOnCrit && lifestealEnabled) {
          const crit = rng ? rng() < 0.2 : ((tick + h + skillToCast.baseCd) % 5) === 0;
          if (crit) {
            const sustain = loop.sustainOnCrit * healMul;
            sustainRaw += sustain;
            pushEvent(events, {
              tick,
              time: tick * tickSeconds,
              source: skillToCast.name,
              target: '玩家',
              amount: sustain,
              kind: 'SUSTAIN',
              type: '暴击回能',
              note: loop.name,
              extra: { event: 'SUSTAIN_GAINED', amount: sustain, kind: 'energy', source: skillToCast.id, crit: true },
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
            const gain = damage * EDGE_RUNES.SUSTAIN_LINK.ratio * healMul;
            sustainRaw += gain;
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

        if (dotRefreshEnabled) {
          const markDuration = 4 + markBonus;
          applyMark(skillToCast.element, tick, markDuration, markConfig, skillToCast.name);

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
      }

      // conditional accel
      if (dotRefreshEnabled && loop?.accelOnMark && target.mark) {
        applyCooldownReduction(skillToCast, loop.accelOnMark, '印记加速', tick, events);
      }
      if (dotRefreshEnabled && trait?.accelOnMark && hadMarkBeforeAny) {
        applyCooldownReduction(skillToCast, trait.accelOnMark, `卦位${gua}潮汐`, tick, events);
      }

      if (trait?.damageToSustainRatio && skillToCast.kind === 'output') {
        const gain = totalMul * (skillToCast.baseDamage || 0) * trait.damageToSustainRatio * healMul;
        sustainRaw += gain;
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: skillToCast.name,
          target: '玩家',
          amount: gain,
          kind: 'SUSTAIN',
          type: '续航',
          note: `卦位${gua}壁垒`,
          extra: { event: 'SUSTAIN_GAINED', amount: gain, kind: 'energy', source: skillToCast.id },
        });
      }

      if (trait?.flatSustain) {
        const gain = trait.flatSustain * healMul;
        sustainRaw += gain;
        pushEvent(events, {
          tick,
          time: tick * tickSeconds,
          source: '玩家',
          target: '玩家',
          amount: gain,
          kind: 'SUSTAIN',
          type: '回元',
          note: `卦位${gua}回元`,
          extra: { event: 'SUSTAIN_GAINED', amount: gain, kind: 'energy', source: skillToCast.id },
        });
      }
    }

    const durationSeconds = maxTicks * tickSeconds;
    const dps = durationSeconds > 0 ? totalDamage / durationSeconds : 0;
    const sustainEffective = drStackingEnabled ? sustainRaw : 0;
    const ehp = overhealToShieldEnabled ? sustainRaw * 0.4 : 0;
    const dotUptimeRatio = maxTicks > 0 ? dotActiveTicks / maxTicks : 0;
    const dotAvgStacks = dotActiveTicks > 0 ? dotStackSum / dotActiveTicks : 0;
    const fieldUptimeRatio = maxTicks > 0 ? fieldActiveTicks / maxTicks : 0;
    const totalReactions = Object.values(reactionCounts).reduce((a, b) => a + b, 0);
    const reactionsPer10s = durationSeconds > 0 ? (totalReactions / durationSeconds) * 10 : 0;
    const result = {
      totals: {
        dps,
        sustain: sustainEffective,
        sustain_raw: sustainRaw,
        ehp,
        base_ehp: baseEhp,
        stability: 0,
        mechanism_flags: mechanismFlags,
        damage_breakdown: {
          hit: Number(hitDamage.toFixed(3)),
          dot: Number(dotDamage.toFixed(3)),
          field: Number(fieldDamage.toFixed(3)),
          reaction_bonus: Number(reactionBonusDamage.toFixed(3)),
        },
      },
      metrics: {
        casts_per_skill: castsPerSkill,
        reaction_counts: reactionCounts,
        downtime_ticks: downtimeTicks,
        sustain_total: sustainRaw,
        dot_uptime_ratio: Number(dotUptimeRatio.toFixed(3)),
        dot_avg_stacks: Number(dotAvgStacks.toFixed(3)),
        field_uptime_ratio: Number(fieldUptimeRatio.toFixed(3)),
        reactions_per_10s: Number(reactionsPer10s.toFixed(3)),
        damage_breakdown: {
          hit: Number(hitDamage.toFixed(3)),
          dot: Number(dotDamage.toFixed(3)),
          field: Number(fieldDamage.toFixed(3)),
          reaction_bonus: Number(reactionBonusDamage.toFixed(3)),
        },
      },
      logs: [
        dotSkillList.length ? `DOT技能：${dotSkillList.join('、')}` : 'DOT技能：无',
        `${(maxTicks * tickSeconds).toFixed(0)}秒${targetLabel}：施放${Object.values(castsPerSkill).reduce((a, b) => a + b, 0)}次`,
        `反应次数：${totalReactions}次`,
        `DOT覆盖率：${(dotUptimeRatio * 100).toFixed(1)}% | 平均叠层：${dotAvgStacks.toFixed(2)}`,
        `反应场覆盖率：${(fieldUptimeRatio * 100).toFixed(1)}% | 10秒反应：${reactionsPer10s.toFixed(2)}`,
        `空窗：${downtimeTicks} tick`,
      ],
      events,
    };

    return result;
  }

  function simulateBoss(result, bossProfile, options = {}) {
    const boss = bossProfile || BOSS_PROFILES[0] || { name: 'Boss', hp: 1200, dps: 0, spike: 0, spikeInterval: 10 };
    if (global.CircuitCore?.simulateCombat) {
      return global.CircuitCore.simulateCombat(result, boss, options);
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
    SKILL_LIBRARY: resolveSkillLibrary(),
    setSkillLibrary,
    setRuneLibrary,
    setReactions,
    setGuaTraits,
    setBossProfiles,
    setMechanismFlags,
    setGuaConfig,
    FORM_RUNES,
    LOOP_RUNES,
    EDGE_RUNES,
    REACTIONS,
    BOSS_PROFILES,
    GUA_INFO,
    GUA_TRAITS,
  };
})(window);
