#!/usr/bin/env python3
"""Generate the Will It DDC? site from data/monitors.json.

Output is committed, so the host needs no build step:

    python3 build.py

Every monitor gets its own page. That's the whole point -- each model number is
a search query someone types when their volume slider greys out.
"""

import json
import os
import shutil
from html import escape
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "monitors.json")
OUT = os.path.join(ROOT, "docs")

SITE = "https://shravankb301.github.io/willitddc"
REPO = "https://github.com/shravankb301/willitddc"
CHECK_CMD = "curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash"

CSS = open(os.path.join(ROOT, "assets", "style.css")).read()

# A monitor with a light-sweep across the glass. Reads at 20px, which is all a
# mark in a pill has to do.
LOGO_SVG = """<svg width="19" height="19" viewBox="0 0 20 20" fill="none" aria-hidden="true">\
<rect x="1.6" y="3.2" width="16.8" height="11.6" rx="3.2" stroke="url(#lg)" stroke-width="1.4"/>\
<path d="M3 12.6 17 5.6" stroke="rgba(255,255,255,.30)" stroke-width="1.2" stroke-linecap="round"/>\
<path d="M7.2 17.6h5.6" stroke="url(#lg)" stroke-width="1.4" stroke-linecap="round"/>\
<defs><linearGradient id="lg" x1="0" y1="0" x2="20" y2="20">\
<stop stop-color="#6ee7a8"/><stop offset="1" stop-color="#5aa9e6"/></linearGradient></defs></svg>"""

FAVICON = ("data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
    '<rect width="20" height="20" rx="4.5" fill="#0b0d12"/>'
    '<rect x="3.2" y="4.6" width="13.6" height="9.4" rx="2.4" fill="none" '
    'stroke="#6ee7a8" stroke-width="1.5"/>'
    '<path d="M4.4 12.2 15.6 6.4" stroke="rgba(255,255,255,.45)" stroke-width="1.2" '
    'stroke-linecap="round"/>'
    '<path d="M7.8 16.2h4.4" stroke="#6ee7a8" stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>'))

BRAND = f'<div class="brand">{LOGO_SVG}<span>Will It DDC?</span></div>'


COPY_JS = """
document.querySelectorAll('.copy').forEach(function(b){
  b.addEventListener('click',async function(){
    var t=b.parentElement.querySelector('.c').textContent;
    try{await navigator.clipboard.writeText(t)}catch(e){
      var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);
      a.select();document.execCommand('copy');a.remove()}
    b.textContent='Copied';b.classList.add('done');
    setTimeout(function(){b.textContent='Copy';b.classList.remove('done')},1600)})});
"""


