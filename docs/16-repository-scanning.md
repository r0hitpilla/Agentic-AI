# 16 · Repository and artifact scanning

**Code finds agents before they run, including ones no platform API will ever list.** Scan every repository and image registry for agent frameworks, agent constructs, MCP and A2A files, prompts and infrastructure-as-code, then link each finding to a running workload so it becomes a deployment record rather than a guess. Detection patterns live in [`knowledge/detection-signatures.yaml`](../knowledge/detection-signatures.yaml).

## Pipeline

```mermaid
flowchart LR
    E["1 · Enumerate repos<br/>GitHub · GitLab ·<br/>Azure DevOps · Bitbucket"] --> T["2 · Cheap triage<br/>code search for agent files<br/>and imports; SBOM export"]
    T --> C["3 · Shallow clone<br/>priority repos first,<br/>all repos nightly"]
    C --> D["4 · Detectors<br/>manifests · imports · constructs ·<br/>MCP / A2A files · prompts · IaC"]
    D --> B["5 · Emit AI-BOM<br/>CycloneDX 1.7"]
    B --> L["6 · Link to runtime<br/>repo → pipeline →<br/>image digest → workload"]
    L --> OBS["Observation<br/>plane = code"]

    IMG["Image registries<br/>ECR · ACR · Artifact Registry ·<br/>Artifactory · Harbor · Nexus"] --> D
```

| Step | How | Watch out for |
|---|---|---|
| 1 Enumerate | GitHub `GET /orgs/{org}/repos`; GitLab `GET /groups/:id/projects?include_subgroups=true`; Azure DevOps `GET {org}/_apis/git/repositories`; Bitbucket `GET /2.0/repositories/{workspace}` | Archived repos, forks, personal namespaces, mirrors of vendor code |
| 2 Triage | GitHub code search for `filename:mcp.json`, `agent-card.json`, `SKILL.md`, `AGENTS.md`, framework imports; dependency-graph SBOM export per repo | Code search is rate-limited and capped: use it to prioritise, never as the system of record |
| 3 Clone | Shallow clone, default branch plus release branches | Large monorepos: scan by path; secrets in history are a separate scan |
| 4 Detect | Static detectors only; never execute code or start MCP servers | See signature groups below |
| 5 AI-BOM | `cdxgen` (`aibom` mode) or Cisco AI BOM → CycloneDX 1.7, agent fields as custom `properties` | No standard models agent → tool → permission edges well yet; keep your graph as the source of truth |
| 6 Link | CI metadata and image labels (`org.opencontainers.image.source`, `revision`) → image digest → running pod/function/ARN | Without this link, a code finding stays "declared" or "dormant" |

## What the detectors look for

```mermaid
mindmap
  root((Code signals))
    Manifests
      requirements and pyproject
      package.json and lockfiles
      go.mod, pom.xml, csproj
    Framework imports
      langgraph, langchain, crewai
      autogen, ag2, semantic-kernel
      openai-agents, google-adk
      claude-agent-sdk, llama-index
      pydantic-ai, smolagents, mcp
    Agent constructs
      StateGraph, Agent, Crew
      create_react_agent, tool decorators
      MCP ClientSession, stdio_client
      system_prompt strings
    Config files
      mcp.json, .mcp.json
      .cursor and .vscode mcp.json
      claude_desktop_config.json
      agent-card.json, AGENTS.md, SKILL.md
    Secrets and env
      OPENAI_API_KEY, ANTHROPIC_API_KEY
      AZURE_OPENAI_*, GOOGLE_API_KEY
    Infrastructure as code
      Terraform aws_bedrockagent_*
      aws_bedrockagentcore_*
      google_vertex_ai_reasoning_engine
      CloudFormation AWS::Bedrock::Agent
      kagent Agent manifests
      n8n, Flowise, Dify exports
```

## "Uses an LLM" is not the same as "is an agent"

