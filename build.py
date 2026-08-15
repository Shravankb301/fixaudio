#!/usr/bin/env python3
"""Generate the Will It DDC? site from data/monitors.json.

    python3 build.py

Output is committed, so neither host needs a build step. Markup follows
shadcn/ui component anatomy (card / badge / button / input / table) so the
styles in assets/style.css map 1:1 onto the real components if this ever moves
to React.

Every monitor gets its own page. That's the point — each model number is a
search query someone types when their volume slider greys out.
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
SUBMIT = REPO + "/issues/new?template=report.yml"
CHECK_CMD = "curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash"

CSS = open(os.path.join(ROOT, "assets", "style.css")).read()

# Neutral mark: a display on a stand. Inherits currentColor so it works on
# either theme without a second asset.
LOGO = ('<svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true">'
        '<rect x="1.8" y="3.4" width="16.4" height="11.2" rx="2.4" stroke="currentColor" '
        'stroke-width="1.5"/>'
        '<path d="M7.4 17.6h5.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
        '</svg>')

FAVICON = "data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
    '<rect width="20" height="20" rx="4.5" fill="#18181b"/>'
    '<rect x="3.4" y="4.8" width="13.2" height="9" rx="2" fill="none" '
    'stroke="#fafafa" stroke-width="1.5"/>'
    '<path d="M7.9 16.4h4.2" stroke="#fafafa" stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>')

BRAND = ('<a href="./" class="badge badge-outline brand">'
         f'{LOGO}<span>Will It DDC?</span></a>')

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
<meta name="color-scheme" content="light dark">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
<script>{COPY_JS}{extra_js}</script>
</body>
</html>
"""


def codeblock(cmd):
    return (f'<div class="codeblock"><pre><span class="prompt">$ </span>'
            f'<span class="c">{escape(cmd)}</span></pre>'
            f'<button class="copy">Copy</button></div>')


def verdict(v):
    if v == "works":
        return '<span class="badge badge-success">Works</span>'
    if v == "no":
        return '<span class="badge badge-destructive">No</span>'
    return '<span class="badge badge-secondary">Untested</span>'


def reads_badge(r):
    if r == "broken":
        return '<span class="badge badge-outline badge-mono">reads broken</span>'
    if r == "ok":
        return '<span class="badge badge-secondary badge-mono">reads ok</span>'
    return '<span class="muted">&mdash;</span>'


def monitor_name(m):
    return f"{m['brand']} {m['model']}"


def card(title, description, content):
    desc = f'<p class="card-description">{description}</p>' if description else ""
    return f"""<section class="card">
  <div class="card-header">
    <h2 class="card-title">{title}</h2>
    {desc}
  </div>
  <div class="card-content">
{content}
  </div>
</section>"""


# --- index -------------------------------------------------------------------