def page(title, desc, body, canonical, extra_js=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{FAVICON}">
<meta name="theme-color" content="#07080b">
<meta name="color-scheme" content="dark">
<style>{CSS}</style>
</head>
<body>
<div class="bg"></div>
<div class="wrap">
{body}
</div>
<script>{COPY_JS}{extra_js}</script>
</body>
</html>
"""


def cmdbox(cmd):
    return (f'<div class="cmd"><pre><span class="p">$ </span>'
            f'<span class="c">{escape(cmd)}</span></pre>'
            f'<button class="copy">Copy</button></div>')


def verdict(v):
    return {
        "works": '<span class="yes">Works</span>',
        "no": '<span class="no">No</span>',
    }.get(v, '<span class="unk">Untested</span>')


def reads_cell(r):
    if r == "broken":
        return '<span class="pill broken">reads broken</span>'
    if r == "ok":
        return '<span class="pill">reads ok</span>'
    return '<span class="unk">—</span>'


def monitor_name(m):
    return f"{m['brand']} {m['model']}"


# --- index -------------------------------------------------------------------

def build_index(monitors):
    rows = []
    for m in monitors:
        for r in m["reports"]:
            rows.append(
                '<tr data-s="{s}">'
                '<td class="m"><a href="m/{slug}.html">{name}</a></td>'
                '<td>{mac}</td><td>{conn}</td><td>{vol}</td><td>{reads}</td>'
                "</tr>".format(
                    s=escape(f"{monitor_name(m)} {m.get('aka','')} {r['mac']} {r['connection']}".lower()),
                    slug=m["slug"],
                    name=escape(monitor_name(m)),
                    mac=escape(r["mac"]),
                    conn=escape(r["connection"]),
                    vol=verdict(r["volume"]),
                    reads=reads_cell(r["reads"]),
                )
            )

    count = sum(len(m["reports"]) for m in monitors)
    body = f"""
<header>
  {BRAND}
  <h1>Will it DDC?</h1>
  <p class="lede">
    Your Mac greys out the volume slider when sound goes to your monitor. Whether
    you can fix that depends on your exact monitor, your exact Mac, and which
    port you used &mdash; and nobody documents it. So let's document it.
  </p>
  {cmdbox(CHECK_CMD)}
  <p class="sub">Installs nothing but a diagnostic. Prints a report you can paste.</p>
</header>

<section>
  <h2>What people have found so far</h2>
  <p>
    {count} verified report{'s' if count != 1 else ''}. Every row is real
    diagnostic output from a real machine &mdash; nothing is inferred or
    guessed, which is why this list is short.
    <a href="{REPO}/issues/new?template=report.yml">Add yours</a>.
  </p>
  <input id="filter" type="search" placeholder="Filter by monitor, Mac, or connection…" autocomplete="off">
  <div class="tw">
    <table>
      <thead><tr><th>Monitor</th><th>Mac</th><th>Connection</th><th>Volume</th><th>DDC reads</th></tr></thead>
      <tbody id="rows">
        {chr(10).join(rows)}
      </tbody>
    </table>
  </div>
  <div class="empty" id="noresults" style="display:none">
    No match yet &mdash; which means nobody has reported that combination.
    <a href="{REPO}/issues/new?template=report.yml">Be the first</a>.
  </div>
</section>

<section>
  <h2>Why is the volume slider greyed out on my Mac?</h2>
  <p>
    Because the sound is travelling over your display cable. When audio goes out
    over HDMI or DisplayPort to a monitor, macOS decides the volume is the
    monitor's business rather than its own and disables its own control
    entirely. The Control Center slider greys out and the keyboard volume keys
    stop doing anything.
  </p>
  <p>
    The monitor is usually still listening. Most of them accept
    <strong>DDC/CI</strong> commands over that same cable &mdash; a decades-old
    standard for telling a display to change its own settings. Whether yours
    obeys the volume command is entirely up to its firmware, which is why this
    site exists.
  </p>
</section>

<section>
  <h2>Three things determine the answer</h2>
  <ul>
    <li><strong>Your monitor's firmware.</strong> DDC volume support is optional and inconsistently implemented. Some monitors accept the command, some ignore it, and some accept writes while returning nonsense on reads.</li>
    <li><strong>Your Mac's port.</strong> Macs with built-in HDMI convert DisplayPort using an MCDP2900 chip, and Apple cuts off the I2C channel DDC needs once the display's EDID has been read. This is why <a href="https://github.com/MonitorControl/MonitorControl/discussions/750">MonitorControl disables itself</a> on the built-in HDMI port of 2018 Intel Mac minis, all M1 Macs, and the entry-level M2 Mac mini.</li>
    <li><strong>What's in between.</strong> Docks, KVMs and adapters frequently drop DDC even when both ends support it.</li>
  </ul>
  <div class="callout">
    <p>
      This is why "does monitor X work" has no general answer, and why every
      tool in this space has support threads full of the same question. The
      combination is what matters, so the combination is what gets recorded here.
    </p>
  </div>
</section>

<section>
  <h2>The case everyone gets wrong: monitors that lie</h2>
  <p>
    Some monitors accept DDC writes perfectly but return garbage when asked
    what their current settings are. The Samsung CF791 reports the same value
    for <em>every</em> setting and claims its maximum volume is <code>-128</code>.
  </p>
  <p>
    Most control apps read the current value before changing it, so on hardware
    like this they appear broken even though the monitor is fully controllable.
    If your report comes back <span class="pill broken">reads broken</span>,
    that's the bucket you're in &mdash; and it's fixable with a tool that never
    reads. <a href="{REPO}">There's one in this repo</a>.
  </p>
</section>

<section>
  <h2>Questions</h2>

  <h3 class="q">What does the check actually do?</h3>
  <p>
    Installs <a href="https://github.com/waydabber/m1ddc">m1ddc</a> via Homebrew
    if you don't have it, asks your display a few harmless questions, and prints
    a report. It changes no settings.
    <a href="{REPO}/blob/main/check.sh">Read it first</a> &mdash; it's short.
  </p>

  <h3 class="q">My monitor isn't listed. What do I do?</h3>
  <p>
    Run the check and post the output. That's the entire contribution, it takes
    a minute, and it's the only way this list gets useful for the next person
    with your monitor.
  </p>

  <h3 class="q">My monitor says DDC works. Now what?</h3>
  <p>
    Use whichever tool you like &mdash;
    <a href="https://github.com/MonitorControl/MonitorControl">MonitorControl</a>
    is free and excellent,
    <a href="https://github.com/waydabber/BetterDisplay">BetterDisplay</a> does
    more and handles HDMI ports MonitorControl won't. This site isn't trying to
    replace them; it tells you in advance whether they'll work for you.
  </p>

  <h3 class="q">Who runs this?</h3>
  <p>
    It started because one Samsung ultrawide wouldn't behave and the answer took
    an evening to find. It's open source and the data is
    <a href="{REPO}/blob/main/data/monitors.json">a JSON file you can read</a>.
  </p>
</section>

<footer>
  <a href="{REPO}">GitHub</a>
  <a href="{REPO}/issues/new?template=report.yml">Submit a report</a>
  <a href="{REPO}/blob/main/data/monitors.json">Raw data</a>
  <span>MIT</span>
</footer>
"""

    filter_js = """
var f=document.getElementById('filter'),rows=document.getElementById('rows'),
nr=document.getElementById('noresults');
f.addEventListener('input',function(){
  var q=f.value.toLowerCase().trim(),shown=0;
  Array.prototype.forEach.call(rows.rows,function(tr){
    var hit=!q||tr.dataset.s.indexOf(q)>-1;
    tr.style.display=hit?'':'none';if(hit)shown++});
  nr.style.display=shown?'none':'block'});
"""

    return page(
        "Will It DDC? — Does your monitor's volume work on a Mac?",
        "Find out whether your monitor supports DDC volume control on macOS. "
        "A crowdsourced compatibility list of monitor, Mac and connection combinations.",
        body, SITE + "/", filter_js)


# --- per-monitor -------------------------------------------------------------

def build_monitor(m):
    name = monitor_name(m)
    rows = "".join(
        '<tr><td>{mac}</td><td>{conn}</td><td>{vol}</td><td>{reads}</td><td>{macos}</td></tr>'.format(
            mac=escape(r["mac"]), conn=escape(r["connection"]),
            vol=verdict(r["volume"]), reads=reads_cell(r["reads"]),
            macos=escape(r.get("macos", "—")))
        for r in m["reports"])

    notes = "".join(
        f'<div class="callout"><p><strong>{escape(r["mac"])}, {escape(r["connection"])}:</strong> '
        f'{escape(r["notes"])}</p></div>'
        for r in m["reports"] if r.get("notes"))

    works = any(r["volume"] == "works" for r in m["reports"])
    broken_reads = any(r["reads"] == "broken" for r in m["reports"])

    if works and broken_reads:
        verdict_text = (
            f"<strong>Yes, with the right tool.</strong> The {escape(name)} accepts DDC "
            "volume commands, but lies when asked about its current state. Apps that read "
            "before writing will look broken; a write-only tool works fine.")
    elif works:
        verdict_text = f"<strong>Yes.</strong> The {escape(name)} accepts DDC volume commands."
    else:
        verdict_text = (f"Not established yet for the {escape(name)} &mdash; "
                        "the reports below are what we have.")

    aka = f'<p>Also sold as {escape(m["aka"])}.</p>' if m.get("aka") else ""

    body = f"""
<header>
  <a class="back" href="../">← Will It DDC?</a>
  {BRAND}
  <h1>Does the {escape(name)} support volume control on a Mac?</h1>
  <p class="lede">{verdict_text}</p>
  {aka}
</header>

<section>
  <h2>Verified reports</h2>
  <div class="tw">
    <table>
      <thead><tr><th>Mac</th><th>Connection</th><th>Volume</th><th>DDC reads</th><th>macOS</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  {notes}
  <p>
    Different Mac or port than the ones listed? The answer can change with both.
    <a href="{REPO}/issues/new?template=report.yml">Add your result</a>.
  </p>
</section>

<section>
  <h2>Check your own setup</h2>
  <p>Same monitor doesn't guarantee the same result &mdash; the port matters as much as the panel.</p>
  {cmdbox(CHECK_CMD)}
</section>

<footer>
  <a href="../">All monitors</a>
  <a href="{REPO}">GitHub</a>
  <a href="{REPO}/issues/new?template=report.yml">Submit a report</a>
  <span>MIT</span>
</footer>
"""

    desc = (f"Does the {name} support DDC volume control on macOS? "
            "Verified reports by Mac model and connection type.")
    return page(f"{name} — DDC volume control on Mac? | Will It DDC?",
                desc, body, f"{SITE}/m/{m['slug']}.html")


def main():
    data = json.load(open(DATA))
    monitors = sorted(data["monitors"], key=lambda m: (m["brand"], m["model"]))

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "m"), exist_ok=True)

    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(build_index(monitors))

    for m in monitors:
        with open(os.path.join(OUT, "m", m["slug"] + ".html"), "w") as f:
            f.write(build_monitor(m))

    # sitemap: every model page is a search landing surface, so make them findable
    urls = [f"{SITE}/"] + [f"{SITE}/m/{m['slug']}.html" for m in monitors]
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for u in urls:
            f.write(f"  <url><loc>{u}</loc></url>\n")
        f.write("</urlset>\n")

    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")

    print(f"built {len(monitors)} monitor page(s), {len(urls)} urls")


if __name__ == "__main__":
    main()
