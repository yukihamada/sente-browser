const HOST = "io.teai.sente_browser";
let port;
let connecting;
let grantEpoch = 0;
// Grants are session-local: a service-worker restart revokes them too.
const grants = new Map();
const allowedURL = (url) => /^https?:\/\//.test(url || "") &&
  !/^https:\/\/(chromewebstore\.google\.com|chrome\.google\.com\/webstore)(\/|$)/.test(url);

function badge() {
  chrome.action.setBadgeText({text: grants.size ? String(grants.size) : ""});
  chrome.action.setBadgeBackgroundColor({color: "#52812e"});
}
chrome.tabs.onRemoved.addListener((id) => { grantEpoch++; grants.delete(id); badge(); });
chrome.tabs.onUpdated.addListener((id, change) => {
  if (change.status === "loading" || change.url) { grantEpoch++; grants.delete(id); badge(); }
});
async function dispatch(request) {
  const {op, tabId, ...args} = request;
  if (op === "tabs") {
    const tabs = [];
    for (const [id, grant] of grants) {
      try {
        const tab = await chrome.tabs.get(id);
        if (grants.get(id) !== grant) continue;
        if (tab.url === grant.url) tabs.push({tabId: id, title: tab.title, url: tab.url});
        else grants.delete(id);
      } catch { grants.delete(id); }
    }
    badge();
    return {tabs};
  }
  if (!["read", "click", "fill", "scroll"].includes(op)) throw new Error("unsupported_operation");
  const grant = grants.get(tabId);
  if (!grant) throw new Error("tab_not_shared");
  const tab = await chrome.tabs.get(tabId);
  if (grants.get(tabId) !== grant) throw new Error("tab_not_shared");
  if (!allowedURL(tab.url) || tab.url !== grant.url) {
    grants.delete(tabId); badge(); throw new Error("tab_not_shared");
  }
  const reply = await chrome.tabs.sendMessage(tabId, {type: "sente-action", op, ...args}, {documentId: grant.documentId});
  if (grants.get(tabId) !== grant) throw new Error("sharing_ended_result_unknown_do_not_retry_mutations");
  if (!reply?.ok) throw new Error(reply?.error || "page_unavailable");
  return reply.result;
}
async function connect() {
  if (port) return;
  if (connecting) return connecting;
  connecting = openConnection();
  try { await connecting; } finally { connecting = undefined; }
}
async function openConnection() {
  const candidate = chrome.runtime.connectNative(HOST);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => { candidate.disconnect(); reject(new Error("install")); }, 5000);
    candidate.onMessage.addListener((message) => {
      if (message.type === "ready") { clearTimeout(timer); port = candidate; resolve(); return; }
      if (message.type !== "request") return;
      dispatch(message.request).then(
        (result) => ({id: message.id, ok: true, result}),
        (error) => ({id: message.id, ok: false, error: error.message}),
      ).then((reply) => { if (port === candidate) candidate.postMessage(reply); });
    });
    candidate.onDisconnect.addListener(() => {
      const error = chrome.runtime.lastError;
      if (error) console.warn("Sente native host:", error.message);
      clearTimeout(timer);
      if (port === candidate) { grantEpoch++; port = undefined; grants.clear(); badge(); }
      reject(new Error(error ? "install" : "disconnected"));
    });
  });
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  // Only extension popup pages can grant/revoke. Content scripts never gain this authority.
  if (sender.id !== chrome.runtime.id || sender.url !== chrome.runtime.getURL("popup.html") ||
      sender.origin !== `chrome-extension://${chrome.runtime.id}`) return;
  (async () => {
    if (message.type === "status") {
      const {tabs} = await dispatch({op: "tabs"});
      return {connected: Boolean(port), count: tabs.length, tabs};
    }
    if (message.type === "revoke") {
      grantEpoch++; grants.delete(message.tabId); badge(); return {ok: true};
    }
    if (message.type === "stop") {
      grantEpoch++; grants.clear(); badge();
      if (connecting) { try { await connecting; } catch {} }
      grants.clear(); badge();
      if (port) { port.disconnect(); port = undefined; }
      return {ok: true};
    }
    if (message.type !== "grant") return {ok: false, error: "grantFailed"};
    const epoch = grantEpoch;
    const tab = await chrome.tabs.get(message.tabId);
    if (!allowedURL(tab.url)) return {ok: false, error: "unsupported"};
    await connect();
    if (!port) throw new Error("grantFailed");
    const activePort = port;
    const injected = await chrome.scripting.executeScript({target: {tabId: tab.id}, files: ["content.js"]});
    const main = injected.find((frame) => frame.frameId === 0);
    const current = await chrome.tabs.get(tab.id);
    if (grantEpoch !== epoch || port !== activePort || !main?.documentId || current.url !== tab.url || current.status === "loading") throw new Error("grantFailed");
    grants.set(tab.id, {url: tab.url, documentId: main.documentId}); badge();
    return {ok: true};
  })().then(respond, (error) => respond({ok: false, error: error.message === "install" ? "install" : "grantFailed"}));
  return true;
});
