const button = document.querySelector('#language');
const copyFeedback = document.querySelector('#copy-feedback');
const fallback = document.querySelector('#copy-fallback');
const result = document.querySelector('#practice-result');
let lastCopyButton;
let feedbackTimer;
let practiceState = '';
const copy = {
  ja: {copied: 'コピーしました', empty: '練習メモを入力してください。', done: '入力とクリックを確認しました。外部送信はしていません。', reset: '練習フォームをリセットしました。'},
  en: {copied: 'Copied', empty: 'Enter a practice note first.', done: 'Input and click confirmed. Nothing was sent externally.', reset: 'Practice form reset.'},
};
const language = () => document.documentElement.lang;
function setLanguage(lang) {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-ja][data-en]').forEach(el => { el.innerHTML = el.dataset[lang]; });
  document.title = lang === 'ja' ? '先手ブラウザ — 今開いているページから、一緒に。' : 'Sente Browser — Work from the tab you already have open.';
  button.textContent = lang === 'ja' ? 'EN' : '日本語';
  button.setAttribute('aria-label', lang === 'ja' ? 'Read in English' : '日本語で読む');
  document.querySelectorAll('[data-aria-ja][data-aria-en]').forEach(el => el.setAttribute('aria-label', el.getAttribute(`data-aria-${lang}`)));
  document.querySelector('meta[name="description"]').content = lang === 'ja' ? '共有したChromeタブを先手が確認・入力・クリック。Mac向け拡張の導入手順、実操作動画、送信なしの練習フォーム。' : 'Let Sente read, fill and click the Chrome tab you share. Mac setup guide, real demo video and a local practice form.';
  document.querySelectorAll('a[href="privacy.html"], a[href^="privacy.html?"]').forEach(el => { el.href = `privacy.html?lang=${lang}${lang === 'ja' ? '#ja' : ''}`; });
  if (practiceState) result.textContent = copy[lang][practiceState];
  const url = new URL(location.href); url.searchParams.set('lang', lang); history.replaceState(null, '', url);
}
button.addEventListener('click', () => setLanguage(document.documentElement.lang === 'ja' ? 'en' : 'ja'));
setLanguage(new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : new URLSearchParams(location.search).get('lang') === 'ja' ? 'ja' : navigator.language.startsWith('ja') ? 'ja' : 'en');

const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
document.querySelector('#device-note').hidden = !mobile && /Mac/i.test(navigator.platform);
document.querySelectorAll('[data-copy]').forEach(control => {
  control.addEventListener('click', async () => {
    const target = control.dataset.copy;
    const text = target === 'page-url' ? `https://yukihamada.github.io/sente-browser/?lang=${language()}` : document.getElementById(target).textContent.trim();
    lastCopyButton = control;
    try {
      await navigator.clipboard.writeText(text);
      copyFeedback.textContent = copy[language()].copied;
      clearTimeout(feedbackTimer);
      feedbackTimer = setTimeout(() => { copyFeedback.textContent = ''; }, 3000);
    } catch {
      fallback.hidden = false;
      const field = document.querySelector('#fallback-text');
      field.value = text;
      field.focus();
      field.select();
    }
  });
});
function closeFallback() {
  fallback.hidden = true;
  lastCopyButton?.focus();
}
document.querySelector('#close-fallback').addEventListener('click', closeFallback);
fallback.addEventListener('keydown', event => { if (event.key === 'Escape') closeFallback(); });
document.querySelector('#practice-form').addEventListener('submit', event => {
  event.preventDefault();
  const field = document.querySelector('#practice-note');
  practiceState = field.value.trim() ? 'done' : 'empty';
  field.setAttribute('aria-invalid', String(practiceState === 'empty'));
  result.textContent = copy[language()][practiceState];
  if (practiceState === 'empty') field.focus();
});
document.querySelector('#practice-form').addEventListener('reset', () => {
  practiceState = 'reset';
  document.querySelector('#practice-note').removeAttribute('aria-invalid');
  result.textContent = copy[language()].reset;
});
