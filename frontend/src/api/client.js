import {state} from '../stores/state.js';

async function request(path, {body, download = false} = {}) {
  const headers = state.token ? {Authorization: `Bearer ${state.token}`} : {};
  if (body) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {method: body ? 'POST' : 'GET', headers, body: body && JSON.stringify(body)});
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const detail = typeof error.detail === 'string' ? error.detail : '请检查表单数值、时间和必填项。';
    throw Object.assign(new Error(detail), {status: response.status});
  }
  return download ? response.blob() : response.json();
}

export const api = {
  login: body => request('/session', {body}), profile: () => request('/session'),
  stations: () => request('/stations'), shifts: () => request('/shifts'),
  shift: id => request(`/shifts/${id}`), newShift: body => request('/shifts', {body}),
  reading: (id, body) => request(`/shifts/${id}/readings`, {body}),
  backfill: (id, body) => request(`/shifts/${id}/backfill`, {body}),
  rules: () => request('/rules'), publish: body => request('/rules', {body}), queue: () => request('/queue'),
  inbox: mailbox => request(`/inbox${mailbox ? `?mailbox=${encodeURIComponent(mailbox)}` : ''}`),
  revisions: mailbox => request(`/reminder-revisions${mailbox ? `?mailbox=${encodeURIComponent(mailbox)}` : ''}`),
  receipt: id => request(`/inbox/${id}`), export: id => request(`/inbox/${id}/export.csv`, {download: true}),
};
