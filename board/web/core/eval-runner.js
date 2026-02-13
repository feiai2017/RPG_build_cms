(function (global) {
  const DEFAULT_MECHANISM_FLAGS = {
    lifesteal_loop_enabled: true,
    overheal_to_shield_enabled: true,
    dot_refresh_enabled: true,
    dr_stacking_enabled: true,
  };

  const DEFAULT_MECHANISM_MODES = [
    { id: 'on', label: '机制开启', overrides: {} },
    {
      id: 'off',
      label: '机制关闭',
      overrides: {
        lifesteal_loop_enabled: false,
        overheal_to_shield_enabled: false,
        dot_refresh_enabled: false,
        dr_stacking_enabled: false,
      },
    },
  ];

  function mean(values) {
    if (!values.length) return 0;
    return values.reduce((sum, v) => sum + v, 0) / values.length;
  }

  function variance(values) {
    if (values.length <= 1) return 0;
    const avg = mean(values);
    return mean(values.map((v) => (v - avg) ** 2));
  }

  function linearSlope(points) {
    if (points.length <= 1) return 0;
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    const avgX = mean(xs);
    const avgY = mean(ys);
    let num = 0;
    let den = 0;
    points.forEach((p) => {
      const dx = p.x - avgX;
      num += dx * (p.y - avgY);
      den += dx * dx;
    });
    return den === 0 ? 0 : num / den;
  }

  function resolveMechanismFlags(defaults, overrides) {
    const base = global.BD_MECHANISM_FLAGS || DEFAULT_MECHANISM_FLAGS;
    return { ...base, ...(defaults || {}), ...(overrides || {}) };
  }

  function buildBossInstance(bossDef) {
    const profile = bossDef?.dps_profile || {};
    return {
      id: bossDef.boss_id || bossDef.id,
      name: bossDef.name || bossDef.boss_id || 'Boss',
      hp: bossDef.base_hp ?? bossDef.hp ?? 1000,
      dps: profile.dps ?? bossDef.dps ?? 0,
      spike: profile.spike ?? bossDef.spike ?? 0,
      spikeInterval: profile.spike_interval ?? bossDef.spikeInterval ?? 10,
      thresholds: bossDef.thresholds || { max_ttk: 40, min_survival_margin: 0.2 },
      mechanic_flags: bossDef.mechanic_flags || [],
    };
  }

  function isBaselineProfile(profile) {
    if (!profile) return false;
    if (profile.id === 'baseline') return true;
    return profile.damage_mul === 1 && profile.heal_mul === 1 && profile.shield_mul === 1;
  }

  function computeSurvivalMargin(result, fight, boss) {
    const hpPool = fight?.hp_pool ?? ((result?.totals?.base_ehp ?? 100) + (result?.totals?.ehp ?? 0));
    const netIncoming = fight?.net_incoming ?? Math.max(0, (boss?.dps ?? 0) - (result?.totals?.sustain ?? 0));
    if (netIncoming <= 0) return 1;
    const ttk = Number.isFinite(fight?.time_to_kill) ? fight.time_to_kill : Infinity;
    const ts = Number.isFinite(fight?.time_survived) ? fight.time_survived : 0;
    const t = Math.min(ttk, ts);
    const damageTaken = Number.isFinite(t) ? t * netIncoming : hpPool;
    if (!Number.isFinite(hpPool) || hpPool <= 0) return 0;
    return (hpPool - damageTaken) / hpPool;
  }

  function computeSummary(rows, bossSuites, nerfProfiles, mechanismModes) {
    const modes = mechanismModes?.length ? mechanismModes : DEFAULT_MECHANISM_MODES;
    const onMode = modes[0];
    const offMode = modes[1] || null;
    const baselineProfile = nerfProfiles.find(isBaselineProfile) || nerfProfiles[0];

    const onRows = rows.filter((r) => r.mechanism_mode === onMode.id);
    const robustPassRate = onRows.length
      ? onRows.filter((r) => r.pass_flag).length / onRows.length
      : 0;

    const slope = linearSlope(onRows.map((r) => ({ x: r.damage_mul, y: r.ttk })));

    const baselineRowsOn = rows.filter(
      (r) => r.mechanism_mode === onMode.id && r.nerf_profile_id === baselineProfile?.id,
    );
    const baselineRowsOff = offMode
      ? rows.filter((r) => r.mechanism_mode === offMode.id && r.nerf_profile_id === baselineProfile?.id)
      : [];
    const ttkOn = mean(baselineRowsOn.map((r) => r.ttk));
    const ttkOff = mean(baselineRowsOff.map((r) => r.ttk));
    const marginOn = mean(baselineRowsOn.map((r) => r.survival_margin));
    const marginOff = mean(baselineRowsOff.map((r) => r.survival_margin));
    const mechanismDeltaTtk = ttkOn > 0 ? ttkOff / ttkOn : 0;
    const mechanismDeltaSurvival = marginOn - marginOff;

    const suiteStats = bossSuites.map((suite) => {
      const suiteRows = baselineRowsOn.filter((r) => r.suite_id === suite.suite_id);
      return {
        ttk: mean(suiteRows.map((r) => r.ttk)),
        margin: mean(suiteRows.map((r) => r.survival_margin)),
      };
    });
    const ttkValues = suiteStats.map((s) => s.ttk).filter((v) => Number.isFinite(v));
    const marginValues = suiteStats.map((s) => s.margin).filter((v) => Number.isFinite(v));
    const ttkVar = variance(ttkValues);
    const marginVar = variance(marginValues);
    const ttkMean = mean(ttkValues);
    const ttkCv = ttkMean > 0 ? Math.sqrt(ttkVar) / ttkMean : 0;
    const marginStd = Math.sqrt(marginVar);
    const specializationScore = ttkCv + marginStd;

    let finalLabel = '混合驱动';
    if (robustPassRate >= 0.6 && mechanismDeltaTtk >= 1.3) {
      finalLabel = '机制驱动';
    } else if (robustPassRate < 0.4 && mechanismDeltaTtk < 1.15) {
      finalLabel = '数值驱动';
    }

    return {
      robust_pass_rate: Number(robustPassRate.toFixed(2)),
      sensitivity_ttk_damage: Number(slope.toFixed(3)),
      mechanism_delta_ttk: Number(mechanismDeltaTtk.toFixed(3)),
      mechanism_delta_survival: Number(mechanismDeltaSurvival.toFixed(3)),
      specialization_score: Number(specializationScore.toFixed(3)),
      final_label: finalLabel,
      baseline_profile_id: baselineProfile?.id || null,
      on_mode_id: onMode.id,
      off_mode_id: offMode?.id || null,
    };
  }

  function runEvaluation(params) {
    const solver = global.BaguaSolver;
    if (!solver?.simulateBuild || !solver?.simulateBoss) {
      return { rows: [], summary: { error: 'simulateBuild unavailable' } };
    }

    const build = params.build;
    if (!build?.build_data) {
      return { rows: [], summary: { error: 'build_data missing' } };
    }
    const bossSuites = params.bossSuites || [];
    const nerfProfiles = params.nerfProfiles || [];
    const mechanismModes = params.mechanismModes?.length ? params.mechanismModes : DEFAULT_MECHANISM_MODES;
    const seeds = params.seeds?.length ? params.seeds : [101, 102, 103];
    const maxTicks = params.maxTicks ?? 120;
    const tickSeconds = params.tickSeconds ?? 0.5;
    const baseEhp = params.baseEhp ?? 100;

    const rows = [];

    bossSuites.forEach((suite) => {
      const suiteId = suite.suite_id || suite.id;
      const suiteName = suite.name || suiteId;
      const bosses = suite.bosses || [];
      bosses.forEach((bossDef) => {
        const boss = buildBossInstance(bossDef);
        nerfProfiles.forEach((profile) => {
          mechanismModes.forEach((mode) => {
            const flags = resolveMechanismFlags(build.feature_flags_default, mode.overrides);
            const seedResults = seeds.map((seed) => {
              const result = solver.simulateBuild(build.build_data, {
                maxTicks,
                tickSeconds,
                targetName: boss.name,
                targetId: boss.id,
                target: boss,
                damageMul: profile.damage_mul,
                healMul: profile.heal_mul,
                shieldMul: profile.shield_mul,
                mechanismFlags: flags,
                seed,
                baseEhp,
              });
              const fight = solver.simulateBoss(result, boss);
              const survivalMargin = computeSurvivalMargin(result, fight, boss);
              const pass =
                fight.time_to_kill <= boss.thresholds.max_ttk &&
                survivalMargin >= boss.thresholds.min_survival_margin;
              return { result, fight, survivalMargin, pass };
            });

            const avgDps = mean(seedResults.map((r) => r.result?.totals?.dps ?? 0));
            const avgTtk = mean(seedResults.map((r) => r.fight?.time_to_kill ?? 0));
            const avgMargin = mean(seedResults.map((r) => r.survivalMargin ?? 0));
            const passCount = seedResults.filter((r) => r.pass).length;
            const seedPassRate = seeds.length ? passCount / seeds.length : 0;
            const passFlag = seedPassRate >= 0.5;

            rows.push({
              build_id: build.build_id,
              build_name: build.name,
              suite_id: suiteId,
              suite_name: suiteName,
              boss_id: boss.id,
              boss_name: boss.name,
              nerf_profile_id: profile.id,
              nerf_label: profile.label,
              damage_mul: profile.damage_mul,
              heal_mul: profile.heal_mul,
              shield_mul: profile.shield_mul,
              mechanism_mode: mode.id,
              mechanism_label: mode.label,
              effective_dps: Number(avgDps.toFixed(3)),
              ttk: Number(avgTtk.toFixed(3)),
              survival_margin: Number(avgMargin.toFixed(3)),
              seed_pass_rate: Number(seedPassRate.toFixed(2)),
              pass_flag: passFlag,
              thresholds: boss.thresholds,
            });
          });
        });
      });
    });

    const summary = computeSummary(rows, bossSuites, nerfProfiles, mechanismModes);

    return { rows, summary };
  }

  global.BDEval = {
    runEvaluation,
    computeSummary,
    DEFAULT_MECHANISM_MODES,
  };
})(window);
