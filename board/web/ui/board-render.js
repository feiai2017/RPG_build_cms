(function () {
  const Model = window.TiandaoModel;

  const WUXING_COLORS = {
    金: '#E6E6E6',
    木: '#39D98A',
    水: '#3AA0FF',
    火: '#FF4D4D',
    土: '#FFD166',
  };

  const SLOT_FILL = 'rgba(255,255,255,0.06)';
  const SLOT_VISUAL = {
    skill: { size: 20, stroke: 2.8, label: 14 },
    form: { size: 10, stroke: 2.0, label: 9 },
    loop: { size: 11, stroke: 2.0, label: 9 },
    edge: { size: 14, stroke: 2.6, label: 10 },
    edgeEmpty: { size: 12, stroke: 1.6, label: 9 },
  };

  const TERM_GLOSSARY = {
    火印记: '火系印记。再次被非火元素命中时触发元素反应并消耗印记。',
    水印记: '水系印记。再次被非水元素命中时触发元素反应并消耗印记。',
    木印记: '木系印记。再次被非木元素命中时触发元素反应并消耗印记。',
    金印记: '金系印记。再次被非金元素命中时触发元素反应并消耗印记。',
    土印记: '土系印记。再次被非土元素命中时触发元素反应并消耗印记。',
  };

  let termTooltip = null;

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function renderWithGlossary(text) {
    if (!text) return '-';
    let html = escapeHtml(text).replace(/\n/g, '<br>');
    Object.entries(TERM_GLOSSARY).forEach(([term, tip]) => {
      const safeTerm = escapeHtml(term);
      const safeTip = escapeHtml(tip);
      html = html.split(safeTerm).join(`<span class="term" data-tip="${safeTip}">${safeTerm}</span>`);
    });
    return html;
  }

  function ensureTermTooltip() {
    if (termTooltip) return termTooltip;
    termTooltip = document.createElement('div');
    termTooltip.id = 'term-tooltip';
    termTooltip.style.display = 'none';
    document.body.appendChild(termTooltip);
    return termTooltip;
  }

  function showTermTooltip(text, evt) {
    const tip = ensureTermTooltip();
    tip.textContent = text;
    tip.style.display = 'block';
    moveTermTooltip(evt);
  }

  function moveTermTooltip(evt) {
    if (!termTooltip) return;
    const padding = 12;
    const maxX = window.innerWidth - termTooltip.offsetWidth - padding;
    const maxY = window.innerHeight - termTooltip.offsetHeight - padding;
    const x = Math.min(maxX, evt.clientX + 14);
    const y = Math.min(maxY, evt.clientY + 16);
    termTooltip.style.left = `${Math.max(padding, x)}px`;
    termTooltip.style.top = `${Math.max(padding, y)}px`;
  }

  function hideTermTooltip() {
    if (!termTooltip) return;
    termTooltip.style.display = 'none';
  }

  function bindGlossaryTooltips(root) {
    if (!root) return;
    root.querySelectorAll('.term').forEach((node) => {
      node.addEventListener('mouseenter', (evt) => showTermTooltip(node.dataset.tip, evt));
      node.addEventListener('mousemove', moveTermTooltip);
      node.addEventListener('mouseleave', hideTermTooltip);
    });
  }

  function formatRune(prefix, item) {
    if (!item) return `${prefix}: 空`;
    return `${prefix}: ${item.name}（${item.desc || item.name}）`;
  }

  function formatSkillKind(kind) {
    return kind === 'support' ? '辅助技能' : '输出技能';
  }

  function formatSkillEffect(item) {
    if (!item) return '空槽位';
    const parts = [];
    if (item.desc) parts.push(item.desc);
    return parts.length ? parts.join('；') : '空槽位';
  }

  function computeSkillDetailText(skill, form, loop) {
    if (!skill) return '空槽位';
    const lines = [];
    const baseCd = Math.max(1, (skill.baseCd || 0) + (form?.cdAdd || 0) + (loop?.cdDelta || 0));
    const markTerm = skill.element ? `${skill.element}印记` : null;
    if (skill.kind === 'support') {
      const mult = form?.mult || 1;
      const sustain = (skill.sustain || 0) * mult;
      if (skill.sustain != null) lines.push(`护持:${sustain.toFixed(1)}`);
      if (form?.mult) lines.push(`形态倍率:${mult.toFixed(2)}x`);
      if (loop?.charges) lines.push(`充能:${loop.charges}`);
      if (loop?.recastDelay) lines.push(`复施:${loop.recastDelay}tick`);
      if (loop?.sustainOnHit) lines.push(`命中回能:+${loop.sustainOnHit}`);
      if (loop?.sustainOnCrit) lines.push(`暴击回能:+${loop.sustainOnCrit}`);
    } else {
      const hits = form?.hits || 1;
      const mult = form?.mult || 1;
      const perHit = (skill.baseDamage || 0) * mult;
      const total = perHit * hits;
      if (skill.baseDamage != null) lines.push(`基础伤害:${skill.baseDamage}`);
      lines.push(`多段:${hits} 每段:${perHit.toFixed(1)} 总计:${total.toFixed(1)}`);
      if (form?.mult) lines.push(`形态倍率:${mult.toFixed(2)}x`);
      if (form?.markBonus) lines.push(`印记强化:+${form.markBonus}`);
      if (markTerm) lines.push(`印记:${markTerm}`);
      if (loop?.charges) lines.push(`充能:${loop.charges}`);
      if (loop?.recastDelay) lines.push(`复施:${loop.recastDelay}tick`);
      if (loop?.accelOnMark) lines.push(`印记加速:-${loop.accelOnMark}tick`);
      if (loop?.sustainOnHit) lines.push(`命中回能:+${loop.sustainOnHit}`);
      if (loop?.sustainOnCrit) lines.push(`暴击回能:+${loop.sustainOnCrit}`);
    }
    lines.push(`冷却:${baseCd}tick(${(baseCd * Model.TICK_SECONDS).toFixed(1)}s)`);
    return lines.join('\n');
  }

  function dimOpacity(slotId, focusSet) {
    if (!focusSet) return 1;
    return focusSet.has(slotId) ? 1 : 0.15;
  }

  function renderEdgeSocket(state, slot, focusSet) {
    const isActive = !!slot.item_id;
    const isFocused = !focusSet || focusSet.has(slot.id);
    const opacity = isFocused ? 1 : 0.15;
    const sizeCfg = isActive ? SLOT_VISUAL.edge : SLOT_VISUAL.edgeEmpty;
    const size = sizeCfg.size;
    const strokeW = sizeCfg.stroke;
    const aColor = WUXING_COLORS[Model.GUA_INFO[slot.gua_a]?.element || '金'];
    const bColor = WUXING_COLORS[Model.GUA_INFO[slot.gua_b]?.element || '金'];
    const r = size;
    const rInner = size * 0.68;
    const outerPoints = `${slot.x},${slot.y - r} ${slot.x + r},${slot.y} ${slot.x},${slot.y + r} ${slot.x - r},${slot.y}`;
    const innerPoints = `${slot.x},${slot.y - rInner} ${slot.x + rInner},${slot.y} ${slot.x},${slot.y + rInner} ${slot.x - rInner},${slot.y}`;
    const edgeItem = Model.getItemById(slot.item_id);
    const title = edgeItem ? `联结槽：${edgeItem.name} - ${edgeItem.desc}` : '联结槽：空';
    let svg = '';
    svg += `<g data-slot-id="${slot.id}">`;
    svg += `<title>${title}</title>`;
    svg += `<polygon points="${outerPoints}" fill="${SLOT_FILL}" stroke="${aColor}" stroke-width="${strokeW}" opacity="${opacity}" />`;
    svg += `<polygon points="${innerPoints}" fill="none" stroke="${bColor}" stroke-width="${strokeW - 0.6}" opacity="${opacity}" />`;
    if (isActive) {
      svg += `<polygon points="${outerPoints}" fill="none" stroke="rgba(255,255,255,0.35)" stroke-width="1.4" opacity="${opacity}" />`;
      svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 6}" fill="none" stroke="rgba(140,220,255,0.35)" stroke-width="1.2" opacity="${opacity}" />`;
    }
    svg += `<text x="${slot.x}" y="${slot.y + 4}" text-anchor="middle" font-size="${SLOT_VISUAL.edge.label}" fill="rgba(230,240,250,0.95)" opacity="${opacity}">⛓</text>`;
    svg += `<circle data-slot-id="${slot.id}" cx="${slot.x}" cy="${slot.y}" r="${size + 10}" fill="transparent" stroke="none" pointer-events="all" />`;
    svg += `</g>`;
    return svg;
  }

  function renderBoard(state, selectedSlotId, focusId) {
    const size = Model.VISUAL.size;
    const cx = size / 2;
    const cy = size / 2;
    const focusSet = Model.computeRelatedIds(state, focusId);

    let svg = `<svg class="board" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">`;
    svg += '<defs><filter id="glow"><feGaussianBlur stdDeviation="4" result="blur" /><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>';

    // sectors
    const sectorAngle = (Math.PI * 2) / Model.GUA_ORDER.length;
    Model.GUA_ORDER.forEach((gua, idx) => {
      const start = idx * sectorAngle - Math.PI / 2;
      const end = start + sectorAngle;
      const r = 300;
      const x1 = cx + Math.cos(start) * r;
      const y1 = cy + Math.sin(start) * r;
      const x2 = cx + Math.cos(end) * r;
      const y2 = cy + Math.sin(end) * r;
      const large = sectorAngle > Math.PI ? 1 : 0;
      svg += `<path d="M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z" fill="rgba(120,140,160,0.08)" stroke="rgba(140,170,200,0.35)" stroke-width="1" />`;
    });

    // outer labels
    Model.GUA_ORDER.forEach((gua, idx) => {
      const theta = Model.START_ANGLE + idx * Model.SECTOR_ANGLE + Model.CENTER_OFFSET;
      const x = cx + Math.cos(theta) * Model.VISUAL.outerLabelR;
      const y = cy + Math.sin(theta) * Model.VISUAL.outerLabelR;
      const info = Model.GUA_INFO[gua];
      svg += `<text x="${x}" y="${y - 6}" text-anchor="middle" font-size="18" fill="rgba(230,240,250,0.95)" stroke="rgba(6,8,12,0.7)" stroke-width="3" paint-order="stroke">${info.symbol}</text>`;
      svg += `<text x="${x}" y="${y + 12}" text-anchor="middle" font-size="13" fill="rgba(220,232,244,0.9)" stroke="rgba(6,8,12,0.7)" stroke-width="3" paint-order="stroke">${gua}</text>`;
    });

    // edge lines
    const edgeRunes = state.build.edge_runes || {};
    Object.entries(edgeRunes).forEach(([key, rune]) => {
      if (!rune) return;
      const [a, b] = key.split('|');
      const slotA = state.slots.find((s) => s.kind === Model.SLOT_KIND.SKILL && s.gua === a);
      const slotB = state.slots.find((s) => s.kind === Model.SLOT_KIND.SKILL && s.gua === b);
      const edgeSlot = state.slots.find((s) => s.kind === Model.SLOT_KIND.EDGE && s.gua === key);
      if (!slotA || !slotB) return;
      const lineOpacity = focusSet ? (focusSet.has(edgeSlot?.id) ? 0.5 : 0.12) : 0.45;
      svg += `<line x1="${slotA.x}" y1="${slotA.y}" x2="${slotB.x}" y2="${slotB.y}" stroke="rgba(120,200,255,${lineOpacity})" stroke-width="1.3" />`;
    });

    // slots
    state.slots.forEach((slot) => {
      const opacity = dimOpacity(slot.id, focusSet);
      const stroke = WUXING_COLORS[slot.element] || '#dfe8f2';

      if (slot.kind === Model.SLOT_KIND.EDGE) {
        svg += renderEdgeSocket(state, slot, focusSet);
        return;
      }

      const sizeCfg = slot.kind === Model.SLOT_KIND.SKILL ? SLOT_VISUAL.skill : slot.kind === Model.SLOT_KIND.LOOP ? SLOT_VISUAL.loop : SLOT_VISUAL.form;
      const size = sizeCfg.size;
      const strokeWidth = sizeCfg.stroke;
      const slotItem = Model.getItemById(slot.item_id);
      let title = '空槽位';
      if (slot.kind === Model.SLOT_KIND.SKILL) {
        if (slotItem) {
          const baseSkill = Model.SKILL_LIBRARY[slotItem.id] || slotItem;
          const runes = state.build.private_runes?.[slot.gua] || {};
          const form = Model.FORM_RUNES_LIB[runes.form];
          const loop = Model.LOOP_RUNES_LIB[runes.loop];
          const detailText = computeSkillDetailText(baseSkill, form, loop).replace(/\n/g, ' | ');
          title = `技能：${slotItem.name} | ${formatSkillKind(baseSkill.kind)} | 元素:${baseSkill.element} | ${detailText}`;
        } else {
          title = '技能槽：空';
        }
      } else if (slot.kind === Model.SLOT_KIND.FORM) {
        title = slotItem ? `Form：${slotItem.name} - ${slotItem.desc}` : 'Form 槽：空';
      } else if (slot.kind === Model.SLOT_KIND.LOOP) {
        title = slotItem ? `Loop：${slotItem.name} - ${slotItem.desc}` : 'Loop 槽：空';
      }

      svg += `<g data-slot-id="${slot.id}"><title>${title}</title>`;

      if (slot.kind === Model.SLOT_KIND.SKILL) {
        const r = size;
        const points = [];
        for (let i = 0; i < 6; i += 1) {
          const angle = Math.PI / 3 * i + Math.PI / 6;
          points.push(`${slot.x + Math.cos(angle) * r},${slot.y + Math.sin(angle) * r}`);
        }
        svg += `<polygon points="${points.join(' ')}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
      } else if (slot.kind === Model.SLOT_KIND.LOOP) {
        const r = size;
        const points = `${slot.x},${slot.y - r} ${slot.x + r},${slot.y} ${slot.x},${slot.y + r} ${slot.x - r},${slot.y}`;
        svg += `<polygon points="${points}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
      } else {
        svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size}" fill="${SLOT_FILL}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}" />`;
      }

      const label = slot.kind === Model.SLOT_KIND.SKILL ? Model.GUA_INFO[slot.gua].verb : slot.kind === Model.SLOT_KIND.FORM ? 'F' : 'L';
      const labelSize = slot.kind === Model.SLOT_KIND.SKILL ? SLOT_VISUAL.skill.label : SLOT_VISUAL.form.label;
      svg += `<text x="${slot.x}" y="${slot.y + 5}" text-anchor="middle" font-size="${labelSize}" fill="rgba(240,244,250,0.95)" font-weight="700" opacity="${opacity}" pointer-events="none">${label}</text>`;

      if (slot.id === selectedSlotId) {
        svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 8}" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.6" />`;
        svg += `<circle cx="${slot.x}" cy="${slot.y}" r="${size + 12}" fill="none" stroke="rgba(120,220,255,0.55)" stroke-width="1.2" />`;
      }
      svg += `<circle data-slot-id="${slot.id}" cx="${slot.x}" cy="${slot.y}" r="${size + 10}" fill="transparent" stroke="none" pointer-events="all" />`;
      svg += `</g>`;
    });

    svg += '</svg>';
    return svg;
  }

  function updateDetail(dom, state, slot, verbose) {
    if (!slot) return;
    const info = Model.GUA_INFO[slot.gua] || { element: '-', verb: '-' };
    const item = Model.getItemById(slot.item_id);
    const friendly = item?.name ? `${info.verb}·${item.name}` : `${info.verb}·空槽`;
    dom.detail.name.textContent = friendly;
    dom.detail.element.textContent = info.element;
    dom.detail.type.textContent = slot.kind;
    dom.detail.trigram.textContent = `${slot.gua} · ${info.verb}`;
    if (slot.kind === Model.SLOT_KIND.SKILL && item) {
      const baseSkill = Model.SKILL_LIBRARY[item.id] || item;
      const runes = state.build.private_runes?.[slot.gua] || {};
      const form = Model.FORM_RUNES_LIB[runes.form];
      const loop = Model.LOOP_RUNES_LIB[runes.loop];
      dom.detail.component.textContent = verbose ? `${item.category} · ${formatSkillKind(baseSkill.kind)} · 元素:${baseSkill.element}` : `${item.category} · ${formatSkillKind(baseSkill.kind)}`;
      const detailText = verbose ? `${computeSkillDetailText(baseSkill, form, loop)}\nID:${item.id}` : formatSkillEffect(item);
      dom.detail.effect.innerHTML = renderWithGlossary(detailText);
    } else {
      dom.detail.component.textContent = item?.category || '-';
      dom.detail.effect.textContent = item?.desc || '空槽位';
    }
    if (dom.detail.id) dom.detail.id.textContent = slot.id;
    if (dom.detail.runes) {
      if (slot.kind === Model.SLOT_KIND.SKILL) {
        const runes = state.build.private_runes?.[slot.gua] || { form: null, loop: null };
        const formItem = Model.FORM_RUNES_LIB[runes.form] || Model.getItemById(runes.form);
        const loopItem = Model.LOOP_RUNES_LIB[runes.loop] || Model.getItemById(runes.loop);
        dom.detail.runes.textContent = `${formatRune('F', formItem)} / ${formatRune('L', loopItem)}`;
      } else if (slot.kind === Model.SLOT_KIND.FORM) {
        dom.detail.runes.textContent = formatRune('F', item);
      } else if (slot.kind === Model.SLOT_KIND.LOOP) {
        dom.detail.runes.textContent = formatRune('L', item);
      } else {
        dom.detail.runes.textContent = '-';
      }
    }
    if (dom.detail.effect) {
      bindGlossaryTooltips(dom.detail.effect);
    }

    if (dom.detail.links) {
      if (slot.kind === Model.SLOT_KIND.EDGE) {
        const rune = state.build.edge_runes?.[slot.gua] || '空';
        dom.detail.links.textContent = `${slot.gua_a} ↔ ${slot.gua_b} · ${rune}`;
      } else if (slot.kind === Model.SLOT_KIND.SKILL) {
        const prev = Model.GUA_ORDER[(Model.GUA_ORDER.indexOf(slot.gua) - 1 + Model.GUA_ORDER.length) % Model.GUA_ORDER.length];
        const next = Model.nextGua(slot.gua);
        const edges = [];
        const edgePrev = state.build.edge_runes?.[Model.canonicalEdgeKey(prev, slot.gua)];
        const edgeNext = state.build.edge_runes?.[Model.canonicalEdgeKey(slot.gua, next)];
        if (edgePrev) edges.push(`${prev}↔${slot.gua}:${edgePrev}`);
        if (edgeNext) edges.push(`${slot.gua}↔${next}:${edgeNext}`);
        dom.detail.links.textContent = edges.length ? edges.join(' | ') : '无联结';
      } else {
        dom.detail.links.textContent = '-';
      }
    }
  }

  function formatCasts(castsPerSkill) {
    if (!castsPerSkill || !Object.keys(castsPerSkill).length) return '-';
    return Object.entries(castsPerSkill)
      .map(([skillId, count]) => {
        const skill = Model.SKILL_LIBRARY[skillId];
        const name = skill?.name || skillId;
        return `${name} × ${count}`;
      })
      .join('\n');
  }

  function formatReactions(reactionCounts) {
    if (!reactionCounts || !Object.keys(reactionCounts).length) return '-';
    const map = {};
    Object.values(Model.REACTIONS || {}).forEach((r) => {
      map[r.type] = r.name;
    });
    return Object.entries(reactionCounts)
      .map(([type, count]) => `${map[type] || type} × ${count}`)
      .join('\n');
  }

  window.TiandaoRender = {
    renderBoard,
    updateDetail,
    bindGlossaryTooltips,
    renderWithGlossary,
    formatCasts,
    formatReactions,
  };
})();
