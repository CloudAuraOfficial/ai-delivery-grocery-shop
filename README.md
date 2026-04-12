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
