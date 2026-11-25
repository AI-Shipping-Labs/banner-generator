// Builds the dtc-event-speaker picture from <body data-*> and fits the text. The renderer
// awaits window.bannerReady before taking the screenshot.
(() => {
  const body = document.body;
  const d = body.dataset;
  const KINDS = ["webinar", "workshop", "podcast", "conference"];
  const kind = (d.kind || "webinar").split("·")[0].trim().toLowerCase();
  let speakers = [];
  try { speakers = JSON.parse(d.speakers || "[]"); } catch (e) { speakers = []; }
  const shown = speakers.slice(0, 4);
  const n = shown.length;
  const landscape = window.innerWidth > window.innerHeight * 1.2;
  body.classList.add(landscape ? "landscape" : "square", "t-" + (KINDS.includes(kind) ? kind : "webinar"));
  // A 16:9 canvas (YouTube thumbnail / video poster, 1280x720) gets larger portraits.
  if (landscape && window.innerHeight >= 700) body.classList.add("tall");
  // Optional series line under the speaker names, e.g. "DataTalks.Club Podcast · S15 E6".
  const series = (d.series || "").trim();
  if (series) body.classList.add("has-series");

  // A title that fits at a large size is kept whole (sibling events such as
  // "Course: Launch" and "Course: Live Q&A" must not share one headline). Only a
  // long "Main part: details" title that does not fit falls back to the main part;
  // a series episode ("Series #2: Topic: details") keeps the series and the topic.
  const shortOf = (t) => {
    if (t.length > 60 && t.includes(":")) {
      const parts = t.split(":").map((p) => p.trim());
      if (/#\d+$/.test(parts[0])) return parts.length > 2 ? `${parts[0]}: ${parts[1]}` : t;
      if (parts[0].length >= 12) return parts[0];
    }
    return t;
  };
  const fullTitle = d.title || "";
  const shortTitle = d.headline || shortOf(fullTitle);
  const headline = d.headline || fullTitle;

  // Optional sponsor: {"name", "logo_url", "label"} drawn as "Sponsored by" + logo.
  let sponsor = null;
  try { sponsor = JSON.parse(d.sponsor || "null"); } catch (e) { sponsor = null; }
  if (sponsor && !(sponsor.name || sponsor.logo_url)) sponsor = null;
  if (sponsor) body.classList.add("has-sponsor");

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
  else {  // No speakers: the disc carries the date and time.
    const disc = el("div", "avatar datedisc");
    const words = (d.date || "").split(" ");
    const year = words.length > 1 && /^\d{4}$/.test(words[words.length - 1]) ? words.pop() : "";
    const span = el("span");
    span.append(el("b", "", words.join(" ")));
    if (year) span.append(el("b", "", year));
    if (d.time) span.append(el("i", "", d.time));
    disc.append(span);
    faces.appendChild(disc);
  }

  const sponsorRow = () => {
    const row = el("div", "sponsor");
    row.append(el("span", "sponsor-label", sponsor.label || "Sponsored by"));
    const plate = el("div", "sponsor-plate");
    if (sponsor.logo_url) {
      const img = el("img");
      img.alt = sponsor.name || "";
      images.push(new Promise((ok) => { img.onload = img.onerror = ok; }));
      img.src = sponsor.logo_url;
      plate.append(img);
    } else {
      plate.append(el("b", "", sponsor.name));
    }
    row.append(plate);
    return row;
  };

  const pill = el("span", "pill", kind || "event");
  const title = el("h1", "", headline);
  const titleBox = el("div", "title-box fit-box");
  titleBox.append(title);
  const who = el("div", "who");
  const when = el("div", "when");
  if (n) { when.append(el("b", "", d.date || "")); if (d.time) when.append(el("span", "", d.time)); }

  const fits = [];
  if (landscape) {
    title.dataset.fit = sponsor ? "44 92" : "52 92"; title.dataset.lines = "4";
    if (n === 1 || n === 2) {
      const b = el("b", "", shown.map((s) => s.name).join(" & "));
      b.style.fontSize = "52px"; b.dataset.fit = "40 52"; who.append(b);
    } else if (n > 2) {
      const b = el("b", "", `${speakers.length} speakers`); b.style.fontSize = "52px"; who.append(b);
    }
    const meta = el("div", "meta");
    meta.append(who); if (series) meta.append(el("div", "series", series)); if (n) meta.append(when);
    const copy = el("div", "copy");
    copy.append(pill, titleBox, meta);
    if (sponsor) copy.append(sponsorRow());
    body.append(faces, copy);
  } else {
    title.dataset.fit = "64 128"; title.dataset.lines = "4";
    const size = { 1: 74, 2: 56, 3: 48 }[n] || 48;
    if (n >= 4) {
      const b = el("b", "", `${speakers.length} speakers`); b.style.fontSize = "66px"; who.append(b);
    } else {
      shown.forEach((s) => { const b = el("b", "", s.name); b.style.fontSize = size + "px"; b.dataset.fit = `48 ${size}`; who.append(b); });
    }
    const side = el("div", "side");
    side.append(pill, who);
    if (series) side.append(el("div", "series", series));
    if (n) side.append(when);
    const top = el("div", "top");
    top.append(faces, side);
    body.append(top, titleBox);
    if (sponsor) body.append(sponsorRow());
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
