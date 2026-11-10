# 03 · Agent CMDB data model

**Model every agent in three layers** (definition, governance record, deployment) and attach identity, model, tools, data and business flow as first-class entities joined by typed relationships. This mirrors ServiceNow AI Control Tower, so a from-scratch build can sync to ServiceNow later without remodelling.

## Three layers per agent

One KYC onboarding agent running in DEV, UAT and PROD:

```mermaid
flowchart LR
    DEF["Agent definition<br/>KYC onboarding agent<br/><i>what type of agent is this?</i>"]
    GOV["Governance record<br/>owner, approval, risk tier<br/><i>who owns it, is it allowed?</i>"]
    DEV["Deployment CI<br/>DEV"]
    UAT["Deployment CI<br/>UAT"]
    PRD["Deployment CI<br/>PROD"]

    DEF -->|governed by| GOV
    DEF -->|instance of| DEV
    DEF -->|instance of| UAT
    DEF -->|instance of| PRD

    classDef def fill:#ede7f6,stroke:#5e35b1,color:#1b1b1b
    classDef gov fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef ci fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    class DEF def
    class GOV gov
    class DEV,UAT,PRD ci
```

Each deployment CI can be paused or retired on its own. A SaaS agent you cannot see inside still gets a definition and a governance record, with **zero** CIs.

| Layer | Question it answers | ServiceNow equivalent | Cardinality |
|---|---|---|---|
| Agent definition | What type of agent is this? | `cmdb_ai_system_product_model` | One per agent type |
| Governance record | Who owns it, is it approved, what is the risk? | `alm_ai_system_digital_asset` + governance details | One per agent; exists even with no deployment visibility |
| Deployment CI | Where is it running right now? | `cmdb_ci_function_ai` (cloud/SaaS) or `cmdb_ci_appl_ai_application` (on-prem) | One per environment or region |

## Entity-relationship model

```mermaid
erDiagram
    AGENT_DEFINITION ||--|| GOVERNANCE_RECORD : "governed by"
    AGENT_DEFINITION ||--o{ AGENT_DEPLOYMENT : "instance of"
    GOVERNANCE_RECORD }o--|| OWNER : "owned by"
    AGENT_DEPLOYMENT }o--|| IDENTITY : "runs as"
    AGENT_DEPLOYMENT }o--o{ CREDENTIAL : "holds"
    AGENT_DEPLOYMENT }o--o{ MODEL : "uses model"
    AGENT_DEPLOYMENT }o--o{ TOOL : "calls tool"
    AGENT_DEPLOYMENT }o--o{ DATA_SOURCE : "reads or writes"
    TOOL }o--o{ DATA_SOURCE : "reads or writes"
    AGENT_DEPLOYMENT }o--o{ AGENT_DEPLOYMENT : "delegates to"
    AGENT_DEPLOYMENT }o--o{ CHANNEL : "triggered by"
    AGENT_DEPLOYMENT }o--o{ BUSINESS_FLOW : "supports"
    AGENT_DEPLOYMENT }o--|| CODE_ARTIFACT : "deployed from"
    AGENT_DEPLOYMENT }o--o{ GUARDRAIL : "protected by"

    AGENT_DEPLOYMENT {
        string agent_uid PK "same value as the agent key in telemetry"
        string external_ids "ARN, Entra object ID, K8s UID, image digest"
        string platform
        string environment
        string version
        string managed_status "managed, unmanaged, shadow, dormant, declared"
        int identity_level "0 to 3"
        int confidence "0 to 100"
        datetime first_seen
        datetime last_seen
    }
    IDENTITY {
        string identity_id PK
        string type "Entra agent ID, AgentCore, SPIFFE, IAM role, SA, API key"
        string issuer
        string credential_type
        datetime last_used
        boolean onboarded
    }
    GOVERNANCE_RECORD {
        string record_id PK
        string approval_status
        string risk_tier
        date next_review
    }
    OWNER {
        string owner_id PK
        string business_owner
        string technical_owner
        string team
        string cost_centre
    }
    MODEL {
        string model_id PK
        string provider
        string version
        string hosting
    }
    TOOL {
        string tool_id PK
        string kind "MCP, REST, Lambda, connector, A2A peer"
        string endpoint
        string access "read or write"
    }
    DATA_SOURCE {
        string source_id PK
        string system "CBS, LOS, CRM, KYC store, vector DB"
        string classification "PII, account, card"
    }
    BUSINESS_FLOW {
        string flow_id PK
        string name "account opening, transfer, loan sanction, claims"
    }
```

## Why each entity matters for a bank

```mermaid
mindmap
  root((Agent deployment))
    Identity
      drives the onboarded count
    Owner
      orphaned agents are an audit finding
    Model
      a model change triggers re-validation
    Tool and MCP server
      what the agent can do
    Data source
      what the agent can see
    Credential
      hidden blast radius
    Channel
      untrusted input paths
    Business flow
      joins inventory to provenance
    Code artifact
      shadow evidence and version lineage
    Guardrail
      control coverage
```

## ServiceNow AI Control Tower mapping

| Asset type | Product model table | Digital asset table | CI table |
|---|---|---|---|
| Agents and skills | `cmdb_ai_system_product_model` | `alm_ai_system_digital_asset` | `cmdb_ci_function_ai` |
| Models | `cmdb_ai_model_product_model` | `alm_ai_model_digital_asset` | `cmdb_ci_ai_model_deployment` |
| MCP servers | `cmdb_mcp_product_model` | `alm_mcp_digital_asset` | `cmdb_ci_function_mcp` |
| Prompts | `cmdb_ai_prompt_product_model` | `alm_ai_prompt_digital_asset` | — |
| Datasets | `cmdb_ai_dataset_product_model` | `alm_ai_dataset_digital_asset` | — |

`cmdb_rel_asset_ci` links a digital asset to its CIs. Table names come from a ServiceNow employee's community blog and the Zurich docs; verify on the target instance.

## Fields worth borrowing from the CSA draft

The Cloud Security Alliance's Agent Registry Specification (draft, March 2026) adds fields a classic CMDB lacks:

```mermaid
flowchart LR
    CSA["CSA agent profile"] --> F1["toolAccessList"]
    CSA --> F2["permissionBoundaries<br/>max data class, prohibited actions,<br/>allowed data sources"]
    CSA --> F3["frameworkId / frameworkVersion"]
    CSA --> F4["foundationModelVersion<br/>pinned"]
    CSA --> F5["behavioralFingerprints<br/>hashes of test results"]
    CSA --> F6["status<br/>active, suspended,<br/>deprecated, revoked"]
```

It grounds the profile in the IETF SCIM agents extension draft and uses SPIFFE URIs as agent IDs.

> **One rule ties this to the rest of the platform:** `agent_uid` must be the same value the agent carries on every span (as a resource attribute, and as `gen_ai.agent.id` where the OpenTelemetry conventions define it; see [09](09-telemetry-provenance.md)). If the CMDB key and the trace value differ, provenance joins break.

See [`schemas/agent-record.schema.json`](../schemas/agent-record.schema.json) and the [example record](../examples/kyc-onboarding-agent.yaml).

---
[← 02 Inventory tree](02-inventory-tree.md) · [Index](README.md) · [Next: 04 Discovery →](04-discovery.md)
