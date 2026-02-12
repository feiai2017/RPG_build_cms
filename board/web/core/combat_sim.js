(function (global) {
  function inferTickSeconds(solveResult) {
    const events = solveResult?.events || [];
    for (const evt of events) {
      if (typeof evt?.tick === 'number' && evt.tick > 0 && typeof evt.time === 'number' && evt.time > 0) {
        return evt.time / evt.tick;
      }
    }
    return 0.5;
  }

  function simulateCombat(solveResult, bossProfile, options = {}) {
    const logs = [];
    const events = [];
    const boss = bossProfile || {
      name: '玄铁巨兽',
      hp: 1200,
      dps: 28,
      spike: 80,
      spikeInterval: 10,
    };

    let dps = solveResult.totals.dps;
    const baseEhp = solveResult.totals.base_ehp ?? 100;
    const ehp = baseEhp + solveResult.totals.ehp;
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
    const netIncoming = Math.max(0, boss.dps - sustain);
    const maxSimSeconds = options.maxSimSeconds ?? 60;
    const timeSurvived = netIncoming > 0 ? ehp / netIncoming : maxSimSeconds;

    const tickSeconds = inferTickSeconds(solveResult);
    const spikeInterval = boss.spikeInterval || 0;
    const spikeTicks = spikeInterval > 0 ? Math.max(1, Math.round(spikeInterval / tickSeconds)) : 0;
    const fightEnd = Math.min(timeToKill, timeSurvived, maxSimSeconds);
    const maxTicks = Math.floor(fightEnd / tickSeconds);

    events.push({
      tick: 0,
      time: 0,
      source: boss.name,
      target: '玩家',
      amount: 0,
      kind: 'BOSS',
      type: 'START',
      note: `Boss: ${boss.name} HP=${boss.hp} DPS=${boss.dps}`,
      extra: { event: 'BOSS_START', boss_id: boss.id || null },
    });

    for (let tick = 1; tick <= maxTicks; tick += 1) {
      const time = Number((tick * tickSeconds).toFixed(2));
      const baseDamage = Number((netIncoming * tickSeconds).toFixed(2));
      if (baseDamage > 0) {
        events.push({
          tick,
          time,
          source: boss.name,
          target: '玩家',
          amount: baseDamage,
          kind: 'BOSS',
          type: 'DPS',
          note: '持续伤害',
          extra: { event: 'BOSS_TICK', dps: boss.dps, net_incoming: netIncoming },
        });
      }

      if (spikeTicks && boss.spike && tick % spikeTicks === 0) {
        events.push({
          tick,
          time,
          source: boss.name,
          target: '玩家',
          amount: boss.spike,
          kind: 'BOSS',
          type: 'SPIKE',
          note: `爆发 ${boss.spike}/${boss.spikeInterval}s`,
          extra: { event: 'BOSS_SPIKE', spike: boss.spike, interval: boss.spikeInterval },
        });
      }
    }

    const spikeThreat = boss.spike / Math.max(1, ehp * 0.2);
    if (spikeThreat > 1.2) {
      logs.push('Boss 爆发偏高，注意减载');
    }

    const win = timeToKill <= timeSurvived;
    logs.push(`Boss: ${boss.name} HP=${boss.hp} DPS=${boss.dps}`);
    logs.push(`击杀时间 ${timeToKill.toFixed(1)}s | 存活时间 ${timeSurvived.toFixed(1)}s`);

    const endNote = win ? '击杀Boss' : '玩家倒下';
    events.push({
      tick: maxTicks,
      time: Number(fightEnd.toFixed(2)),
      source: win ? '玩家' : boss.name,
      target: win ? boss.name : '玩家',
      amount: '-',
      kind: 'BOSS',
      type: 'RESULT',
      note: `${endNote} @ ${fightEnd.toFixed(1)}s`,
      extra: { event: 'BOSS_RESULT', win },
    });

    if (fightEnd === maxSimSeconds) {
      events.push({
        tick: maxTicks,
        time: Number(fightEnd.toFixed(2)),
        source: '系统',
        target: '日志',
        amount: '-',
        kind: 'BOSS',
        type: 'TRUNCATED',
        note: `日志仅展示前 ${maxSimSeconds}s`,
        extra: { event: 'BOSS_LOG_TRUNCATED', max_seconds: maxSimSeconds },
      });
    }

    return {
      win,
      time_to_kill: Number(timeToKill.toFixed(1)),
      time_survived: Number(timeSurvived.toFixed(1)),
      boss: boss.name,
      timeline_logs: logs,
      hp_pool: Number(ehp.toFixed(2)),
      net_incoming: Number(netIncoming.toFixed(2)),
      events,
    };
  }

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.simulateCombat = simulateCombat;
})(window);
