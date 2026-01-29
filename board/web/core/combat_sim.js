(function (global) {
  function simulateCombat(solveResult, bossProfile) {
    const logs = [];
    const boss = bossProfile || {
      name: '玄铁巨兽',
      hp: 1200,
      dps: 28,
      spike: 80,
      spikeInterval: 10,
    };

    let dps = solveResult.totals.dps;
    const ehp = solveResult.totals.ehp;
    const sustain = solveResult.totals.sustain;

    if (solveResult.totals.overload_count > 0) {
      const penalty = Math.min(0.4, solveResult.totals.overload_count * 0.05);
      dps *= 1 - penalty;
      logs.push(`过载惩罚：DPS -${Math.round(penalty * 100)}%`);
    }
    if (solveResult.totals.burned_count > 0) {
      const penalty = Math.min(0.5, solveResult.totals.burned_count * 0.12);
      dps *= 1 - penalty;
      logs.push(`烧毁惩罚：DPS -${Math.round(penalty * 100)}%`);
    }

    const timeToKill = dps > 0 ? boss.hp / dps : Infinity;
    const netIncoming = Math.max(1, boss.dps - sustain);
    const timeSurvived = ehp / netIncoming;

    const spikeThreat = boss.spike / Math.max(1, ehp * 0.2);
    if (spikeThreat > 1.2) {
      logs.push('Boss爆发偏高，注意减载');
    }

    const win = timeToKill <= timeSurvived;
    logs.push(`Boss: ${boss.name} HP=${boss.hp} DPS=${boss.dps}`);
    logs.push(`击杀时间 ${timeToKill.toFixed(1)}s | 存活时间 ${timeSurvived.toFixed(1)}s`);

    return {
      win,
      time_to_kill: Number(timeToKill.toFixed(1)),
      time_survived: Number(timeSurvived.toFixed(1)),
      boss: boss.name,
      timeline_logs: logs,
    };
  }

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.simulateCombat = simulateCombat;
})(window);
