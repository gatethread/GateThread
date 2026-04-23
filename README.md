# GateThread

> The AI gateway that routes intelligently, remembers your sessions, and keeps cloud costs under control.
> Local model handles the simple stuff for free. Cloud model when you need it. Context from your last session already there.

---

## The Problem

Every developer using AI tools daily runs into the same frustrations:

- Every new session starts cold — you re-explain your architecture, your constraints, the decision you made last week
- Simple questions burn the same token budget as hard ones — you end up rationing
- Local models are free but can't match cloud quality — cloud models are capable but expensive
- There is no layer that routes intelligently, compresses context, and remembers what matters across sessions

You either accept the inefficiency or start limiting how much you use AI. GateThread is the third option.

---

## How It Works

GateThread is a self-hosted gateway that runs on your own infrastructure. Every prompt from your editor passes through it. A local model inspects each prompt and decides what happens next.

```
Your Editor (Cline, Continue, Cursor, ...)
              │
              │  prompt
              ▼
     ┌──────────────────────┐
     │   GateThread on AWS  │
     │                      │
     │  1. Redact PII first │
     │  2. Local LLM routes │
     └────────┬─────────────┘
              │
   ┌──────────┼──────────┐
   │          │          │
 Local      Cloud      Block
   │          │
   │       Redacted prompt
   │          │
   │          ▼
   │        Claude
   │          │
   │    Restore original values
   │          │
   └──────────┤
              │
              ▼
         Your Editor
```

**The local model decides what happens next.** Simple questions — syntax, boilerplate, lookups — are answered locally for free. Complex prompts that need stronger reasoning go to Claude. The routing call is a fast structured classification, not a full inference pass.

**When a prompt reaches Claude, it arrives optimized.** Before routing, GateThread compresses your session history into structured facts — decisions, constraints, open questions — stored as searchable vectors. The injected context is ranked by relevance and recency, not raw history. You spend fewer tokens and get a better answer.

**Your next session picks up where you left off.** Session facts persist across sessions. When you start working on something related, the relevant context is retrieved and injected automatically. You never re-explain the same thing twice.

**Sensitive data is redacted before anything else.** PII and credentials are replaced with typed placeholders the moment a prompt enters the gateway — before the local model, before Claude, before storage. Sensitive values never leave your infrastructure.

Every routing decision is logged. Nothing is a black box.

---

## Core Principles

**Intelligent routing.** Not every question needs Claude. Simple tasks stay local and cost nothing. The routing decision is a fast classification call, not a full inference pass.

**Memory that works.** Sessions are compressed into structured facts — decisions, constraints, open questions — stored as searchable vectors. When you reach a paid model, the context injected is the most relevant, most recent facts from your previous work — not a raw transcript dump.

**Private by default.** Sensitive data is redacted at the door — before routing, before the local model, before storage. One rule, applied once.

**Full auditability.** Every prompt is logged: who asked, where it went, what was redacted. The audit log is on a separate access path — it cannot be accessed with the same credential that controls the gateway.

**Operator-grade deployment.** Infrastructure-as-code from day one. No manual setup. Repeatable across environments.

---

## Who This Is For

| Use case | Why GateThread |
|----------|----------------|
| Developers hitting token limits | Simple questions route local for free — cloud budget goes further |
| Teams losing context between sessions | Knowledge graph persists across sessions — never start cold again |
| Companies with proprietary code | Your codebase is your IP — stays on your infrastructure |
| Teams under GDPR | Customer data cannot leave your infrastructure |
| Healthcare & finance | HIPAA, PCI-DSS, data residency requirements |
| Defense & government | Air-gapped environments, zero cloud exposure *(V2.0)* |

---

## Quickstart

**Requirements:** Terraform, AWS credentials

```bash
git clone https://github.com/gatethread/GateThread
cd GateThread
cp config.example.yaml config.yaml
terraform -chdir=deploy/aws init
terraform -chdir=deploy/aws apply
```

GateThread will output the gateway URL. Point your editor at it.

> **Note on startup time:** The first `terraform apply` on a fresh instance pulls the Ollama model (~4 GB). Expect 5–10 minutes on first boot. Subsequent starts are faster once the model is cached on the EBS volume. Use `gatethread warm` to pre-load the model before your session.

**Connect your editor:**

<details>
<summary>Cline (VS Code)</summary>

```
Provider : OpenAI Compatible
Base URL : https://<your-gateway-url>/v1
API Key  : <your-api-key from config.yaml>
Model    : auto
```
</details>

<details>
<summary>Continue (VS Code / JetBrains)</summary>

```json
{
  "models": [{
    "title": "GateThread",
    "provider": "openai",
    "model": "auto",
    "apiBase": "https://<your-gateway-url>/v1",
    "apiKey": "<your-api-key from config.yaml>"
  }]
}
```
</details>

<details>
<summary>curl</summary>

```bash
curl https://<your-gateway-url>/v1/chat/completions \
  -H "Authorization: Bearer <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "explain this function"}]
  }'
```
</details>

---

## Local Development

Run the full stack locally without AWS. You need Docker, Python 3.11+, and Ollama.

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp config.example.yaml config.yaml
# Edit config.yaml — set gateway.api_key and cloud.anthropic_api_key at minimum
```

### 3. Start PostgreSQL and Redis

```bash
docker compose up -d
```

Wait for both services to show `healthy`:

```bash
docker compose ps
```

### 4. Pull local models

```bash
ollama pull qwen2.5-coder:7b   # routing and local responses
ollama pull nomic-embed-text    # memory embeddings
```

### 5. Run migrations

```bash
alembic upgrade head
```

### 6. Start the gateway

```bash
uvicorn app.main:app --reload --port 8000
```

The gateway is now available at `http://localhost:8000`. Connect your editor
using `http://localhost:8000/v1` as the base URL.

### Running tests

```bash
pytest          # full suite
ruff check .    # lint check
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Gateway API | Python + FastAPI |
| Local LLM runtime | Ollama |
| Local LLM model | Qwen2.5-Coder 7B |
| Cloud LLM client | LiteLLM |
| Cloud provider | Anthropic Claude |
| PII redaction | Microsoft Presidio |
| Database | PostgreSQL + pgvector |
| Session buffer | Redis (ephemeral, no disk persistence) |
| Infrastructure | Terraform (AWS EC2) |
| Compute (V1.0 — single dev) | AWS EC2 `c5.2xlarge` (CPU) — sized for one developer. GPU (`g4dn.xlarge`) added in V1.1. |

---

## Roadmap

V1.0 → V1.1 → V1.2 → V1.3 → V1.4 → V2.0 → V3.0

For the full milestone plan, success criteria, and tech stack rationale, see [PROJECT.md](PROJECT.md).

---

## Contributing

GateThread is open source. See [PROJECT.md](PROJECT.md) for the milestone structure and `CONTRIBUTING.md` for the PR process.

If you work in a regulated environment and have requirements not covered here — open an issue. Real use cases shape the roadmap.

---

## License

MIT
