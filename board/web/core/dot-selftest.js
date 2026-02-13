const DotSelfTest = (function () {
  async function loadPreset(name) {
    const res = await fetch(`./configs/${name}.json?t=${Date.now()}`);
    if (!res.ok) throw new Error(`Failed to load preset ${name}`);
    return res.json();
  }

  async function runDotSelfTest() {
    if (!window.BaguaSolver?.simulateBuild) {
      return { ok: false, error: 'BaguaSolver unavailable' };
    }
    if (window.SkillLoader?.loadCatalog) {
      await window.SkillLoader.loadCatalog();
    }
    const build = await loadPreset('preset_1_reaction_loop');
    const result = window.BaguaSolver.simulateBuild(build, {
      maxTicks: 40,
      tickSeconds: 0.5,
      seed: 101,
      targetName: '木桩',
    });
    const metrics = result?.metrics || {};
    const dotUptime = metrics.dot_uptime_ratio ?? 0;
    const fieldUptime = metrics.field_uptime_ratio ?? 0;
    const dotDamage = metrics.damage_breakdown?.dot ?? 0;
    const ok = dotUptime > 0.6 && fieldUptime > 0 && dotDamage > 0;
    return { ok, dot_uptime_ratio: dotUptime, field_uptime_ratio: fieldUptime, dot_damage: dotDamage };
  }

  return { runDotSelfTest };
})();

window.runDotSelfTest = DotSelfTest.runDotSelfTest;
