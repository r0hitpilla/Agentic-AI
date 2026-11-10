#!/usr/bin/env python3
"""Render knowledge/scenarios.yaml into the generated section of docs/19-scenarios.md.

Usage:  python3 scripts/render_scenarios.py          # rewrite the doc
        python3 scripts/render_scenarios.py --check  # exit 1 if the doc is stale
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "knowledge" / "scenarios.yaml"
DOC = ROOT / "docs" / "19-scenarios.md"
BEGIN = "<!-- BEGIN GENERATED: scenarios -->"
END = "<!-- END GENERATED: scenarios -->"

RECORD_LABELS = {
    "agent": "Agent",
    "ai_system": "AI system",
    "endpoint_agent": "Endpoint agent",
    "infrastructure": "Infrastructure",
    "external_agent": "External agent",
    "not_agent": "Not an agent",
    "procedure": "Procedure",
}


def cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def render(data):
    out = []
    by_group = {}
    for sc in data["scenarios"]:
        by_group.setdefault(sc["group"], []).append(sc)
    total = len(data["scenarios"])
    out.append(f"{total} scenarios in {len(data['groups'])} groups.\n")
    for g in data["groups"]:
        rows = by_group.get(g["id"], [])
        out.append(f"## {g['id']} · {g['name']}\n")
        out.append("| ID | Situation | Evidence | Record as · expected | Action |")
        out.append("|---|---|---|---|---|")
        for sc in rows:
            signals = "; ".join(sc["signals"])
            record = RECORD_LABELS[sc["record_as"]]
            out.append(
                f"| {sc['id']} | **{cell(sc['title'])}**. {cell(sc['situation'])} "
                f"| {cell(signals)} | **{record}**: {cell(sc['expected'])} | {cell(sc['action'])} |"
            )
        out.append("")
    return "\n".join(out)


def main():
    data = yaml.safe_load(SRC.read_text())
    doc = DOC.read_text()
    head, rest = doc.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    new = head + BEGIN + "\n" + render(data) + "\n" + END + tail
    if "--check" in sys.argv:
        if new != doc:
            print("docs/19-scenarios.md is stale; run scripts/render_scenarios.py")
            sys.exit(1)
        print("docs/19-scenarios.md is up to date")
        return
    DOC.write_text(new)
    print(f"rendered {len(data['scenarios'])} scenarios into {DOC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
