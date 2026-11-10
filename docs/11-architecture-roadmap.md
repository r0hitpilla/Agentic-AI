# 11 · Reference architecture and roadmap

**Six kinds of source feed one reconciliation engine and one agent CMDB; the dashboard, provenance join, registry sync and alerts all read from that single store.** Build it in four phases, starting where evidence is cheapest (cloud and SaaS APIs) and ending where it is hardest (runtime identity and provenance).

## Component view

```mermaid
flowchart TB
    subgraph SRC["1 · Discovery sources"]
        direction LR
        C1["Cloud agent APIs<br/>Bedrock, AgentCore,<br/>Foundry, Agent Runtime"]
        C2["SaaS platforms<br/>ServiceNow, Salesforce,<br/>Copilot Studio"]
        C3["Code and artifacts<br/>Git, image registries,<br/>AI-BOM, IaC"]
        C4["Workloads<br/>Kubernetes, OpenShift,<br/>VMs, eBPF"]
        C5["Network and gateway<br/>AI gateway, egress,<br/>DNS, model servers"]
        C6["Identity<br/>IdP, SPIRE, IAM,<br/>secret vaults"]
    end

    BUS["2 · Collectors publish normalized observations<br/>Kafka or NATS"]
    REC["3 · Reconciliation and classification<br/>merge · source of truth · status · identity level · confidence"]
    CMDB[("4 · Agent CMDB<br/>definitions · governance records · deployment CIs<br/>relationship graph · CI history")]

    subgraph OUT["5 · Consumers"]
        direction LR
        O1["Dashboard and API"]
        O2["Provenance join"]
        O3["Registry sync<br/>ServiceNow, clouds"]
        O4["Alerts and reports"]
    end

    SRC --> BUS --> REC --> CMDB --> OUT
    O2 -.->|"unknown agent IDs,<br/>identity mismatches"| REC

    classDef anchor fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d1b2a
    class CMDB anchor
```

The dashed line is the feedback loop: spans that reference unknown agents, or show a different identity, go back into reconciliation as new evidence.

## Data flow for one new agent

What happens when a team deploys a new loan agent on OpenShift without telling anyone:

```mermaid
sequenceDiagram
    autonumber
    participant K8s as OpenShift
    participant GW as AI gateway
    participant EB as eBPF collector
    participant BUS as Event bus
    participant REC as Reconciliation
    participant CMDB as Agent CMDB
    participant ST as AI steward

    K8s->>BUS: New pod, image has langgraph + LLM key env var
    EB->>BUS: Pod calls an LLM endpoint
    GW->>BUS: Unknown caller rejected (no virtual key)
    BUS->>REC: Three observations, same pod UID
    REC->>REC: Merge on workload fingerprint (rank 4)
    REC->>CMDB: New CI · managed_status = shadow · identity_level = 0
    CMDB->>ST: Shadow queue item with evidence and suggested owner
    ST->>CMDB: Owner found, intake started
    Note over ST,CMDB: After approval, SPIFFE ID and gateway key issued,<br/>status moves to managed, identity level to 2
```

## Phased roadmap

Phases follow dependencies, not a calendar: identity work needs the gateway and collectors in place, and the provenance join needs stable agent IDs. Durations depend on the size of the bank's estate and whether ServiceNow is in play.

```mermaid
flowchart LR
    P1["Phase 1 · Foundation<br/>data model, intake,<br/>cloud and SaaS connectors"]
    G1{{"Gate: every cloud and<br/>SaaS agent in the CMDB"}}
    P2["Phase 2 · On-prem and code<br/>repo and AI-BOM scan,<br/>K8s and VM collectors,<br/>AI gateway rollout"]
    G2{{"Gate: prod LLM egress<br/>only via the gateway"}}
    P3["Phase 3 · Identity<br/>identity-level join,<br/>SPIRE on-prem,<br/>shadow rules and eBPF"]
    G3{{"Gate: identity level<br/>known for every agent"}}
    P4["Phase 4 · Provenance<br/>OTel span join,<br/>drift reviews,<br/>ServiceNow sync"]
    G4{{"Gate: first half-yearly<br/>inventory snapshot"}}

    P1 --> G1 --> P2 --> G2 --> P3 --> G3 --> P4 --> G4

    classDef gate fill:#e3f2fd,stroke:#1565c0,color:#0d1b2a
    class G1,G2,G3,G4 gate
```

| Phase | Builds | Depends on | Exit gate |
|---|---|---|---|
| 1 · Foundation | Three-layer data model, intake form, AWS / Azure / GCP / SaaS connectors, first dashboard | — | Every cloud and SaaS agent has a CI and a governance record |
| 2 · On-prem and code | cdxgen AI-BOM scan, OpenShift and VM collectors, model-server scan, bank AI gateway with per-agent keys | Phase 1 data model | Production LLM egress only via the gateway |
| 3 · Identity | `RUNS_AS` join, SPIRE on-prem, identity-level computation, shadow classification, eBPF evidence | Gateway and collectors | Identity level known for every deployment |
| 4 · Provenance | `gen_ai.agent.id` = `agent_uid` enforced, span join, PROV graph, drift reviews, ServiceNow sync | Stable agent IDs and identities | First half-yearly inventory snapshot (FREE-AI) |

## Where it runs

```mermaid
flowchart TB
    subgraph DC["Bank data centre · all inventory data stays here"]
        CMDB[("Agent CMDB")]
        ENG["Reconciliation engine"]
        COL["On-prem collectors"]
        GW["AI gateway"]
        SPIRE["SPIRE server"]
        OTC["OTel Collector"]
    end
    subgraph CLOUD["Cloud accounts"]
        RO["Read-only inventory roles<br/>per account / subscription / project"]
    end
    subgraph SAAS["SaaS"]
        API["Read-only API users"]
    end

    RO -->|"pull, private link"| ENG
    API -->|pull| ENG
    COL --> ENG
    GW --> ENG
    SPIRE --> ENG
    OTC --> ENG
    ENG --> CMDB
```

Keep collectors and the store in-house: some open-source tools can send results to a vendor platform by default (see [13](13-open-questions.md)).

---
[← 10 Regulatory drivers](10-regulatory.md) · [Index](README.md) · [Next: 12 KPIs →](12-kpis.md)
