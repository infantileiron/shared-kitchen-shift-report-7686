import {api} from '../api/client.js';
import {instrument} from '../components/common/instrument.js';
import {badge, empty, options, pageHead, table} from '../components/common/views.js';
import {DeliveryKinds, Mailboxes, Outcomes, Reasons, ShiftKinds, States} from '../constants/enums.js';
import {download} from '../hooks/events.js';
import {state} from '../stores/state.js';
import {h, number, time} from '../utils/format.js';

function reason(row) {
  const detail = row.detail || {};
  const streak = detail.longest_streak ? `最长连超 ${detail.longest_streak.old} → ${detail.longest_streak.new} 格（门槛 ${detail.consecutive} 格）` : '';
  const boundary = detail.cooldown_until ? `冷却边界 ${time(detail.cooldown_until.old)} → ${time(detail.cooldown_until.new)}` : '';
  return `${h(Reasons[row.reason])}<small class="cell-sub">${h(row.reason === 'readings_backfilled' ? streak : boundary)}</small>`;
}

export async function inbox(render) {
  const [messages, reminder] = await Promise.all([api.inbox(state.mailbox), api.revisions(state.mailbox)]);
  state.inbox = messages;
  const filters = `<div class="mailbox-field"><label for="mailbox">收件箱</label><select id="mailbox">${options({'':'全部收件箱', ...Mailboxes})}</select></div>`;
  const changes = reminder.revisions;
  const notes = `${reminder.pending ? `<p class="form-note">补录重算进行中 ${reminder.pending} 项，算齐后在此展示提醒变化与原因。</p>` : ''}
    ${reminder.failed ? `<p class="form-note">${reminder.failed} 项重算未成功，可按原来源版本重新补录。</p>` : ''}`;
  const panel = (changes.length || reminder.pending || reminder.failed) ? `<section class="panel"><div class="panel-head"><div><h2>提醒变化</h2><p>补录已发班报后，按各班原规则和计划时刻重算并顺推冷却的结果，原回执不变。</p></div><span class="index">${changes.length} 项</span></div>
    ${notes}
    ${changes.length ? table(['班次','原判定','重算判定','原因','来源版本','算齐（上海）'], changes.map(row => [
      `<strong>${h(row.shift_code)}</strong><small class="cell-sub">${h(row.station_label)} · ${h(ShiftKinds[row.shift_kind])} · V${row.rule_version}</small>`,
      badge(Outcomes[row.previous_outcome], row.previous_outcome === 'alerted' ? 'warm' : 'muted'),
      badge(Outcomes[row.revised_outcome], row.revised_outcome === 'alerted' ? 'warm' : 'muted'),
      reason(row), `<span class="mono">V${row.source_version}</span>`, `<span class="mono">${time(row.finished_at, true)}</span>`,
    ])) : ''}</section>` : '';
  if (!render(`${pageHead('04 / 回执归档', '模拟收件箱', '查看已送达的班报和偏差提醒，按收件箱核对投递证据。', '<button id="refresh" class="neutral">刷新收件箱</button>')}
    ${panel}
    <section class="panel mail-list"><div class="panel-head"><div><h2>投递回执</h2><p>${messages.length} 条消息</p></div>${filters}</div>
    ${messages.length ? table(['主题','判定','收件箱','实际投递（上海）','回执'], messages.map(row => [
      `<a href="#/inbox/${row.id}"><strong>${h(row.station_label)} · ${h(DeliveryKinds[row.kind])}</strong></a><small class="cell-sub mono">${h(row.shift_code)} · ${h(ShiftKinds[row.shift_kind])} · V${row.rule_version}</small>`,
      badge(Outcomes[row.outcome], row.kind === 'alert' ? 'warm' : 'muted'), h(Mailboxes[row.mailbox]), `<span class="mono">${time(row.delivered_at, true)}</span>`,
      `<a aria-label="查看回执 ${row.id}" class="mono" href="#/inbox/${row.id}">#${row.id} ↗</a>`,
    ])) : empty('没有投递回执','班次到点后，班报会出现在绑定的收件箱。')}</section>`)) return;
  const filter = document.querySelector('#mailbox');
  filter.value = state.mailbox;
  filter.onchange = () => { state.mailbox = filter.value; window.dispatchEvent(new Event('refresh-view')); };
  document.querySelector('#refresh').onclick = () => window.dispatchEvent(new Event('refresh-view'));
}

export async function receipt(render, id) {
  const message = await api.receipt(id);
  const e = message.evidence;
  const rule = e.rule;
  if (!render(`<a class="breadcrumb" href="#/inbox">← 返回模拟收件箱</a>
    ${pageHead(`04 / ${Mailboxes[message.mailbox]} / 回执 #${id}`, `${message.station_label} · ${DeliveryKinds[message.kind]}`, `${message.shift_code} · ${ShiftKinds[message.shift_kind]} · ${time(message.starts_at)} 至 ${time(message.ends_at)}`, '<button id="export" class="primary">导出证据 CSV ↓</button>')}
    <section class="strip"><div><label>投递判定</label><strong class="strip-code">${badge(Outcomes[e.outcome], e.outcome === 'alerted' ? 'warm' : 'muted')}</strong></div><div><label>最长连续超限</label><strong>${e.longest_streak}<small> / ${rule.consecutive} 格</small></strong></div>
    <div><label>实际投递（上海）</label><strong class="strip-code">${time(message.delivered_at, true)}</strong><small>计划 ${time(message.due_at, true)}</small></div></section>
    <div class="split"><section class="panel"><div class="panel-head"><div><h2>时格证据</h2><p>${e.valid_slots} 格有炉时 · ${e.missing_slots} 格未报 · ${e.idle_slots} 格停炉</p></div><span class="index">规则 V${rule.rule_version}</span></div>
    ${table(['时格起点','气量 m³','炉分钟','m³ / 炉时','读数判定','连超'], e.slots.map(slot => [
      `<span class="mono">${time(slot.sampled_at)}</span>`, number(slot.gas_m3), slot.burner_minutes ?? '—',
      `<strong class="mono">${number(slot.intensity)}</strong>`, badge(States[slot.state], slot.state === 'over' ? 'warm' : 'muted'), slot.streak,
    ]))}<div class="panel-footer">当格强度等于阈值、停炉或缺测时，连超计数归零。</div></section>
    <aside class="panel focus"><div class="panel-head"><div><p class="section-tag">${h(e.station_code)} / 已冻结</p><h2>班次燃气强度</h2></div></div>
    ${instrument(e.intensity, rule.threshold, `${number(e.gas_m3)} m³ · ${e.burner_minutes} 炉分钟`)}
    <dl class="property"><div><dt>提醒冷却</dt><dd>${rule.cooldown_minutes} 分钟</dd></div><div><dt>上次提醒计划</dt><dd>${time(e.previous_alert_due)}</dd></div><div><dt>冷却边界</dt><dd>${time(e.cooldown_until)}</dd></div></dl></aside></div>
    <p id="export-error" role="status" class="form-note"></p>`)) return;
  document.querySelector('#export').onclick = async () => {
    try { download(await api.export(id), `receipt-${id}.csv`); }
    catch (error) { document.querySelector('#export-error').textContent = error.message; }
  };
}
