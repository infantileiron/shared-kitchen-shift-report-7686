import {api} from '../api/client.js';
import {badge, empty, field, formStatus, options, pageHead, table} from '../components/common/views.js';
import {Mailboxes, ShiftKinds} from '../constants/enums.js';
import {bindForm} from '../hooks/events.js';
import {state} from '../stores/state.js';
import {h, number} from '../utils/format.js';

export async function rules(render, notice = '') {
  const [all, stations] = await Promise.all([api.rules(), api.stations()]);
  Object.assign(state, {rules: all, stations});
  const rows = all.map(rule => [
    `<strong>${h(rule.station_label)}</strong><small class="cell-sub">${h(rule.station_code)} · ${h(ShiftKinds[rule.shift_kind])}</small>`,
    `V${rule.version}`, `<span class="mono">${number(rule.threshold)}</span>`, `${rule.consecutive} 格`,
    `${rule.cooldown_minutes} 分钟`, `＋${rule.delay_minutes} 分钟`, badge(rule.current ? '现行' : '历史', rule.current ? 'live' : 'muted'),
  ]);
  const stationsById = Object.fromEntries(stations.map(s => [s.id, `${s.code} · ${s.label}`]));
  const canPublish = state.account.role === 'manager';
  const controls = canPublish ? `<section class="panel"><div class="panel-head"><div><h2>发布新版本</h2><p>新班次使用最新版本。已登记的班次沿用原规则。</p></div></div><form id="rule-form" class="side-form">
      ${field('灶台', `<select name="station_id">${options(stationsById)}</select>`)}
      ${field('班别', `<select name="shift_kind">${options(ShiftKinds)}</select>`)}
      ${field('强度阈值（m³ / 炉时）', '<input type="number" name="threshold" step="0.001" min="0.001" max="999999" value="1.500" required>')}
      ${field('连续超限（格）', '<input type="number" name="consecutive" min="2" max="12" value="2" required>')}
      ${field('提醒冷却（分钟）', '<input type="number" name="cooldown_minutes" min="0" max="1440" value="45" required>')}
      ${field('收档后投递（分钟）', '<input type="number" name="delay_minutes" min="0" max="120" value="8" required>')}
      ${field('模拟收件箱', `<select name="mailbox">${options(Mailboxes)}</select>`)}
      <button class="primary" type="submit">发布规则</button>${formStatus()}</form></section>` : '';
  if (!render(`${pageHead('02 / 规则配置', '分发规则', '按灶台与班别设定连续超限、提醒冷却和投递时刻。')}
    ${notice ? `<p class="notice" role="status">${h(notice)}</p>` : ''}<div class="split"><section class="panel"><div class="panel-head"><div><h2>版本账</h2><p>燃气强度以 m³ / 炉时计，收档后按计划发送。</p></div><span class="index">${all.length} 项</span></div>
    ${rows.length ? table(['灶台 / 班别','版本','阈值','连超','冷却','收档后','版本状态'],rows) : empty('尚无规则','厨房经理可发布第一版规则。')}
    </section>${controls}</div>`)) return;
  bindForm(document.querySelector('#rule-form'), async data => {
    const result = await api.publish({...data, station_id: Number(data.station_id), consecutive: Number(data.consecutive),
      cooldown_minutes: Number(data.cooldown_minutes), delay_minutes: Number(data.delay_minutes)});
    await rules(render, `V${result.version} 已发布。`);
  });
}
