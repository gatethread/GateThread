# LLMGate — Project Definition

> A self-hosted AI gateway for engineering teams that need privacy, auditability, and intelligent routing — without giving up model quality.

---

## The Problem

Every engineering team that adopts AI tooling faces the same unresolved tension:

- The best models are cloud-hosted — your code and data leave your infrastructure
- Local models are private — but they can't match cloud model quality
- There is no middle layer that makes intelligent decisions, protects sensitive data, and remembers context across sessions

Teams either accept the risk or block AI tools entirely. LLMGate is the third option.

---

## What LLMGate Is

LLMGate is a self-hosted AI gateway that runs on your own infrastructure. Every prompt from your editor passes through it. A local model inspects each prompt and decides what happens next: answer locally, route to a cloud model with sensitive data redacted, or block the request entirely.

When your session ends, LLMGate compresses and organizes what was discussed into structured facts. The next time you work on something related, that context is retrieved automatically — cheap, precise, and immediately useful.

Every decision is logged. Nothing is a black box.

---

## How It Differs From Existing Tools

There are good tools for routing between cloud providers. LLMGate does something different.

| | LiteLLM | Portkey | Helicone | LLMGate |
|-|:-------:|:-------:|:--------:|:-------:|
| Routes between cloud providers | ✅ | ✅ | ❌ | ✅ |
| Local model as first responder | ❌ | ❌ | ❌ | ✅ |
| PII redaction before cloud | ❌ | ❌ | ❌ | ✅ |
| Data stays on your infrastructure | ❌ | ❌ | ❌ | ✅ |
| Session memory and compression | ❌ | ❌ | ❌ | ✅ |
| On-demand context retrieval | ❌ | ❌ | ❌ | ✅ |
| Audit log with redaction record | ❌ | Partial | ✅ | ✅ |
| Self-hosted, no SaaS dependency | Partial | ❌ | ❌ | ✅ |

LiteLLM handles the provider abstraction layer well. LLMGate uses it internally and builds the privacy and intelligence layer on top.

---

## Core Principles

**Private by default.** Sensitive data never reaches a cloud provider unredacted. The local model makes the call on every prompt.

**Intelligent routing.** Not every question needs Claude. Simple tasks stay local and cost nothing. Hard tasks go to the best available model.

**Memory that works.** Sessions are compressed into structured facts, not raw transcripts. Context is retrieved on demand — only when relevant, never as noise.

**Full auditability.** Every prompt is logged: who asked, where it went, what was redacted. Teams can prove compliance without guesswork.

**Operator-grade deployment.** Infrastructure-as-code from day one. No manual setup. Repeatable across environments.

---

## V1 Features — Definition of Done

These are the features that define a working first version. Nothing ships until all of these work end to end.

### 1. OpenAI-Compatible API
The gateway exposes a `/v1/chat/completions` endpoint. Any editor that supports a custom OpenAI base URL (Cline, Continue, Cursor, etc.) works without modification. No custom plugins required.

### 2. Local LLM Routing
Every incoming prompt is evaluated by the local model (Qwen2.5-Coder 7B via Ollama). The model decides:
- **Local** — handle the prompt on the gateway, no cloud call
- **Cloud** — the prompt needs more capability, route to Claude
- **Block** — the prompt contains something that should never leave or be processed

> **Note:** Qwen2.5-Coder is optimized for code tasks. Its suitability as a security and routing classifier will be benchmarked in V1 testing. If routing quality is insufficient, a general-purpose model (Llama 3.2) will be used for routing decisions while Qwen handles local answers.

### 3. Redact First — Everything
Every prompt is redacted the moment it enters the gateway — before routing, before storage, before anything else. Credentials, PII, internal URLs, and customer identifiers are replaced with typed placeholders. The original values are held in a redaction map in Redis memory only, with a short TTL.

This means:
- The session buffer (Redis) holds only redacted transcripts
- The local LLM only ever sees redacted prompts
- Claude only ever sees redacted prompts
- Compressed session facts are clean by the time they are stored
- The redaction map is deleted immediately after context rehydration

One rule, applied once, at the door. Everything downstream is clean.

> **Known limitation:** Presidio has false positive rates on certain patterns — variable names that resemble emails, numeric IDs that match phone number formats. The audit log records every redaction so developers can review what was removed. Sensitivity thresholds are configurable.

### 4. Context Restoration
After Claude responds, the redaction map is used once to restore the original values into the response. The developer receives a complete, coherent answer. The redaction map is then deleted from Redis.

