function formatNumber(value) {
  if (value == null || Number.isNaN(value)) return '-';
  return typeof value === 'number' ? value.toFixed(1) : String(value);
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
    fightSummaryEl.textContent = '请回到棋盘点击 Simulate 生成日志。';
    return;
  }

  const payload = JSON.parse(raw);
  const bd = payload.bd || {};
  const fight = payload.fight || {};
  const result = payload.result || {};
  const events = fight.events || [];

  const styleMap = {
    金: '锋锐',
    木: '扩散',
    水: '续航',
    火: '爆发',
    土: '防御',
    无: '均衡',
  };
  const styleLabel = styleMap[bd.dominant] || '均衡';
  bdSummaryEl.innerHTML = `
    <div>构筑：${bd.name || '未命名'}</div>
    <div>灵根：${bd.linggen || '-'}</div>
    <div>主导元素：${bd.dominant || '-'}</div>
    <div>流派：${styleLabel}</div>
  `;
  fightSummaryEl.innerHTML = `
    <div>Boss：${fight.boss?.name || '-'}</div>
    <div>胜负：${fight.win ? '胜利' : '失败'}</div>
    <div>击杀：${fight.timeToKill ? formatNumber(fight.timeToKill) + 's' : '-'}</div>
    <div>存活：${fight.timeSurvive ? formatNumber(fight.timeSurvive) + 's' : '-'}</div>
  `;
  resultSummaryEl.innerHTML = `
    <div>DPS：${formatNumber(result.totals?.dps)}</div>
    <div>EHP：${formatNumber(result.totals?.ehp)}</div>
    <div>续航：${formatNumber(result.totals?.sustain)}</div>
    <div>稳定：${formatNumber(result.totals?.stability)}</div>
  `;

  const elementCounts = bd.elementCounts || {};
  const elementLine = Object.keys(elementCounts)
    .map((k) => `${k}:${elementCounts[k]}`)
    .join(' / ');
  const infoLines = [
    `灵根：${bd.linggen || '-'}`,
    `主导元素：${bd.dominant || '-'}`,
    `流派倾向：${styleLabel}`,
    `元素占比：${elementLine || '-'}`,
  ];
  infoLines.forEach((line) => {
    const li = document.createElement('li');
    li.textContent = line;
    bdInfoEl.appendChild(li);
  });

  const stoneCats = bd.stones || {};
  Object.keys(stoneCats).forEach((cat) => {
    const list = stoneCats[cat] || [];
    const header = document.createElement('li');
    header.textContent = `${cat} (${list.length})`;
    header.style.color = '#9ec9ff';
    stoneInfoEl.appendChild(header);
    list.forEach((item) => {
      const li = document.createElement('li');
      li.textContent = `${item.name} · ${item.element} · ${item.slotType} · ${item.trigram} · ${item.slot}`;
      stoneInfoEl.appendChild(li);
    });
  });

  if (!events.length) {
    emptyEl.classList.remove('hidden');
    return;
  }
  emptyEl.classList.add('hidden');

  events.forEach((evt) => {
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
      <td>${evt.bossHp != null ? formatNumber(evt.bossHp) : '-'}</td>
      <td>${evt.playerHp != null ? formatNumber(evt.playerHp) : '-'}</td>
    `;
    tableBody.appendChild(row);
  });
}

document.getElementById('refresh-log').addEventListener('click', () => {
  render();
});

render();
