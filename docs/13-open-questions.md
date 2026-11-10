# 13 · Open questions, risks and caveats

**Settle six questions with the bank before build; they decide scope, path and ownership.** Then track the risks below, most of which come from standards and regulation still being in draft.

## Questions to settle before build

```mermaid
flowchart TD
    Q1{"Which environments<br/>are in phase 1?"} --> S["Scope of collectors"]
    Q2{"ServiceNow AICT<br/>licensed, with connectors?"} --> P["Path A or Path B<br/>(see 08)"]
    Q3{"Which IdP is<br/>authoritative? SPIRE on-prem?"} --> I["Identity design<br/>(see 06)"]
    Q4{"Can egress be forced<br/>through one AI gateway?"} --> SH["Shadow detection strength<br/>(see 04, 05)"]
    Q5{"Who owns the inventory<br/>as AI steward?"} --> O["Operating model"]
    Q6{"Which business flow<br/>goes first?"} --> PI["Pilot scope"]

    classDef q fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    classDef d fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    class Q1,Q2,Q3,Q4,Q5,Q6 q
    class S,P,I,SH,O,PI d
```

- [ ] Which environments are in scope for phase 1: which clouds, which on-prem platforms (OpenShift, VMware, bare metal), which SaaS agent platforms?
- [ ] Is ServiceNow AI Control Tower licensed, including the cloud connectors? That decides Path A or Path B.
- [ ] Which identity provider is authoritative (Entra, Okta, other), and will the bank run SPIRE on-prem?
- [ ] Can the bank enforce LLM and MCP egress through a single AI gateway? Without it, shadow detection falls back to logs and eBPF.
- [ ] Who owns the inventory as AI steward: CISO, model risk, or the CTO's office?
- [ ] Which business flow goes first? Account opening or loan sanction are good pilots because both touch PII and credit decisions.

## Risk map

```mermaid
quadrantChart
    title Risks by likelihood and impact on the inventory
    x-axis Low likelihood --> High likelihood
    y-axis Low impact --> High impact
    quadrant-1 Mitigate now
    quadrant-2 Plan a fallback
    quadrant-3 Monitor
    quadrant-4 Design around it
    OTel attribute renames: [0.85, 0.36]
    Regulatory field changes: [0.66, 0.26]
    ServiceNow release differences: [0.58, 0.14]
    eBPF blocked on hardened clusters: [0.6, 0.6]
    Vendor claims fail in pilot: [0.7, 0.72]
    PII leaking into telemetry: [0.4, 0.9]
    Collector data leaves the bank: [0.22, 0.74]
```

Positions are a starting judgement for the risk register, not a measured assessment.

## Risks and caveats

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Standards are still drafts** | OpenTelemetry `gen_ai.*` attributes are at Development status; the CSA Agent Registry Specification and the IETF SCIM agents extension are drafts; NIST's tenets are guidance and the NCCoE practice guide is not yet published | Keep mapping layers so renames are cheap |
| **Regulation is in motion** | FREE-AI is not yet binding and RBI's model-risk guidance is still a draft | Model fields generously; re-check when directions are issued |
| **ServiceNow specifics vary by release** | Table and class names here come largely from a ServiceNow employee's community blog and the Zurich docs | Verify on the target instance and release |
| **eBPF needs privileges** | Kernel probes need privileged agents and recent kernels (AIOStack lists Kubernetes 1.29+ and Linux 5.15+); OpenShift security context constraints may block them | Agree an exception early, or lean on gateway and egress logs |
| **Telemetry carries PII risk** | Spans flow to observability tools with wide access | Prompt and response content off by default in production; tokenise customer identifiers; align retention with the DPDP Act |
| **Vendor claims are untested** | Capabilities attributed to ServiceNow, Okta, AWS, Microsoft and open-source tools come from documentation and announcements | Prove each in a pilot with seeded test agents |
| **Collector data may leave the bank** | AIOStack's dashboard is hosted at app.aurva.io; AgentDiscover can optionally upload results to DefendAI's platform | Use collectors that keep all data in-house, or self-host their back ends |

## Pilot with seeded agents

The quickest way to test every claim in these docs: plant known agents and check what the inventory finds.

```mermaid
flowchart LR
    subgraph SEED["Seed one of each"]
        A1["Managed Bedrock agent"]
        A2["Copilot Studio agent<br/>no owner"]
        A3["OpenShift pod with LLM key<br/>no record"]
        A4["Laptop MCP config"]
        A5["Agent on a human's<br/>credentials"]
        A6["Retired agent with<br/>live key"]
    end
    subgraph EXPECT["Expected classification"]
        E1["managed · L2"]
        E2["unmanaged"]
        E3["shadow · L1"]
        E4["shadow · L0"]
        E5["identity L0"]
        E6["dormant · live credentials"]
    end
    A1 --> E1
    A2 --> E2
    A3 --> E3
    A4 --> E4
    A5 --> E5
    A6 --> E6
```

Measure detection rate and time-to-detect per seed; any miss shows which collector or rule needs work.

---
[← 12 KPIs](12-kpis.md) · [Index](README.md) · [References →](references.md)
