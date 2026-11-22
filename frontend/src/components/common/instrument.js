import {h, number} from '../../utils/format.js';

export function instrument(reading, threshold, label) {
  const valid = reading != null;
  const sweep = valid ? (Math.min(Number(reading) / (Number(threshold) * 1.5), 1) * 270) : 0;
  const above = valid && Number(reading) > Number(threshold);
  return `<figure class="instrument ${above ? 'hot' : ''}">
    <figcaption>${h(label)}</figcaption>
    <div class="dial" style="--sweep:${sweep}deg"><div class="dial-core"><strong>${number(reading)}</strong><small>m³ / 炉时</small></div></div>
    <div class="scale"><span>0</span><span>参考线 ${number(threshold)}</span><span>${number(Number(threshold)*1.5)}</span></div>
  </figure>`;
}
