# GateThread — Project Definition

> A self-hosted AI gateway for engineering teams that need privacy, auditability, and intelligent routing — without giving up model quality.

---

## The Problem

Every engineering team that adopts AI tooling faces the same unresolved tension:

- The best models are cloud-hosted — your code and data leave your infrastructure
- Local models are private — but they can't match cloud model quality
- There is no middle layer that makes intelligent decisions, protects sensitive data, and remembers context across sessions

Teams either accept the risk or block AI tools entirely. GateThread is the third option.

---

## What GateThread Is

GateThread is a self-hosted AI gateway that runs on your own infrastructure. Every prompt from your editor passes through it.

**Redaction happens first — before anything else.** The moment a prompt enters the gateway, PII and credentials are replaced with typed placeholders. The local model, the cloud model, and the session buffer all see only the redacted form. Sensitive values never leave the machine.

After redaction, a local model makes a fast routing classification: answer locally, route to Claude, or block. The routing call is a short structured classification prompt — not a full inference pass — to keep latency acceptable on CPU.

When your session ends, GateThread compresses the conversation into a structured knowledge graph. Facts are nodes. Relationships between facts are edges. Scores decay over time so recent knowledge surfaces first. Contradictions are detected and resolved. The next session retrieves the relevant neighborhood of the knowledge graph automatically.

Every decision is logged. Nothing is a black box.

---

## Known Design Tensions

These are acknowledged tradeoffs, not oversights.

**Redaction degrades the routing signal.** The local model routes based on the redacted prompt. A prompt like "why does my AWS secret key keep rotating?" becomes "why does my `<CREDENTIAL_1>` keep rotating?" The routing decision is made on a partially-degraded input. The mitigation: routing uses a short classification prompt that focuses on task type, not sensitive values. Routing quality is benchmarked in V1 testing.

**Routing latency on CPU is real.** Qwen2.5-Coder 7B on a CPU-only instance produces the routing classification in roughly 2–4 seconds for a short prompt. This is acceptable for most workflows but perceptible. The GPU path (V1.1) brings this under 1 second. The routing prompt is kept minimal — one structured classification output, not a full answer.

**Cold start takes time.** First boot on a fresh EC2 instance requires pulling the Ollama model (~4 GB). Expect 5–10 minutes. The EBS volume retains the model across restarts. `gatethread warm` pre-loads the model so the first prompt is not slow.

**Tool-gated retrieval is unreliable at 7B scale.** Asking the local model to decide when to retrieve context requires metacognitive reliability that 7B models do not consistently have. GateThread uses always-on retrieval instead: every request triggers a retrieval pass against the knowledge graph, and context is injected only when the relevance score exceeds a configurable threshold. The model never decides whether to retrieve — the system does.

---

## How It Differs From Existing Tools

| | LiteLLM | Portkey | Helicone | GateThread |
|-|:-------:|:-------:|:--------:|:----------:|
| Routes between cloud providers | ✅ | ✅ | ❌ | ✅ |
| Local model as first responder | ❌ | ❌ | ❌ | ✅ |
| PII redaction before cloud | ❌ | ❌ | ❌ | ✅ |
| Data stays on your infrastructure | ❌ | ❌ | ❌ | ✅ |
| Session memory and compression | ❌ | ❌ | ❌ | ✅ |
| Knowledge graph context retrieval | ❌ | ❌ | ❌ | ✅ |
| Audit log with redaction record | ❌ | Partial | ✅ | ✅ |
| Self-hosted, no SaaS dependency | Partial | ❌ | ❌ | ✅ |

LiteLLM handles the provider abstraction layer well. GateThread uses it internally and builds the privacy and intelligence layer on top.

---

## Core Principles

**Private by default.** Sensitive data is redacted at the door — before routing, before the local model, before storage. One rule, applied once, at the entry point.

**Intelligent routing.** Not every question needs Claude. The routing decision is a fast structured classification, not a full inference pass. Simple tasks stay local and cost nothing.

**Memory that works.** Sessions are compressed into a knowledge graph, not a flat list of facts. Relationships between facts are explicit. Scores decay with time. Contradictions are resolved by a belief revision engine. Context retrieved is always the most relevant, most recent, non-contradicted neighborhood of what the developer was working on.

