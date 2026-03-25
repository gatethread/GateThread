# LLMGate

> A privacy-aware AI gateway for engineering teams.
> One endpoint. Sensitive data stays local. Cloud models when you need them.

---

## The problem

Your team wants AI assistance in the editor. Your company has data that cannot reach OpenAI or Anthropic — customer records, credentials, proprietary code, incident details, internal infrastructure.

So you either block AI tools entirely, or accept the risk.

**LLMGate is the third option.**

---

## How it works

```
                         Your Editor
                              │
                              │  prompt
                              ▼
                    ┌──────────────────┐
                    │    Classifier    │
                    │    + PII scan    │
                    └────────┬─────────┘
                             │
               ┌─────────────┴─────────────┐
               │                           │
             safe                      sensitive
               │                           │
               ▼                           ▼
       ┌───────────────┐         ┌──────────────────┐
       │    Ollama     │         │    Presidio      │
       │  local model  │         │   redact PII     │
       └───────┬───────┘         └────────┬─────────┘
               │                          │
               │                          ▼
               │                 ┌──────────────────┐
               │                 │     Claude       │
               │                 │  cloud reasoning │
               │                 └────────┬─────────┘
               │                          │
               │                          ▼
               │                 ┌──────────────────┐
               │                 │   Rehydrate      │
               │                 │  restore context │
               │                 └────────┬─────────┘
               │                          │
               └──────────────┬───────────┘
                              │
                              │  response
                              ▼
                         Your Editor
```

Sensitive data never leaves your infrastructure.
Non-sensitive reasoning goes to the best model for the job.

---

## Who this is for

| Use case | Why LLMGate |
|----------|-------------|
| Teams under GDPR | Customer data cannot leave your infrastructure |
| Healthcare & finance | HIPAA, PCI-DSS, data residency requirements |
| Defense & government | Air-gapped environments, zero cloud exposure |
| Companies with proprietary code | Your codebase is your IP — keep it local |
| Cost-conscious teams | Cheap tasks stay local, hard tasks go to Claude |

---

## Quickstart

**Requirements:** Docker + Docker Compose

```bash
git clone https://github.com/zoolaph/llmgate
cd llmgate
cp config.example.yaml config.yaml
docker compose up
```

LLMGate is now running at `http://localhost:8080/v1` — fully OpenAI-compatible.

**Connect your editor:**

<details>
<summary>Continue (VS Code / JetBrains)</summary>

```json
{
  "models": [{
    "title": "LLMGate",
    "provider": "openai",
    "model": "auto",
    "apiBase": "http://localhost:8080/v1",
    "apiKey": "llmgate"
  }]
}
```
</details>

<details>
<summary>Cline / Roo Code</summary>

```
Provider : OpenAI Compatible
Base URL : http://localhost:8080/v1
API Key  : llmgate
Model    : auto
```
</details>

<details>
<summary>curl</summary>

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer llmgate" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "explain kubernetes ingress"}]
  }'
```
</details>

---

## Configuration

```yaml
# config.yaml

gateway:
  port: 8080
  api_key: llmgate

models:
  local: ollama/llama3.2
  cloud: claude-3-5-sonnet-20241022

routing:
  default: auto          # auto | local | cloud | sensitive

privacy:
  redact:
    - credentials        # API keys, tokens, passwords
    - pii                # Names, emails, phone numbers
    - internal_urls      # Hostnames, internal IPs
    - customer_ids       # UUIDs, account numbers

policy:
  - if: contains_credentials
    then: block
  - if: sensitive_pii
    then: sensitive      # redact → cloud → rehydrate
  - if: low_complexity
    then: local
  - if: high_complexity
    then: cloud

observability:
  tracing: true
  metrics_port: 9090
```

---

## Routing modes

| Mode | Behaviour |
|------|-----------|
| `auto` | LLMGate decides — local for simple, cloud for complex |
| `local` | Always Ollama — nothing leaves your machine |
| `cloud` | Always Claude — full model capability |
| `sensitive` | Redact → Claude → Rehydrate |
| `block` | Request rejected — no model called |

---

## Deployment

**Local / single developer**
```bash
docker compose up
```

**Kubernetes (Helm)**
```bash
helm repo add llmgate https://charts.llmgate.dev
helm install llmgate llmgate/llmgate -f values.yaml
```

**AWS EKS with IRSA** — no API keys in your cluster
```bash
helm install llmgate llmgate/llmgate \
  --set aws.irsa.enabled=true \
  --set aws.irsa.roleArn=arn:aws:iam::ACCOUNT:role/llmgate
```

**Air-gapped / on-prem** — no cloud calls
```bash
docker compose -f docker-compose.airgap.yaml up
```

---

## Why not LiteLLM?

LiteLLM is excellent for routing between cloud providers.
LLMGate does something different.

| | LiteLLM | LLMGate |
|-|:-------:|:-------:|
| Multi-provider routing | ✅ | ✅ |
| OpenAI-compatible API | ✅ | ✅ |
| PII redaction before cloud | ❌ | ✅ |
| Context rehydration | ❌ | ✅ |
| Policy-as-code routing | ❌ | ✅ |
| Air-gapped deployment | ❌ | ✅ |
| Production Helm chart | Partial | ✅ |
| GitOps-ready | ❌ | ✅ |

LLMGate uses LiteLLM internally for provider abstraction.
It adds the privacy and compliance layer on top.

---

## Stack

| Component | Role |
|-----------|------|
| FastAPI | Gateway and API layer |
| LiteLLM | Provider abstraction (Ollama, Claude, Bedrock) |
| Ollama | Local model serving |
| Presidio | PII detection and redaction |
| OPA | Policy-as-code routing decisions |
| OpenTelemetry | Distributed tracing |
| Prometheus + Grafana | Metrics and dashboards |

---

## Roadmap

**v0.1 — Core gateway**
- [x] OpenAI-compatible API (`/v1/chat/completions`, `/v1/models`, `/healthz`)
- [x] Local routing via Ollama
- [x] Cloud routing via Claude
- [x] Docker Compose quickstart

**v0.2 — Privacy layer**
- [ ] PII detection with Presidio
- [ ] Redaction before cloud calls
- [ ] Context rehydration after cloud response

**v0.3 — Policy and control**
- [ ] OPA policy-as-code routing
- [ ] Request blocking rules
- [ ] Audit log

**v0.4 — Production**
- [ ] Kubernetes Helm chart
- [ ] IRSA support for AWS
- [ ] Air-gapped deployment mode
- [ ] OpenTelemetry tracing
- [ ] Prometheus metrics + Grafana dashboard
- [ ] ArgoCD GitOps manifests

---

## Contributing

LLMGate is early-stage. Issues, ideas, and pull requests are welcome.

If you work in a regulated environment and have requirements this doesn't cover — open an issue. Real use cases shape the roadmap.

---

## License

MIT