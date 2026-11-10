# 09 · Linking the inventory to telemetry and provenance

**Make the inventory and the telemetry share one key:** every agent emits its CMDB `agent_uid` as `gen_ai.agent.id` on its agent spans, and every model call, tool call and data lookup is a child span. The provenance graph is then a join of spans to CMDB records, and the same join exposes shadow agents.

## One key, two systems

```mermaid
flowchart LR
    subgraph CMDB["Agent CMDB"]
        CI["Deployment CI<br/>agent_uid = agt-kyc-prod"]
    end
    subgraph OTEL["Telemetry"]
        SP["invoke_agent span<br/>gen_ai.agent.id = agt-kyc-prod"]
    end
    CI <==>|"same value"| SP
    SP --> J["Provenance join"]
    CI --> J
    J --> G[("Lineage graph<br/>who · what · on whose behalf")]

    classDef key fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d1b2a
    class CI,SP key
```

If the CMDB key and the trace attribute differ, every downstream join breaks. Set the value at deploy time from the CMDB record, never by hand in code.

## One account-opening request as a span tree

OpenTelemetry's GenAI conventions already define the span types an agent run needs: `invoke_agent`, `invoke_workflow`, `execute_tool`, `retrieval`, and inference calls such as `chat`.

```mermaid
flowchart TB
    W["invoke_workflow<br/>gen_ai.workflow.name = account_opening<br/>gen_ai.conversation.id = case-7f3a"]
    A["invoke_agent<br/>gen_ai.agent.id = agt-kyc-prod<br/>gen_ai.agent.version = 2.4.1"]
    C1["chat<br/>gen_ai.request.model · gen_ai.response.model<br/>gen_ai.provider.name"]
    R["retrieval<br/>gen_ai.data_source.id = kyc-policy-kb"]
    T1["execute_tool<br/>gen_ai.tool.name = ckyc_lookup"]
    T2["execute_tool<br/>gen_ai.tool.name = cbs_create_customer"]
    C2["chat<br/>final decision summary"]

    W --> A
    A --> C1
    A --> R
    A --> T1
    A --> T2
    A --> C2

    classDef wf fill:#ede7f6,stroke:#5e35b1,color:#1b1b1b
    classDef ag fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef ch fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    classDef tl fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    class W wf
    class A ag
    class C1,C2 ch
    class R,T1,T2 tl
```

## Join keys

| Telemetry attribute | Joins to CMDB entity | Bank use |
|---|---|---|
| `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.version` | Agent deployment CI (`agent_uid`, version) | Which approved agent and version acted |
| `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.provider.name` | Model | The model that actually served the call (response model), for re-validation |
| `gen_ai.tool.name`, `gen_ai.tool.type` | Tool / MCP server | Which CBS, LOS or KYC API was called |
| `gen_ai.data_source.id` (retrieval spans) | Data source | Which knowledge base or customer store was read |
| `gen_ai.workflow.name` (`invoke_workflow`) | Business flow | Account opening, transfer, loan sanction, claim |
| `gen_ai.conversation.id` | Case or session | Ties steps of one customer request together |
| Resource attributes (`service.name`, `k8s.pod.uid`, container image) | Workload fingerprint on the deployment CI | Confirms which deployment emitted the span |
| Custom: runtime SPIFFE ID, on-behalf-of principal, case ID (tokenised) | Identity, owner, business record | Who the agent acted for, without raw PII in spans |

> **Stability warning.** Every `gen_ai.*` attribute is still at Development status, and on 12 June 2026 the conventions moved to a dedicated [`semantic-conventions-genai`](https://github.com/open-telemetry/semantic-conventions-genai) repository with no tagged release yet. Keep attribute names behind a mapping layer, normalise older SDK dialects in an OpenTelemetry Collector `transform` processor, and expect renames. Prompt and response text are opt-in events, not span attributes, which suits a bank's PII posture.

## From spans to provenance: W3C PROV

Map the joined data onto the W3C PROV model, which provenance and audit teams will recognise.

```mermaid
flowchart LR
    EMP(["prov:Agent<br/>Branch employee"])
    AG(["prov:Agent<br/>agt-kyc-prod<br/>(CMDB deployment CI)"])
    ACT["prov:Activity<br/>execute_tool<br/>cbs_create_customer"]
    IN[("prov:Entity<br/>KYC documents")]
    OUT[("prov:Entity<br/>Customer record<br/>in core banking")]

    AG -->|actedOnBehalfOf| EMP
    ACT -->|wasAssociatedWith| AG
    ACT -->|used| IN
    OUT -->|wasGeneratedBy| ACT
    OUT -->|wasAttributedTo| AG

    classDef agent fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef act fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef ent fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    class EMP,AG agent
    class ACT act
    class IN,OUT ent
```

| PROV concept | Comes from |
|---|---|
| **Agent** (`prov:Agent`) | The CMDB agent deployment, plus the employee or customer it acted for (`actedOnBehalfOf`) |
| **Activity** (`prov:Activity`) | Each `invoke_agent`, `execute_tool` and `retrieval` span |
| **Entity** (`prov:Entity`) | The customer record, document, account or loan file read (`used`) or created (`wasGeneratedBy`) |

For dataset-level lineage between batch systems, emit OpenLineage events with the job namespace set to `agent_uid`, so record-level and dataset-level lineage share the same agent key.

## Telemetry feeds the inventory back

Run three checks continuously on the span stream:

```mermaid
flowchart TD
    S(["Span stream"]) --> Q1{"gen_ai.agent.id<br/>has a CMDB record?"}
    Q1 -- No --> X1["Shadow agent alert"]
    Q1 -- Yes --> Q3{"Runtime identity =<br/>registered identity?"}
    Q3 -- No --> X3["Impersonation or<br/>credential-sharing flag"]
    Q3 -- Yes --> OK["Join to provenance graph"]

    CM(["CMDB, scheduled check"]) --> Q2{"Agent emitted any<br/>spans in 30 days?"}
    Q2 -- No --> X2["Instrumentation gap<br/>or dormant agent"]
    Q2 -- Yes --> OK2["Telemetry coverage OK"]

    X1 --> REC["Reconciliation<br/>(new evidence)"]
    X2 --> REC
    X3 --> REC

    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    classDef warn fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef good fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    class X1,X3 bad
    class X2 warn
    class OK,OK2 good
```

---
[← 08 ServiceNow vs scratch](08-servicenow-vs-scratch.md) · [Index](README.md) · [Next: 10 Regulatory drivers →](10-regulatory.md)