**Full auditability.** Every prompt is logged: who asked, where it went, what was redacted. The audit log is append-only and lives on a separate access credential — it cannot be read or tampered with using the same key that controls the gateway.

**Operator-grade deployment.** Infrastructure-as-code from day one. No manual setup. Repeatable across environments.

---

## V1 Features — Definition of Done

These are the features that define a working first version. Nothing ships until all of these work end to end.

### 1. OpenAI-Compatible API
The gateway exposes a `/v1/chat/completions` endpoint. Any editor that supports a custom OpenAI base URL (Cline, Continue, Cursor, etc.) works without modification. No custom plugins required.

### 2. Local LLM Routing
Every incoming prompt — after redaction — is evaluated by the local model (Qwen2.5-Coder 7B via Ollama). The model makes a fast routing classification:
- **Local** — handle the prompt on the gateway, no cloud call
- **Cloud** — the prompt needs more capability, route to Claude
- **Block** — the prompt should not be processed

The routing call is a short structured prompt designed to minimize inference time. It does not require the model to produce a full answer — only a single classification token. Target: under 3 seconds on CPU for a prompt up to 500 tokens.

> **Note:** Qwen2.5-Coder is optimized for code tasks. Its suitability as a routing classifier will be benchmarked in V1 testing (Issue #16). If routing quality is insufficient, a smaller general-purpose model may be used for routing while Qwen handles local answers.

### 3. Redact First — Everything
Every prompt is redacted the moment it enters the gateway — before routing, before storage, before anything else. Credentials, PII, internal URLs, and customer identifiers are replaced with cryptographically-prefixed placeholders that cannot occur naturally in developer text (format: `GT-<TYPE>-<UUID4-prefix>`). The original values are held in a redaction map in Redis memory only, with a TTL extended on active cloud calls to prevent expiry during retries.

This means:
- The session buffer (Redis) holds only redacted transcripts
- The local LLM only ever sees redacted prompts
- Claude only ever sees redacted prompts
- Compressed session facts are clean by the time they are stored
- The redaction map is deleted immediately after successful context rehydration

One rule, applied once, at the door. Everything downstream is clean.

> **Known limitation:** Presidio has false positive rates on certain patterns — variable names that resemble emails, numeric IDs that match phone number formats. The audit log records every redaction category so developers can review what was removed. Sensitivity thresholds are configurable. Precision/recall is measured against a real-prompt evaluation set in V1 testing.

### 4. Context Restoration
After Claude responds, the redaction map is used once to restore the original values into the response. The developer receives a complete, coherent answer. The redaction map is then deleted from Redis. If a placeholder appears in Claude's reasoning (e.g., Claude references `GT-CREDENTIAL-a3f2` by name), it is still restored — the developer sees the original value.

### 5. Conversation History
The gateway maintains the full multi-turn conversation in Redis. All turns are already redacted. When context approaches the model's token limit, older turns are summarized rather than truncated — the summary preserves semantic content without unbounded token growth. The raw conversation is held in memory only — never written to disk. It is discarded after session compression completes.

> **Known limitation:** The fallback session identity (`SHA256(client_ip + date)`) will produce a new session ID if the developer's IP changes mid-day (VPN reconnect, DHCP renewal). When this happens, the conversation context is lost for that session. The `X-GateThread-Client` header UUID is the reliable path and should always be configured.

### 6. Session Compression
When the developer goes idle, the local model processes the session asynchronously. The raw transcript is compressed into structured knowledge graph nodes: decisions made, files changed, bugs fixed, architectural constraints, open questions. The number of nodes extracted scales with session length and information density — not a fixed cap.

If structured extraction fails (malformed JSON, schema validation error), the system retries with a simplified prompt. If that fails, key sentences are extracted verbatim as low-confidence nodes rather than losing the session entirely. Raw transcript is deleted only after successful compression or after explicit fallback extraction.

### 7. Always-On Context Retrieval
Every incoming request triggers a retrieval pass against the knowledge graph. Context is injected into the prompt if and only if the top-ranked nodes exceed a configurable relevance threshold. The retrieval pipeline: embed the query → graph-augmented vector search (seed nodes via pgvector, expand via edge traversal) → rank by composite score (Bayesian posterior: similarity × recency prior) → enforce token budget → inject.

The model never decides whether to retrieve. The system decides, based on a measurable signal.

### 8. Audit Log
Every prompt produces an audit record:
- Timestamp
- Client identifier
- Routing decision (local / cloud / blocked)
- Redaction categories applied (if any)
- Session ID

No prompt content or code is stored in the audit log — only metadata. The audit endpoint (`GET /v1/audit`) requires a separate admin credential, not the gateway API key. Queryable. Exportable.

### 9. Data Retention and Deletion
- Raw transcripts: deleted immediately after successful compression
- Knowledge graph nodes: retained for 90 days by default (configurable)
- Audit records: retained for 1 year by default; cannot be deleted via API
- Developers can delete their own session history via API at any time

### 10. Gateway Security
- All traffic over HTTPS — TLS termination at the gateway
- Gateway API key required on every endpoint except `/healthz`
- Audit log on a separate admin credential
- Redis and PostgreSQL bound to localhost — not exposed externally
- AWS credentials managed via IAM roles — no hardcoded keys anywhere
- EC2 security group: port 443 open to a configurable CIDR range (not a single IP, to handle dynamic IPs)
- `pip audit` in CI fails on high and critical severity vulnerabilities

### 11. Developer Interface — Cline + GateThread
GateThread does not ship its own UI in V1. Developers use **Cline** (VS Code extension) pointed at the GateThread gateway. Cline provides the chat panel, file reading, file editing, and terminal access. GateThread provides the intelligence, privacy, and memory underneath.

```bash
gatethread start   # starts the gateway on AWS, waits for ready, prints connection config
gatethread warm    # pre-loads the Ollama model so the first prompt is not slow
gatethread stop    # stops the EC2 instance
```

> **Cold start reality:** First boot on a fresh instance takes 5–10 minutes (model download). Subsequent starts reuse the EBS-cached model and take ~2 minutes. `gatethread warm` should be run before a session if the instance was stopped.

### 12. AWS Deployment via Terraform
The full stack deploys to AWS with a single `terraform apply`. CPU-optimized EC2 instance for V1 (GPU upgrade path defined for V1.1). Auto-stop when idle to minimize cost. The EBS volume persists the Ollama model across instance stops so cold start is only paid once.

---

## Tech Stack

| Component | Technology | Reason |
|---|---|---|
| Gateway API | Python + FastAPI | Every library we need has its best implementation in Python. Async throughout. |
| Local LLM runtime | Ollama | Handles GPU/CPU automatically. One-command model switching. Clean HTTP API. |
| Local LLM model | Qwen2.5-Coder 7B | Best performing open model for code tasks at this size. Routing quality benchmarked in V1. |
| Cloud LLM client | LiteLLM | Unified API across providers. Claude in V1, GPT-4o in V1.2 — one config line change. |
| Cloud provider (V1) | Anthropic Claude | Best reasoning quality for complex prompts. |
| PII redaction | Microsoft Presidio | Mature, open source. False positives are a known tradeoff — mitigated by configurable thresholds and audit log visibility. |
| Primary database | PostgreSQL + pgvector | Relational data + vector search + graph edges (via recursive CTEs) in one service. No separate vector DB or graph DB. |
| Session buffer | Redis | Ephemeral by design. Never touches disk. TTL-based expiry. |
| Infrastructure | Terraform (AWS) | IaC from day one. Any infrastructure engineer knows it. |
| Compute (V1) | AWS EC2 CPU-optimized (`c5.2xlarge`) | Proof of concept sizing. GPU path (`g4dn.xlarge`) defined for V1.1. |

---

## Roadmap

### V1.0 — Foundation
*Goal: One developer uses GateThread as their primary AI coding interface and gains privacy, memory, and a full audit trail without losing model quality.*

**Success criteria:**
- Routing classification latency under 3 seconds on CPU for prompts up to 500 tokens
- Zero credentials or PII transmitted to Claude in a standard coding session (verified via audit log + redaction map inspection)
- Knowledge graph context from a previous session correctly retrieved and injected in a new session on a related prompt
- Full stack deployed via Terraform in under 15 minutes on a fresh AWS account (model download included)
- Retrieval pipeline precision measured against a held-out eval set — must outperform raw cosine similarity baseline

**Features:**
- [ ] OpenAI-compatible gateway API
- [ ] Local LLM routing (Qwen2.5-Coder via Ollama)
- [ ] PII and credential redaction (Presidio) with cryptographic placeholders
- [ ] Context rehydration after cloud response
- [ ] Multi-turn conversation history with windowed summarization
- [ ] Claude integration via LiteLLM
- [ ] Async session compression to knowledge graph
- [ ] Always-on context retrieval (graph-augmented vector search)
- [ ] Audit log with separate admin credential
- [ ] Data retention and deletion API
- [ ] Gateway security (HTTPS, IAM, configurable CIDR)
- [ ] Terraform deployment on AWS EC2 (CPU)

---

### V1.1 — Multi-Developer
*Goal: A team of up to 5 developers shares one GateThread instance with full session and audit isolation between them.*

**Success criteria:**
- No session data visible across developer accounts
- Concurrent usage by 3 developers with no degradation in routing latency
- GPU instance brings routing latency under 1 second

**Features:**
- [ ] Per-developer session isolation
- [ ] GPU instance support (EC2 `g4dn.xlarge`) for faster local inference
- [ ] Usage metrics per developer (prompts routed local vs cloud)

---

### V1.2 — Multi-Provider
*Goal: GateThread can route to more than one cloud provider.*

**Features:**
- [ ] OpenAI GPT-4o integration
- [ ] Cost tracking per provider per session

---

### V1.3 — Audit Dashboard
*Goal: A compliance officer or team lead can review AI usage without touching the database.*

**Features:**
- [ ] Web UI for audit log browsing (read-only, admin credential required)
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

### V1.5 — THREAD Benchmark
*Goal: Publish a standardized, open benchmark for cross-session context quality — and prove GateThread wins it on real developer sessions.*

**Features:**
- [ ] THREAD benchmark design and real-session dataset (anonymized real developer logs)
- [ ] Three-dimensional scoring: Compression Fidelity, Retrieval Precision, Answer Quality Delta
- [ ] Public leaderboard with scores for GateThread and competing approaches

---

### V2.0 — Team Scale
*Goal: GateThread is production infrastructure for an engineering organization.*

**Features:**
- [ ] Admin controls and developer management
- [ ] Per-developer usage limits and cost budgets
- [ ] Kubernetes deployment (Helm chart)
- [ ] SSO integration (SAML/OIDC)
- [ ] Air-gapped deployment mode (zero cloud calls, for defense and government)

---

### V3.0 — Native Editor Experience
*Goal: GateThread ships its own VS Code extension — full control over the interface, branding, and UX.*

**Features:**
- [ ] VS Code extension with native chat panel
- [ ] Direct file access and editing from the extension
- [ ] Session history browser, redaction visibility, audit log inline

---

## Non-Goals

**Fine-tuning or training models on your codebase.**
GateThread achieves personalization through the knowledge graph and context retrieval — no training pipeline needed.

**Storing full conversation history.**
Raw transcripts grow without bound and are expensive to search. Session compression trades completeness for precision. A structured knowledge graph node is more useful in future context than a 3,000-token raw log.

**A hosted SaaS version.**
GateThread's core value is that your data stays on your infrastructure. A hosted version would contradict that entirely.

**A custom editor plugin before V3.0.**
Cline covers the V1 use case completely. Building a custom extension before the gateway itself is proven would be building in the wrong order.

---

## Contributing

GateThread is open source and in active development.

**To contribute:**
1. Check the open issues — work is organized by milestone
2. Comment on an issue before starting work — avoid duplicate effort
3. One feature or fix per pull request
4. All code must include tests
5. Python style: `ruff` for formatting and linting (config in `pyproject.toml`)
6. Every PR is reviewed before merge — no direct commits to `main`

**To report a real-world requirement:**
If you work in a regulated environment and have requirements not covered here, open an issue with your use case. Real constraints shape the roadmap.