def build_index(monitors):
    rows = []
    for m in monitors:
        for r in m["reports"]:
            rows.append(
                '<tr data-s="{s}">'
                '<td class="name"><a class="link" href="m/{slug}.html">{name}</a></td>'
                '<td>{mac}</td><td>{conn}</td><td>{vol}</td><td>{reads}</td>'
                "</tr>".format(
                    s=escape(f"{monitor_name(m)} {m.get('aka','')} {r['mac']} {r['connection']}".lower()),
                    slug=m["slug"], name=escape(monitor_name(m)),
                    mac=escape(r["mac"]), conn=escape(r["connection"]),
                    vol=verdict(r["volume"]), reads=reads_badge(r["reads"]))
            )

    count = sum(len(m["reports"]) for m in monitors)
    plural = "s" if count != 1 else ""

    header = f"""<header>
  {BRAND}
  <h1 class="h1">Will it DDC?</h1>
  <p class="lead">
    Your Mac greys out the volume slider when sound goes to your monitor.
    Whether you can get it back depends on your exact monitor, your exact Mac,
    and which port you used &mdash; and nobody documents the combination.
    So let's document it.
  </p>

  <div class="card osd" role="img"
       aria-label="A monitor's on-screen menu with the volume row greyed out.">
    <div class="osd-head"><span>Sound</span><span>Your monitor</span></div>
    <div class="osd-row disabled">
      <span class="label">Volume</span>
      <div class="progress"><div style="width:62%"></div></div>
      <span class="val">62</span>
    </div>
    <div class="osd-row">
      <span class="label">Bass</span>
      <div class="progress"><div style="width:50%"></div></div>
      <span class="val">50</span>
    </div>
    <div class="osd-row">
      <span class="label">Treble</span>
      <div class="progress"><div style="width:50%"></div></div>
      <span class="val">50</span>
    </div>
  </div>
  <p class="small muted">Right now, this is your volume control.</p>

  {codeblock(CHECK_CMD)}
  <p class="small muted">Installs nothing but a diagnostic. Changes no settings. Prints a report you can paste.</p>
</header>"""

    results = card(
        "What people have found so far",
        f"{count} verified report{plural}. Every row is real diagnostic output from a "
        "real machine &mdash; nothing inferred or guessed, which is why this list is short.",
        f"""    <input id="filter" class="input" type="search"
           placeholder="Filter by monitor, Mac, or connection…" autocomplete="off">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Monitor</th><th>Mac</th><th>Connection</th><th>Volume</th><th>DDC reads</th></tr></thead>
        <tbody id="rows">
{chr(10).join("          " + r for r in rows)}
        </tbody>
      </table>
    </div>
    <div class="empty" id="noresults" style="display:none">
      No match yet &mdash; which means nobody has reported that combination.
    </div>
    <div class="row">
      <a class="btn btn-primary" href="{SUBMIT}">Add your monitor</a>
      <a class="btn btn-outline" href="{REPO}/blob/main/data/monitors.json">View raw data</a>
    </div>""")

    why = card(
        "Why is the volume slider greyed out on my Mac?", "",
        """    <p class="muted">
      Because the sound is travelling over your display cable. When audio goes out
      over HDMI or DisplayPort to a monitor, macOS decides the volume is the
      monitor's business rather than its own and disables its own control entirely.
      The Control Center slider greys out and the keyboard volume keys stop doing
      anything.
    </p>
    <p class="muted">
      The monitor is usually still listening. Most of them accept <strong>DDC/CI</strong>
      commands over that same cable &mdash; a decades-old standard for telling a display
      to change its own settings. Whether yours obeys the volume command is entirely up
      to its firmware, which is why this site exists.
    </p>""")

    three = card(
        "Three things determine the answer", "",
        """    <ul class="list">
      <li><strong>Your monitor's firmware.</strong> DDC volume support is optional and
        inconsistently implemented. Some monitors accept the command, some ignore it,
        and some accept writes while returning nonsense on reads.</li>
      <li><strong>Your Mac's port.</strong> Macs with built-in HDMI convert DisplayPort
        using an MCDP2900 chip, and Apple cuts off the I2C channel DDC needs once the
        display's EDID has been read. This is why
        <a class="link" href="https://github.com/MonitorControl/MonitorControl/discussions/750">MonitorControl
        disables itself</a> on the built-in HDMI port of 2018 Intel Mac minis, all M1
        Macs, and the entry-level M2 Mac mini.</li>
      <li><strong>What's in between.</strong> Docks, KVMs and adapters frequently drop
        DDC even when both ends support it.</li>
    </ul>
    <p class="muted small">
      So &ldquo;does monitor X work&rdquo; has no general answer. The combination is what
      matters, so the combination is what gets recorded here.
    </p>""")

    lying = card(
        "The case every tool gets wrong", "",
        f"""    <p class="muted">
      Some monitors accept DDC writes perfectly but return garbage when asked what their
      current settings are. The Samsung CF791 reports the same value for <em>every</em>
      setting and claims its maximum volume is <code>-128</code>.
    </p>
    <p class="muted">
      Most control apps read the current value before changing it, so on hardware like
      this they appear broken even though the monitor is fully controllable. If your
      report comes back <span class="badge badge-outline badge-mono">reads broken</span>,
      that's the bucket you're in &mdash; and it's fixable with a tool that never reads.
      <a class="link" href="{REPO}/blob/main/TOOL.md">There's one in this repo</a>.
    </p>""")

    faq = card(
        "Questions", "",
        f"""    <h3 class="h3">What does the check actually do?</h3>
    <p class="muted">
      Installs <a class="link" href="https://github.com/waydabber/m1ddc">m1ddc</a> via
      Homebrew if you don't have it, asks your display a few harmless questions, and
      prints a report. It changes no settings.
      <a class="link" href="{REPO}/blob/main/check.sh">Read it first</a> &mdash; it's short.
    </p>

    <h3 class="h3">My monitor isn't listed. What do I do?</h3>
    <p class="muted">
      Run the check and post the output. That's the entire contribution, it takes a
      minute, and it's the only way this list gets useful for the next person with
      your monitor.
    </p>

    <h3 class="h3">My monitor says DDC works. Now what?</h3>
    <p class="muted">
      Use whichever tool you like &mdash;
      <a class="link" href="https://github.com/MonitorControl/MonitorControl">MonitorControl</a>
      is free and excellent,
      <a class="link" href="https://github.com/waydabber/BetterDisplay">BetterDisplay</a>
      does more and handles HDMI ports MonitorControl won't. This site isn't trying to
      replace them; it tells you in advance whether they'll work for you.
    </p>

    <h3 class="h3">Who runs this?</h3>
    <p class="muted">
      It started because one Samsung ultrawide wouldn't behave and the answer took an
      evening to find. It's open source and the data is
      <a class="link" href="{REPO}/blob/main/data/monitors.json">a JSON file you can read</a>.
    </p>""")

    body = f"""{header}
<main>
{results}
{why}
{three}
{lying}
{faq}
</main>
<footer>
  <a class="link" href="{REPO}">GitHub</a>
  <a class="link" href="{SUBMIT}">Submit a report</a>
  <a class="link" href="{REPO}/blob/main/TOOL.md">The volume tool</a>
  <span>MIT</span>
</footer>"""

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
        "Find out whether your monitor supports DDC volume control on macOS. A "
        "crowdsourced compatibility list of monitor, Mac and connection combinations.",
        body, SITE + "/", filter_js)


