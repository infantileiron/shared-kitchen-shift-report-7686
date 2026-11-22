import {api} from './api/client.js';
import {empty} from './components/common/views.js';
import {Roles} from './constants/enums.js';
import {inbox, receipt} from './pages/inbox.js';
import {ledger} from './pages/ledger.js';
import {queue} from './pages/queue.js';
import {rules} from './pages/rules.js';
import {brand, signIn} from './pages/session.js';
import {locationView, navigation} from './router/routes.js';
import {setSession, state} from './stores/state.js';
import {h} from './utils/format.js';

const app = document.querySelector('#app');
let generation = 0;
let ticker;

function exit() {
  generation++;
  clearInterval(ticker);
  setSession(null);
  signIn(app, enter);
}

async function enter() {
  const {account} = state;
  app.innerHTML = `<div class="shell"><aside class="rail">${brand}<span class="rail-label">值班工作区</span><nav aria-label="工作区">${Object.entries(navigation).map(([key,[index,label]]) =>
    `<a href="#/${key}" data-nav="${key}"><span>${index}</span>${h(label)}<i></i></a>`).join('')}</nav><div class="rail-foot"><span class="rail-dot"></span><div>应用内模拟投递<small>时区　Asia/Shanghai</small></div></div></aside>
    <div class="workspace"><header class="topbar"><span class="workspace-label">燃气偏差班报</span><div class="user"><span class="initial">${h(account.display_name.slice(0,1))}</span><span><strong>${h(account.display_name)}</strong><small>${h(Roles[account.role])}</small></span><button id="logout" class="text-button">退出</button></div></header><main id="view" class="content" aria-live="polite"></main></div></div>`;
  document.querySelector('#logout').onclick = () => { history.replaceState(null, '', location.pathname); exit(); };
  await route();
}

async function route({scroll = true} = {}) {
  if (!state.account) return;
  const revision = ++generation;
  const {name, id} = locationView();
  clearInterval(ticker);
  const view = document.querySelector('#view');
  const render = template => {
    if (revision !== generation) return false;
    view.innerHTML = template;
    return true;
  };
  document.querySelectorAll('[data-nav]').forEach(link => {
    if (link.dataset.nav === name) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  if (scroll) window.scrollTo(0, 0);
  try {
    if (name === 'rules') await rules(render);
    else if (name === 'queue') await queue(render);
    else if (name === 'inbox' && id) await receipt(render, id);
    else if (name === 'inbox') await inbox(render);
    else await ledger(render, id);
    if (generation === revision && name === 'queue') ticker = setInterval(() => route({scroll:false}), 3000);
  } catch (error) {
    if (revision !== generation) return;
    if (error.status === 401) { exit(); return; }
    render(`${empty('无法载入工作区', error.message)}<button class="neutral" id="retry">重试</button>`);
    document.querySelector('#retry').onclick = () => route();
  }
}

window.addEventListener('hashchange', () => route());
window.addEventListener('refresh-view', () => route({scroll:false}));
if (state.token) {
  try { state.account = await api.profile(); await enter(); } catch { exit(); }
} else exit();
