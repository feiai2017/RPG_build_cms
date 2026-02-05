function formatNumber(value) {
  if (value == null || Number.isNaN(value)) return '-';
  return typeof value === 'number' ? value.toFixed(1) : String(value);
}

let filterValue = 'all';

function formatCasts(casts, catalog) {
  if (!casts || !Object.keys(casts).length) return '-';
  return Object.entries(casts)
    .map(([id, count]) => `${catalog?.skills?.[id]?.name || id} × ${count}`)
    .join('<br>');
}

function formatReactions(reactions, catalog) {
  if (!reactions || !Object.keys(reactions).length) return '-';
  const nameMap = {};
  Object.values(catalog?.reactions || {}).forEach((r) => {
    nameMap[r.type] = r.name;
  });
  return Object.entries(reactions)
    .map(([id, count]) => `${nameMap[id] || id} × ${count}`)
    .join('<br>');
}

function render() {
  const raw = localStorage.getItem('battle_log');
  const bdSummaryEl = document.getElementById('bd-summary');
  const fightSummaryEl = document.getElementById('fight-summary');
  const resultSummaryEl = document.getElementById('result-summary');
  const bdInfoEl = document.getElementById('bd-info');
  const stoneInfoEl = document.getElementById('stone-info');
  const tableBody = document.getElementById('log-table-body');
  const emptyEl = document.getElementById('log-empty');

  bdSummaryEl.textContent = '';
  fightSummaryEl.textContent = '';
  resultSummaryEl.textContent = '';
  bdInfoEl.innerHTML = '';
  stoneInfoEl.innerHTML = '';
  tableBody.innerHTML = '';

  if (!raw) {
    emptyEl.classList.remove('hidden');
    bdSummaryEl.textContent = '暂无日志';
    fightSummaryEl.textContent = '请回到棋盘点击 Run 10s 生成日志。';
    return;
  }

  const payload = JSON.parse(raw);
  const bd = payload.bd || {};
  const result = payload.result || {};
  const fight = payload.fight || {};
  const events = fight.events || [];
  const boss = payload.boss || {};
  const catalog = payload.catalog || {};

  bdSummaryEl.innerHTML = `
    <div>构筑：${bd.name || '未命名'}</div>
    <div>技能槽：${Object.keys(bd.skills || {}).length}</div>
    <div>联结槽：${Object.keys(bd.edges || {}).length}</div>
  `;

  fightSummaryEl.innerHTML = `
    <div>Boss：${boss.name || '木桩'}</div>
    <div>施放统计：<br>${formatCasts(result.metrics?.casts_per_skill || {}, catalog)}</div>
    <div>反应统计：<br>${formatReactions(result.metrics?.reaction_counts || {}, catalog)}</div>
  `;

  resultSummaryEl.innerHTML = `
    <div>空窗：${formatNumber(result.metrics?.downtime_ticks)}</div>
    <div>续航：${formatNumber(result.metrics?.sustain_total)}</div>
    <div>TTK：${formatNumber(fight.summary?.time_to_kill)}</div>
    <div>存活：${formatNumber(fight.summary?.time_survived)}</div>
  `;

  Object.entries(bd.skills || {}).forEach(([gua, skillId]) => {
    const name = catalog.skills?.[skillId]?.name || skillId || '-';
    const li = document.createElement('li');
    li.textContent = `${gua}：${name}`;
    bdInfoEl.appendChild(li);
  });

  Object.entries(bd.runes || {}).forEach(([gua, runes]) => {
    const formName = catalog.form_runes?.[runes.form]?.name || runes.form || '-';
    const loopName = catalog.loop_runes?.[runes.loop]?.name || runes.loop || '-';
    const li = document.createElement('li');
    li.textContent = `${gua}: Form=${formName} / Loop=${loopName}`;
    stoneInfoEl.appendChild(li);
  });
  Object.entries(bd.edges || {}).forEach(([edge, rune]) => {
    const runeName = catalog.edge_runes?.[rune]?.name || rune || '-';
    const li = document.createElement('li');
    li.textContent = `联结 ${edge}: ${runeName}`;
    stoneInfoEl.appendChild(li);
  });

  if (!events.length) {
    emptyEl.classList.remove('hidden');
    return;
  }
  emptyEl.classList.add('hidden');

  const filtered = filterValue === 'all' ? events : events.filter((evt) => evt.kind === filterValue);

  filtered.forEach((evt) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${evt.tick}</td>
      <td>${formatNumber(evt.time)}</td>
      <td>${evt.source}</td>
      <td>${evt.target}</td>
      <td>${formatNumber(evt.amount)}</td>
      <td>${evt.kind}</td>
      <td>${evt.type}</td>
      <td>${evt.note || ''}</td>
    `;
    tableBody.appendChild(row);
  });
}

document.getElementById('refresh-log').addEventListener('click', () => {
  render();
});

const filterEl = document.getElementById('event-filter');
if (filterEl) {
  filterEl.addEventListener('change', () => {
    filterValue = filterEl.value;
    render();
  });
}

render();
