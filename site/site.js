const button = document.querySelector('#language');
function setLanguage(lang) {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-ja][data-en]').forEach(el => { el.innerHTML = el.dataset[lang]; });
  document.title = lang === 'ja' ? '先手ブラウザ — 今開いているページから、一緒に。' : 'Sente Browser — Work from the tab you already have open.';
  button.textContent = lang === 'ja' ? 'EN' : '日本語';
  const url = new URL(location.href); url.searchParams.set('lang', lang); history.replaceState(null, '', url);
}
button.addEventListener('click', () => setLanguage(document.documentElement.lang === 'ja' ? 'en' : 'ja'));
setLanguage(new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : new URLSearchParams(location.search).get('lang') === 'ja' ? 'ja' : navigator.language.startsWith('ja') ? 'ja' : 'en');
