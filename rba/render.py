"""Standalone synthetic risk timeline with local entity selection and replay controls."""
import json
from pathlib import Path


def markdown(value):
    lines = ["# Atlas Financial: synthetic entity risk", "", "Evidence: **synthetic**. No Sentinel incident was created.",
             f"Policy: {value['policy_version']}; evaluated as of {value['as_of']}.", "",
             "| Account | Current score | Peak score | Finding |", "|---|---|---|---|"]
    found = {f["entity_id"]:f for f in value["findings"]}
    for entity in value["entities"]:
        lines.append(f"| {entity['entity_id']} | {entity['current']['score']} | {entity['peak']['score']} | {'High priority' if entity['entity_id'] in found else 'No qualifying sequence'} |")
    for finding in value["findings"]:
        lines.extend(["", "## " + finding["entity_id"], "", f"First detection: {finding['first_detected']}; score {finding['first_score']}; peak {finding['peak_score']}.",
            f"Confidence: {finding['confidence']} (not calibrated); health limitations: {', '.join(finding['health_limitations']) or 'none'}.",
            "Possible ATT&CK techniques: " + ", ".join(finding["techniques"]) + ".", "", "Investigation steps:", ""])
        lines.extend("- " + step for step in finding["investigation_steps"])
        lines.extend(["", "Evidence chain (all synthetic):", "", "| UTC time | Source | Signal | Original event ID | Host / scope |",
                      "|---|---|---|---|---|"])
        lines.extend(f"| {e['time']} | {e['source']} | {e['kind']} | {e['source_event_id']} | {e['host'] or e['resource'] or 'Unknown'} |"
                     for e in finding['evidence_chain'])
    lines.extend(["", "Scores are explainable lab heuristics, not probabilities or production verdicts.",
                  "Health gaps limit confidence without suppressing otherwise valid evidence. Related IPs/hosts do not merge actors.",
                  "Network calls, Azure changes and actual incident creation: zero."])
    return "\n".join(lines) + "\n"


def dashboard(value):
    # Prevent script termination even if a future report adds free-form text.
    embedded = json.dumps(value, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atlas Financial synthetic risk timeline</title><style>
body{margin:0;background:#0b1424;color:#e5edf9;font:16px system-ui,sans-serif;line-height:1.5;padding:28px}main{max-width:1180px;margin:auto}h1,h2{color:#79d8c8}.notice{background:#243248;border-left:4px solid #f1c75c;padding:16px}label{display:block;margin-top:14px}select,input{font:inherit;padding:6px}input{width:100%;padding:0}table{border-collapse:collapse;display:block;overflow:auto;width:100%;margin:16px 0}td,th{border:1px solid #3a4c64;padding:9px;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere}.cards{display:flex;gap:24px;flex-wrap:wrap}.cards p{padding:16px;background:#192a41}.score{font-size:1.8rem}svg{width:100%;height:190px;background:#15233a}polyline{fill:none;stroke:#79d8c8;stroke-width:3}line{stroke:#ecb55a;stroke-dasharray:6 4}
</style><main><h1>Atlas Financial · entity risk timeline</h1><p class="notice"><strong>SYNTHETIC LABORATORY SCENARIO.</strong> No Azure events were generated and no Sentinel incident was created. Priority and confidence are different; these scores are not probabilities.</p>
<label for="actor">Account</label><select id="actor"></select><label for="replay">Replay observed event times</label><input id="replay" type="range" min="0" value="0"><p id="at"></p><div class="cards"><p>Replay score<br><strong class="score" id="score"></strong></p><p>Entity peak<br><strong class="score" id="peak"></strong></p><p>Ordered sequence qualifies<br><strong id="eligible"></strong></p></div>
<svg viewBox="0 0 1000 180" role="img" aria-label="Entity risk score across recorded event times"><line id="threshold" x1="0" x2="1000" y1="72" y2="72"></line><polyline id="curve"></polyline></svg><p>Dashed line: finding threshold. X axis: ordered replay samples; timestamps are listed below.</p>
<table><caption>Score history</caption><thead><tr><th>UTC time</th><th>Score</th><th>Sequence bonus</th><th>Eligible</th></tr></thead><tbody id="timeline"></tbody></table>
<h2>Current contribution ledger</h2><p>Each contribution includes confidence, baseline factor, decay and cap allocation. The replay uses engine-generated scores.</p><pre id="contributions"></pre>
<h2>Synthetic finding and investigation context</h2><pre id="finding"></pre><h2>Related entities</h2><pre id="related"></pre><h2>Health and analysis limits</h2><pre id="limits"></pre><footer>Offline only. No external assets, tracking or requests.</footer></main>
<script id="data" type="application/json">""" + embedded + """</script><script>
const report=JSON.parse(document.getElementById('data').textContent),select=document.getElementById('actor'),slider=document.getElementById('replay');
for(const entity of report.entities){const option=document.createElement('option');option.value=entity.entity_id;option.textContent=entity.entity_id;select.appendChild(option);}
function render(reset){const entity=report.entities.find(e=>e.entity_id===select.value);if(!entity){document.getElementById('at').textContent='No retained synthetic events.';return;}if(reset){slider.max=entity.timeline.length-1;slider.value=slider.max;}const point=entity.timeline[Number(slider.value)];document.getElementById('at').textContent='Replay time: '+point.time+' · Analysis as of '+report.as_of;document.getElementById('score').textContent=point.score.toFixed(2);document.getElementById('peak').textContent=entity.peak.score.toFixed(2);document.getElementById('eligible').textContent=String(point.eligible);document.getElementById('curve').setAttribute('points',entity.timeline.map((p,i)=>(entity.timeline.length===1?0:1000*i/(entity.timeline.length-1))+','+(180-1.8*p.score)).join(' '));const thresholdY=180-1.8*report.policy.finding_threshold;document.getElementById('threshold').setAttribute('y1',thresholdY);document.getElementById('threshold').setAttribute('y2',thresholdY);const rows=document.getElementById('timeline');rows.replaceChildren();for(const p of entity.timeline){const row=document.createElement('tr');for(const value of [p.time,p.score,p.sequence_bonus,p.eligible]){const td=document.createElement('td');td.textContent=String(value);row.appendChild(td);}rows.appendChild(row);}document.getElementById('contributions').textContent=JSON.stringify({as_of:report.as_of,score:entity.current.score,sequence_bonus:entity.current.sequence_bonus,contributions:entity.current.contributions},null,2);document.getElementById('finding').textContent=JSON.stringify(report.findings.filter(f=>f.entity_id===entity.entity_id),null,2);document.getElementById('related').textContent=JSON.stringify(entity.related_entities,null,2);document.getElementById('limits').textContent=JSON.stringify({health:report.health_context,limits:report.limits,counts:report.counts},null,2);}
select.addEventListener('change',()=>render(true));slider.addEventListener('input',()=>render(false));render(true);
</script></html>"""


def write_report(value, output):
    path = Path(output)
    path.mkdir(parents=True, exist_ok=True)
    for filename, text in (("report.json", json.dumps(value, indent=2, allow_nan=False) + "\n"),
                           ("investigation.md", markdown(value)), ("dashboard.html", dashboard(value))):
        (path / filename).write_text(text, encoding="utf-8")
