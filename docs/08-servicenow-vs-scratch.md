# 08 · Two deployment paths: ServiceNow or from scratch

**Build the same collectors and reconciliation engine in both cases; only the system of record and the governance workflows change.** If the bank runs ServiceNow AI Control Tower, it becomes one source and the sink. If not, your platform hosts the agent CMDB itself, modelled so it can sync to ServiceNow later.

## Which path?

```mermaid
flowchart TD
    Q1{"Bank runs ServiceNow<br/>AI Control Tower?"}
    Q1 -- Yes --> Q2{"AICT cloud connectors<br/>entitled?"}
    Q2 -- Yes --> A["Path A<br/>AICT = source and sink<br/>your platform fills the gaps"]
    Q2 -- No --> A2["Path A, reduced<br/>your platform also runs<br/>the cloud connectors"]
    Q1 -- "No, or another CMDB" --> B["Path B<br/>your platform hosts<br/>the agent CMDB"]
    B -.->|"later sync,<br/>not a migration"| A

    classDef a fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef b fill:#ede7f6,stroke:#5e35b1,color:#1b1b1b
    class A,A2 a
    class B b
```

## Path A: ServiceNow AI Control Tower already in place

AICT holds an AI asset inventory in the CMDB (AI systems, models, prompts, datasets, MCP servers) with a managed/unmanaged flag, steward review and duplicate detection. Its discovery covers ServiceNow-native AI, hyperscaler connectors (AWS Bedrock and SageMaker, Azure AI Foundry, GCP Vertex) and agent auto-discovery from observability logs. The data-model foundation plugin is free; cloud connectors may need an AICT entitlement.

```mermaid
flowchart LR
    subgraph SN["ServiceNow"]
        AICT["AI Control Tower<br/>inventory, steward review,<br/>lifecycle, GRC"]
        TBL[("alm_ai_system_digital_asset<br/>cmdb_ci_function_ai<br/>cmdb_ci_appl_ai_application<br/>cmdb_ci_function_mcp")]
        AICT --- TBL
    end

    subgraph YOU["Your platform"]
        COL["On-prem collectors<br/>eBPF, gateway, model-server scans"]
        IDJ["Identity-level join"]
        SHD["Shadow classification"]
        ENG["Reconciliation engine"]
        COL --> ENG
        IDJ --> ENG
        SHD --> ENG
    end

    TBL -->|"1 · read as a source"| ENG
    ENG -->|"3 · write back CIs via<br/>identification and<br/>reconciliation API"| TBL
    ENG -->|"3 · digital assets via<br/>POST /sn_ent/asset/ai_system"| AICT
    AICT -->|"4 · reuse steward review<br/>and lifecycle workflows"| ENG
```

Step 2 is the gap-filling inside your platform: on-prem runtime discovery, the identity join and shadow classification, which AICT does not cover well.

## Path B: no CMDB, start from scratch

```mermaid
flowchart TB
    subgraph IN["Ingest"]
        COLL["Collectors"] --> BUS["Kafka or NATS<br/>normalized observations"]
        OTC["OpenTelemetry Collector"] --> BUS
        EBPF["eBPF<br/>Tetragon, OpenLIT"] --> BUS
        GW["AI gateway<br/>LiteLLM or agentgateway"] --> BUS
        BOM["cdxgen<br/>CycloneDX AI-BOM"] --> BUS
    end

    BUS --> ENG["Reconciliation engine"]

    subgraph STORE["System of record"]
        PG[("PostgreSQL<br/>CI history, audit")]
        GR[("Graph layer<br/>Apache AGE or Neo4j<br/>agent → tool → data → identity")]
        PG --- GR
    end
    ENG --> PG

    SPIRE["SPIRE + cloud agent<br/>identities, federated to IdP"] --> ENG

    subgraph OUTB["Interfaces out"]
        API["REST API"]
        CDX["CycloneDX export"]
        SCIM["SCIM /Agents to IdP"]
        SNM["ServiceNow-compatible<br/>class mapping"]
    end
    PG --> API
    PG --> CDX
    PG --> SCIM
    PG --> SNM
```

Build the three-layer model (definition, governance record, deployment CI) from day one, using the same class names as AICT where possible.

## Comparison

| Question | Path A (ServiceNow) | Path B (scratch) |
|---|---|---|
| Who owns governance workflows? | ServiceNow (steward review, change, GRC) | Your platform |
| Time to first inventory | Faster for cloud and ServiceNow-native agents | Slower; you build intake and UI |
| On-prem and shadow coverage | Still needs your collectors | Your collectors |
| Licence dependency | AICT entitlement for connectors | None beyond infrastructure |
| Provenance join | Export AICT IDs into traces | Native; same store |

---
[← 07 Reconciliation](07-reconciliation.md) · [Index](README.md) · [Next: 09 Telemetry and provenance →](09-telemetry-provenance.md)
