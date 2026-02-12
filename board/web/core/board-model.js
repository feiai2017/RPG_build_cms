(function () {
  const Model = {};

  const SOLVER_CATALOG = window.BaguaSolver || {};
  const SKILL_LIBRARY = SOLVER_CATALOG.SKILL_LIBRARY || {};
  const FORM_RUNES_LIB = SOLVER_CATALOG.FORM_RUNES || {};
  const LOOP_RUNES_LIB = SOLVER_CATALOG.LOOP_RUNES || {};
  const EDGE_RUNES_LIB = SOLVER_CATALOG.EDGE_RUNES || {};
  const REACTIONS = SOLVER_CATALOG.REACTIONS || {};
  const BOSS_PROFILES = SOLVER_CATALOG.BOSS_PROFILES || [];
  const GUA_TRAITS = SOLVER_CATALOG.GUA_TRAITS || {};

  const GUA_ORDER = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤'];
  const GUA_INFO = {
    乾: { element: '金', verb: '贯', symbol: '☰' },
    兑: { element: '金', verb: '回', symbol: '☱' },
    离: { element: '火', verb: '燃', symbol: '☲' },
    震: { element: '木', verb: '连', symbol: '☳' },
    巽: { element: '木', verb: '散', symbol: '☴' },
    坎: { element: '水', verb: '控', symbol: '☵' },
    艮: { element: '土', verb: '镇', symbol: '☶' },
    坤: { element: '土', verb: '护', symbol: '☷' },
  };

  const SLOT_KIND = {
    SKILL: 'skill',
    FORM: 'form',
    LOOP: 'loop',
    EDGE: 'edge',
  };

  const ITEM_CATEGORY = {
    SKILL: 'SKILL',
    FORM: 'FORM',
    LOOP: 'LOOP',
    EDGE: 'EDGE',
  };

  const SKILL_DESC = {
    skill_qian_pierce: '单体穿透',
    skill_dui_echo: '连击回荡',
    skill_li_flare: '爆发焰击',
    skill_zhen_chain: '连锁突刺',
    skill_kan_tide: '水势压制',
    skill_xun_guard: '护盾辅助',
    skill_gen_shell: '高护持',
    skill_kun_reforge: '持续守护',
  };

  const SKILLS = Object.values(SKILL_LIBRARY).map((skill) => ({
    ...skill,
    desc: SKILL_DESC[skill.id] || skill.desc || '',
  }));

  const FORM_RUNES = Object.values(FORM_RUNES_LIB).map((r) => ({
    ...r,
    desc: r.desc || r.name,
  }));

  const LOOP_RUNES = Object.values(LOOP_RUNES_LIB).map((r) => ({
    ...r,
    desc: r.desc || r.name,
  }));

  const EDGE_RUNES = Object.values(EDGE_RUNES_LIB).map((r) => ({
    ...r,
    desc: r.desc || r.name,
  }));

  const ITEMS = [
    ...SKILLS.map((s) => ({ ...s, category: ITEM_CATEGORY.SKILL })),
    ...FORM_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.FORM })),
    ...LOOP_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.LOOP })),
    ...EDGE_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.EDGE })),
  ];

  const SLOT_ACCEPTS = {
    [SLOT_KIND.SKILL]: [ITEM_CATEGORY.SKILL],
    [SLOT_KIND.FORM]: [ITEM_CATEGORY.FORM],
    [SLOT_KIND.LOOP]: [ITEM_CATEGORY.LOOP],
    [SLOT_KIND.EDGE]: [ITEM_CATEGORY.EDGE],
  };

  const TICK_SECONDS = 0.5;
  const EDGE_ENABLED_CAP = 3;
  const PER_SKILL_EDGE_CAP = 2;

  const VISUAL = {
    size: 880,
    skillR: 190,
    runeR: 140,
    edgeR: 240,
    outerLabelR: 320,
  };
  const SECTOR_ANGLE = (Math.PI * 2) / GUA_ORDER.length;
  const START_ANGLE = -Math.PI / 2;
  const CENTER_OFFSET = SECTOR_ANGLE / 2;

  function canonicalEdgeKey(a, b) {
    const ai = GUA_ORDER.indexOf(a);
    const bi = GUA_ORDER.indexOf(b);
    return ai <= bi ? `${a}|${b}` : `${b}|${a}`;
  }

  function nextGua(gua) {
    const idx = GUA_ORDER.indexOf(gua);
    return GUA_ORDER[(idx + 1) % GUA_ORDER.length];
  }

  function buildDefaultConfig() {
    const skills_by_gua = {};
    SKILLS.forEach((skill) => {
      skills_by_gua[skill.gua] = skill.id;
    });
    const private_runes = {};
    GUA_ORDER.forEach((gua) => {
      private_runes[gua] = { form: null, loop: null };
    });
    return { name: 'default', skills_by_gua, private_runes, edge_runes: {} };
  }

  function buildBoardState(preset) {
    const cfg = preset || buildDefaultConfig();
    const slots = [];
    const cx = VISUAL.size / 2;
    const cy = VISUAL.size / 2;

    GUA_ORDER.forEach((gua, idx) => {
      const theta = START_ANGLE + idx * SECTOR_ANGLE + CENTER_OFFSET;
      const info = GUA_INFO[gua];

      const skillSlot = {
        id: `skill_${gua}`,
        kind: SLOT_KIND.SKILL,
        gua,
        angle: theta,
        r: VISUAL.skillR,
        x: cx + Math.cos(theta) * VISUAL.skillR,
        y: cy + Math.sin(theta) * VISUAL.skillR,
        item_id: cfg.skills_by_gua?.[gua] || null,
        element: info.element,
      };
      slots.push(skillSlot);

      const formTheta = theta - SECTOR_ANGLE * 0.18;
      const loopTheta = theta + SECTOR_ANGLE * 0.18;
      slots.push({
        id: `form_${gua}`,
        kind: SLOT_KIND.FORM,
        gua,
        angle: formTheta,
        r: VISUAL.runeR,
        x: cx + Math.cos(formTheta) * VISUAL.runeR,
        y: cy + Math.sin(formTheta) * VISUAL.runeR,
        item_id: cfg.private_runes?.[gua]?.form || null,
        element: info.element,
      });
      slots.push({
        id: `loop_${gua}`,
        kind: SLOT_KIND.LOOP,
        gua,
        angle: loopTheta,
        r: VISUAL.runeR,
        x: cx + Math.cos(loopTheta) * VISUAL.runeR,
        y: cy + Math.sin(loopTheta) * VISUAL.runeR,
        item_id: cfg.private_runes?.[gua]?.loop || null,
        element: info.element,
      });

      const edgeGua = nextGua(gua);
      const edgeKey = canonicalEdgeKey(gua, edgeGua);
      const edgeTheta = START_ANGLE + (idx + 1) * SECTOR_ANGLE;
      slots.push({
        id: `edge_${edgeKey}`,
        kind: SLOT_KIND.EDGE,
        gua: edgeKey,
        gua_a: gua,
        gua_b: edgeGua,
        angle: edgeTheta,
        r: VISUAL.edgeR,
        x: cx + Math.cos(edgeTheta) * VISUAL.edgeR,
        y: cy + Math.sin(edgeTheta) * VISUAL.edgeR,
        item_id: cfg.edge_runes?.[edgeKey] || null,
        element: info.element,
      });
    });

    return {
      build: JSON.parse(JSON.stringify(cfg)),
      slots,
      layout: {
        size: VISUAL.size,
        center: { x: cx, y: cy },
        skillR: VISUAL.skillR,
        runeR: VISUAL.runeR,
        edgeR: VISUAL.edgeR,
        outerLabelR: VISUAL.outerLabelR,
        sectorAngle: SECTOR_ANGLE,
        startAngle: START_ANGLE,
        centerOffset: CENTER_OFFSET,
      },
    };
  }

  function getSlot(state, slotId) {
    return state?.slots?.find((s) => s.id === slotId) || null;
  }

  function getItemById(itemId) {
    if (!itemId) return null;
    return ITEMS.find((it) => it.id === itemId) || null;
  }

  function applyItem(state, slotId, itemId) {
    const slot = getSlot(state, slotId);
    const item = getItemById(itemId);
    if (!slot || !item) return null;
    if (!SLOT_ACCEPTS[slot.kind]?.includes(item.category)) return null;
    slot.item_id = item.id;
    const gua = slot.gua;
    if (slot.kind === SLOT_KIND.SKILL) {
      state.build.skills_by_gua[gua] = item.id;
    } else if (slot.kind === SLOT_KIND.FORM) {
      state.build.private_runes[gua] = state.build.private_runes[gua] || { form: null, loop: null };
      state.build.private_runes[gua].form = item.id;
    } else if (slot.kind === SLOT_KIND.LOOP) {
      state.build.private_runes[gua] = state.build.private_runes[gua] || { form: null, loop: null };
      state.build.private_runes[gua].loop = item.id;
    } else if (slot.kind === SLOT_KIND.EDGE) {
      state.build.edge_runes[slot.gua] = item.id;
    }
    return slot;
  }

  function clearSlot(state, slotId) {
    const slot = getSlot(state, slotId);
    if (!slot) return null;
    if (slot.kind === SLOT_KIND.SKILL) {
      state.build.skills_by_gua[slot.gua] = null;
    } else if (slot.kind === SLOT_KIND.FORM) {
      state.build.private_runes[slot.gua].form = null;
    } else if (slot.kind === SLOT_KIND.LOOP) {
      state.build.private_runes[slot.gua].loop = null;
    } else if (slot.kind === SLOT_KIND.EDGE) {
      delete state.build.edge_runes[slot.gua];
    }
    slot.item_id = null;
    return slot;
  }

  function validateBuild(state) {
    const issuesOut = [];
    const edgeRunes = state?.build?.edge_runes || {};
    const enabledEdges = Object.entries(edgeRunes).filter(([, v]) => v);
    if (enabledEdges.length > EDGE_ENABLED_CAP) {
      issuesOut.push({ id: 'edge_cap', message: `联结槽启用超过上限（${enabledEdges.length}/${EDGE_ENABLED_CAP}）` });
    }
    const perSkillEdges = {};
    enabledEdges.forEach(([key]) => {
      const [a, b] = key.split('|');
      perSkillEdges[a] = (perSkillEdges[a] || 0) + 1;
      perSkillEdges[b] = (perSkillEdges[b] || 0) + 1;
      if (!state.build.skills_by_gua?.[a] || !state.build.skills_by_gua?.[b]) {
        issuesOut.push({ id: `edge_skill_${key}`, message: `联结 ${key} 需要两侧技能` });
      }
    });
    Object.entries(perSkillEdges).forEach(([gua, count]) => {
      if (count > PER_SKILL_EDGE_CAP) {
        issuesOut.push({ id: `skill_edge_${gua}`, message: `${gua} 参与联结超过上限（${count}/${PER_SKILL_EDGE_CAP}）` });
      }
    });
    return issuesOut;
  }

  function computeRelatedIds(state, targetId) {
    if (!targetId) return null;
    const slot = getSlot(state, targetId);
    if (!slot) return null;
    const related = new Set([slot.id]);
    if (slot.kind === SLOT_KIND.SKILL) {
      const gua = slot.gua;
      const form = getSlot(state, `form_${gua}`);
      const loop = getSlot(state, `loop_${gua}`);
      if (form) related.add(form.id);
      if (loop) related.add(loop.id);
      const prev = GUA_ORDER[(GUA_ORDER.indexOf(gua) - 1 + GUA_ORDER.length) % GUA_ORDER.length];
      const next = nextGua(gua);
      const edgePrev = getSlot(state, `edge_${canonicalEdgeKey(prev, gua)}`);
      const edgeNext = getSlot(state, `edge_${canonicalEdgeKey(gua, next)}`);
      if (edgePrev && edgePrev.item_id) related.add(edgePrev.id);
      if (edgeNext && edgeNext.item_id) related.add(edgeNext.id);
    }
    if (slot.kind === SLOT_KIND.EDGE) {
      const a = slot.gua_a;
      const b = slot.gua_b;
      const skillA = getSlot(state, `skill_${a}`);
      const skillB = getSlot(state, `skill_${b}`);
      const formA = getSlot(state, `form_${a}`);
      const loopA = getSlot(state, `loop_${a}`);
      const formB = getSlot(state, `form_${b}`);
      const loopB = getSlot(state, `loop_${b}`);
      [skillA, skillB, formA, loopA, formB, loopB].forEach((s) => s && related.add(s.id));
    }
    return related;
  }

  Model.GUA_ORDER = GUA_ORDER;
  Model.GUA_INFO = GUA_INFO;
  Model.SLOT_KIND = SLOT_KIND;
  Model.ITEM_CATEGORY = ITEM_CATEGORY;
  Model.SLOT_ACCEPTS = SLOT_ACCEPTS;
  Model.TICK_SECONDS = TICK_SECONDS;
  Model.EDGE_ENABLED_CAP = EDGE_ENABLED_CAP;
  Model.PER_SKILL_EDGE_CAP = PER_SKILL_EDGE_CAP;
  Model.VISUAL = VISUAL;
  Model.SECTOR_ANGLE = SECTOR_ANGLE;
  Model.START_ANGLE = START_ANGLE;
  Model.CENTER_OFFSET = CENTER_OFFSET;
  Model.SKILL_LIBRARY = SKILL_LIBRARY;
  Model.FORM_RUNES_LIB = FORM_RUNES_LIB;
  Model.LOOP_RUNES_LIB = LOOP_RUNES_LIB;
  Model.EDGE_RUNES_LIB = EDGE_RUNES_LIB;
  Model.REACTIONS = REACTIONS;
  Model.BOSS_PROFILES = BOSS_PROFILES;
  Model.GUA_TRAITS = GUA_TRAITS;
  Model.SKILLS = SKILLS;
  Model.FORM_RUNES = FORM_RUNES;
  Model.LOOP_RUNES = LOOP_RUNES;
  Model.EDGE_RUNES = EDGE_RUNES;
  Model.ITEMS = ITEMS;
  Model.canonicalEdgeKey = canonicalEdgeKey;
  Model.nextGua = nextGua;
  Model.buildDefaultConfig = buildDefaultConfig;
  Model.buildBoardState = buildBoardState;
  Model.getSlot = getSlot;
  Model.getItemById = getItemById;
  Model.applyItem = applyItem;
  Model.clearSlot = clearSlot;
  Model.validateBuild = validateBuild;
  Model.computeRelatedIds = computeRelatedIds;

  Model.simulateBuild = function simulateBuild(state, options) {
    if (!window.BaguaSolver?.simulateBuild) return null;
    const maxTicks = options?.maxTicks ?? 20;
    const tickSeconds = options?.tickSeconds ?? TICK_SECONDS;
    const targetName = options?.targetName;
    const targetId = options?.targetId;
    const target = options?.target;
    const payload = { ...(options || {}), maxTicks, tickSeconds, targetName, targetId, target };
    return window.BaguaSolver.simulateBuild(state.build, payload);
  };

  Model.simulateBoss = function simulateBoss(result, bossProfile) {
    if (!window.BaguaSolver?.simulateBoss) return null;
    return window.BaguaSolver.simulateBoss(result, bossProfile);
  };

  window.TiandaoModel = Model;
})();
