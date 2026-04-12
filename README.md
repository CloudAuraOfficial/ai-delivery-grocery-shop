# AIDeliveryGroceryShop

AI-powered grocery delivery platform demonstrating enterprise-grade engineering across C#, Python, TypeScript, and Azure cloud services.

## Architecture

- **Backend API**: ASP.NET Core 8 Web API (C#)
- **AI Service**: FastAPI with RAG pipeline (Python)
- **Frontend**: Next.js 14 with TypeScript
- **Azure Functions**: Deal rotation, product embeddings, notifications (.NET 8)
- **Infrastructure**: Docker Compose (VPS) + Terraform (Azure)

## Features

- 3,000+ product catalog across 6 categories
- 3 deal types: BOGO, Weekly Deals, Daily Deals
- 9 store locations (Lakeland, FL area)
- AI chatbot with RAG-powered product search and recommendations
- OpenTelemetry observability with Grafana dashboards

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | C# / .NET 8 / ASP.NET Core / Entity Framework |
| AI | Python / FastAPI / Qdrant / Ollama / Azure OpenAI |
| Frontend | TypeScript / Next.js 14 / Tailwind CSS |
| Functions | Azure Functions (.NET 8 Isolated Worker) / Azurite |
| Database | PostgreSQL (local) / Azure SQL (prod) |
| Cache | Redis |
| IaC | Terraform (7 Azure modules) |
| CI/CD | GitHub Actions |
| Observability | OpenTelemetry / Prometheus / Grafana |

## Live

- **App**: https://aideliverygroceryshop.cloudaura.cloud
- **Plan**: https://cloudaura.cloud/ai-delivery-grocery-shop-plan.html
