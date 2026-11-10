# 07 · Reconciliation and classification engine

**Every collector emits raw observations; the engine merges them into one deployment CI per agent**, decides which source wins for each attribute, and computes managed status, identity level and a confidence score. Without this step, one agent seen by five collectors becomes five inventory rows.

## Pipeline

```mermaid
flowchart LR
    O1["Platform API<br/>observation"] --> N
    O2["Gateway<br/>observation"] --> N
    O3["eBPF / workload<br/>observation"] --> N
    O4["Identity<br/>observation"] --> N
    O5["Code / AI-BOM<br/>observation"] --> N

    N["Normalize<br/>common schema"] --> I["Identify<br/>strongest key first"]
    I --> M{"Strong match?"}
    M -- yes --> MG["Auto-merge into<br/>existing CI"]
    M -- weak --> Q["Steward queue<br/>candidate merge"]
    M -- none --> NEW["Create new CI"]
    MG --> P["Apply source-of-truth<br/>per attribute"]
    Q --> P
    NEW --> P
    P --> C["Compute<br/>managed_status · identity_level<br/>confidence · drift"]
    C --> CMDB[("Agent CMDB")]
```

## Identification rules, strongest first

```mermaid
flowchart TB
    R1["1 · Platform-native ID<br/>Bedrock ARN, Entra object ID,<br/>Reasoning Engine name, sn_aia_agent sys_id"]
    R2["2 · Runtime identity<br/>SPIFFE ID, AgentCore workload identity,<br/>service principal app ID"]
    R3["3 · Gateway credential<br/>per-agent virtual key or client ID"]
    R4["4 · Workload fingerprint<br/>K8s UID + image digest,<br/>VM host + process path"]
    R5["5 · Code location<br/>repo + path + agent name"]
    R6["6 · Name similarity<br/>same name, two environments"]

    R1 --> R2 --> R3 --> R4 --> R5 --> R6

    classDef auto fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    classDef env fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef cand fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef never fill:#ffebee,stroke:#c62828,color:#1b1b1b
    class R1,R2,R3 auto
    class R4 env
    class R5 cand
    class R6 never
```

| Rank | Merge behaviour |
|---|---|
| 1–3 | Auto-merge |
| 4 | Auto-merge within one environment only |
| 5 | Candidate merge; a steward confirms |
| 6 | Candidate only; never auto-merge |

This mirrors how ServiceNow's identification and reconciliation engine treats CIs; AI Control Tower also ships duplicate-AI-asset detection for steward review.

## Which source wins, per attribute

```mermaid
flowchart LR
    subgraph PEOPLE["People assert"]
        G["Governance record"] --> A1["owner · business flow · risk tier"]
    end
    subgraph IAM["Access systems grant"]
        I["IdP / IAM"] --> A2["identity · permissions"]
    end
    subgraph RUNTIME["Runtime proves"]
        R["Gateway, traces,<br/>eBPF, logs"] --> A3["model actually used ·<br/>status · last seen"]
    end
    subgraph DECLARED["Platforms declare"]
        D["Platform API,<br/>image digest"] --> A4["version · declared tools<br/>and data sources"]
    end
```

| Attribute | Source of truth | Why |
|---|---|---|
| Owner, business flow, risk tier | Governance record | Only people can assert accountability |
| Identity and permissions | IdP / IAM | Configuration can lie; the IdP grants access |
| Model actually used | Gateway or traces, then platform API | Runtime beats configuration |
| Tools and data sources | Platform API **plus** gateway MCP/tool logs | Union; flag observed-but-undeclared |
| Status, last seen | Runtime evidence | No traffic means dormant, whatever the config says |
| Version | Platform API or image digest | Ties to the code artifact |

## Confidence score

How many independent planes corroborate a record. Suggested starting weights (capped at 100); records below 40 go to a steward queue.

```mermaid
pie showData
    title Confidence weights per evidence plane
    "Platform API" : 40
    "Identity" : 25
    "Runtime" : 20
    "Code" : 15
```

## Drift and re-review

A change in model, a new tool or data source, a new identity, or a new caller raises a re-review task. The CSA registry draft uses the same triggers (model update, capability expansion) to invalidate an agent's trust profile.

```mermaid
stateDiagram-v2
    [*] --> Managed
    Managed --> DriftDetected: model, tool, data,<br/>identity or caller changed
    DriftDetected --> UnderReview: re-review task raised
    UnderReview --> Managed: change approved
    UnderReview --> Suspended: change rejected or risky
    Suspended --> Managed: remediated
    Managed --> Dormant: no activity 30+ days
    Dormant --> Retired: owner confirms
    Dormant --> Managed: activity resumes
    Retired --> [*]
```

---
[← 06 Identity](06-identity-onboarding.md) · [Index](README.md) · [Next: 08 ServiceNow vs scratch →](08-servicenow-vs-scratch.md)
