#!/usr/bin/env python3
"""Turn a submitted report issue into a data/monitors.json entry.

Reads the issue body on stdin, writes the updated data file, and prints a short
summary for the pull request. Exits non-zero with a human-readable reason if the
issue can't be parsed — the workflow posts that back as a comment rather than
failing silently.

Everything here treats the issue body as hostile input: fields are length-capped
and whitelisted, and nothing is ever auto-merged. A human reviews the PR.
"""

import json
import os
import re
import sys

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "monitors.json")

MAX_FIELD = 120
MAX_NOTES = 600


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def sections(body):
    """GitHub issue forms render as '### Label\\n\\nvalue'."""
    out, key, buf = {}, None, []
    for line in body.splitlines():
        if line.startswith("### "):
            if key:
                out[key] = "\n".join(buf).strip()
            key, buf = line[4:].strip().lower(), []
        elif key:
            buf.append(line)
    if key:
        out[key] = "\n".join(buf).strip()
    return out


def clean(s, limit=MAX_FIELD):
    s = re.sub(r"[\x00-\x1f\x7f]", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "unknown"


def field(report, name):
    m = re.search(rf"^{name}:\s*(.+)$", report, re.M)
    return clean(m.group(1)) if m else ""


CONNECTIONS = {
    "built-in hdmi port on the mac": "Built-in HDMI",
    "usb-c / thunderbolt straight to the monitor": "USB-C",
    "displayport": "DisplayPort",
    "through a dock or hub": "Dock / hub",
    "through a kvm": "KVM",
    "other / not sure": "Other",
}


def main():
    body = sys.stdin.read()
    if not body.strip():
        fail("The issue body was empty.")

    sec = sections(body)
    monitor = clean(sec.get("monitor", ""))
    if not monitor:
        fail("No **Monitor** given. Please fill in the brand and model.")

    report = sec.get("report output", "")
    report = re.sub(r"^```[a-z]*$|^```$", "", report, flags=re.M)
    if "will-it-ddc report" not in report:
        fail("No report block found. Run the check and paste the whole "
             "`--- will-it-ddc report ---` section.")

    # Free text in the dropdown answers, so match rather than trust exact values.
    conn_raw = clean(sec.get("how is it connected?", "")).lower()
    connection = next((v for k, v in CONNECTIONS.items() if k in conn_raw), None)
    if not connection:
        connection = clean(sec.get("how is it connected?", "")) or "Other"

    vol_raw = clean(sec.get("did the volume actually change?", "")).lower()
    if vol_raw.startswith("yes"):
        volume = "works"
    elif vol_raw.startswith("no"):
        volume = "no"
    else:
        volume = "untested"

    display = field(report, "display")
    mac_model = field(report, "mac_model")
    chip = field(report, "chip")
    macos = field(report, "macos")
    visible = field(report, "ddc_visible").lower().startswith("y")

    reads_raw = field(report, "reads").lower()
    reads = "broken" if "broken" in reads_raw else ("ok" if "ok" in reads_raw else None)

    writes_raw = field(report, "writes").lower()
    if writes_raw.startswith("works"):
        writes = "works"
    elif writes_raw.startswith("no"):
        writes = "no"
    else:
        writes = "untested"

    # The report's own volume line is authoritative when the test actually ran.
    rep_vol = field(report, "volume").lower()
    if rep_vol.startswith("works"):
        volume = "works"
    elif rep_vol.startswith("no"):
        volume = "no"

    if not mac_model:
        fail("The report block is missing `mac_model`. Please paste it unedited.")

    parts = monitor.split(None, 1)
    brand = parts[0]
    model = parts[1] if len(parts) > 1 else display or monitor

    mac = f"{mac_model}" + (f" ({chip.replace('Apple ', '')})" if chip else "")

    entry = {
        "mac": clean(mac),
        "macos": macos or "—",
        "connection": clean(connection),
        "ddc_visible": visible,
        "volume": volume,
        "writes": writes,
        "by": clean(os.environ.get("ISSUE_AUTHOR", "contributor"), 40),
        "issue": int(os.environ.get("ISSUE_NUMBER", "0") or 0),
    }
    if reads:
        entry["reads"] = reads

    notes = clean(sec.get("anything else?", ""), MAX_NOTES)
    if notes and notes.lower() not in ("_no response_", "n/a", "none"):
        entry["notes"] = notes

    data = json.load(open(DATA))
    slug = slugify(f"{brand}-{model}")

    for m in data["monitors"]:
        if m["slug"] == slug:
            # Same machine and port reported twice: replace rather than duplicate.
            m["reports"] = [r for r in m["reports"]
                            if not (r.get("mac") == entry["mac"]
                                    and r.get("connection") == entry["connection"])]
            m["reports"].append(entry)
            break
    else:
        data["monitors"].append({
            "slug": slug,
            "brand": clean(brand, 40),
            "model": clean(model, 60),
            "reports": [entry],
        })

    with open(DATA, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")

    print(f"{brand} {model} · {entry['mac']} · {entry['connection']} · "
          f"writes={writes} volume={volume} reads={reads or 'unknown'}")


if __name__ == "__main__":
    main()
