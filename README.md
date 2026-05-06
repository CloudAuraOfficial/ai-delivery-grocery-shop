# AIDeliveryGroceryShop

AI-powered grocery delivery platform demonstrating enterprise-grade engineering across C#, Python, TypeScript, and Azure cloud services. Built as a portfolio project showcasing the full tech stack for an AI Delivery Lead Software Engineer role.

## Architecture

```
                      Cloudflare DNS
                           |
                 Nginx + Let's Encrypt SSL
                  /        |          \
          Next.js 16    .NET 8 API   FastAPI
          (TypeScript)  (C#)         (Python RAG)
          :3002         :8020        :8021
            \              |            /
             \     PostgreSQL:5436    /
              \     Redis:6380      /
               \        |         /
                +-- Qdrant:6333 --+     ← Vector search (3,674 vectors)
                +-- Ollama:11434 -+     ← Embeddings (nomic-embed-text)
                        |
                 Azure OpenAI (gpt-4o)  ← LLM generation (~1.4s/query)
                 Azure App Insights     ← Telemetry
                 Azure Blob Storage     ← Product images + queues
```

## Features

- **3,300+ products** across 6 categories (Baby, Beverages, Household, Fresh, Meat & Seafood, Deli)
- **365 deals** — BOGO (200), Weekly (150), Daily (15 rotating)
- **9 store locations** in the Lakeland, FL area
- **AI chatbot** powered by Azure OpenAI gpt-4o with RAG (~1.4s response time)
- **13 frontend pages** — product catalog, deals, store locator, cart, checkout, AI chat
- **Full observability** — OpenTelemetry + Azure Application Insights + Prometheus

## Azure Resources (Live)

| Resource | Type | Purpose |
|---|---|---|
| `grocery-openai` | Azure OpenAI (S0) | gpt-4o chat + text-embedding-ada-002 |
| `grocerystorage2026` | Storage Account | Blob containers (product/category images) + Queues |
| `grocery-logs` | Log Analytics Workspace | Centralized logging (30-day retention) |
| `grocery-insights` | Application Insights | APM telemetry from .NET API |

## Tech Stack (21 technologies)

| Layer | Technology |
|-------|-----------|
| API | C# / .NET 8 / ASP.NET Core / Entity Framework Core / Dapper |
| AI Service | Python / FastAPI / Qdrant / Azure OpenAI (gpt-4o) |
| Frontend | TypeScript / Next.js 16 / React 19 / Tailwind CSS v4 |
| Functions | Azure Functions (.NET 8 Isolated Worker) / Azurite |
| Database | PostgreSQL (VPS) / Azure SQL Database (Terraform) |
| Cache | Redis (cart sessions + chat history) |
| Data Pipeline | PySpark / Databricks notebooks |
| Cloud | Azure OpenAI / App Insights / Blob Storage / Log Analytics |
| IaC | Terraform (8 Azure modules) |
| CI/CD | GitHub Actions + Azure DevOps |
| Observability | OpenTelemetry / Azure Application Insights / Prometheus |
| MLOps | RAG evaluation framework (quality, regression, latency) |

## Project Structure

```
├── src/
│   ├── GroceryShop.Core/           # Domain entities, DTOs, interfaces
│   ├── GroceryShop.Infrastructure/  # EF Core, Dapper, services
│   ├── GroceryShop.Api/            # ASP.NET Core Web API (30+ endpoints)
│   └── GroceryShop.Functions/      # Azure Functions (3 functions)
├── ai-service/                     # Python FastAPI RAG chatbot
│   ├── app/services/               # Embedder, retriever, generator, chat
│   └── evaluation/                 # RAG quality, regression, latency tests
├── web/                            # Next.js 16 frontend (13 routes)
├── data-pipeline/                  # Product generation + DB seeding
├── databricks/                     # PySpark analytics notebooks
├── infra/                          # Terraform (8 Azure modules)
├── notebooks/                      # Prompt optimization A/B testing
├── docker-compose.yml              # 5 services + Azurite
├── azure-pipelines.yml             # Azure DevOps CI/CD
└── .github/workflows/ci-cd.yml     # GitHub Actions CI/CD
```

## Quick Start

```bash
# Start infrastructure
docker compose up -d grocery-db grocery-redis

# Run data pipeline
python data-pipeline/generate_products.py
python data-pipeline/generate_deals.py
python data-pipeline/seed_database.py

# Index products into Qdrant
python data-pipeline/index_vectors.py

# Start all services
docker compose up -d

# Verify
curl http://localhost:8020/health          # API
curl http://localhost:8021/health          # AI Service
curl http://localhost:3002                 # Frontend
```

## Live

