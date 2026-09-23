const msg = (key, args) => chrome.i18n.getMessage(key, args);
document.documentElement.lang = chrome.i18n.getUILanguage();
document.title = msg("name");
for (const el of document.querySelectorAll("[data-i18n]")) el.textContent = msg(el.dataset.i18n);
const feedbackURL = new URL('https://teai.io/browser-feedback');
feedbackURL.searchParams.set('lang', chrome.i18n.getUILanguage().startsWith('ja') ? 'ja' : 'en');
feedbackURL.searchParams.set('version', chrome.runtime.getManifest().version);
document.querySelector('#feedback').href = feedbackURL.href;
async function refresh() {
  const state = await chrome.runtime.sendMessage({type: "status"});
  document.querySelector("#status").textContent = msg(state.connected ? "connected" : "disconnected");
  document.querySelector("#count").textContent = msg("shared", String(state.count));
  document.querySelector("#tabs").setAttribute("aria-label", msg("sharedTabs"));
  document.querySelector("#tabs").replaceChildren(...state.tabs.map((tab) => {
    const li = document.createElement("li");
    const title = document.createElement("span");
    title.textContent = tab.title || new URL(tab.url).hostname;
    title.title = new URL(tab.url).hostname;
    const revoke = document.createElement("button");
    revoke.className = "revoke"; revoke.textContent = msg("revoke");
    revoke.onclick = async () => {
      await chrome.runtime.sendMessage({type: "revoke", tabId: tab.tabId});
      await refresh();
    };
    li.append(title, revoke); return li;
  }));
  document.querySelector("#stop").disabled = !state.connected;
}
document.querySelector("#share").onclick = async () => {
  const button = document.querySelector("#share");
  button.disabled = true;
  document.querySelector("#error").textContent = "";
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const result = await chrome.runtime.sendMessage({type: "grant", tabId: tab?.id});
    if (!result.ok) document.querySelector("#error").textContent = msg(result.error || "grantFailed");
    await refresh();
  } catch { document.querySelector("#error").textContent = msg("grantFailed"); }
  finally { button.disabled = false; }
};
document.querySelector("#stop").onclick = async () => {
  await chrome.runtime.sendMessage({type: "stop"});
  await refresh();
};
refresh().catch(() => { document.querySelector("#error").textContent = msg("grantFailed"); });
