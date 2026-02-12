(function (global) {
  const { Trigram } = global.CircuitCore.types;

  const TRIGRAM_STEPS = [
    Trigram.qian,
    Trigram.dui,
    Trigram.li,
    Trigram.zhen,
    Trigram.xun,
    Trigram.kan,
  ];

  const TRIGRAM_LABELS = {
    [Trigram.qian]: '乾',
    [Trigram.dui]: '兑',
    [Trigram.li]: '离',
    [Trigram.zhen]: '震',
    [Trigram.xun]: '巽',
    [Trigram.kan]: '坎',
    [Trigram.gen]: '艮',
    [Trigram.kun]: '坤',
  };

  function normDeg(deg) {
    let v = deg % 360;
    if (v < 0) v += 360;
    return v;
  }

  function get_trigram(rotationDeg) {
    const normalized = normDeg(rotationDeg);
    const step = Math.round(normalized / 60) % TRIGRAM_STEPS.length;
    return TRIGRAM_STEPS[step];
  }

  function apply_trigram_modifiers(context) {
    const { trigram, logs, modifiers, resources } = context;
    switch (trigram) {
      case Trigram.qian:
        modifiers.dpsMul *= 1.2;
        modifiers.overloadThresholdMul *= 0.85;
        logs.push('乾：输出放大，过载阈值降低');
        break;
      case Trigram.kan:
        modifiers.sustainMul *= 1.2;
        modifiers.lifesteal += 0.08;
        logs.push('坎：回流强化，生存提升');
        break;
      case Trigram.li:
        modifiers.dpsMul *= 1.1;
        modifiers.overloadThresholdMul *= 0.9;
        logs.push('离：高频触发，输出略增但更热');
        break;
      case Trigram.zhen:
        modifiers.dpsMul *= 1.25;
        modifiers.overloadThresholdMul *= 0.8;
        modifiers.stabilityMul *= 0.9;
        logs.push('震：爆发增强，但更易过载');
        break;
      case Trigram.xun:
        modifiers.dpsMul *= 1.08;
        modifiers.spread += 1;
        logs.push('巽：扩散增强，多链路收益');
        break;
      case Trigram.gen:
        modifiers.stabilityMul *= 1.2;
        modifiers.overloadThresholdMul *= 1.1;
        logs.push('艮：锁定稳固，抗过载');
        break;
      case Trigram.kun:
        resources.power *= 1.2;
        resources.bandwidth *= 1.2;
        modifiers.dpsMul *= 0.95;
        logs.push('坤：容量提升，启动偏慢');
        break;
      case Trigram.dui:
        modifiers.conditional = { minActive: 6, dpsMul: 1.2 };
        logs.push('兑：条件增益，达成后输出提升');
        break;
      default:
        break;
    }
  }

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.rules = {
    get_trigram,
    apply_trigram_modifiers,
    TRIGRAM_LABELS,
  };
})(window);
