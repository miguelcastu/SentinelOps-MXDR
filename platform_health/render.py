"""Standalone local HTML/Markdown reports, with escaped allowlisted aggregate fields."""
import html
import json
from pathlib import Path

from platform_health.engine import REASONS


def markdown(value):
    lines = ["# SentinelOps platform health", "", "Evidence: **" + value["evidence"] + "**. Overall: **" + value["state"] + "**.",
             "Observed: " + value["observed_at"] + ". Unknown means insufficient evidence, not an outage.", "",
             "| Source / onboarding | State | Events | p95 latency (s) | Explanation |", "|---|---|---|---|---|"]
    for source in value["sources"]:
        lines.append("| " + " | ".join(str(v) if v is not None else "Unknown" for v in
            (source["source_id"] + " / " + source["onboarding_state"], source["state"], source["total_events"], source["latency_p95_seconds"], source["explanation"])) + " |")
    lines.extend(["", "| Configuration / workflow | State | Explanation |", "|---|---|---|"])
    for check in value["checks"]:
        lines.append(f"| {check['id']} | {check['state']} | {REASONS[check['reason']]} |")
    rules, cost = value["rules"], value["cost"]
    lines.extend(["", f"Managed scheduled rules (AZ-DET-001/002): {rules['matching']} matching / {rules['expected']} expected; {rules['active']} active; {rules['intentionally_disabled']} intentionally disabled. Fusion is outside these counts.",
        "Configuration agreement does not prove rule execution or active detection coverage.", "",
        "Cost evidence complete: " + str(cost["complete"]) + "; observed billable bytes: " + str(cost["observed_billable_bytes"]) + ".",
        "Cost figures are partial planning estimates, not a verified invoice or remaining credit.", "",
        "This health evaluation executes no log queries, creates no resources and has no recurring schedule."])
    if value.get("fault_injection"):
        lines.extend(["", "## Synthetic fault injection", "", "| Scenario | State | Expected |", "|---|---|---|"])
        lines.extend(f"| {r['scenario']} | {r['state']} | {r['expected']} |" for r in value["fault_injection"])
    return "\n".join(lines) + "\n"


def dashboard(value):
    esc = lambda v: html.escape(str(v) if v is not None else "Unknown", quote=True)
    rows = "".join(f"<tr data-state='{esc(s['state'])}'><td>{esc(s['source_id'])}<br><small>{esc(s['table'])} · {esc(s['onboarding_state'])}</small></td><td>{esc(s['state'])}</td>"
                   f"<td>{esc(s['total_events'])}</td><td>{esc(s['last_seen'])}</td><td>{esc(s['latency_p95_seconds'])}</td>"
                   f"<td>{esc(s['explanation'])}</td></tr>" for s in value["sources"])
    checks = "".join(f"<li><strong>{esc(c['id'])}: {esc(c['state'])}</strong> — {esc(REASONS[c['reason']])}</li>" for c in value["checks"])
    faults = "".join(f"<tr><td>{esc(r['scenario'])}</td><td>{esc(r['state'])}</td><td>{esc(r['expected'])}</td></tr>"
                     for r in value.get("fault_injection", []))
    volumes = "".join(f"<li>{esc(s['source_id'])}: " + (", ".join(f"{esc(b['start'])}: {esc(b['events'])}" for b in s['hourly_volume']) or "Not collected") + "</li>" for s in value["sources"])
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SentinelOps platform health</title><style>
body{font:16px system-ui,sans-serif;background:#0b1424;color:#e4ecf7;margin:0;padding:30px;line-height:1.5}main{max-width:1250px;margin:auto}h1,h2{color:#79d8c8}table{border-collapse:collapse;width:100%;margin:16px 0;overflow:auto;display:block}td,th{border:1px solid #35475e;padding:10px;text-align:left}th{background:#1c3049}select{font:inherit;padding:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere}.note{padding:14px;border-left:4px solid #f3cc70;background:#18283d}caption{text-align:left;font-weight:700}footer{margin-top:30px}
</style><main><h1>SentinelOps MXDR · platform health</h1><p class="note">Evidence: <strong>""" + esc(value["evidence"]) + "</strong>. Overall: <strong>" + esc(value["state"]) + "</strong>. Observed " + esc(value["observed_at"]) + """. Unknown means insufficient evidence, not an outage. Atlas Financial is fictional.</p>
<label for="state">Source state: </label><select id="state"><option>All</option><option>Healthy</option><option>Delayed</option><option>Missing</option><option>Misconfigured</option><option>Unknown</option></select>
<table><caption>Source coverage</caption><thead><tr><th>Source</th><th>State</th><th>Events</th><th>Last seen UTC</th><th>p95 latency (s)</th><th>Explanation</th></tr></thead><tbody id="sources">""" + rows + "</tbody></table><h2>Configuration and workflow checks</h2><ul>" + checks + "</ul><h2>Observed volume by time bucket</h2><ul>" + volumes + "</ul><h2>Managed scheduled rule coverage (AZ-DET-001/002)</h2><pre>" + esc(json.dumps(value["rules"], indent=2)) + "</pre><p>Matching disabled rules establish configuration, not active detection coverage or execution health. Fusion is outside these counts.</p><h2>Cost awareness</h2><pre>" + esc(json.dumps(value["cost"], indent=2)) + "</pre><p>Partial estimates are not a billing statement or a spending cap.</p>" + ("<h2>Synthetic fault injection</h2><table><tr><th>Scenario</th><th>Observed state</th><th>Expected state</th></tr>" + faults + "</table>" if faults else "") + """<footer>No external assets, requests, telemetry, log queries or recurring tasks.</footer></main><script>
document.getElementById('state').addEventListener('change',function(){document.querySelectorAll('#sources tr').forEach(row=>{row.hidden=this.value!=='All'&&row.dataset.state!==this.value;});});
</script></html>"""


def write_report(value, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, text in (("report.json", json.dumps(value, indent=2) + "\n"),
                       ("report.md", markdown(value)), ("dashboard.html", dashboard(value))):
        (output / name).write_text(text, encoding="utf-8")
