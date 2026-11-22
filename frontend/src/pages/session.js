import {api} from '../api/client.js';
import {field, formStatus} from '../components/common/views.js';
import {bindForm} from '../hooks/events.js';
import {setSession} from '../stores/state.js';

export const brand = `<div class="brand"><span class="emblem" aria-hidden="true"><b></b><b></b><b></b></span><span><strong>烘邻共享灶</strong><small>厨房巡查台</small></span></div>`;

export function signIn(target, enter) {
  target.innerHTML = `<main class="login"><section class="login-visual">${brand}<div class="login-caption"><div class="tick-dial" aria-hidden="true"><span></span><i></i></div><h1>燃气偏差班报</h1><p>归一炉时、核对连续超限、按班送达交接记录。</p></div><footer>烘邻社区厨房　/　用气交接工作台</footer></section>
    <section class="login-panel"><form id="login"><p class="section-tag">厨房值班交接</p><h2>登录巡查台</h2><p>使用你的交接账号查看灶台记录和投递回执。</p>
    ${field('交接邮箱', '<input type="email" name="email" autocomplete="username" placeholder="recorder@demo.local" required>')}
    ${field('密码', '<input name="password" type="password" autocomplete="current-password" required>')}
    <button class="primary" type="submit">进入巡查台</button>${formStatus()}</form>
    <aside class="demo"><span>模拟交接账号</span><div><button data-demo="manager">经理</button><button data-demo="recorder">记录员</button><button data-demo="observer">观察员</button></div></aside></section></main>`;
  const form = target.querySelector('form');
  target.querySelectorAll('[data-demo]').forEach(button => button.onclick = () => {
    form.elements.email.value = `${button.dataset.demo}@demo.local`;
    form.elements.password.value = 'HobShift#21';
  });
  bindForm(form, async body => { setSession(await api.login(body)); await enter(); });
}
