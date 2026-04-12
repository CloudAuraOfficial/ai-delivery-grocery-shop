import Link from "next/link";

const techStack = [
  { name: "C# / .NET 8", desc: "Web API + Azure Functions", color: "bg-purple-100 text-purple-800" },
  { name: "Python / FastAPI", desc: "AI/RAG Service", color: "bg-blue-100 text-blue-800" },
  { name: "TypeScript / Next.js", desc: "Frontend (this site)", color: "bg-cyan-100 text-cyan-800" },
  { name: "Entity Framework", desc: "ORM + Migrations", color: "bg-indigo-100 text-indigo-800" },
  { name: "Dapper", desc: "Full-text search", color: "bg-violet-100 text-violet-800" },
  { name: "PostgreSQL", desc: "Primary database", color: "bg-blue-100 text-blue-800" },
  { name: "Redis", desc: "Cart + Chat sessions", color: "bg-red-100 text-red-800" },
  { name: "Qdrant", desc: "Vector search (RAG)", color: "bg-orange-100 text-orange-800" },
  { name: "Ollama / Azure OpenAI", desc: "LLM + Embeddings", color: "bg-green-100 text-green-800" },
  { name: "Azure Functions", desc: "Serverless deal engine", color: "bg-sky-100 text-sky-800" },
  { name: "Terraform", desc: "8 Azure IaC modules", color: "bg-violet-100 text-violet-800" },
  { name: "OpenTelemetry", desc: "Distributed tracing", color: "bg-yellow-100 text-yellow-800" },
  { name: "Application Insights", desc: "Azure observability", color: "bg-pink-100 text-pink-800" },
  { name: "Databricks", desc: "PySpark data pipelines", color: "bg-orange-100 text-orange-800" },
  { name: "Docker", desc: "7 containerized services", color: "bg-blue-100 text-blue-800" },
  { name: "GitHub Actions + Azure DevOps", desc: "Dual CI/CD", color: "bg-gray-100 text-gray-800" },
];

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-2">About This Project</h1>
      <p className="text-muted mb-8">
        AIDeliveryGroceryShop is a portfolio engineering project demonstrating enterprise-grade
        full-stack development with AI integration.
      </p>

      <div className="bg-surface border border-border rounded-xl p-6 mb-8">
        <h2 className="font-semibold text-foreground mb-4">Architecture</h2>
        <pre className="text-xs text-muted font-mono overflow-x-auto leading-relaxed">{`
              Cloudflare DNS
                   |
         Nginx Proxy Manager (SSL)
          /        |          \\
  Next.js 14    .NET 8 API   FastAPI
  (TypeScript)  (C#)         (Python RAG)
  :3002         :8020        :8021
    \\              |            /
     \\     PostgreSQL:5436    /
      \\     Redis:6380      /
       \\        |         /
        +-- Qdrant:6333 --+
        +-- Ollama:11434 -+
              |
      Azure Functions (.NET 8)
      (Deal Rotation + Embeddings)
        `}</pre>
      </div>

      <h2 className="font-semibold text-foreground mb-4">Technology Stack ({techStack.length} technologies)</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {techStack.map((tech) => (
          <div key={tech.name} className="flex items-center gap-3 p-3 bg-white border border-border rounded-lg">
            <span className={`${tech.color} text-xs font-medium px-2.5 py-1 rounded shrink-0`}>{tech.name}</span>
            <span className="text-sm text-muted">{tech.desc}</span>
          </div>
        ))}
      </div>

      <div className="flex gap-4">
        <Link
          href="https://cloudaura.cloud/ai-delivery-grocery-shop-plan.html"
          className="px-6 py-3 bg-primary text-white font-medium rounded-lg hover:bg-primary-dark transition-colors"
          target="_blank"
        >
          View Full Plan
        </Link>
        <Link
          href="https://github.com/CloudAuraOfficial/ai-delivery-grocery-shop"
          className="px-6 py-3 border border-border text-foreground font-medium rounded-lg hover:bg-surface transition-colors"
          target="_blank"
        >
          GitHub Repo
        </Link>
      </div>
    </div>
  );
}
