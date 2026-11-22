import {api} from '../api/client.js';
import {instrument} from '../components/common/instrument.js';
import {badge, empty, field, formStatus, options, pageHead, table} from '../components/common/views.js';
import {Outcomes, ShiftKinds} from '../constants/enums.js';
import {bindForm} from '../hooks/events.js';
import {state} from '../stores/state.js';
import {h, number, shanghaiInput, time, toStamp} from '../utils/format.js';

export async function ledger(render, preferred) {
  const [stations, shifts] = await Promise.all([api.stations(), api.shifts()]);
  Object.assign(state, {stations, shifts});
  const selected = shifts.find(s => s.id === (preferred ?? state.shiftId)) ?? shifts.find(s => s.outcome === 'alerted') ?? shifts[0];
  state.shiftId = selected?.id ?? null;
  const [detail, report] = await Promise.all([selected ? api.shift(selected.id) : null, selected?.report_id ? api.receipt(selected.report_id) : null]);
  const writes = state.account.role !== 'observer';
  const current = detail?.shift;
  const rows = shifts.map(row => [
    `<button class="text-button mono" data-shift="${row.id}" aria-pressed="${row.id === selected?.id}">${h(row.code)}</button>`,
    h(row.station_label), h(ShiftKinds[row.shift_kind]), `<span class="mono">${time(row.ends_at)}</span>`,
    `<span class="mono">${row.reading_count}</span>`,
    row.outcome ? badge(Outcomes[row.outcome], row.outcome === 'alerted' ? 'warm' : 'muted') : badge('待投递', 'live'),
  ]);
  const editable = writes && current && !current.evaluated_at && Date.parse(current.due_at) > Date.now();
  const readingTable = detail?.readings.length ? table(['时格起点', '用气量 m³', '炉分钟'], detail.readings.map(row => [
    `<span class="mono">${time(row.sampled_at)}</span>`, number(row.gas_m3), row.burner_minutes,
  ])) : empty('尚无读数', '时格结束后可录入气量和炉分钟。');
  const stationOptions = options(Object.fromEntries(stations.map(s => [s.id, `${s.code} · ${s.label}`])));
  const station = stations.find(s => s.id === current?.station_id);
  const active = shifts.filter(s => !s.evaluated_at).length;
  const frozen = shifts.find(s => s.outcome === 'alerted');
  const summary = current?.station_label ? `<article class="panel focus"><div class="panel-head"><div><p class="section-tag">${h(station.code)} / ${h(station.area)}</p><h2>${h(current.station_label)}</h2></div>${badge(ShiftKinds[current.shift_kind])}</div>
     ${instrument(report?.evidence.intensity, current.threshold, report ? '班次加权燃气强度' : '班报将在投递后生成')}
     <dl class="property"><div><dt>计划投递</dt><dd>${time(current.due_at)}</dd></div><div><dt>已绑定规则</dt><dd>V${current.rule_version} · 连超 ${current.consecutive} 格</dd></div></dl>
     ${report ? `<a class="soft" href="#/inbox/${report.id}">查看冻结班报 <span>↗</span></a>` : '<a class="soft" href="#/queue">查看待发队列 <span>↗</span></a>'}</article>` : '';
  const create = writes ? `<details class="panel fold" id="create-shift" ${!current ? 'open' : ''}><summary>登记灶台班次</summary><form id="shift-form" class="grid-form">
    ${field('班次编号', '<input name="code" placeholder="HL-1121-E01" pattern="[A-Z0-9][A-Z0-9\\-]{2,39}" required>')}
    ${field('灶台', `<select name="station_id">${stationOptions}</select>`)}
    ${field('班别', `<select name="shift_kind">${options(ShiftKinds)}</select>`)}
    ${field('开班时间（上海）', '<input type="datetime-local" name="starts_at" required>')}
    ${field('收档时间（上海）', '<input type="datetime-local" name="ends_at" required>')}
    <button class="primary" type="submit">登记并排程</button>${formStatus()}</form></details>` : '';
  const entry = editable ? `<form id="reading-form" class="grid-form reading-form">
    ${field('时格起点（上海）', `<input type="datetime-local" name="sampled_at" value="${h(shanghaiInput(current.starts_at))}" required>`)}
    ${field('用气量（m³）', '<input type="number" name="gas_m3" min="0" max="9999999" step="0.001" required>')}
    ${field('炉分钟', '<input type="number" name="burner_minutes" min="0" max="180" step="1" required>')}
    <button class="primary" type="submit">记入用气账</button>${formStatus()}</form>` : '';
  if (!render(`${pageHead('01 / 用气交接', '灶台用气账', '按 15 分钟时格登记表差和炉分钟，交接时查看已冻结的班报。', writes ? '<button id="start-shift" class="primary">＋ 登记班次</button>' : '')}
    <section class="strip"><div><label>纳入巡查</label><strong>${stations.length}<small> 台灶</small></strong></div><div><label>计划投递</label><strong>${active}<small> 个班次</small></strong></div><div><label>最近偏差提醒</label><strong class="strip-code">${frozen ? h(frozen.code) : '暂无'}</strong></div></section>
    <div class="split"><div class="stack"><section class="panel"><div class="panel-head"><div><h2>班次台账</h2><p>点击班次编号查看该班的读数与规则。</p></div><span class="index">${shifts.length} 班</span></div>
    ${rows.length ? table(['班次编号','灶台','班别','收档','读数','判定'], rows) : empty('尚无班次','发布对应班别规则后登记一个班次。')}</section>${create}
    ${detail ? `<section class="panel" id="readings"><div class="panel-head"><div><h2>测量时格</h2><p class="mono">${h(current.code)} · ${time(current.starts_at)} → ${time(current.ends_at)}</p></div>${current.evaluated_at ? badge('已冻结') : ''}</div>${readingTable}${entry}</section>` : ''}</div>${summary}</div>`)) return;
  document.querySelectorAll('[data-shift]').forEach(button => button.onclick = () => { location.hash = `/ledger/${button.dataset.shift}`; });
  document.querySelector('#start-shift')?.addEventListener('click', () => {
    const form = document.querySelector('#create-shift'); form.open = true; form.scrollIntoView({block:'center'}); form.querySelector('input').focus();
  });
  bindForm(document.querySelector('#shift-form'), async data => {
    const created = await api.newShift({...data, station_id: Number(data.station_id), starts_at: toStamp(data.starts_at), ends_at: toStamp(data.ends_at)});
    location.hash = `/ledger/${created.id}`;
  });
  bindForm(document.querySelector('#reading-form'), async data => {
    await api.reading(current.id, {sampled_at: toStamp(data.sampled_at), gas_m3: data.gas_m3, burner_minutes: Number(data.burner_minutes)});
    await ledger(render, current.id);
    document.querySelector('#readings')?.scrollIntoView({block:'nearest'});
  });
}
