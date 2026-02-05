(function () {
  const Model = window.TiandaoModel;

  function buildMinimalPayload(state) {
    const elements = Array.from(new Set(Object.values(Model.GUA_INFO).map((info) => info.element)));

    const rings = [
      { id: 'skill', radius: state.layout.skillR },
      { id: 'rune', radius: state.layout.runeR },
      { id: 'edge', radius: state.layout.edgeR },
      { id: 'outer', radius: state.layout.outerLabelR },
    ];

    const nodes = state.slots.map((slot) => {
      let ring = 'rune';
      if (slot.kind === Model.SLOT_KIND.SKILL) ring = 'skill';
      if (slot.kind === Model.SLOT_KIND.EDGE) ring = 'edge';
      return {
        id: slot.id,
        ring,
        element: slot.element,
        type: slot.kind,
        angle: slot.angle,
        radius: slot.r,
        x: slot.x,
        y: slot.y,
        gua: slot.gua,
        gua_a: slot.gua_a || null,
        gua_b: slot.gua_b || null,
      };
    });

    const edges = state.slots
      .filter((slot) => slot.kind === Model.SLOT_KIND.EDGE)
      .map((slot) => ({
        a: `skill_${slot.gua_a}`,
        b: `skill_${slot.gua_b}`,
        kind: 'gua',
        id: slot.id,
      }));

    const build = {
      slots: state.slots.map((slot) => ({
        id: slot.id,
        kind: slot.kind,
        gua: slot.gua,
        gua_a: slot.gua_a || null,
        gua_b: slot.gua_b || null,
        item_id: slot.item_id || null,
      })),
    };

    return {
      meta: {
        elements,
      },
      rings,
      nodes,
      edges,
      build,
    };
  }

  function persistPayload(state) {
    const payload = buildMinimalPayload(state);
    localStorage.setItem('tiandao_board', JSON.stringify(payload));
    return payload;
  }

  window.TiandaoGodotExport = {
    buildMinimalPayload,
    persistPayload,
  };
})();
