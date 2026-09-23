(() => {
  if (globalThis.__senteBrowserInstalled) {
    globalThis.__senteBrowserInstalled.reset();
    return;
  }
  let snapshot = "";
  let refs = new Map();
  globalThis.__senteBrowserInstalled = {reset: () => { snapshot = ""; refs.clear(); }};
  const disabled = (el) => el.matches(":disabled") || el.getAttribute("aria-disabled") === "true";
  const visible = (el) => el.isConnected && el.getClientRects().length > 0 &&
    getComputedStyle(el).visibility !== "hidden" && !el.closest("[inert], [aria-hidden='true']");
  const label = (el) => (el.getAttribute("aria-label") ||
    [...(el.labels || [])].map((x) => x.innerText).join(" ") ||
    el.getAttribute("placeholder") || el.innerText || el.getAttribute("title") || "").trim().slice(0, 200);
  function read() {
    snapshot = crypto.randomUUID(); refs = new Map();
    const elements = [];
    for (const el of document.querySelectorAll("a[href], button, input, textarea, select, [role='button'], [role='link'], [contenteditable='true']")) {
      if (!visible(el) || elements.length >= 300) continue;
      const ref = `e${elements.length + 1}`;
      refs.set(ref, {el, label: label(el), href: el.getAttribute("href"), type: el.getAttribute("type")});
      elements.push({ref, tag: el.tagName.toLowerCase(), role: el.getAttribute("role"), type: el.getAttribute("type"), label: label(el), disabled: disabled(el)});
    }
    return {untrusted: true, snapshot, url: location.href, title: document.title,
      text: (document.body?.innerText || "").slice(0, 30000), elements};
  }
  function act(message) {
    if (message.op === "read") return read();
    if (!snapshot || message.snapshot !== snapshot) throw new Error("stale_snapshot_read_again");
    if (message.op === "scroll") {
      if (!["up", "down"].includes(message.direction)) throw new Error("invalid_direction");
      window.scrollBy(0, (message.direction === "up" ? -1 : 1) * innerHeight * .8);
      snapshot = "";
      return {performed: "scroll", readAgain: true};
    }
    const saved = refs.get(message.ref);
    const el = saved?.el;
    if (!el || !visible(el) || disabled(el)) throw new Error("element_unavailable");
    if (label(el) !== saved.label || el.getAttribute("href") !== saved.href || el.getAttribute("type") !== saved.type) throw new Error("element_changed_read_again");
    if (message.op === "click") {
      snapshot = "";
      el.click();
      return {performed: "click", readAgain: true};
    }
    if (message.op !== "fill" || typeof message.text !== "string" || Array.from(message.text).length > 10000) throw new Error("invalid_input");
    if (el.readOnly || !["INPUT", "TEXTAREA"].includes(el.tagName)) throw new Error("not_text_input");
    if (el.tagName === "INPUT" && !["text", "search", "email", "url", "tel"].includes(el.type)) throw new Error("unsupported_input_type");
    if (el.maxLength >= 0 && message.text.length > el.maxLength) throw new Error("input_exceeds_maxlength");
    el.focus();
    // Focus handlers can replace, disable or turn a field into a password input.
    if (!visible(el) || disabled(el) || el.readOnly || label(el) !== saved.label || el.getAttribute("type") !== saved.type) throw new Error("element_changed_read_again");
    if (el.maxLength >= 0 && message.text.length > el.maxLength) throw new Error("input_exceeds_maxlength");
    snapshot = "";
    const proto = el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, "value").set.call(el, message.text);
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
    return {performed: "fill", readAgain: true};
  }
  chrome.runtime.onMessage.addListener((message, sender, respond) => {
    if (sender.id !== chrome.runtime.id || message.type !== "sente-action") return;
    try { respond({ok: true, result: act(message)}); }
    catch (error) { respond({ok: false, error: error.message}); }
  });
})();
