(function () {
  const Model = {};

  const SOLVER_CATALOG = window.BaguaSolver || {};
  let SKILL_LIBRARY = SOLVER_CATALOG.SKILL_LIBRARY || {};
  let FORM_RUNES_LIB = SOLVER_CATALOG.FORM_RUNES || {};
  let LOOP_RUNES_LIB = SOLVER_CATALOG.LOOP_RUNES || {};
  let EDGE_RUNES_LIB = SOLVER_CATALOG.EDGE_RUNES || {};
  let REACTIONS = SOLVER_CATALOG.REACTIONS || {};
  let BOSS_PROFILES = SOLVER_CATALOG.BOSS_PROFILES || [];
  let GUA_TRAITS = SOLVER_CATALOG.GUA_TRAITS || {};

  const DEFAULT_BOARD_CONFIG = {
    gua_order: ['\u4e7e', '\u5151', '\u79bb', '\u9707', '\u5dfd', '\u574e', '\u826e', '\u5764'],
    gua_info: {
      '\u4e7e': { element: '\u91d1', verb: '\u8d2f', symbol: '\u2630' },
      '\u5151': { element: '\u91d1', verb: '\u56de', symbol: '\u2631' },
      '\u79bb': { element: '\u706b', verb: '\u71c3', symbol: '\u2632' },
      '\u9707': { element: '\u6728', verb: '\u8fde', symbol: '\u2633' },
      '\u5dfd': { element: '\u6728', verb: '\u6563', symbol: '\u2634' },
      '\u574e': { element: '\u6c34', verb: '\u63a7', symbol: '\u2635' },
      '\u826e': { element: '\u571f', verb: '\u9547', symbol: '\u2636' },
      '\u5764': { element: '\u571f', verb: '\u62a4', symbol: '\u2637' },
    },
    tick_seconds: 0.5,
    edge_limits: { total: 3, per_skill: 2 },
    visual: { size: 880, skillR: 190, runeR: 140, edgeR: 240, outerLabelR: 320 },
    start_angle: -1.5707963267948966,
    center_offset: null,
  };

  let GUA_ORDER = DEFAULT_BOARD_CONFIG.gua_order.slice();
  let GUA_INFO = Object.assign({}, DEFAULT_BOARD_CONFIG.gua_info);
  let TICK_SECONDS = DEFAULT_BOARD_CONFIG.tick_seconds;
  let EDGE_ENABLED_CAP = DEFAULT_BOARD_CONFIG.edge_limits.total;
  let PER_SKILL_EDGE_CAP = DEFAULT_BOARD_CONFIG.edge_limits.per_skill;
  let VISUAL = Object.assign({}, DEFAULT_BOARD_CONFIG.visual);
  let SECTOR_ANGLE = (Math.PI * 2) / GUA_ORDER.length;
  let START_ANGLE = DEFAULT_BOARD_CONFIG.start_angle ?? -Math.PI / 2;
  let CENTER_OFFSET = DEFAULT_BOARD_CONFIG.center_offset ?? SECTOR_ANGLE / 2;

  function applyBoardConfig(config) {
    const cfg = Object.assign({}, DEFAULT_BOARD_CONFIG, config || {});
    GUA_ORDER = Array.isArray(cfg.gua_order) && cfg.gua_order.length ? cfg.gua_order.slice() : DEFAULT_BOARD_CONFIG.gua_order.slice();
    GUA_INFO = Object.assign({}, DEFAULT_BOARD_CONFIG.gua_info, cfg.gua_info || {});
    TICK_SECONDS = Number.isFinite(cfg.tick_seconds) ? cfg.tick_seconds : DEFAULT_BOARD_CONFIG.tick_seconds;
    EDGE_ENABLED_CAP = cfg.edge_limits?.total ?? DEFAULT_BOARD_CONFIG.edge_limits.total;
    PER_SKILL_EDGE_CAP = cfg.edge_limits?.per_skill ?? DEFAULT_BOARD_CONFIG.edge_limits.per_skill;
    VISUAL = Object.assign({}, DEFAULT_BOARD_CONFIG.visual, cfg.visual || {});
    SECTOR_ANGLE = (Math.PI * 2) / GUA_ORDER.length;
    START_ANGLE = Number.isFinite(cfg.start_angle) ? cfg.start_angle : DEFAULT_BOARD_CONFIG.start_angle;
    CENTER_OFFSET = Number.isFinite(cfg.center_offset) ? cfg.center_offset : SECTOR_ANGLE / 2;

    Model.GUA_ORDER = GUA_ORDER;
    Model.GUA_INFO = GUA_INFO;
    Model.TICK_SECONDS = TICK_SECONDS;
    Model.EDGE_ENABLED_CAP = EDGE_ENABLED_CAP;
    Model.PER_SKILL_EDGE_CAP = PER_SKILL_EDGE_CAP;
    Model.VISUAL = VISUAL;
    Model.SECTOR_ANGLE = SECTOR_ANGLE;
    Model.START_ANGLE = START_ANGLE;
    Model.CENTER_OFFSET = CENTER_OFFSET;
  }

  applyBoardConfig(DEFAULT_BOARD_CONFIG);

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

  const SLOT_ACCEPTS = {
    [SLOT_KIND.SKILL]: [ITEM_CATEGORY.SKILL],
    [SLOT_KIND.FORM]: [ITEM_CATEGORY.FORM],
    [SLOT_KIND.LOOP]: [ITEM_CATEGORY.LOOP],
    [SLOT_KIND.EDGE]: [ITEM_CATEGORY.EDGE],
  };

  let SKILLS = [];
  let FORM_RUNES = [];
  let LOOP_RUNES = [];
  let EDGE_RUNES = [];
  let ITEMS = [];

  function rebuildItems() {
    SKILLS = Object.values(SKILL_LIBRARY || {}).map((skill) => ({
      ...skill,
      desc: skill.desc || '',
    }));
    FORM_RUNES = Object.values(FORM_RUNES_LIB || {}).map((r) => ({
      ...r,
      desc: r.desc || r.name,
    }));
    LOOP_RUNES = Object.values(LOOP_RUNES_LIB || {}).map((r) => ({
      ...r,
      desc: r.desc || r.name,
    }));
    EDGE_RUNES = Object.values(EDGE_RUNES_LIB || {}).map((r) => ({
      ...r,
      desc: r.desc || r.name,
    }));
    ITEMS = [
      ...SKILLS.map((s) => ({ ...s, category: ITEM_CATEGORY.SKILL })),
      ...FORM_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.FORM })),
      ...LOOP_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.LOOP })),
      ...EDGE_RUNES.map((r) => ({ ...r, category: ITEM_CATEGORY.EDGE })),
    ];

    Model.SKILLS = SKILLS;
    Model.FORM_RUNES = FORM_RUNES;
    Model.LOOP_RUNES = LOOP_RUNES;
    Model.EDGE_RUNES = EDGE_RUNES;
    Model.ITEMS = ITEMS;
  }

  rebuildItems();

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
      issuesOut.push({
        id: 'edge_cap',
        message: `\u8054\u7ed3\u69fd\u542f\u7528\u8d85\u8fc7\u4e0a\u9650\uff08${enabledEdges.length}/${EDGE_ENABLED_CAP}\uff09`,
      });
    }
    const perSkillEdges = {};
    enabledEdges.forEach(([key]) => {
      const [a, b] = key.split('|');
      perSkillEdges[a] = (perSkillEdges[a] || 0) + 1;
      perSkillEdges[b] = (perSkillEdges[b] || 0) + 1;
      if (!state.build.skills_by_gua?.[a] || !state.build.skills_by_gua?.[b]) {
        issuesOut.push({
          id: `edge_skill_${key}`,
          message: `\u8054\u7ed3 ${key} \u9700\u8981\u4e24\u4fa7\u6280\u80fd`,
        });
      }
    });
    Object.entries(perSkillEdges).forEach(([gua, count]) => {
      if (count > PER_SKILL_EDGE_CAP) {
        issuesOut.push({
          id: `skill_edge_${gua}`,
          message: `${gua} \u53c2\u4e0e\u8054\u7ed3\u8d85\u8fc7\u4e0a\u9650\uff08${count}/${PER_SKILL_EDGE_CAP}\uff09`,
        });
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
  Model.setSkillLibrary = function setSkillLibrary(library) {
    SKILL_LIBRARY = library || {};
    Model.SKILL_LIBRARY = SKILL_LIBRARY;
    rebuildItems();
  };
  Model.setRuneLibrary = function setRuneLibrary(runes) {
    FORM_RUNES_LIB = runes?.form_runes || {};
    LOOP_RUNES_LIB = runes?.loop_runes || {};
    EDGE_RUNES_LIB = runes?.edge_runes || {};
    Model.FORM_RUNES_LIB = FORM_RUNES_LIB;
    Model.LOOP_RUNES_LIB = LOOP_RUNES_LIB;
    Model.EDGE_RUNES_LIB = EDGE_RUNES_LIB;
    rebuildItems();
  };
  Model.setReactions = function setReactions(reactions) {
    REACTIONS = reactions || {};
    Model.REACTIONS = REACTIONS;
  };
  Model.setGuaTraits = function setGuaTraits(traits) {
    GUA_TRAITS = traits || {};
    Model.GUA_TRAITS = GUA_TRAITS;
  };
  Model.setBossProfiles = function setBossProfiles(bosses) {
    BOSS_PROFILES = Array.isArray(bosses) ? bosses : [];
    Model.BOSS_PROFILES = BOSS_PROFILES;
  };
  Model.setBoardConfig = function setBoardConfig(config) {
    applyBoardConfig(config);
  };
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
