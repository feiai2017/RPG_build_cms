function formatNumber(value) {
  if (value == null || Number.isNaN(value)) return '-';
  return typeof value === 'number' ? value.toFixed(1) : String(value);
}

let filterValue = 'all';

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

  bdSummaryEl.innerHTML = `
    <div>构筑：${bd.name || '未命名'}</div>
    <div>技能槽：${Object.keys(bd.skills || {}).length}</div>
    <div>联结槽：${Object.keys(bd.edges || {}).length}</div>
  `;

  fightSummaryEl.innerHTML = `
    <div>施放统计：${JSON.stringify(result.metrics?.casts_per_skill || {})}</div>
    <div>反应统计：${JSON.stringify(result.metrics?.reaction_counts || {})}</div>
  `;

  resultSummaryEl.innerHTML = `
    <div>空窗：${formatNumber(result.metrics?.downtime_ticks)}</div>
    <div>续航：${formatNumber(result.metrics?.sustain_total)}</div>
  `;

  const infoLines = [
    `技能配置：${JSON.stringify(bd.skills || {})}`,
    `私有符文：${JSON.stringify(bd.runes || {})}`,
    `联结符文：${JSON.stringify(bd.edges || {})}`,
  ];
  infoLines.forEach((line) => {
    const li = document.createElement('li');
    li.textContent = line;
    bdInfoEl.appendChild(li);
  });

  const runeLines = [];
  Object.entries(bd.runes || {}).forEach(([gua, runes]) => {
    runeLines.push(`${gua}: Form=${runes.form || '-'} / Loop=${runes.loop || '-'}`);
  });
  Object.entries(bd.edges || {}).forEach(([edge, rune]) => {
    runeLines.push(`联结 ${edge}: ${rune}`);
  });
  runeLines.forEach((line) => {
    const li = document.createElement('li');
    li.textContent = line;
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
