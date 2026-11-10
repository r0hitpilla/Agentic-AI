# 05 · Finding shadow agents

**A shadow agent is any agent whose runtime activity cannot be matched to an approved governance record and its registered identity.** Find them by comparing three evidence planes and classifying every mismatch.

## Three planes

```mermaid
flowchart LR
    R["Registered<br/>CMDB or platform API"]
    C["Code<br/>repo or image found"]
    T["Runtime<br/>traffic, traces, logs"]

    R --- RC(("compare"))
    C --- RC
    T --- RC
    RC --> OUT["Five outcomes"]
```

## Classification flow

```mermaid
flowchart TD
    S(["Evidence for one agent"]) --> R{"Registered with an<br/>approved governance record?"}

    R -- Yes --> T1{"Runtime in<br/>last 30 days?"}
    T1 -- Yes --> MAN["Managed (sanctioned)<br/>monitor, reconcile drift"]
    T1 -- No --> DOR["Dormant / zombie<br/>confirm, retire, revoke credentials"]

    R -- "Found by platform API,<br/>no record or owner" --> UNM["Unmanaged<br/>assign owner, run intake"]

    R -- No --> T2{"Runtime seen?"}
    T2 -- Yes --> C2{"Code found<br/>anywhere?"}
    C2 -- Yes --> SH["Shadow<br/>find owner, contain,<br/>onboard or kill"]
    C2 -- No --> GH["Shadow · ghost<br/>highest priority"]
    T2 -- No --> C3{"Code found?"}
    C3 -- Yes --> DOR
    C3 -- No --> DEC["Declared only<br/>planned, or SaaS<br/>with no visibility"]

    classDef good fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    classDef warn fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    classDef worst fill:#c62828,stroke:#8e0000,color:#ffffff
    classDef neutral fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    class MAN good
    class UNM warn
    class SH bad
    class GH worst
    class DOR,DEC neutral
```

| Registered | Code found | Runtime seen | Classification | Action |
|---|---|---|---|---|
| Yes, approved | Yes | Yes | **Managed (sanctioned)** | Monitor; reconcile drift |
| No | Yes or no | Yes | **Shadow** ("ghost" if no code anywhere) | Find owner, contain, onboard or kill |
| Platform API only, no record or owner | Any | Any | **Unmanaged** | Assign owner, run intake |
| Yes or code only | Yes | No (30+ days) | **Dormant** ("zombie") | Confirm, retire, revoke credentials |
| Record only | No | No | **Declared only** | Keep as a governance record |

The ghost and zombie labels come from the open-source DefendAI AgentDiscover scanner, which flags workloads making live LLM calls with no corresponding source code: exactly what a code-only inventory misses.

## Shadow-agent signals

```mermaid
mindmap
  root((Shadow signals))
    Network
      LLM traffic bypassing the gateway
      unknown caller of an internal model server
      new A2A agent card or MCP endpoint
    Secrets
      LLM keys in code or CI variables
      keys in env vars or personal accounts
    Cloud logs
      InvokeModel or Converse by unexpected principals
      Azure OpenAI calls by unlinked principals
    Identity
      human account calling CBS at machine rates
      OAuth grants to AI apps
    Endpoints
      MCP config files on laptops
      coding-agent processes
    Platforms
      maker agents in default environments
      embedded vendor AI features
```

The "human account behaving like a machine" signal matters most in a bank: an employee principal calling core banking APIs around the clock at machine rates usually means an agent is running on that person's credentials (identity level 0).

## Decision rule

```mermaid
flowchart LR
    A{"Approved<br/>governance record?"} -->|yes| B{"Runtime identity =<br/>registered identity?"}
    B -->|yes| C{"Model and tool traffic<br/>via the gateway?"}
    C -->|yes| OK["Managed"]
    A -->|no| NO["Shadow or unmanaged"]
    B -->|no| NO
    C -->|no| NO

    classDef good fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    class OK good
    class NO bad
```

Fail any one check and the agent is not managed. The rule is cheap to evaluate continuously once the gateway ([04](04-discovery.md)) and the identity join ([06](06-identity-onboarding.md)) are in place.

---
[← 04 Discovery](04-discovery.md) · [Index](README.md) · [Next: 06 Identity →](06-identity-onboarding.md)
