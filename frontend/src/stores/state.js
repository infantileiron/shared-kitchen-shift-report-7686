/** @type {{token: string|null, account: import('../types/records.js').Account|null, stations: import('../types/records.js').Station[], shifts: import('../types/records.js').Shift[], rules: object[], mailbox: string, shiftId: number|null, queue: object|null, inbox: object[]}} */
export const state = {token: sessionStorage.getItem('hob-token'), account: null, stations: [], shifts: [], rules: [], mailbox: '', shiftId: null, queue: null, inbox: []};

export function setSession(session) {
  state.token = session?.token ?? null;
  state.account = session?.account ?? null;
  if (state.token) sessionStorage.setItem('hob-token', state.token);
  else sessionStorage.removeItem('hob-token');
  state.mailbox = '';
  state.shiftId = null;
}
