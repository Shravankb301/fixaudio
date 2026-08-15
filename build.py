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

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "monitors.json")
OUT = os.path.join(ROOT, "docs")

SITE = "https://shravankb301.github.io/willitddc"
REPO = "https://github.com/shravankb301/willitddc"
CHECK_CMD = "curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash"

CSS = """
:root{--bg:#0c0d10;--raised:#14161b;--sunken:#08090b;--line:#24272f;--soft:#1b1e25;
--text:#e8eaed;--dim:#9aa1ad;--faint:#6b7280;--ok:#6ee7a8;--okdim:#2f6b4f;
--warn:#f0b866;--bad:#f0806c;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);
line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:820px;margin:0 auto;padding:0 24px}
a{color:var(--ok);text-decoration:none}a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.9em;background:var(--raised);
border:1px solid var(--soft);border-radius:4px;padding:.1em .4em}
header{padding:72px 0 40px}
.eyebrow{font-family:var(--mono);font-size:13px;color:var(--ok);margin-bottom:18px}
h1{font-size:clamp(34px,6vw,54px);line-height:1.08;letter-spacing:-.025em;
margin:0 0 18px;font-weight:640}
.lede{font-size:clamp(17px,2.4vw,20px);color:var(--dim);margin:0 0 8px;max-width:62ch}
.cmd{margin:32px 0 12px;display:flex;background:var(--sunken);border:1px solid var(--line);
border-radius:10px;overflow:hidden}
.cmd pre{margin:0;padding:15px 18px;font-family:var(--mono);font-size:13.5px;
overflow-x:auto;flex:1;white-space:pre}
.cmd .p{color:var(--faint);user-select:none}
.copy{flex-shrink:0;border:none;border-left:1px solid var(--line);background:var(--raised);
color:var(--dim);font-family:var(--sans);font-size:13px;font-weight:500;padding:0 18px;
cursor:pointer}
.copy:hover{background:#1b1e25;color:var(--text)}.copy.done{color:var(--ok)}
.sub{font-size:14px;color:var(--faint);margin:0}
section{padding:44px 0;border-top:1px solid var(--soft)}
h2{font-size:24px;letter-spacing:-.015em;margin:0 0 14px;font-weight:620}
h3.q{font-size:16.5px;font-weight:600;margin:24px 0 6px;color:var(--text)}
p{margin:0 0 16px;color:var(--dim)}strong{color:var(--text);font-weight:600}
ul{margin:0 0 16px;padding-left:0;list-style:none}
li{color:var(--dim);margin-bottom:11px;padding-left:24px;position:relative}
li::before{content:"";position:absolute;left:5px;top:11px;width:5px;height:5px;
border-radius:50%;background:var(--okdim)}
.callout{background:var(--raised);border:1px solid var(--line);border-left:2px solid var(--okdim);
border-radius:0 10px 10px 0;padding:17px 19px;margin:0 0 16px}
.callout.warn{border-left-color:var(--warn)}.callout p:last-child{margin-bottom:0}
.tw{overflow-x:auto;margin:0 0 8px}
table{width:100%;border-collapse:collapse;font-size:14.5px}
th{text-align:left;padding:0 14px 9px 0;font-size:11.5px;font-weight:600;color:var(--faint);
text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid var(--line);
white-space:nowrap}
td{padding:10px 14px 10px 0;border-bottom:1px solid var(--soft);vertical-align:top;color:var(--dim)}
td.m{white-space:nowrap}
.yes{color:var(--ok);font-weight:600}.no{color:var(--bad);font-weight:600}
.unk{color:var(--faint)}
.pill{display:inline-block;font-size:11.5px;font-family:var(--mono);padding:2px 7px;
border-radius:20px;border:1px solid var(--line);color:var(--dim)}
.pill.broken{border-color:#5c4326;color:var(--warn)}
#filter{width:100%;padding:11px 14px;margin:0 0 18px;background:var(--sunken);
border:1px solid var(--line);border-radius:8px;color:var(--text);font-family:var(--sans);
font-size:15px}
#filter:focus{outline:none;border-color:var(--okdim)}
.empty{color:var(--faint);font-size:14.5px;padding:14px 0}
footer{padding:38px 0 70px;border-top:1px solid var(--soft);color:var(--faint);
font-size:14px;display:flex;gap:20px;flex-wrap:wrap}
.back{font-size:14px;color:var(--faint);margin-bottom:26px;display:block}
"""

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
  <div class="eyebrow">macOS · Apple Silicon</div>
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
