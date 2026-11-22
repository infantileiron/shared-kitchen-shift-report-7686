import {api} from '../api/client.js';
import {badge, empty, pageHead, table} from '../components/common/views.js';
import {Mailboxes, Outcomes, ShiftKinds} from '../constants/enums.js';
import {state} from '../stores/state.js';
import {h, time} from '../utils/format.js';

export async function queue(render) {
  const info = await api.queue();
  state.queue = info;
  const waiting = info.windows.filter(row => !row.evaluated_at);
  const archive = info.windows.filter(row => row.evaluated_at);
  const next = waiting[0];
  const refresh = '<button type="button" class="neutral" id="refresh">刷新队列</button>';
  if (!render(`${pageHead('03 / 定时分发', '待发队列', 'worker 按计划时刻取件，并将班报直接写入应用内收件箱。', refresh)}
    <section class="strip"><div><label>尚待投递</label><strong>${waiting.length}<small> 班</small></strong></div><div><label>已完成</label><strong>${archive.length}<small> 班</small></strong></div>
    <div><label>调度状态</label><strong class="strip-code">${info.scheduler ? badge('轮询中', 'live') : badge('心跳超时', 'warm')}</strong><small>最近扫描 ${time(info.scheduler?.checked_at, true)}</small></div></section>
    <div class="split"><div class="stack"><section class="panel"><div class="panel-head"><div><h2>待到点</h2><p>到点后冻结用气账，班报按其绑定版本生成。</p></div></div>
    ${waiting.length ? table(['班次','灶台 / 班别','计划投递','规则','收件箱','状态'], waiting.map(row => [
      `<a class="mono" href="#/ledger/${row.id}">${h(row.code)}</a>`, h(`${row.station_label} · ${ShiftKinds[row.shift_kind]}`), `<span class="mono">${time(row.due_at, true)}</span>`,
      `V${row.rule_version}`, h(Mailboxes[row.mailbox]), badge(Date.parse(row.due_at) <= Date.now() ? '待取件' : '等候到点', 'live'),
    ])) : empty('暂无待发班次','台账登记班次后，会在此显示投递计划。')}</section>
    <section class="panel"><div class="panel-head"><div><h2>已完成班次</h2><p>打开班报查看 worker 冻结的证据。</p></div></div>
    ${archive.length ? table(['班次','已处理（上海）','判定','班报'], archive.map(row => [h(row.code), `<span class="mono">${time(row.evaluated_at, true)}</span>`,
      badge(Outcomes[row.outcome], row.outcome === 'alerted' ? 'warm' : 'muted'), `<a href="#/inbox/${row.report_id}">查看班报 ↗</a>`,
    ])) : empty('尚无已完成班次','第一个班次到点后，会显示完成状态。')}</section></div>
    <article class="panel focus"><div class="panel-head"><div><p class="section-tag">即将投递</p><h2>${next ? h(next.station_label) : '队列已清空'}</h2></div></div>
    ${next ? `<div class="next-time"><strong>${time(next.due_at)}</strong><span>${h(next.code)}</span></div><dl class="property"><div><dt>收件箱</dt><dd>${h(Mailboxes[next.mailbox])}</dd></div><div><dt>绑定规则</dt><dd>V${next.rule_version}</dd></div></dl>` : '<p>登记新班次后会显示下一份班报的计划。</p>'}
    <a class="soft" href="#/inbox">打开模拟收件箱 <span>↗</span></a></article></div>`)) return;
  document.querySelector('#refresh').onclick = () => window.dispatchEvent(new Event('refresh-view'));
}
