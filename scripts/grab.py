"""Screenshot a web page that backs a fact in the video, with the fact located on the page.

Opens the page in your installed Edge (or Chrome) through Playwright, declines cookie banners,
hides sticky bars/pop-ups, scrolls the fact to the middle of the screen and saves:

  <out>.png    the visible page (clean, no highlight baked in)
  <out>.json   url, domain, page title, viewport, and the boxes of each line of the fact,
               so animations/compositions/fact-card.html can zoom to it and highlight it

Usage:
  .venv\\Scripts\\python.exe scripts\\grab.py URL --find "exact words from the page" \\
      --out projects\\<name>\\assets\\facts\\fact-1.png

--find must be words that appear on the page (case and spacing don't matter). Keep it to the
sentence or phrase that proves the fact; that's what gets highlighted in the video.
"""

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent.parent
ANIM_FACTS = ROOT / "animations" / "assets" / "facts"

# Buttons that refuse non-essential cookies, then plain "close" buttons. Privacy-first.
DECLINE = [
    "Reject all", "Reject All", "Decline", "Decline all", "Reject", "Only necessary",
    "Necessary only", "Use necessary cookies only", "Refuse all", "Deny", "Continue without accepting",
    "No thanks", "Not now",
]

FIND_JS = r"""
(needle) => {
  const norm = s => s.replace(/\s+/g, ' ').toLowerCase();
  const target = norm(needle.trim());
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: n => {
      const el = n.parentElement;
      if (!el) return NodeFilter.FILTER_REJECT;
      const tag = el.tagName;
      if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  // Flatten visible text, remembering where each normalized character came from.
  let flat = '', map = [], prevSpace = true;
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const t = n.nodeValue;
    for (let i = 0; i < t.length; i++) {
      const isSpace = /\s/.test(t[i]);
      if (isSpace) { if (prevSpace) continue; flat += ' '; prevSpace = true; }
      else { flat += t[i].toLowerCase(); prevSpace = false; }
      map.push([n, i]);
    }
    if (!prevSpace) { flat += ' '; map.push([n, t.length]); prevSpace = true; }
  }
  const at = flat.indexOf(target);
  if (at < 0) return null;
  const [sn, so] = map[at];
  const [en, eo] = map[at + target.length - 1];
  const range = document.createRange();
  range.setStart(sn, so);
  range.setEnd(en, Math.min(eo + 1, en.nodeValue.length));
  window.__factRange = range;
  const r = range.getBoundingClientRect();
  window.scrollBy(0, r.top + r.height / 2 - window.innerHeight * 0.5);
  return true;
}
"""

RECTS_JS = r"""
() => {
  const range = window.__factRange;
  // Merge the range's boxes into one box per text line.
  const lines = [];
  for (const r of range.getClientRects()) {
    if (r.width < 2 || r.height < 2) continue;
    const line = lines.find(l => Math.abs(l.y + l.h / 2 - (r.top + r.height / 2)) < r.height * 0.5);
    if (line) {
      const x2 = Math.max(line.x + line.w, r.right), y2 = Math.max(line.y + line.h, r.bottom);
      line.x = Math.min(line.x, r.left); line.y = Math.min(line.y, r.top);
      line.w = x2 - line.x; line.h = y2 - line.y;
    } else lines.push({ x: r.left, y: r.top, w: r.width, h: r.height });
  }
  return lines.map(l => ({ x: Math.round(l.x), y: Math.round(l.y), w: Math.round(l.w), h: Math.round(l.h) }));
}
"""

# Hide things that float over the content: sticky headers, chat bubbles, leftover banners.
HIDE_FLOATING_JS = r"""
() => {
  for (const el of document.querySelectorAll('body *')) {
    const cs = getComputedStyle(el);
    if ((cs.position === 'fixed' || cs.position === 'sticky') && el.offsetHeight > 0) {
      el.style.setProperty('visibility', 'hidden', 'important');
    }
  }
  document.documentElement.style.setProperty('overflow', 'auto', 'important');
  document.body.style.setProperty('overflow', 'auto', 'important');
}
"""


def dismiss_banners(page):
    for frame in [page.main_frame, *page.frames]:
        for label in DECLINE:
            try:
                btn = frame.get_by_role("button", name=label, exact=False).first
                if btn.is_visible(timeout=200):
                    btn.click(timeout=1500)
                    page.wait_for_timeout(600)
                    return label
            except Exception:
                continue
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--find", required=True, help="words on the page that prove the fact")
    ap.add_argument("--out", required=True, help="output .png (a .json is written next to it)")
    ap.add_argument("--width", type=int, default=1440, help="page width in CSS px (default 1440)")
    ap.add_argument("--height", type=int, default=900, help="page height in CSS px (default 900)")
    ap.add_argument("--scale", type=float, default=2, help="pixel density, 2 = sharp at 4K (default 2)")
    ap.add_argument("--browser", choices=["msedge", "chrome"], default="msedge")
    ap.add_argument("--keep-floating", action="store_true", help="don't hide sticky headers/pop-ups")
    ap.add_argument("--wait", type=float, default=2.0, help="extra seconds for the page to settle")
    a = ap.parse_args()

    out = Path(a.out).with_suffix(".png")
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=a.browser, headless=True)
        ctx = browser.new_context(
            viewport={"width": a.width, "height": a.height},
            device_scale_factor=a.scale,
            locale="en-US",
        )
        page = ctx.new_page()
        try:
            page.goto(a.url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_load_state("networkidle", timeout=15000)
        except PWTimeout:
            pass  # busy pages never go idle; carry on with what has loaded
        page.wait_for_timeout(int(a.wait * 1000))
        declined = dismiss_banners(page)
        if not a.keep_floating:
            page.evaluate(HIDE_FLOATING_JS)

        found = page.evaluate(FIND_JS, a.find)
        if not found:
            page.screenshot(path=str(out))
            browser.close()
            sys.exit(f"!! '{a.find}' is not on the page (saved the top of the page to {out} so you can look).")
        page.wait_for_timeout(800)  # lazy images below the fold
        rects = page.evaluate(RECTS_JS)
        title = page.title()
        final_url = page.url
        page.screenshot(path=str(out))
        browser.close()

    domain = urlparse(final_url).netloc.removeprefix("www.")
    info = {
        "url": final_url,
        "domain": domain,
        "title": title,
        "find": a.find,
        "captured": date.today().isoformat(),
        "viewport": {"w": a.width, "h": a.height, "scale": a.scale},
        "rects": rects,
        "cookie_banner": declined,
    }
    out.with_suffix(".json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")

    # The HyperFrames renderer only serves files inside animations/, so keep a copy there.
    ANIM_FACTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out, ANIM_FACTS / out.name)

    print(f"saved   {out}  ({len(rects)} line(s) of the fact found)")
    print(f"page    {title}  [{domain}]")
    if declined:
        print(f"cookies declined via '{declined}'")
    print("fact-card variables:")
    print(json.dumps({
        "shot": f"assets/facts/{out.name}",
        "rects": json.dumps(rects),
        "vw": a.width, "vh": a.height,
        "domain": domain,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