# --- per-monitor -------------------------------------------------------------

def build_monitor(m):
    name = monitor_name(m)

    rows = "".join(
        '<tr><td class="name">{mac}</td><td>{conn}</td><td>{vol}</td>'
        '<td>{reads}</td><td class="muted">{macos}</td></tr>'.format(
            mac=escape(r["mac"]), conn=escape(r["connection"]),
            vol=verdict(r["volume"]), reads=reads_badge(r["reads"]),
            macos=escape(r.get("macos", "—")))
        for r in m["reports"])

    notes = "".join(
        f'<p class="muted small"><strong>{escape(r["mac"])}, {escape(r["connection"])}:</strong> '
        f'{escape(r["notes"])}</p>'
        for r in m["reports"] if r.get("notes"))

    works = any(r["volume"] == "works" for r in m["reports"])
    broken = any(r["reads"] == "broken" for r in m["reports"])

    if works and broken:
        answer = (f"<strong>Yes, with the right tool.</strong> The {escape(name)} accepts "
                  "DDC volume commands but lies when asked about its current state. Apps "
                  "that read before writing will look broken; a write-only tool works fine.")
    elif works:
        answer = f"<strong>Yes.</strong> The {escape(name)} accepts DDC volume commands."
    else:
        answer = (f"Not established yet for the {escape(name)} &mdash; the reports below "
                  "are what we have.")

    aka = (f'<p class="small muted">Also sold as {escape(m["aka"])}.</p>'
           if m.get("aka") else "")

    header = f"""<header>
  <a href="../" class="badge badge-outline brand">{LOGO}<span>Will It DDC?</span></a>
  <h1 class="h1">Does the {escape(name)} support volume control on a Mac?</h1>
  <p class="lead">{answer}</p>
  {aka}
</header>"""

    reports = card(
        "Verified reports",
        "The answer can change with a different Mac or a different port.",
        f"""    <div class="table-wrap">
      <table>
        <thead><tr><th>Mac</th><th>Connection</th><th>Volume</th><th>DDC reads</th><th>macOS</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
{notes}
    <div class="row">
      <a class="btn btn-primary" href="{SUBMIT}">Add your result</a>
      <a class="btn btn-outline" href="../">All monitors</a>
    </div>""")

    check = card(
        "Check your own setup",
        "Same monitor doesn't guarantee the same result &mdash; the port matters as much "
        "as the panel.",
        "    " + codeblock(CHECK_CMD))

    body = f"""{header}
<main>
{reports}
{check}
</main>
<footer>
  <a class="link" href="../">All monitors</a>
  <a class="link" href="{REPO}">GitHub</a>
  <a class="link" href="{SUBMIT}">Submit a report</a>
  <span>MIT</span>
</footer>"""

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
