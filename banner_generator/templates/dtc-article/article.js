// Builds the dtc-article preview from <body data-*> and fits the text. The renderer
// awaits window.bannerReady before taking the screenshot. Same structure as
// dtc-event-speaker: portraits, a type pill, names, date line and the title.
(() => {
  const body = document.body;
  const d = body.dataset;
  // The pill shows `kind` as written ("Article", "Survey", "Case study"); the colour
  // comes from `tone`, or from the kind when no tone is given.
  const TONES = ["coral", "teal", "plum"];
  const KIND_TONES = { guide: "teal", course: "teal", tutorial: "teal", survey: "plum",
    research: "plum", "case study": "plum" };
  const kind = (d.kind || "Article").trim() || "Article";
  const toneOf = (k) => KIND_TONES[k.toLowerCase()] || "coral";
  const tone = TONES.includes((d.tone || "").toLowerCase()) ? d.tone.toLowerCase() : toneOf(kind);
  let authors = [];
  try { authors = JSON.parse(d.authors || "[]"); } catch (e) { authors = []; }
  const shown = authors.slice(0, 4);
  const n = shown.length;
  const landscape = window.innerWidth > window.innerHeight * 1.2;
  body.classList.add(landscape ? "landscape" : "square", "t-" + tone);

  // A title that fits at a large size is kept whole. A long "Main part: details"
  // (or "Main part — details") title that does not fit falls back to the main part,
  // which is how article titles are written ("Topic: what the reader gets").
  const shortOf = (t) => {
    const cut = t.match(/^(.{12,}?)(?::\s| [—–] )/);
    return t.length > 50 && cut ? cut[1].trim() : t;
  };
  const fullTitle = d.title || "";
  const shortTitle = d.headline || shortOf(fullTitle);
  const headline = d.headline || fullTitle;

  const el = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  };
  const initials = (name) => {
    const parts = name.split(/\s+/).filter((p) => /^\p{L}/u.test(p));
    return parts.length ? (parts[0][0] + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase() : "";
  };
  const images = [];
  const avatar = (s) => {
    const a = el("div", "avatar");
    const url = s.image_url || s.image || "";
    if (url) {
      a.classList.add("photo");
      a.style.backgroundImage = `url(${JSON.stringify(url)})`;
      // crop: {"zoom": 1.5, "x": 65, "y": 20} zooms the portrait and moves the
      // focus point (percent) to hide stray edge content in the source photo.
      const c = s.crop || {};
      if (c.zoom) a.style.backgroundSize = `${c.zoom * 100}%`;
      if (c.x != null || c.y != null) a.style.backgroundPosition = `${c.x ?? 50}% ${c.y ?? 50}%`;
      images.push(new Promise((ok) => { const i = new Image(); i.onload = i.onerror = ok; i.src = url; }));
    } else {
      a.textContent = initials(s.name || "");
    }
    return a;
  };

  const faces = el("div", "faces n" + Math.max(n, 1));
  if (n) shown.forEach((s) => faces.appendChild(avatar(s)));
  else {  // No author on record: the disc carries the reading time.
    const disc = el("div", "avatar readdisc");
    const span = el("span");
    const minutes = (d.reading || "").match(/^(\d+)\s*(.*)$/);
    if (minutes) { span.append(el("b", "", minutes[1]), el("i", "", minutes[2] || "min read")); }
    else span.append(el("i", "", d.reading || kind));
    disc.append(span);
    faces.appendChild(disc);
  }

  const pill = el("span", "pill", kind);
  const title = el("h1", "", headline);
  const titleBox = el("div", "title-box fit-box");
  titleBox.append(title);
  const who = el("div", "who");
  const when = el("div", "when");
  if (d.date) when.append(el("b", "", d.date));
  if (d.reading && n) when.append(el("span", "", d.reading));

  if (landscape) {
    title.dataset.fit = "52 92"; title.dataset.lines = "4";
    if (n === 1 || n === 2) {
      const b = el("b", "", shown.map((s) => s.name).join(" & "));
      b.style.fontSize = "48px"; b.dataset.fit = "40 48"; who.append(b);
    } else if (n > 2) {
      const b = el("b", "", `${authors.length} authors`); b.style.fontSize = "48px"; who.append(b);
    }
    const meta = el("div", "meta");
    meta.append(who, when);
    const copy = el("div", "copy");
    copy.append(pill, titleBox, meta);
    body.append(faces, copy);
  } else {
    title.dataset.fit = "64 120"; title.dataset.lines = "4";
    const size = { 1: 68, 2: 54, 3: 48 }[n] || 48;
    if (n >= 4) {
      const b = el("b", "", `${authors.length} authors`); b.style.fontSize = "62px"; who.append(b);
    } else {
      shown.forEach((s) => { const b = el("b", "", s.name); b.style.fontSize = size + "px"; b.dataset.fit = `44 ${size}`; who.append(b); });
    }
    const side = el("div", "side");
    side.append(pill, who, when);
    const top = el("div", "top");
    top.append(faces, side);
    body.append(top, titleBox);
  }

  // Shrink a [data-fit="min max"] element until its .fit-box stops overflowing,
  // no word is wider than the line, and it has at most data-lines lines.
  const fitNode = (node, probe, floor) => {
    const [min0, max] = node.dataset.fit.split(" ").map(Number);
    const min = floor || min0;
    const maxLines = Number(node.dataset.lines || 99);
    const box = node.closest(".fit-box");
    let size = max, ok = false;
    for (; size >= min; size -= 2) {
      node.style.fontSize = size + "px";
      const cs = getComputedStyle(node);
      probe.style.font = cs.font; probe.style.letterSpacing = cs.letterSpacing;
      let widest = 0;
      for (const w of node.textContent.split(/[\s-]+/)) { probe.textContent = w; widest = Math.max(widest, probe.getBoundingClientRect().width); }
      const pad = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom);
      const lines = Math.round((node.getBoundingClientRect().height - pad) / parseFloat(cs.lineHeight));
      if ((!box || box.scrollHeight <= box.clientHeight + 1) && widest <= node.clientWidth + 0.5 && lines <= maxLines) { ok = true; break; }
    }
    return { text: node.textContent.slice(0, 40), size: Math.max(size, min), ok };
  };
  const fit = () => {
    const probe = el("span");
    probe.style.cssText = "position:absolute;visibility:hidden;white-space:nowrap";
    body.appendChild(probe);
    // The whole title stays when it fits at a large size (72px square, 60px social);
    // otherwise the shortened headline is fitted in the normal range.
    if (headline !== shortTitle && !fitNode(title, probe, landscape ? 60 : 72).ok) {
      title.textContent = shortTitle;
    }
    const report = [...document.querySelectorAll("[data-fit]")].map((node) => fitNode(node, probe));
    probe.remove();
    return report;
  };

  window.bannerReady = (async () => {
    await document.fonts.ready;
    await Promise.all(images);
    window.bannerFit = fit();
    return window.bannerFit;
  })();
})();
