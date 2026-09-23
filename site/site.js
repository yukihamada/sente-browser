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
const platform = document.querySelector('#platform');
const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
platform.value = /Win/i.test(navigator.platform) ? 'windows' : /Linux/i.test(navigator.platform) && !mobile ? 'linux' : 'macos';
const platforms = {
  macos: {command: 'python3 install.py', path: '~/Library/Application Support/Sente Browser/extension', ja: 'ZIPを展開。ターミナルで cd と半角スペースを入力し、展開したフォルダをドラッグしてReturn。その後、次を実行します。', en: 'Extract the ZIP. In Terminal, type cd and a space, drag the extracted folder into the window and press Return. Then run:'},
  windows: {command: 'py -3 install.py', path: '%LOCALAPPDATA%\\Sente Browser\\extension', ja: 'ZIPを右クリックして「すべて展開」。展開先のinstall.pyがあるフォルダを開き、エクスプローラーのアドレス欄に powershell と入力してEnter。次を実行します。', en: 'Right-click the ZIP and choose Extract All. Open the extracted folder containing install.py. Type powershell in the Explorer address bar and press Enter. Then run:'},
  linux: {command: 'python3 install.py', path: '~/.local/share/sente-browser/extension', ja: 'ZIPを展開し、install.pyがあるフォルダでターミナルを開いて次を実行します。通常のChrome/Chromiumが対象です（Snap/Flatpak版は非対応）。', en: 'Extract the ZIP, open a terminal in the folder containing install.py, then run the command below. Use a regular Chrome/Chromium installation, not Snap or Flatpak.'},
};
function setPlatform() {
  const config = platforms[platform.value];
  document.querySelector('#install-command').textContent = config.command;
  document.querySelector('#extension-path').textContent = config.path;
  document.querySelector('#platform-instructions').textContent = config[language()];
  const request = document.querySelector('#ai-request');
  request.textContent = request.dataset[language()];
  if (platform.value === 'windows') {
    request.textContent = request.textContent.replace('~/.local/share/sente-browser/cli.py', '%LOCALAPPDATA%\\Sente Browser\\cli.py').replace('python3', 'py -3');
    request.textContent += language() === 'ja' ? ' Windows PowerShellで実行例: py -3 "$env:LOCALAPPDATA\\Sente Browser\\cli.py" tabs' : ' Windows PowerShell example: py -3 "$env:LOCALAPPDATA\\Sente Browser\\cli.py" tabs';
  }
}
platform.addEventListener('change', setPlatform);
function setLanguage(lang) {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-ja][data-en]').forEach(el => { el.innerHTML = el.dataset[lang]; });
  // Keep existing versioned setup and release links aligned with the current package.
  document.querySelectorAll('a[href*="/sente-browser/releases/"]').forEach(el => {
    el.href = el.href.replaceAll('0.3.0', '0.3.1');
    if (el.classList.contains('download')) el.textContent = lang === 'ja' ? 'v0.3.1をダウンロード · 3 OS共通ZIP' : 'Download v0.3.1 · ZIP for all 3 OSes';
  });
  document.title = lang === 'ja' ? '先手ブラウザ — 今開いているページから、一緒に。' : 'Sente Browser — Work from the tab you already have open.';
  button.textContent = lang === 'ja' ? 'EN' : '日本語';
  button.setAttribute('aria-label', lang === 'ja' ? 'Read in English' : '日本語で読む');
  document.querySelectorAll('[data-aria-ja][data-aria-en]').forEach(el => el.setAttribute('aria-label', el.getAttribute(`data-aria-${lang}`)));
  document.querySelector('meta[name="description"]').content = lang === 'ja' ? '共有したChromeタブを先手が確認・入力・クリック。Windows・macOS・Linuxの導入手順、実操作動画、練習フォーム。' : 'Let Sente read, fill and click the Chrome tab you share. Windows, macOS and Linux setup, real demo video and a local practice form.';
  document.querySelectorAll('a[href="privacy.html"], a[href^="privacy.html?"]').forEach(el => { el.href = `privacy.html?lang=${lang}${lang === 'ja' ? '#ja' : ''}`; });
  if (practiceState) result.textContent = copy[lang][practiceState];
  setPlatform();
  const url = new URL(location.href); url.searchParams.set('lang', lang); history.replaceState(null, '', url);
}
button.addEventListener('click', () => setLanguage(document.documentElement.lang === 'ja' ? 'en' : 'ja'));
setLanguage(new URLSearchParams(location.search).get('lang') === 'en' ? 'en' : new URLSearchParams(location.search).get('lang') === 'ja' ? 'ja' : navigator.language.startsWith('ja') ? 'ja' : 'en');

document.querySelector('#device-note').hidden = !mobile && !/CrOS/i.test(navigator.userAgent);
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
