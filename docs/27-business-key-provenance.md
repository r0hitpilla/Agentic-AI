# 27 · Provenance through business keys, flow by flow

**Every bank flow already carries identifiers that every system records: application numbers, UTRs, loan account numbers, claim numbers.** Tokenise them once with a bank-held key and they join agent traces, core-banking logs and database changes into one lineage chain, even where no trace context survives. The key catalogue is [`knowledge/business-keys.yaml`](../knowledge/business-keys.yaml).

## Tokenise once, join everywhere

```mermaid
flowchart LR
    V["Raw key<br/>e.g. loan application number"] --> H["HMAC-SHA256<br/>with bank-held key<br/>(HSM / KMS)"]
    H --> T["Token<br/>same value → same token<br/>in every system"]
    T --> S1["Agent spans"]
    T --> S2["Gateway logs"]
    T --> S3["CBS / LOS audit"]
    T --> S4["CDC events"]
    S1 --> J[("Provenance graph<br/>joins on token")]
    S2 --> J
    S3 --> J
    S4 --> J
```

- Deterministic tokens allow joins without exposing values. Plain hashes of short numeric IDs can be reversed by brute force, so use a keyed HMAC.
- Aadhaar numbers never enter telemetry; use the reference token from the bank's Aadhaar data vault.
- Tokenisation happens in the bank's Collector ([23](23-telemetry-without-code-changes.md)), not in the applications.

## Account opening

```mermaid
flowchart LR
    A1["Customer / branch<br/>case_id"] --> A2["KYC agent<br/>application_number"]
    A2 --> A3["CKYC lookup<br/>ckyc_number"]
    A2 --> A4["Sanctions agent<br/>case_id"]
    A2 --> A5["CBS create customer<br/>customer_id"]
    A5 --> A6["CBS open account<br/>account_number"]
    A6 --> A7[("CDC: account row")]

    classDef obs fill:#e8f5e9,stroke:#2e7d32,color:#1b1b1b
    classDef key fill:#fff8e1,stroke:#f9a825,color:#1b1b1b
    class A2,A4 obs
    class A3,A5,A6,A7 key
```

Green: usually joined by trace context. Amber: usually joined by business key or data change.

## Transfers

```mermaid
flowchart LR
    T1["Payments agent<br/>conversation_id"] --> T2["Payment hub<br/>NEFT/RTGS UTR or<br/>IMPS/UPI RRN"]
    T2 --> T3["CBS debit<br/>account_number + UTR"]
    T2 --> T4["Switch / NPCI / RBI rails<br/>RRN or UTR"]
    T3 --> T5[("CDC: ledger entry")]
```

## Loan sanction

```mermaid
flowchart LR
    L1["Origination agent<br/>application_number"] --> L2["LOS<br/>application_number"]
    L2 --> L3["Bureau pull<br/>bureau_enquiry_ref"]
    L2 --> L4["Credit agent<br/>scores applicant"]
    L4 --> L5["Credit officer approval<br/>sanction_reference"]
    L5 --> L6["CBS loan account<br/>loan_account_number"]
    L6 --> L7[("CDC: loan account row")]
```

The credit officer's approval is a `prov:Activity` by a human agent; the credit agent's score is an input `prov:Entity` it `used`. This is how the graph shows a human in the loop for a decision regulators treat as high-risk ([10](10-regulatory.md)).

## Claims

```mermaid
flowchart LR
    C1["Claims intake agent<br/>claim_number"] --> C2["Document agent<br/>document_id"]
    C2 --> C3["Claims system<br/>claim_number"]
    C3 --> C4["Payout via CBS<br/>account_number + UTR"]
    C4 --> C5[("CDC: payout row")]
```

## Edge confidence

| How the edge was made | Confidence | Shown to auditors as |
|---|---|---|
| Same trace (propagated `traceparent`) | High | Observed |
| Same tokenised business key | Medium-high | Stitched by key |
| Data change written by A and read by B | Medium | Data lineage |
| Same identity in a short time window | Low; needs review | Inferred |

Report coverage per flow: the share of steps joined by observed or key-stitched edges. A loan file where every step is green or amber is audit-ready; any "inferred" step is a gap to close.

## What to ask each bank in week 0

- [ ] For each flow, which of the keys in the catalogue exist, and in which systems?
- [ ] Where do they appear: URL path, header, body, message key, database column?
- [ ] Which keys are already masked or tokenised, and with what scheme?
- [ ] Can CDC or audit logging be turned on for the tables agents write?
- [ ] Who owns the HMAC key, and where is it held?

---
[← 26 Operating model](26-operating-model.md) · [Index](README.md) · [Next: 28 AI systems and integrations →](28-ai-systems-and-integrations.md)
