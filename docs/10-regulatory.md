# 10 · Banking regulatory drivers

**Every major banking regulator now expects an AI inventory, and their field lists converge on the same data model:** owner, purpose, models, data sources, dependencies, lifecycle status and risk. For an Indian bank, RBI's FREE-AI report is the primary driver today; MAS, the EU AI Act and DORA apply to banks with operations in those jurisdictions.

## Timeline

```mermaid
timeline
    title Regulatory milestones that touch the agent inventory
    2025 : Jan · DORA applies (EU)
         : 13 Aug · RBI FREE-AI report released
    2026 : 24 Jun · RBI draft Model Risk Management guidance
         : Jun · EU Digital Omnibus adopted, high-risk dates moved
         : 7 Oct · MAS AI Risk Management Guidelines issued
    2027 : 7 Oct · MAS governance requirements apply
         : 2 Dec · EU AI Act Annex III high-risk obligations apply
    2028 : 7 Oct · MAS lifecycle requirements apply
```

## What each framework asks for

| Framework | Status (November 2026) | What it asks of the inventory |
|---|---|---|
| [RBI FREE-AI report](https://www.mondaq.com/india/financial-services/1672260/rbis-move-toward-ethical-and-responsible-ai-in-financial-sector) | Released 13 August 2025; recommendations not yet binding, expected to flow into RBI master directions | An AI-inventory recommendation (numbered 11 in Mondaq's summary; other summaries number it differently, so cite it by title): a comprehensive internal AI inventory, updated half-yearly, covering all models, use cases, target groups, dependencies, risks and grievances. Also proposes access controls for autonomous AI in the IT Governance Master Direction |
| [RBI draft Model Risk Management guidance](https://www.rbi.org.in/Scripts/Bs_Connect2RegulateDetails.aspx?prid=487) | Draft released 24 June 2026; comments closed 24 July 2026 | Governance and oversight of models, explicitly including AI/ML and third-party models. Check the final text for inventory specifics |
| [MAS Guidelines on AI Risk Management](https://hlc.com/en/publications/mas-issues-new-ai-risk-management-guidelines-for-financial-institutions) | Issued 7 October 2026; governance requirements from 7 October 2027, lifecycle requirements from 7 October 2028 | Inventory recording purpose, ownership, data sources, dependencies, lifecycle status and risk classification, integrated with data, vendor and outsourcing registers. Explicitly covers AI agents and AI embedded in third-party products |
| [EU AI Act](https://www.leaseurope.org/new-application-dates-high-risk-ai-system-rules) (as amended by the Digital Omnibus, adopted June 2026) | Annex III high-risk obligations apply from 2 December 2027 | Creditworthiness assessment of individuals is high-risk, so a loan-sanction agent that scores applicants needs high-risk deployer controls, including logging and human oversight |
| [DORA](https://advisera.com/cdr-2024-1774/ict-asset-management-policy/) (EU) | Applies since January 2025 | Agents are ICT assets. The RTS on ICT risk management requires, per asset: unique identifier, location, classification, owner, business functions supported, continuity requirements, external exposure and interdependencies |

## Where the requirements land in the data model

```mermaid
flowchart LR
    subgraph REG["Regulators ask for"]
        R1["Owner / accountability"]
        R2["Purpose, use case,<br/>business function"]
        R3["Models, incl. third-party"]
        R4["Data sources"]
        R5["Dependencies /<br/>interdependencies"]
        R6["Risk classification"]
        R7["Lifecycle status,<br/>half-yearly snapshot"]
        R8["Unique identifier,<br/>location"]
    end

    subgraph DM["Agent CMDB"]
        D1["OWNER"]
        D2["BUSINESS_FLOW"]
        D3["MODEL<br/>USES_MODEL edge"]
        D4["DATA_SOURCE<br/>READS edge"]
        D5["Graph edges<br/>CALLS_TOOL · READS ·<br/>USES_MODEL · DELEGATES_TO"]
        D6["GOVERNANCE_RECORD<br/>risk_tier"]
        D7["managed_status +<br/>CI history"]
        D8["agent_uid +<br/>platform, environment"]
    end

    R1 --> D1
    R2 --> D2
    R3 --> D3
    R4 --> D4
    R5 --> D5
    R6 --> D6
    R7 --> D7
    R8 --> D8
```

## Coverage by framework

```mermaid
quadrantChart
    title Inventory obligation today vs prescriptiveness of fields
    x-axis Guidance only --> Binding today
    y-axis General --> Field-level detail
    quadrant-1 Build to this now
    quadrant-2 Prepare fields now
    quadrant-3 Watch
    quadrant-4 Map existing controls
    RBI FREE-AI: [0.25, 0.62]
    RBI MRM draft: [0.2, 0.35]
    MAS AIRM: [0.45, 0.8]
    EU AI Act Annex III: [0.4, 0.55]
    DORA RTS: [0.85, 0.85]
```

Positions are a qualitative reading for prioritisation, not a legal assessment.

## What this means for the build

- **Business flow, owner and risk tier are mandatory fields**, not optional enrichment. Every regulator above asks for them.
- **Dependencies must be a graph**, not a text field: DORA's interdependencies and FREE-AI's dependencies are both answered by the `CALLS_TOOL`, `READS`, `USES_MODEL` and `DELEGATES_TO` edges.
- **Third-party AI belongs in the inventory** even with no deployment visibility, as a governance record with zero CIs ([03](03-data-model.md)).
- **Half-yearly snapshots** (FREE-AI) argue for keeping CI history, so the bank can show the inventory as it stood on any reporting date.

Regulation is in motion: FREE-AI is not yet binding and RBI's model-risk guidance is still a draft. This page is a research summary, not legal advice; confirm obligations with the bank's compliance team.

---
[← 09 Telemetry and provenance](09-telemetry-provenance.md) · [Index](README.md) · [Next: 11 Architecture and roadmap →](11-architecture-roadmap.md)
