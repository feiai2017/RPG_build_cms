(function (global) {
  function expect(cond, msg) {
    if (!cond) throw new Error(msg);
  }

  function buildBaseState() {
    return {
      boardId: 'test',
      rotationDeg: 0,
      budgets: { powerCap: 10, bandwidthCap: 10 },
      pointerRule: {
        sectors: [
          { element: 'FIRE', startDeg: 0, endDeg: 72 },
          { element: 'EARTH', startDeg: 72, endDeg: 144 },
          { element: 'METAL', startDeg: 144, endDeg: 216 },
          { element: 'WATER', startDeg: 216, endDeg: 288 },
          { element: 'WOOD', startDeg: 288, endDeg: 360 },
        ],
      },
      nodes: [],
      edges: [],
    };
  }

  function runEvaluatorTests() {
    const EvaluateBoard = global.BDEvaluator?.EvaluateBoard;
    const catalog = global.BD_CATALOG;
    if (!EvaluateBoard || !catalog) {
      console.warn('Evaluator not loaded');
      return;
    }

    // Test 1: 未连通不生效
    {
      const state = buildBaseState();
      state.nodes = [
        { id: 'core', ring: 'CORE', element: 'EARTH', visualType: 'CORE', isLit: true, effectId: null, componentSlot: { type: 'SOURCE' } },
        { id: 'B', ring: 'INNER', element: 'FIRE', visualType: 'NORMAL', isLit: true, effectId: 'STAT_FIRE_DMG_3', componentSlot: { type: 'NONE' } },
      ];
      state.edges = [{ id: 'core|B', from: 'core', to: 'B', baseCost: 1, state: 'DISABLED', componentSlot: { type: 'NONE' } }];
      const result = EvaluateBoard(state, catalog, { enforceBudgets: true });
      expect(!result.derived.energizedNodes.has('B'), 'Test1: B should not be energized');
      expect(!result.combatOutput.stats.mul.FIRE_DMG_PCT, 'Test1: no fire bonus');
    }

    // Test 2: 连通后生效
    {
      const state = buildBaseState();
      state.nodes = [
        { id: 'core', ring: 'CORE', element: 'EARTH', visualType: 'CORE', isLit: true, effectId: null, componentSlot: { type: 'SOURCE' } },
        { id: 'B', ring: 'INNER', element: 'FIRE', visualType: 'NORMAL', isLit: true, effectId: 'STAT_FIRE_DMG_3', componentSlot: { type: 'NONE' } },
      ];
      state.edges = [{ id: 'core|B', from: 'core', to: 'B', baseCost: 1, state: 'ENABLED', componentSlot: { type: 'NONE' } }];
      const result = EvaluateBoard(state, catalog, { enforceBudgets: true });
      expect(result.derived.energizedNodes.has('B'), 'Test2: B should be energized');
      expect(result.combatOutput.stats.mul.FIRE_DMG_PCT > 0, 'Test2: fire bonus applied');
    }

    // Test 3: DIODE 方向阻断
    {
      const state = buildBaseState();
      state.nodes = [
        { id: 'core', ring: 'CORE', element: 'EARTH', visualType: 'CORE', isLit: true, effectId: null, componentSlot: { type: 'SOURCE' } },
        { id: 'B', ring: 'INNER', element: 'FIRE', visualType: 'NORMAL', isLit: true, effectId: 'STAT_FIRE_DMG_3', componentSlot: { type: 'NONE' } },
      ];
      state.edges = [{ id: 'B|core', from: 'B', to: 'core', baseCost: 1, state: 'ENABLED', componentSlot: { type: 'DIODE' } }];
      const result = EvaluateBoard(state, catalog, { enforceBudgets: true });
      expect(!result.derived.energizedNodes.has('B'), 'Test3: diode blocks');
    }

    // Test 4: 带宽超限
    {
      const state = buildBaseState();
      state.budgets.bandwidthCap = 0;
      state.nodes = [
        { id: 'core', ring: 'CORE', element: 'EARTH', visualType: 'CORE', isLit: true, effectId: null, componentSlot: { type: 'SOURCE' } },
        { id: 'B', ring: 'INNER', element: 'FIRE', visualType: 'NORMAL', isLit: true, effectId: 'STAT_FIRE_DMG_3', componentSlot: { type: 'NONE' } },
      ];
      state.edges = [{ id: 'core|B', from: 'core', to: 'B', baseCost: 1, state: 'ENABLED', componentSlot: { type: 'NONE' } }];
      const result = EvaluateBoard(state, catalog, { enforceBudgets: true });
      expect(!result.isValid, 'Test4: should be invalid');
      expect(result.violations.some((v) => v.type === 'BANDWIDTH_OVER'), 'Test4: bandwidth violation');
    }

    console.log('Evaluator tests passed');
  }

  global.BDEvaluatorTests = { runEvaluatorTests };
})(typeof window !== 'undefined' ? window : globalThis);
