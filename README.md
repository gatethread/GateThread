# LLMGate

> The standard for how engineering teams use AI — private, auditable, and cost-efficient.
> One gateway. Sensitive data stays on your infrastructure. Cloud models when you need them.

---

## The Problem

Every engineering team that adopts AI tooling faces the same unresolved tension:

- The best models are cloud-hosted — your code and data leave your infrastructure
- Local models are private — but they can't match cloud model quality
- There is no middle layer that makes intelligent decisions, protects sensitive data, and remembers context across sessions

Teams either accept the risk or block AI tools entirely. LLMGate is the third option.

---

## How It Works

LLMGate is a self-hosted gateway that runs on your own infrastructure. Every prompt from your editor passes through it. A local model inspects each prompt and decides what happens next.

```
Your Editor (Cline, Continue, Cursor, ...)
              │
              │  prompt
              ▼
     ┌────────────────────┐
     │   LLMGate on AWS   │
     │                    │
     │  Local LLM decides │
     └────────┬───────────┘
              │
   ┌──────────┼──────────┐
   │          │          │
 Local      Cloud      Block
   │          │
   │    Redact PII first
   │          │
   │          ▼
   │       Claude
   │          │
   │    Restore context
   │          │
   └──────────┤
              │
              ▼
         Your Editor
```

When your session ends, LLMGate compresses what was discussed into structured facts. The next time you work on something related, that context is retrieved automatically — cheap, structured, and immediately useful.

Every decision is logged. Nothing is a black box.

---

## Core Principles

**Private by default.** Sensitive data never reaches a cloud provider unredacted. The local model makes the call on every prompt.

**Intelligent routing.** Not every question needs Claude. Simple tasks stay local and cost nothing. Hard tasks go to the best available model.

**Memory that works.** Sessions are compressed into structured facts, not raw transcripts. Context is retrieved on demand — only when relevant, never as noise.

**Full auditability.** Every prompt is logged: who asked, where it went, what was redacted. Teams can prove compliance without guesswork.

**Operator-grade deployment.** Infrastructure-as-code from day one. No manual setup. Repeatable across environments.

---

## Who This Is For

| Use case | Why LLMGate |
|----------|-------------|
| Teams under GDPR | Customer data cannot leave your infrastructure |
| Healthcare & finance | HIPAA, PCI-DSS, data residency requirements |
| Defense & government | Air-gapped environments, zero cloud exposure |
| Companies with proprietary code | Your codebase is your IP — keep it local |
| Cost-conscious teams | Simple tasks stay local, hard tasks go to Claude |

---

## Quickstart

**Requirements:** Terraform, AWS credentials

```bash
git clone https://github.com/zoolaph/llmgate
cd llmgate
cp config.example.yaml config.yaml
terraform -chdir=deploy/aws init
terraform -chdir=deploy/aws apply
```

LLMGate will output the gateway URL. Point your editor at it.

**Connect your editor:**

<details>
<summary>Cline (VS Code)</summary>

```
Provider : OpenAI Compatible
Base URL : https://<your-gateway-url>/v1
API Key  : llmgate
Model    : auto
```
</details>

<details>
<summary>Continue (VS Code / JetBrains)</summary>

```json
{
  "models": [{
    "title": "LLMGate",
    "provider": "openai",
    "model": "auto",
    "apiBase": "https://<your-gateway-url>/v1",
    "apiKey": "llmgate"
  }]
}
```
</details>

<details>
<summary>curl</summary>

```bash
curl https://<your-gateway-url>/v1/chat/completions \
  -H "Authorization: Bearer llmgate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "explain this function"}]
  }'
```
</details>

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
| Session buffer | Redis |
| Infrastructure | Terraform (AWS EC2) |

---

## Roadmap

V1.0 → V1.1 → V1.2 → V1.3 → V1.4 → V2.0 → V3.0

For the full milestone plan, success criteria, and tech stack rationale, see [PROJECT.md](PROJECT.md).

---

## Contributing

LLMGate is open source. See [PROJECT.md](PROJECT.md) for the milestone structure and `CONTRIBUTING.md` for the PR process.

If you work in a regulated environment and have requirements not covered here — open an issue. Real use cases shape the roadmap.

---

## License

MIT