### 5. Conversation History
The gateway maintains the full multi-turn conversation on the VM in Redis. All turns are already redacted. When the model switches mid-conversation (local → Claude), Claude receives the complete prior context — clean. The raw conversation is held in memory only — never written to disk. It is discarded after session compression completes.

### 6. Session Compression
When the developer goes idle, the local model processes the session asynchronously. The raw transcript is compressed into structured facts: decisions made, files changed, bugs fixed, open questions. Stored in the database. Raw transcript deleted immediately after.

### 7. On-Demand Context Retrieval
The local LLM is given a `retrieve_past_context` tool — the same tool-calling mechanism Claude Code uses to decide when to read a file. The LLM reads the incoming prompt and decides on its own whether past context is relevant. If it calls the tool, it gets back the structured facts from previous sessions. If it doesn't, nothing is injected. The LLM drives the decision, not a hardcoded similarity threshold.

### 8. Audit Log
Every prompt produces an audit record:
- Timestamp
- Client identifier
- Routing decision (local / cloud / blocked)
- Redaction categories applied (if any)

No prompt content or code is stored in the audit log — only metadata. Queryable. Exportable.

### 9. Data Retention and Deletion
- Raw transcripts: deleted immediately after compression
- Compressed facts: retained for 90 days by default (configurable)
- Audit records: retained for 1 year by default (configurable)
- Developers can delete their own session history via API at any time

### 10. Gateway Security
- All traffic over HTTPS — TLS termination at the gateway
- API key authentication on every endpoint
- Redis and PostgreSQL bound to localhost — not exposed externally
- AWS credentials managed via IAM roles — no hardcoded keys anywhere
- EC2 security group: only port 443 open to the developer's IP

### 11. Developer Interface — Cline + LLMGate
LLMGate does not ship its own UI in V1. Developers use **Cline** (VS Code extension) pointed at the LLMGate gateway. Cline provides the chat panel, file reading, file editing, and terminal access — the same experience as Claude Code. LLMGate provides the intelligence, privacy, and memory underneath.

Setup takes under a minute:
```bash
llmgate start        # starts the gateway on AWS, prints connection details
```
Paste the output into Cline's settings. Done.

### 12. AWS Deployment via Terraform
The full stack deploys to AWS with a single `terraform apply`. CPU-optimized EC2 instance (proof of concept — GPU upgrade path is defined for V1.1). Auto-stop when idle to minimize cost. Redeployable from scratch in under 10 minutes.

---

## Tech Stack

| Component | Technology | Reason |
|---|---|---|
| Gateway API | Python + FastAPI | Every library we need — PII detection, LLM clients, embeddings — has its best implementation in Python. The ecosystem advantage outweighs Go's performance edge at this stage. |
| Local LLM runtime | Ollama | Handles GPU/CPU automatically. One-command model switching. Clean HTTP API. Operationally simple. |
| Local LLM model | Qwen2.5-Coder 7B | Best performing open model for code tasks at this parameter size. Will be benchmarked for routing quality in V1 testing. |
| Cloud LLM client | LiteLLM | Unified API across providers. Claude in V1, GPT-4o in V1.2 — one config line change, not a rewrite. |
| Cloud provider (V1) | Anthropic Claude | Best reasoning quality for complex prompts at the time of writing. |
| PII redaction | Microsoft Presidio | Mature, battle-tested, open source. Handles credentials, PII, and custom patterns. False positives are a known tradeoff — mitigated by configurable thresholds and audit log visibility. |
| Primary database | PostgreSQL + pgvector | Handles relational data and vector search in a single service. No separate vector DB to operate. Team-ready from day one. |
| Session buffer | Redis | Transcripts are ephemeral by design. Redis holds them in memory with auto-TTL. Never touches disk. |
| Infrastructure | Terraform (AWS) | Most widely used IaC tool. Any infrastructure engineer knows it. |
| Compute (V1) | AWS EC2 CPU-optimized | Proof of concept sizing. Slower inference than GPU but sufficient to validate routing quality and architecture. GPU path (EC2 g4dn) is defined for V1.1. |

---

## Roadmap

### V1.0 — Foundation
*Goal: One developer can replace their direct Claude/GPT setup with LLMGate and lose nothing — while gaining privacy, memory, and a full audit trail.*

