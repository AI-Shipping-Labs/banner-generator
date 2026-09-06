"""Render the DTC light/dark matrix and fail on clipped or overlapping content."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from banner_generator.renderer import load_spec, render_html, resolve_template

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "dtc-review"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--no-sandbox"])
        for spec_path in sorted((ROOT / "examples" / "dtc").glob("*.json")):
            spec = load_spec(spec_path)
            width, height = spec.viewport
            for theme in ("light", "dark"):
                name = f"{spec_path.stem}-{theme}"
                data = {**(spec.data or {}), "theme": theme}
                html_path = OUTPUT / f"{name}.html"
                html_path.write_text(render_html(resolve_template(spec.template), data, width, height))
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto(html_path.as_uri())
                page.evaluate("document.fonts.ready")
                page.evaluate("""async () => {
                    await Promise.all([...document.images].map(img => img.decode().catch(() => {})));
                }""")
                errors = page.evaluate(r"""() => {
                    const errors = [];
                    const luminance = color => {
                        const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(n => {
                            const c = n / 255;
                            return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
                        });
                        return channels[0] * .2126 + channels[1] * .7152 + channels[2] * .0722;
                    };
                    const ground = luminance(getComputedStyle(document.body).backgroundColor);
                    for (const selector of ['h1', '.subtitle', '.kicker']) {
                        const el = document.querySelector(selector);
                        if (!el.textContent.trim()) continue;
                        const ink = luminance(getComputedStyle(el).color);
                        const ratio = (Math.max(ink, ground) + .05) / (Math.min(ink, ground) + .05);
                        if (ratio < 4.5) errors.push(`${selector} contrast is only ${ratio.toFixed(2)}:1`);
                    }
                    const visible = el => el.getClientRects().length && getComputedStyle(el).display !== 'none';
                    for (const el of document.querySelectorAll('h1,.kicker,.subtitle,.person-copy,.metadata,.kind,.footer-brand')) {
                        if (!visible(el)) continue;
                        const r = el.getBoundingClientRect();
                        if (r.left < 0 || r.top < 0 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1)
                            errors.push(`${el.className || el.tagName} leaves canvas`);
                        if (el.scrollWidth > el.clientWidth + 1)
                            errors.push(`${el.className || el.tagName} overflows`);
                    }
                    const top = document.querySelector('.top').getBoundingClientRect();
                    const bottom = document.querySelector('.bottom').getBoundingClientRect();
                    for (const el of document.querySelectorAll('.copy > *')) {
                        if (!visible(el)) continue;
                        const range = document.createRange();
                        range.selectNodeContents(el);
                        const r = range.getBoundingClientRect();
                        if (r.top < top.bottom || r.bottom > bottom.top)
                            errors.push(`${el.className || el.tagName} overlaps header/footer`);
                    }
                    for (const img of document.querySelectorAll('.course-art img,.book-art img,.avatar img')) {
                        if (!visible(img) || !img.getAttribute('src') || img.src === 'about:blank') continue;
                        if (!img.naturalWidth) errors.push(`image failed: ${img.getAttribute('src')}`);
                    }
                    return errors;
                }""")
                page.screenshot(path=str(OUTPUT / f"{name}.png"))
                results.append({"name": name, "width": width, "height": height, "errors": errors})
                page.close()
        browser.close()
    (OUTPUT / "checks.json").write_text(json.dumps(results, indent=2) + "\n")
    cards = "\n".join(
        f'<figure><img src="{r["name"]}.png"><figcaption>{r["name"]}</figcaption></figure>'
        for r in results
    )
    (OUTPUT / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>DTC banner review</title>'
        '<style>body{margin:24px;background:#e6e7eb;font:14px system-ui}'
        'main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}'
        'figure{margin:0}img{width:100%;display:block}figcaption{padding:8px 0}</style>'
        f'<h1>DTC banner review · light and dark</h1><main>{cards}</main>'
    )
    failures = [r for r in results if r["errors"]]
    print(f"Rendered {len(results)} banners. Gallery: {OUTPUT / 'index.html'}")
    if failures:
        raise SystemExit(json.dumps(failures, indent=2))
    print("No clipped text, header/footer overlaps, low-contrast copy, or missing content images.")


if __name__ == "__main__":
    main()
