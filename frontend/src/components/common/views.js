import {h} from '../../utils/format.js';

export const badge = (text, tone = 'muted') => `<span class="mark ${h(tone)}"><i></i>${h(text)}</span>`;
export const empty = (title, message) => `<div class="empty"><strong>${h(title)}</strong><p>${h(message)}</p></div>`;
export const pageHead = (line, title, subtitle, action = '') => `<header class="page-head"><div><p class="section-tag">${h(line)}</p><h1>${h(title)}</h1><p>${h(subtitle)}</p></div>${action}</header>`;
export const table = (head, rows) => `<div class="table-wrap"><table><thead><tr>${head.map(item => `<th scope="col">${h(item)}</th>`).join('')}</tr></thead><tbody>${rows.map(cells => `<tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
export const options = (items) => Object.entries(items).map(([value,label]) => `<option value="${h(value)}">${h(label)}</option>`).join('');
export const field = (label, input) => `<label>${h(label)}${input}</label>`;
export const formStatus = () => `<p class="form-note" role="status"></p>`;
