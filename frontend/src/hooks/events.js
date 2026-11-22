export function bindForm(form, submit) {
  if (!form) return;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type=submit]');
    const note = form.querySelector('.form-note');
    button.disabled = true;
    note.textContent = '';
    try {
      await submit(Object.fromEntries(new FormData(form)));
    } catch (error) {
      note.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

export function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement('a'), {href: url, download: filename});
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