- **App**: https://aideliverygroceryshop.cloudaura.cloud
- **Plan**: https://cloudaura.cloud/ai-delivery-grocery-shop-plan.html
- **Explainer**: https://cloudaura.cloud/ai-delivery-grocery-shop-ultra-plan.html
- **Repo**: https://github.com/CloudAuraOfficial/ai-delivery-grocery-shop

## Infrastructure substitutions (portfolio → enterprise)

This project runs cost-efficiently on a single VPS. Each piece is intentionally
the portfolio analogue of the enterprise component it would be replaced with at
production scale. The application code and abstractions are unchanged across
the swap — only the deployment substrate moves.

| Concern             | Portfolio (here)                          | Enterprise (production target)                                | Why the substitution is honest                                                                 |
|---------------------|-------------------------------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| Edge / DNS / WAF    | Cloudflare DNS + host Nginx + Let's Encrypt | Azure Front Door + WAF policies + Application Gateway        | Same TLS termination + L7 routing surface; loses regional failover, native WAF rules, bot protection in our control plane. |
| Compute             | Single Docker host, 3 long-running containers | Azure Container Apps (Consumption) with KEDA autoscale       | Container images are unchanged; only the orchestrator differs. Per-service replica count goes from 1 → autoscaled. |
| Relational DB       | Postgres 16 in container                  | Azure SQL (Hyperscale) **or** Azure DB for PostgreSQL Flexible Server | Dapper + EF Core providers swap with one connection-string change. Loses geo-replication, AAD auth, Always Encrypted, automated backups. |
| Vector store        | Qdrant (self-hosted)                      | Azure AI Search (vector + BM25 + semantic ranker)            | Qdrant is fast and cheap for pure vector; Azure AI Search adds hybrid retrieval, RBAC, multi-tenant index isolation, private endpoints. The retriever interface in `ai-service/app/services/retriever.py` is the abstraction point. |
| Embeddings          | Ollama `nomic-embed-text` (local)         | Azure OpenAI `text-embedding-3-large`                         | `EMBEDDING_PROVIDER` env flips between them; same `app.services.embeddings` interface. |
| LLM                 | Azure OpenAI gpt-4o (already)             | (same)                                                        | Already production-shaped. |
| Background jobs     | `GroceryShop.Functions` (.NET Isolated)   | Azure Functions Premium / Container Apps Jobs                 | Code is identical; runtime swap only. |
| Cache / pubsub      | Redis 7 in container                      | Azure Cache for Redis Premium (zone-redundant)                | Same `redis-py` / `StackExchange.Redis` clients. Adds zone redundancy, persistence, private link. |
| Object storage      | Local + Azurite (dev)                     | Azure Blob Storage (already used in prod path)                | Already production-shaped. |
| Observability       | OpenTelemetry → App Insights              | (same) + Log Analytics workspace + Azure Monitor alerts       | Already production-shaped; alerting rules are what's missing. |
| Secrets             | `.env` + Azure Key Vault when `AZURE_KEY_VAULT_URI` set | Azure Key Vault + Managed Identity on every workload | The resolution path in `ai-service/app/secrets.py` already prefers Key Vault when configured; populate the env var on Container Apps and the lookup goes vault-first with no code change. |
| CI/CD               | GitHub Actions: build only                | GitHub Actions: build → ACR push → Container Apps revision    | The build job is unchanged; the deploy job is the swap. The `deployments/aci-bicep/` template here is one form of that swap. |
| Multi-tenancy       | None (single brand)                       | Tenant-keyed partitions + RBAC per tenant                     | Deliberately not stubbed in code — adding a `TenantId` column without enforcement is worse than no tenancy code at all. The intended approach: row-level security in Postgres, EF query filter in .NET, Qdrant per-tenant collection prefixes. |
| Resilience          | tenacity retry + canned fallback (Python), Polly equivalent on .NET roadmap | Same patterns + chaos drills + DLQs                          | Pattern is in `ai-service/app/services/generator.py`; .NET equivalent (Polly pipeline + Circuit Breaker on outbound HTTP) is the next addition. |
| Rate limiting       | slowapi per-IP on `/api/chat*` (30/min)   | API Management policies + per-tenant quotas + 429 SLOs        | App-layer cap defends against wallet-DoS; APIM moves the policy to the edge and adds per-tenant fairness. |
| Input safety        | Regex-based prompt-injection guard + length cap | Azure AI Content Safety / Prompt Shields + telemetry on blocks | The interface in `ai-service/app/security/input_guard.py` becomes a thin wrapper around the managed service. |

**What this section is not:** a claim that the portfolio infra is production-ready. It is a map showing that every piece has a known, named, drop-in enterprise equivalent — and that the application code does not need to be rewritten when the substitution happens.