**Success criteria:**
- Routing decision latency under 5 seconds on CPU
- Zero credentials or PII transmitted to Claude in a standard coding session (verified via audit log)
- Context from a previous session correctly retrieved within the first prompt of a new session
- Full stack deployed and destroyed via Terraform in under 10 minutes

**Features:**
- [ ] OpenAI-compatible gateway API
- [ ] Local LLM routing (Qwen2.5-Coder via Ollama)
- [ ] PII and credential redaction (Presidio)
- [ ] Context rehydration after cloud response
- [ ] Multi-turn conversation history on VM
- [ ] Claude integration via LiteLLM
- [ ] Async session compression
- [ ] On-demand context retrieval (pgvector)
- [ ] Audit log
- [ ] Data retention and deletion API
- [ ] Gateway security (HTTPS, IAM, security groups)
- [ ] Terraform deployment on AWS EC2 (CPU)

---

### V1.1 — Multi-Developer
*Goal: A team of up to 5 developers shares one LLMGate instance with full session and audit isolation between them.*

**Success criteria:**
- No session data visible across developer accounts
- Concurrent usage by 3 developers with no degradation in routing latency
- GPU instance available as a drop-in replacement for CPU

**Features:**
- [ ] Per-developer session isolation
- [ ] Shared VM, separate contexts and audit logs
- [ ] GPU instance support (EC2 g4dn) for faster local inference
- [ ] Usage metrics per developer (prompts routed local vs cloud)

---

### V1.2 — Multi-Provider
*Goal: LLMGate can route to more than one cloud provider. Best model for the task, not just the default.*

**Success criteria:**
- A prompt can be routed to Claude or GPT-4o based on configurable criteria
- Cost per session tracked and queryable by provider

**Features:**
- [ ] OpenAI GPT-4o integration
- [ ] Provider selection logic (route by task type or cost)
- [ ] Cost tracking per provider per session

---

### V1.3 — Audit Dashboard
*Goal: A compliance officer or team lead can review AI usage without touching the database.*

**Features:**
- [ ] Web UI for audit log browsing
- [ ] Filters: by developer, date range, routing decision, redaction type
- [ ] Export to CSV for compliance reporting

---

### V1.4 — Configurable Routing Policy
*Goal: Teams define their own routing rules in a config file. No code changes required.*

**Features:**
- [ ] Policy-as-config routing rules (block if X, always local if Y)
- [ ] Per-project routing overrides
- [ ] Rule validation and dry-run mode

---

### V2.0 — Team Scale
*Goal: LLMGate is production infrastructure for an engineering organization.*

**Features:**
- [ ] Admin controls and developer management
- [ ] Per-developer usage limits and cost budgets
- [ ] Kubernetes deployment (Helm chart)
- [ ] SSO integration
- [ ] SLA monitoring and alerting
- [ ] Air-gapped deployment mode (zero cloud calls)

---

### V3.0 — Native Editor Experience
*Goal: LLMGate ships its own VS Code extension — full control over the interface, branding, and UX. No dependency on third-party editors.*

**Features:**
- [ ] VS Code extension with native chat panel
- [ ] Direct file access and editing from the extension
- [ ] LLMGate-specific UX (session history browser, redaction visibility, audit log inline)

---

## Non-Goals

These are explicit decisions about what LLMGate will not do, and why.

**Fine-tuning or training models on your codebase.**
Fine-tuning requires labeled data, significant compute, and ongoing maintenance as the codebase evolves. LLMGate achieves personalization through session memory and context retrieval — no training pipeline needed.

**Storing full conversation history.**
Raw transcripts grow without bound and are expensive to search. Compression trades completeness for efficiency — a structured fact is more useful in future context than a 3,000 token conversation log.

**A hosted SaaS version.**
LLMGate's core value is that your data stays on your infrastructure. A hosted version would contradict that entirely.

**A custom editor plugin before V3.0.**
Cline covers the V1 use case completely. Building a custom extension before the gateway itself is proven would be building in the wrong order. It is on the roadmap for V3.0 — not a permanent non-goal.

---

## Contributing

LLMGate is open source and in active development.

**To contribute:**
1. Check the open issues — work is organized by milestone
2. Comment on an issue before starting work — avoid duplicate effort
3. One feature or fix per pull request
4. All code must include tests
5. Python style: `ruff` for formatting and linting (config in `pyproject.toml`)
6. Every PR is reviewed before merge — no direct commits to `main`

**To report a real-world requirement:**
If you work in a regulated environment and have requirements not covered here, open an issue with your use case. Real constraints shape the roadmap.