The inventory must not flood with every app that calls a model. Classify each code finding:

```mermaid
flowchart TD
    F(["Code finding"]) --> L{"Calls an LLM<br/>or model server?"}
    L -- No --> N["Not AI · ignore"]
    L -- Yes --> T{"Gives the model tools,<br/>function calls or MCP?"}
    T -- No --> R{"Retrieval over<br/>bank data?"}
    R -- Yes --> RAG["LLM app (RAG)<br/>inventory as AI system,<br/>not as agent"]
    R -- No --> APP["LLM feature<br/>inventory as AI system"]
    T -- Yes --> LOOP{"Model decides which tool<br/>to call, or loops?"}
    LOOP -- No --> FN["Single tool call<br/>AI system with actions:<br/>treat as agent if tool writes"]
    LOOP -- Yes --> AG["Agent<br/>full agent profile"]

    classDef agent fill:#e3f2fd,stroke:#1565c0,color:#1b1b1b
    classDef sys fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    class AG,FN agent
    class RAG,APP sys
```

Regulators (FREE-AI, RBI MRM draft, MAS) want **all** AI systems in an inventory, so non-agent LLM apps are still recorded, as AI systems rather than agents. The rule above only decides which records need the agent-specific profile.

## AI-BOM formats and Indian guidance

| Format / guidance | Use |
|---|---|
| **CycloneDX 1.7** (ML-BOM / AI-BOM) | Practical interchange format; `cdxgen` emits it for prompt files, AI services, MCP configs and model metadata |
| **SPDX 3.0.1 AI profile** | Model-level documentation; weaker for agent and tool topology |
| **CERT-In Technical Guidelines on SBOM, QBOM & CBOM, AIBOM and HBOM (v2.0, 9 July 2025)** | Advisory, not mandatory; aimed at government, public sector, essential services and software exporters. Its SBOM minimum fields apply to AIBOMs "as applicable". Worth aligning to, since bank vendors will be asked for AIBOMs |
| **OWASP AIBOM Generator** | CycloneDX for Hugging Face models only; model provenance, not agent discovery |

## Tools for this step

| Tool | Strength | Caution |
|---|---|---|
| `cdxgen` (`aibom`) | Best AI-BOM emitter for pipelines; CycloneDX 1.7 and SPDX 3.0.1 | Declared inventory only |
| Cisco AI BOM (open source) | Code, images and cloud; 30 component types incl. agent, tool, MCP server/client, memory, prompt, guardrail, secret | Deepest agent/MCP/A2A detection is Python-only |
| Snyk AI-BOM | Code-level detection incl. MCP usage | Commercial; check data handling |
| SPLX Agentic Radar | Per-repo workflow graphs for LangGraph, CrewAI, n8n, OpenAI Agents SDK, AutoGen; OWASP mapping | Per-repo, not org-scale |
| Syft | Package SBOMs from images | Not agent-aware; pair with signatures |

## Linking code to runtime

```mermaid
flowchart LR
    REPO["Repo<br/>onboarding/kyc-agent"] -->|"CI build"| IMG["Image<br/>sha256:9f2b..."]
    IMG -->|"deployed as"| POD["Pod in OpenShift<br/>ns: onboarding"]
    POD -->|"runs as"| ID["SPIFFE ID"]
    POD -->|"emits"| SPAN["Spans with<br/>agent key"]
    REPO -.->|"no image found"| DECL["Declared only<br/>or dormant"]
    POD -.->|"no repo found"| GHOST["Shadow · ghost"]

    classDef bad fill:#ffebee,stroke:#c62828,color:#1b1b1b
    classDef neutral fill:#f5f5f5,stroke:#757575,color:#1b1b1b
    class GHOST bad
    class DECL neutral
```

---
[← 15 Pulling the inventory](15-pulling-inventory.md) · [Index](README.md) · [Next: 17 Tools landscape →](17-tools-landscape.md)
