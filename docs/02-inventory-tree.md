# 02 · The inventory tree

**Classify every agent on two independent axes:** its governance state (managed, unmanaged, shadow, dormant) and its identity state (onboarded or not). This tree is what the inventory dashboard should show first, with a count in every box.

## The tree

```mermaid
flowchart TD
    ALL["All agents<br/>found by any collector"]
    ALL --> M["Managed<br/>approved, owned, on the gateway"]
    ALL --> NM["Not managed"]
    NM --> U["Unmanaged<br/>known to a platform,<br/>no owner or approval"]
    NM --> S["Shadow<br/>seen at runtime,<br/>never registered"]
    NM --> D["Dormant<br/>no activity 30+ days"]

    M --> M2["Onboarded · L2-3"]
    M --> M0["Not onboarded · L0-1"]
    U --> U2["Onboarded · L2-3"]
    U --> U0["Not onboarded · L0-1"]
    S --> S2["Onboarded · L2-3"]
    S --> S0["Not onboarded · L0-1"]
    D --> D2["Onboarded · L2-3"]
    D --> D0["Not onboarded · L0-1"]

    DEC["Declared-only records<br/>planned, or SaaS with no<br/>deployment visibility"]

    classDef good fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b1b1b
    classDef warn fill:#fff8e1,stroke:#f9a825,stroke-width:2px,color:#1b1b1b
    classDef bad fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#1b1b1b
    classDef neutral fill:#f5f5f5,stroke:#757575,stroke-width:2px,color:#1b1b1b
    classDef side fill:#ffffff,stroke:#9e9e9e,stroke-dasharray: 4 4,color:#1b1b1b
    class M good
    class U warn
    class S bad
    class D neutral
    class DEC side
```

Declared-only records sit **beside** the tree: they are governance records with no running deployment yet (or SaaS agents you can govern but not see).

## How each count is computed

| Count | Rule |
|---|---|
| **All agents** | Distinct deployment CIs with runtime activity in the last 30 days, plus dormant ones |
| **Managed** | Approved governance record **and** runtime identity matches the registered one **and** traffic flows through the AI gateway |
| **Unmanaged** | Found by a platform API or collector, but no approved governance record or active owner |
| **Shadow** | Runtime evidence (traffic, traces, logs) with no matching inventory record |
| **Dormant** | Registered or found in code, with no runtime activity for 30+ days |
| **Identity onboarded** | Identity level 2 or 3 ([06](06-identity-onboarding.md)), counted inside each state |

## How an agent lands in a box

```mermaid
flowchart TD
    START(["Agent observed by any collector"]) --> REG{"Matching inventory<br/>record?"}
    REG -- No --> RT{"Runtime activity?"}
    RT -- Yes --> SHADOW["Shadow"]
    RT -- No --> CANDIDATE["Code-only finding<br/>create unmanaged record"]
    REG -- Yes --> APP{"Approved governance<br/>record and active owner?"}
    APP -- No --> UNM["Unmanaged"]
    APP -- Yes --> ACT{"Activity in<br/>last 30 days?"}
    ACT -- No --> DOR["Dormant"]
    ACT -- Yes --> IDM{"Runtime identity =<br/>registered identity?"}
    IDM -- No --> UNM
    IDM -- Yes --> GW{"Traffic via<br/>AI gateway?"}
    GW -- No --> UNM
    GW -- Yes --> MAN["Managed"]

    SHADOW --> LVL["Then assign identity level 0-3"]
    UNM --> LVL
    DOR --> LVL
    MAN --> LVL
    CANDIDATE --> LVL

    classDef good fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    classDef warn fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    classDef neutral fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    class MAN good
    class UNM,CANDIDATE warn
    class SHADOW bad
    class DOR neutral
```

## What to do in each cell

| Governance state | Identity onboarded (L2–3) | Not onboarded (L0–1) |
|---|---|---|
| **Managed** | Healthy; monitor for drift | **Close first**: already approved, onboarding is quick |
| **Unmanaged** | Assign owner, run intake | Assign owner, run intake, then onboard identity |
| **Shadow** | Rare; investigate why an identity exists without a record | **Highest risk**: find owner, contain, onboard or kill |
| **Dormant** | Confirm, retire, revoke identity | Confirm, retire, rotate or revoke any keys |

## "Managed" ≠ "hosted on a managed service"

```mermaid
quadrantChart
    title Governance and hosting are independent
    x-axis Self-hosted --> Platform-hosted
    y-axis Not governed --> Governed
    quadrant-1 Governed platform agent
    quadrant-2 Governed self-hosted agent
    quadrant-3 Shadow or unmanaged self-hosted
    quadrant-4 Shadow maker agent on a platform
```

A Copilot Studio agent built by an employee in the default environment is platform-hosted **and** shadow. A LangGraph service on OpenShift that passed intake and runs behind the gateway is self-hosted **and** managed. Hosting is a filter on the tree, not a branch of it.

---
[← 01 Why inventory](01-why-inventory.md) · [Index](README.md) · [Next: 03 Data model →](03-data-model.md)
