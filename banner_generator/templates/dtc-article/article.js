// Builds the dtc-article preview from <body data-*> and fits the text. The renderer
// awaits window.bannerReady before taking the screenshot.
//
// An article is laid out title-first so it never reads as a dtc-event-speaker
// picture (big portrait circle on an arc, pill top-right, title at the bottom): no
// pill, the title large from the top of the canvas, and a slim byline at the bottom
// (small portrait, name, date and reading time) under a thin rule. The social card
// adds the DataTalks.Club logo top-left. An optional picture (the article's own image
// or illustration) fills the square list thumbnail alone, and is a cover panel
// beside the logo, title and byline on the social card.
(() => {
  const body = document.body;
  const d = body.dataset;
  // The palette comes from `tone`, or from `kind` ("Article", "Survey", "Case
  // study") when no tone is given.
  const TONES = ["coral", "teal", "plum"];
  const KIND_TONES = { guide: "teal", course: "teal", tutorial: "teal", survey: "plum",
    research: "plum", "case study": "plum" };
  const kind = (d.kind || "Article").trim() || "Article";
  const toneOf = (k) => KIND_TONES[k.toLowerCase()] || "coral";
  const tone = TONES.includes((d.tone || "").toLowerCase()) ? d.tone.toLowerCase() : toneOf(kind);
  let authors = [];
  try { authors = JSON.parse(d.authors || "[]"); } catch (e) { authors = []; }
  const n = authors.length;
  const landscape = window.innerWidth > window.innerHeight * 1.2;

  // Optional picture: {"url", "fit": "contain"|"cover", "frame": bool, "only": bool}.
  // "contain" sets the whole image on a tinted field, so a wide screenshot or an
  // illustration is never cut; "frame" draws the outline and offset shadow a photo
  // needs (a transparent illustration goes without); "only" fills the canvas alone.
  let picture = null;
  try { picture = JSON.parse(d.picture || "null"); } catch (e) { picture = null; }
  if (picture && !picture.url) picture = null;
  const layout = picture ? "picture" : "editorial";
  body.classList.add(landscape ? "landscape" : "square", "t-" + tone, "l-" + layout);

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
  const pictureBox = () => {
    const box = el("div", "picture" + (picture.frame ? " framed" : "") + (picture.fit === "cover" ? " cover" : " contain"));
    const img = el("img");
    img.alt = "";
    images.push(new Promise((ok) => { img.onload = img.onerror = ok; }));
    img.src = picture.url;
    box.append(img);
    return box;
  };
  // The square canvas is a list thumbnail (~120-290px wide): a picture there fills it
  // alone, as it does anywhere with "only".
  if (picture && (picture.only || !landscape)) {
    body.classList.add("picture-only");
    body.append(pictureBox());
    window.bannerReady = (async () => { await document.fonts.ready; await Promise.all(images); return (window.bannerFit = []); })();
    return;
  }

  const names = n === 0 ? "" : n === 1 ? authors[0].name
    : n === 2 ? `${authors[0].name} & ${authors[1].name}` : `${authors[0].name} & ${n - 1} others`;
  const title = el("h1", "", headline);
  const titleBox = el("div", "title-box fit-box");
  titleBox.append(title);
  const fitText = (node, range, lines) => { node.dataset.fit = range; node.dataset.lines = String(lines); return node; };

  // The byline: up to three small overlapping portraits, the name(s), then the date line.
  const byline = (withFaces) => {
    const row = el("div", "byline");
    if (withFaces && n) {
      const faces = el("div", "faces n" + Math.min(n, 3));
      authors.slice(0, 3).forEach((s) => faces.append(avatar(s)));
      row.append(faces);
    }
    const text = el("div", "byline-text");
    if (names) text.append(fitText(el("b", "names", names), landscape ? "40 46" : "40 52", 2));
    // "date · reading time": the two parts stay whole, and wrap between them in the
    // narrow column beside a picture instead of running past the edge.
    if (d.date || d.reading) {
      const meta = el("span", "meta");
      if (d.date) meta.append(el("span", "", d.date + (d.reading ? " ·" : "")));
      if (d.date && d.reading) meta.append(" ");
      if (d.reading) meta.append(el("span", "", d.reading));
      text.append(meta);
    }
    row.append(text);
    return row;
  };

  // The social card travels off-site, so it carries the brand top-left: the site's
  // masthead mark and the DataTalks.Club wordmark, in ink, as in the masthead.
  const brand = () => {
    const b = el("div", "brand");
    const mark = el("img", "brand-mark");
    mark.alt = "";
    images.push(new Promise((ok) => { mark.onload = mark.onerror = ok; }));
    mark.src = "assets/dtc-mark.svg";
    b.append(mark, el("span", "brand-name", "DataTalks.Club"));
    return b;
  };

  let titleFloor;
  if (layout === "editorial") {
    // No type pill: the title starts at the top and takes the room; the palette
    // (coral, teal, plum) still tells the types apart.
    fitText(title, landscape ? "60 116" : "76 156", landscape ? 4 : 6);
    titleFloor = landscape ? 64 : 84;
    if (landscape) body.append(brand());
    body.append(titleBox, byline(true));
  } else {
    fitText(title, "52 88", 4);
    titleFloor = 56;
    const copy = el("div", "copy");
    copy.append(brand(), titleBox, byline(true));
    if (picture && !picture.frame) body.classList.add("picture-bare");
    body.append(pictureBox(), copy);
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
    // Names first: the byline's height sets the room left for the title.
    const others = [...document.querySelectorAll("[data-fit]")].filter((node) => node !== title);
    const report = others.map((node) => fitNode(node, probe));
    // The whole title stays when it fits at a large size; otherwise the shortened
    // headline is fitted in the normal range.
    if (headline !== shortTitle && !fitNode(title, probe, titleFloor).ok) title.textContent = shortTitle;
    report.unshift(fitNode(title, probe));
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
