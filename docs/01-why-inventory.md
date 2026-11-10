# 01 · Why inventory is step 1

**Provenance is only as good as the actor IDs inside it.** Every span, tool call and data read in a business flow must resolve to a known agent record, or the lineage graph has holes exactly where the risk is.

## One business flow, end to end

An account-opening request, traced. The provenance graph can only explain step 7 if the agent ID resolves in the inventory.

```mermaid
sequenceDiagram
    autonumber
    actor Emp as Branch employee
    participant KYC as KYC onboarding agent
    participant CBS as Core banking API
    participant OTel as Telemetry pipeline
    participant PROV as Provenance graph
    participant INV as Agent CMDB

    Emp->>KYC: Open account for customer case C-1029
    KYC->>CBS: create_customer
    KYC-->>OTel: span invoke_agent, gen_ai.agent.id = agt-kyc-prod
    KYC-->>OTel: span execute_tool create_customer
    OTel->>PROV: spans for case C-1029
    PROV->>INV: resolve agt-kyc-prod
    INV-->>PROV: owner, version, model, identity, approval, tools, data access
    Note over PROV,INV: Lineage is attributable only if every agent ID resolves
```

## With and without an inventory

```mermaid
flowchart LR
    subgraph WITHOUT["Without the inventory"]
        direction TB
        X1["Trace shows agent=kyc-bot-v2<br/>called the CBS API"]
        X2["Who owns it? Which model?<br/>Was it approved?"]
        X3["Auditor question on a<br/>loan decision: unanswerable"]
        X4["Shadow agent on the same API<br/>looks legitimate or invisible"]
        X1 --> X2 --> X3
        X2 --> X4
    end

    subgraph WITH["With the inventory"]
        direction TB
        Y1["Trace shows<br/>gen_ai.agent.id = agt-kyc-prod"]
        Y2["CMDB returns owner, version,<br/>model, identity, tools, data"]
        Y3["Decision is explainable<br/>at that point in time"]
        Y4["Unknown agent IDs<br/>raise a shadow alert"]
        Y1 --> Y2 --> Y3
        Y2 --> Y4
    end

    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    classDef good fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    class X1,X2,X3,X4 bad
    class Y1,Y2,Y3,Y4 good
```

## What the inventory module must answer, continuously

```mermaid
flowchart TB
    Q["Agent inventory"]
    Q --> Q1["How many agents exist?"]
    Q --> Q2["How many are managed?"]
    Q --> Q3["How many have an<br/>onboarded identity?"]
    Q --> Q4["Which ones did<br/>nobody approve?"]
    Q1 --> A1["Count of deployment CIs<br/>active in 30 days + dormant"]
    Q2 --> A2["Approved record AND matching<br/>identity AND gateway traffic"]
    Q3 --> A3["Identity level 2 or 3"]
    Q4 --> A4["Shadow + unmanaged<br/>+ dormant with live credentials"]
```

The rest of these docs explain how to compute each answer: the tree ([02](02-inventory-tree.md)), the record ([03](03-data-model.md)), where the evidence comes from ([04](04-discovery.md), [05](05-shadow-agents.md), [06](06-identity-onboarding.md)) and how it is merged ([07](07-reconciliation.md)).

---
[← Index](README.md) · [Next: 02 The inventory tree →](02-inventory-tree.md)
