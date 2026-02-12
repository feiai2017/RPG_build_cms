(function (global) {
  const nodeEffects = {
    STAT_FIRE_DMG_3: {
      id: 'STAT_FIRE_DMG_3',
      category: 'STAT',
      payload: { statKey: 'FIRE_DMG_PCT', op: 'MUL', value: 0.03, stacking: 'SUM' },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.2, OUTER: 1.5 },
        mainElementMultiplier: 1.2,
      },
    },
    STAT_EARTH_HP_5: {
      id: 'STAT_EARTH_HP_5',
      category: 'STAT',
      payload: { statKey: 'HP_PCT', op: 'MUL', value: 0.05, stacking: 'SUM' },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.1, OUTER: 1.3 },
        mainElementMultiplier: 1.1,
      },
    },
    STAT_METAL_CRIT_2: {
      id: 'STAT_METAL_CRIT_2',
      category: 'STAT',
      payload: { statKey: 'CRIT_RATE', op: 'ADD', value: 0.02, stacking: 'SUM', cap: 0.8 },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.1, OUTER: 1.25 },
        mainElementMultiplier: 1.1,
      },
    },
    STAT_WATER_MANA_3: {
      id: 'STAT_WATER_MANA_3',
      category: 'STAT',
      payload: { statKey: 'MANA_REGEN', op: 'ADD', value: 3, stacking: 'SUM' },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.15, OUTER: 1.3 },
        mainElementMultiplier: 1.1,
      },
    },
    STAT_WOOD_REGEN_2: {
      id: 'STAT_WOOD_REGEN_2',
      category: 'STAT',
      payload: { statKey: 'ENERGY_REGEN', op: 'ADD', value: 2, stacking: 'SUM' },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.1, OUTER: 1.25 },
        mainElementMultiplier: 1.1,
      },
    },
    TRG_ONHIT_BURN_15: {
      id: 'TRG_ONHIT_BURN_15',
      category: 'TRIGGER',
      payload: {
        event: 'ON_HIT',
        condition: { any: true },
        effect: { applyStatus: { status: 'BURN', durSec: 2, stacks: 1 }, chance: 0.15 },
        icdSec: 0.6,
        maxPerSec: 2,
        stacking: 'SUM_CHANCE',
      },
      scaling: {
        ringMultiplier: { CORE: 1, INNER: 1, MIDDLE: 1.1, OUTER: 1.25 },
        mainElementMultiplier: 1.1,
      },
    },
    SKM_CONVERT_MAIN_TO_METAL: {
      id: 'SKM_CONVERT_MAIN_TO_METAL',
      category: 'SKILL_MOD',
      payload: {
        target: { type: 'SKILL_TAG', value: 'MAIN' },
        modType: 'CONVERT_ELEMENT',
        params: { element: 'METAL' },
      },
    },
    SKM_ADD_TAG_WATER: {
      id: 'SKM_ADD_TAG_WATER',
      category: 'SKILL_MOD',
      payload: {
        target: { type: 'SKILL_TAG', value: 'MAIN' },
        modType: 'ADD_TAG',
        params: { tag: 'WATER' },
      },
    },
  };

  const componentRules = {
    SOURCE: { type: 'SOURCE', attachTo: 'NODE', behavior: {} },
    SWITCH: { type: 'SWITCH', attachTo: 'EDGE', behavior: { graphModifier: { enabledByParamKey: 'isOn' } } },
    DIODE: { type: 'DIODE', attachTo: 'EDGE', behavior: { graphModifier: { directed: true } } },
    RESISTOR: { type: 'RESISTOR', attachTo: 'EDGE', behavior: { costModifier: { addBandwidth: 1 } } },
    CAPACITOR: { type: 'CAPACITOR', attachTo: 'EDGE', behavior: {} },
    AMPLIFIER: { type: 'AMPLIFIER', attachTo: 'EDGE', behavior: { outputModifier: { mul: 1.2 } } },
  };

  global.BD_CATALOG = {
    nodeEffects,
    componentRules,
    constants: {
      POWER_COST_PER_LIT_NODE: 1,
    },
  };
})(window);
