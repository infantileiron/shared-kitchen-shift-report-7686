export const navigation = {ledger: ['01', '用气账'], rules: ['02', '分发规则'], queue: ['03', '待发队列'], inbox: ['04', '模拟收件箱']};

export function locationView() {
  const [name, id] = location.hash.replace(/^#\/?/, '').split('/');
  return {name: Object.hasOwn(navigation, name) ? name : 'ledger', id: /^\d+$/.test(id) ? Number(id) : null};
}
