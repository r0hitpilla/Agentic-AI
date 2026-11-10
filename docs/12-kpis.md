# 12 · Coverage KPIs and dashboard views

**Lead the dashboard with four numbers: total agents, percent sanctioned, percent identity-onboarded, and open shadow agents.** Everything else explains why those numbers move.

## Headline row

```mermaid
flowchart LR
    K1["Total agents<br/>active 30 days + dormant<br/><i>trend only</i>"]
    K2["Sanctioned rate<br/>managed ÷ total<br/><i>target 100% of prod</i>"]
    K3["Identity onboarded<br/>L2-3 ÷ total<br/><i>target 95% of prod</i>"]
    K4["Open shadow agents<br/>untriaged shadow + unmanaged<br/><i>target 0 older than 7 days</i>"]

    classDef tile fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d1b2a
    class K1,K2,K3,K4 tile
```

## What drives each headline number

```mermaid
flowchart TB
    K2["Sanctioned rate"]
    K3["Identity onboarded"]
    K4["Open shadow agents"]

    D1["Owner coverage"] --> K2
    D2["Gateway coverage"] --> K2
    D3["Drift reviews overdue"] --> K2

    D4["Dormant with<br/>live credentials"] --> K3
    D5["Identity gap list<br/>L0 and L1 by risk tier"] --> K3

    D6["Shadow time-to-detect"] --> K4
    D7["Telemetry coverage"] --> K4
    D2 --> K4

    classDef head fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d1b2a
    classDef drv fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    class K2,K3,K4 head
    class D1,D2,D3,D4,D5,D6,D7 drv
```

## KPI definitions

| KPI | Definition | Suggested starting target |
|---|---|---|
| Total agents | Distinct deployment CIs with activity in the last 30 days, plus dormant ones; declared-only records reported separately | Trend only |
| Sanctioned rate | Sanctioned deployments ÷ total, per the three-part decision rule ([05](05-shadow-agents.md)) | 100% of production |
| Identity onboarded | Deployments at identity level 2 or 3 ÷ total | 95% of production within two quarters |
| Open shadow agents | Shadow and unmanaged records not yet triaged | Zero older than 7 days |
| Shadow time-to-detect | First runtime evidence → shadow alert | Under 24 hours |
| Owner coverage | Deployments with an active named owner | 100% of production |
| Gateway coverage | Agents whose model and tool traffic flows through the AI gateway | 100% of production |
| Telemetry coverage | Agents emitting spans with a valid agent key (resource attribute or `gen_ai.agent.id`) that matches their attested identity | 100% of agents in regulated flows |
| Dormant with live credentials | Dormant agents whose identity or keys are still active | Zero |
| Drift reviews overdue | Model, tool or data changes without a completed re-review | Zero older than 14 days |

The targets are starting proposals for the bank's risk committee to adjust, not industry benchmarks.

## Dashboard views

```mermaid
mindmap
  root((Agent inventory dashboard))
    Inventory tree
      managed, unmanaged, shadow, dormant
      by identity level
      drill to each agent
    Business-flow view
      account opening, transfers, loan sanction, claims
      agents per flow
      identity level, tools, data
    Environment heatmap
      AWS, Azure, GCP
      on-prem, SaaS, endpoints
    Identity gap list
      Level 0 and 1
      sorted by risk tier
    Shadow queue
      evidence
      suggested owner
    Regulatory snapshot
      inventory as of a reporting date
      FREE-AI, MAS, DORA fields
```

| View | Answers | Primary audience |
|---|---|---|
| Inventory tree | How many, how many managed, how many onboarded | CISO, AI steward |
| Business-flow view | Which agents touch account opening, transfers, loan sanction, claims, and with what access | Business owners, model risk |
| Environment heatmap | Where the gaps are: AWS, Azure, GCP, on-prem, SaaS | Platform teams |
| Identity gap list | Which Level 0 and 1 agents to fix first, by risk tier | IAM team |
| Shadow queue | New shadow and unmanaged findings, with evidence and suggested owner | AI steward, SOC |
| Regulatory snapshot | The inventory as of a reporting date, with the fields FREE-AI, MAS or DORA ask for | Compliance, audit |

## Example: what a first snapshot might look like

Made-up numbers, only to show how the tree and the KPIs relate; here the sanctioned rate would be 34 ÷ 120 = 28%. Close the managed-but-not-onboarded box first: those agents are already approved, so onboarding them is quick.

```mermaid
pie showData
    title Illustrative first snapshot · 120 agents by governance state
    "Managed" : 34
    "Unmanaged" : 41
    "Shadow" : 29
    "Dormant" : 16
```

---
[← 11 Architecture and roadmap](11-architecture-roadmap.md) · [Index](README.md) · [Next: 13 Open questions →](13-open-questions.md)
