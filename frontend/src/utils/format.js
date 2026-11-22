const shortDate = new Intl.DateTimeFormat('zh-CN', {timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23'});
const fullDate = new Intl.DateTimeFormat('zh-CN', {timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'});

export const time = (value, full = false) => value ? (full ? fullDate : shortDate).format(new Date(value)) : '—';
export const number = (value, digits = 3) => value == null ? '—' : Number(value).toFixed(digits);
export const toStamp = local => `${local}:00+08:00`;
export const h = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));

export function shanghaiInput(stamp) {
  return new Date(new Date(stamp).getTime() + 8 * 3600000).toISOString().slice(0, 16);
}
