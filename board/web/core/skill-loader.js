(function (global) {
  let cachedCatalog = null;

  async function fetchJson(url) {
    const res = await fetch(url + '?t=' + Date.now());
    if (!res.ok) throw new Error(`Failed to load ${url}`);
    return res.json();
  }

  async function loadCatalog() {
    if (cachedCatalog) return cachedCatalog;
    const [skillsRaw, runesRaw, reactionsRaw, traitsRaw, bossesRaw, boardUiRaw, flagsRaw] = await Promise.all([
      fetchJson('./configs/tiandao_skills.json'),
      fetchJson('./configs/tiandao_runes.json'),
      fetchJson('./configs/tiandao_reactions.json'),
      fetchJson('./configs/tiandao_gua_traits.json'),
      fetchJson('./configs/tiandao_bosses.json'),
      fetchJson('./configs/tiandao_board_ui.json'),
      fetchJson('./configs/tiandao_mechanism_flags.json'),
    ]);

    const skills = skillsRaw?.skills || skillsRaw || {};
    const formRunes = runesRaw?.form_runes || {};
    const loopRunes = runesRaw?.loop_runes || {};
    const edgeRunes = runesRaw?.edge_runes || {};
    const reactions = reactionsRaw?.reactions || reactionsRaw || {};
    const guaTraits = traitsRaw?.gua_traits || traitsRaw || {};
    const bosses = bossesRaw?.bosses || bossesRaw || [];
    const boardUi = boardUiRaw || {};
    const mechanismFlags = flagsRaw?.default_flags || flagsRaw || {};

    cachedCatalog = {
      skills,
      runes: { form_runes: formRunes, loop_runes: loopRunes, edge_runes: edgeRunes },
      reactions,
      guaTraits,
      bosses,
      boardUi,
      mechanismFlags,
    };

    global.BD_SKILLS = skills;
    global.BD_RUNES = cachedCatalog.runes;
    global.BD_REACTIONS = reactions;
    global.BD_GUA_TRAITS = guaTraits;
    global.BD_BOSSES = bosses;
    global.BD_BOARD_CONFIG = boardUi;
    global.BD_MECHANISM_FLAGS = mechanismFlags;

    if (global.BaguaSolver?.setSkillLibrary) {
      global.BaguaSolver.setSkillLibrary(skills);
    } else if (global.BaguaSolver) {
      global.BaguaSolver.SKILL_LIBRARY = skills;
    }
    if (global.BaguaSolver?.setRuneLibrary) {
      global.BaguaSolver.setRuneLibrary(cachedCatalog.runes);
    }
    if (global.BaguaSolver?.setReactions) {
      global.BaguaSolver.setReactions(reactions);
    }
    if (global.BaguaSolver?.setGuaTraits) {
      global.BaguaSolver.setGuaTraits(guaTraits);
    }
    if (global.BaguaSolver?.setBossProfiles) {
      global.BaguaSolver.setBossProfiles(bosses);
    }
    if (global.BaguaSolver?.setMechanismFlags) {
      global.BaguaSolver.setMechanismFlags(mechanismFlags);
    }
    if (global.BaguaSolver?.setGuaConfig) {
      global.BaguaSolver.setGuaConfig(boardUi);
    }

    if (global.TiandaoModel?.setSkillLibrary) {
      global.TiandaoModel.setSkillLibrary(skills);
    }
    if (global.TiandaoModel?.setRuneLibrary) {
      global.TiandaoModel.setRuneLibrary(cachedCatalog.runes);
    }
    if (global.TiandaoModel?.setReactions) {
      global.TiandaoModel.setReactions(reactions);
    }
    if (global.TiandaoModel?.setGuaTraits) {
      global.TiandaoModel.setGuaTraits(guaTraits);
    }
    if (global.TiandaoModel?.setBossProfiles) {
      global.TiandaoModel.setBossProfiles(bosses);
    }
    if (global.TiandaoModel?.setBoardConfig) {
      global.TiandaoModel.setBoardConfig(boardUi);
    }

    return cachedCatalog;
  }

  async function loadSkillLibrary() {
    const catalog = await loadCatalog();
    return catalog.skills;
  }

  global.SkillLoader = { loadCatalog, loadSkillLibrary };
})(window);
