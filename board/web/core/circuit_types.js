(function (global) {
  const Element = Object.freeze({
    metal: 'metal',
    wood: 'wood',
    water: 'water',
    fire: 'fire',
    earth: 'earth',
  });

  const Trigram = Object.freeze({
    qian: 'qian',
    dui: 'dui',
    li: 'li',
    zhen: 'zhen',
    xun: 'xun',
    kan: 'kan',
    gen: 'gen',
    kun: 'kun',
  });

  const NodeType = Object.freeze({
    core: 'core',
    major: 'major',
    normal: 'normal',
  });

  const NodeState = Object.freeze({
    off: 'off',
    charged: 'charged',
    active: 'active',
    overload: 'overload',
    burned: 'burned',
  });

  const EdgeComponent = Object.freeze({
    wire: 'wire',
    resistor: 'resistor',
    capacitor: 'capacitor',
    diode: 'diode',
    amplifier: 'amplifier',
    switch: 'switch',
  });

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.types = {
    Element,
    Trigram,
    NodeType,
    NodeState,
    EdgeComponent,
  };
})(window);
