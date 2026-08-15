# Contributing

The data *is* the project. One report from a monitor nobody has tested is worth
more than any amount of code.

## Report a monitor

```sh
curl -fsSL https://raw.githubusercontent.com/shravankb301/willitddc/main/check.sh | bash
```

Answer the two prompts, then
[open a report](https://github.com/shravankb301/willitddc/issues/new?template=report.yml)
and paste the output. A bot parses it and opens a pull request; a human checks
it against what you pasted before it merges.

**"It doesn't work at all" is a real result.** A confirmed no saves the next
person the same evening you just lost, and the list is dishonest without them.

## What gets recorded, and what doesn't

The report block contains your Mac model, chip, macOS version, display name and
the DDC probe values. No serial numbers, no EDID, nothing identifying — have a
look before you paste it.

Every row is measured. Nothing is inferred from a spec sheet, and a monitor
whose write test nobody ran stays ungraded rather than guessed at. If you find a
row that isn't backed by real output, that's a bug worth filing.

## Grades

| Grade | Meaning |
| --- | --- |
| **A** | Obeys, and tells the truth. |
| **B** | Does what it's told, lies about its own state. |
| **C** | Takes orders, except the one you wanted. |
| **D** | Answers the door, refuses to move. |
| **F** | Not listening. |

A monitor is shown at its *best* recorded grade — a bad port shouldn't condemn
the panel. The per-monitor page lists every combination separately, because the
combination is the thing that actually varies.

## Working on the code

No dependencies beyond Python 3 and a Mac for the shell parts.

```sh
python3 build.py     # regenerates docs/ from data/monitors.json
bash check.sh        # run the diagnostic locally
bash -n check.sh     # syntax check
```

`docs/` is generated output and committed so GitHub Pages needs no build step —
edit `assets/style.css` or `build.py`, never `docs/` directly. Rebuild before
committing, or the site and the data drift apart.

The parser has three paths worth keeping working: a new monitor, a repeat of a
Mac+port combination already recorded (which replaces rather than duplicates),
and a malformed issue (which must fail with a message a human can act on).

## Things that would genuinely help

- **Intel Mac support.** `m1ddc` is Apple Silicon only, so `check.sh` refuses to
  run on Intel. `ddcctl` covers those machines and nobody has wired it in.
- **Reports from Mac minis and Studios over built-in HDMI.** Apple disables the
  I2C channel DDC needs on several of these, but it appears to work on the M4
  mini. That's currently confirmed on exactly one machine.
- **Docks and KVMs**, which drop DDC unpredictably and are barely represented.

## Ground rules

Be decent to people reporting hardware that disappointed them. Criticise
monitors, not each other.
