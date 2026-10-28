"""Offline plan only; never authenticates, installs an agent or sends logs."""
import argparse
import json
from pathlib import Path
from ama.plan import fingerprint, public_plan, resources, validate_dcr

parser = argparse.ArgumentParser(description="Offline AMA plan; never deploys or sends logs")
parser.add_argument("--render-private", action="store_true", help="Render bodies from the existing ignored subscription pin; no Azure call")
args = parser.parse_args()
path = Path(".local/ama")
path.mkdir(parents=True, exist_ok=True)
report = public_plan() | {"plan_sha256": fingerprint(), "evidence": "offline-plan"}
(path / "plan.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
if args.render_private:
    pin = json.loads(Path(".local/azure-target.json").read_text(encoding="utf-8"))
    workspace = ("/subscriptions/" + pin["subscription_id"] + "/resourceGroups/rg-sentinelops-mxdr/providers/"
                 "Microsoft.OperationalInsights/workspaces/law-sentinelops-mxdr-euw")
    bodies = resources(workspace)
    validate_dcr(bodies["dcr"], workspace)
    (path / "resource-bodies.private.json").write_text(json.dumps(bodies, indent=2) + "\n", encoding="utf-8")
    print("Rendered fixed resource bodies into ignored .local/ama/resource-bodies.private.json; Azure requests: 0")
