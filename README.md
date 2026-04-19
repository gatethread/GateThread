# GateThread

> The standard for how engineering teams use AI — private, auditable, and cost-efficient.
> One gateway. Sensitive data stays on your infrastructure. Cloud models when you need them.

---

## The Problem

Every engineering team that adopts AI tooling faces the same unresolved tension:

- The best models are cloud-hosted — your code and data leave your infrastructure
- Local models are private — but they can't match cloud model quality
- There is no middle layer that makes intelligent decisions, protects sensitive data, and remembers context across sessions

Teams either accept the risk or block AI tools entirely. GateThread is the third option.

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

**Redaction happens before routing.** The local model and Claude both see only the redacted prompt. Sensitive values never leave your infrastructure.

When your session ends, GateThread compresses what was discussed into a structured knowledge graph — decisions, constraints, open questions, relationships between facts. The next time you work on something related, relevant context is retrieved automatically and injected into the prompt.

Every decision is logged. Nothing is a black box.

---

## Core Principles

**Private by default.** Sensitive data is redacted at the door — before routing, before the local model, before storage. One rule, applied once.

**Intelligent routing.** Not every question needs Claude. Simple tasks stay local and cost nothing. The routing decision is a fast classification call, not a full inference pass.

**Memory that works.** Sessions are compressed into a knowledge graph — facts with relationships, scores that decay with time, conflicts resolved automatically. Context is retrieved on demand, ranked by recency and relevance.

**Full auditability.** Every prompt is logged: who asked, where it went, what was redacted. The audit log is on a separate access path — it cannot be accessed with the same credential that controls the gateway.

**Operator-grade deployment.** Infrastructure-as-code from day one. No manual setup. Repeatable across environments.

---

## Who This Is For

| Use case | Why GateThread |
|----------|----------------|
| Teams under GDPR | Customer data cannot leave your infrastructure |
| Healthcare & finance | HIPAA, PCI-DSS, data residency requirements |
| Defense & government | Air-gapped environments, zero cloud exposure |
| Companies with proprietary code | Your codebase is your IP — keep it local |
| Cost-conscious teams | Simple tasks stay local, hard tasks go to Claude |

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

---

## Roadmap

V1.0 → V1.1 → V1.2 → V1.3 → V1.4 → V1.5 → V2.0 → V3.0

For the full milestone plan, success criteria, and tech stack rationale, see [PROJECT.md](PROJECT.md).

---

## Contributing

GateThread is open source. See [PROJECT.md](PROJECT.md) for the milestone structure and `CONTRIBUTING.md` for the PR process.

If you work in a regulated environment and have requirements not covered here — open an issue. Real use cases shape the roadmap.

---

## License

MIT
