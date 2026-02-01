(function (global) {
  function elementMultiplier(solveResult, boss, logs) {
    const element = solveResult.dominantElement || solveResult.dominant_element;
    if (!element) return 1;
    const resist = boss.resist?.[element] || 0;
    const vuln = boss.vulnerable?.[element] || 0;
    const mul = Math.max(0.5, Math.min(1.6, 1 - resist + vuln));
    if (resist > 0) logs.push(`元素抗性：${element} -${Math.round(resist * 100)}%`);
    if (vuln > 0) logs.push(`元素易伤：${element} +${Math.round(vuln * 100)}%`);
    return mul;
  }

  function applyPhaseModifiers(base, phase) {
    const mul = phase?.mul || {};
    return {
      dpsMul: mul.dps || 1,
      bossDpsMul: mul.bossDps || 1,
      spikeMul: mul.spike || 1,
      resistMul: mul.resist || 1,
    };
  }

  function simulateCombat(solveResult, bossProfile, opts = {}) {
    const logs = [];
    const eventLogs = [];
    const boss = bossProfile || {
      name: '玄铁巨兽',
      hp: 1200,
      dps: 28,
      spike: 80,
      spikeInterval: 10,
    };
    const stepSec = opts.stepSec || 1;
    const maxTime = opts.maxTimeSec || 180;
    const detailLevel = opts.detailLevel || 'events';
    const maxEventLines = opts.maxEventLines || 2000;
    const slotEffects = opts.slotEffects || solveResult.slotEffects || {};
    const loopInfo = opts.loopInfo || { mainLoops: 0, supportLoops: 0 };
    const energizedSlots = Array.isArray(solveResult.energizedSlots)
      ? solveResult.energizedSlots
      : Array.from(solveResult.energizedSlots || []);

    function pushEvent(line) {
      if (detailLevel === 'summary') return;
      if (eventLogs.length >= maxEventLines) return;
      eventLogs.push(line);
    }

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

    const elemMul = elementMultiplier(solveResult, boss, logs);
    const mechanics = boss.mechanics || [];
    mechanics.forEach((m) => {
      if (m.type === 'loop_disrupt' && loopInfo.mainLoops > 0) {
        const penalty = Math.min(0.4, m.intensity * loopInfo.mainLoops);
        dps *= 1 - penalty;
        pushEvent(`0.0s | 机制 | 主回路受扰 DPS -${Math.round(penalty * 100)}%`);
      }
      if (m.type === 'slow_drain') {
        const penalty = Math.min(0.4, m.intensity);
        dps *= 1 - penalty;
        pushEvent(`0.0s | 机制 | 续航被压制 DPS -${Math.round(penalty * 100)}%`);
      }
      if (m.type === 'mirror') {
        const penalty = Math.min(0.5, m.intensity);
        dps *= 1 - penalty;
        pushEvent(`0.0s | 机制 | 镜像反制 DPS -${Math.round(penalty * 100)}%`);
      }
      if (m.type === 'shield_invert') {
        const penalty = Math.min(0.4, m.intensity);
        dps *= 1 - penalty;
        pushEvent(`0.0s | 机制 | 护盾反转 DPS -${Math.round(penalty * 100)}%`);
      }
    });
    let hpLeft = boss.hp;
    let timeToKill = 0;
    let timeSurvived = 0;
    let ehpLeft = ehp;
    const phases = boss.phases?.length ? boss.phases : [{ until: 0, mul: {} }];
    let phaseIdx = 0;
    let t = 0;
    let nextSpike = boss.spikeInterval || 10;
    const mechTimers = mechanics.map((m) => ({ ...m, next: m.frequency || 10 }));

    logs.push(`开战：Boss=${boss.name} HP=${boss.hp} DPS=${boss.dps}`);
    pushEvent(`0.0s | 开战 | Boss=${boss.name} HP=${boss.hp} DPS=${boss.dps}`);
    pushEvent(`0.0s | 属性 | DPS=${dps.toFixed(1)} EHP=${ehp.toFixed(1)} 续航=${sustain.toFixed(1)} 稳定=${(solveResult.totals?.stability || 0).toFixed(1)}`);
    if (detailLevel === 'full') {
      energizedSlots.forEach((slotId) => {
        const info = slotEffects[slotId];
        if (!info) return;
        const eff = info.effect || {};
        pushEvent(
          `0.0s | 槽位 | ${slotId} | ${info.stone || '-'} | ${info.slot_type || '-'} | ${info.trigram || '-'} | dps ${eff.dps || 0} ehp ${eff.ehp || 0} sustain ${eff.sustain || 0} stability ${eff.stability || 0}`,
        );
      });
    }

    while (t < maxTime && hpLeft > 0 && ehpLeft > 0) {
      const phase = phases[Math.min(phaseIdx, phases.length - 1)];
      const phaseMul = applyPhaseModifiers(boss, phase);
      const targetHp = boss.hp * (phase.until ?? 0);
      if (hpLeft <= targetHp && phaseIdx < phases.length - 1) {
        phaseIdx += 1;
        logs.push(`阶段切换：进入P${phaseIdx + 1}`);
        pushEvent(`${t.toFixed(1)}s | 阶段切换 | P${phaseIdx + 1}`);
      }
      let bossDps = boss.dps * phaseMul.bossDpsMul;
      const phaseDps = Math.max(1, dps * elemMul * phaseMul.dpsMul);

      const dmgToBoss = phaseDps * stepSec;
      hpLeft = Math.max(0, hpLeft - dmgToBoss);

      mechTimers.forEach((m) => {
        if (m.type === 'overload' && t + stepSec >= m.next) {
          bossDps *= 1 + (m.intensity || 0);
          pushEvent(`${(t + stepSec).toFixed(1)}s | 机制 | 过载压制 伤害+${Math.round((m.intensity || 0) * 100)}%`);
          m.next += m.frequency || 10;
        }
        if (m.type === 'backlash' && t + stepSec >= m.next) {
          bossDps *= 1 + (m.intensity || 0);
          pushEvent(`${(t + stepSec).toFixed(1)}s | 机制 | 反噬爆发 伤害+${Math.round((m.intensity || 0) * 100)}%`);
          m.next += m.frequency || 10;
        }
        if (m.type === 'port_lock' && t + stepSec >= m.next) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 机制 | 端口封锁 ${m.target}`);
          m.next += m.frequency || 10;
        }
      });

      const incomingBase = bossDps * stepSec;
      const mitigated = Math.min(incomingBase, sustain * stepSec);
      let incoming = Math.max(1, bossDps - sustain) * stepSec;
      let spikeHit = 0;
      if (boss.spike && t + stepSec >= nextSpike) {
        spikeHit = boss.spike * (phaseMul.spikeMul || 1);
        incoming += spikeHit;
        nextSpike += boss.spikeInterval || 10;
        pushEvent(`${(t + stepSec).toFixed(1)}s | 爆发命中 | 伤害=${spikeHit.toFixed(0)}`);
      }
      ehpLeft = Math.max(0, ehpLeft - incoming);

      if (detailLevel !== 'summary') {
        pushEvent(`${(t + stepSec).toFixed(1)}s | 承伤 | 受到=${incomingBase.toFixed(1)} 抵消=${mitigated.toFixed(1)} 实际=${incoming.toFixed(1)}`);
        const dom = solveResult.dominantElement || solveResult.dominant_element;
        if (dom === '木' && (t + stepSec) % 3 === 0) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 持续伤害 | 木系叠层触发`);
        }
        if (dom === '火' && (t + stepSec) % 4 === 0) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 灼烧跳伤 | 火系燃烧`);
        }
        if (dom === '金' && (t + stepSec) % 5 === 0) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 穿透斩击 | 金系暴击触发`);
        }
        if (dom === '水' && (t + stepSec) % 5 === 0) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 护持回流 | 水系减伤触发`);
        }
        if (dom === '土' && (t + stepSec) % 6 === 0) {
          pushEvent(`${(t + stepSec).toFixed(1)}s | 守御震荡 | 土系护甲触发`);
        }
      }

      const line = [
        `t=${t + stepSec}s`,
        `BossHP=${hpLeft.toFixed(0)}`,
        `EHP=${ehpLeft.toFixed(0)}`,
        `DPS=${phaseDps.toFixed(1)}`,
        `In=${incoming.toFixed(1)}`,
      ];
      if (spikeHit > 0) line.push(`Spike=${spikeHit.toFixed(0)}`);
      logs.push(line.join(' | '));

      t += stepSec;
    }

    timeToKill = hpLeft <= 0 ? t : Infinity;
    timeSurvived = ehpLeft <= 0 ? t : t;

    const spikeThreat = (boss.spike || 0) / Math.max(1, ehp * 0.2);
    if (spikeThreat > 1.2) {
      logs.push('Boss爆发偏高，注意减载');
    }

    const win = timeToKill <= timeSurvived;
    if (win) {
      pushEvent(`${t.toFixed(1)}s | 胜利 | Boss被击杀`);
    } else {
      pushEvent(`${t.toFixed(1)}s | 失败 | 玩家倒下`);
    }
    logs.push(`Boss: ${boss.name} HP=${boss.hp} DPS=${boss.dps}`);
    logs.push(`击杀时间 ${timeToKill.toFixed(1)}s | 存活时间 ${timeSurvived.toFixed(1)}s`);

    const failureReason = win ? '' : (loopInfo.mainLoops > 0 ? '生存不足或回路被干扰' : '缺主回路输出');
    return {
      win,
      time_to_kill: Number(timeToKill.toFixed(1)),
      time_survived: Number(timeSurvived.toFixed(1)),
      boss: boss.name,
      timeline_logs: logs,
      event_logs: eventLogs,
      failure_reason: failureReason,
    };
  }

  global.CircuitCore = global.CircuitCore || {};
  global.CircuitCore.simulateCombat = simulateCombat;
})(window);
