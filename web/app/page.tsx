import Link from "next/link";

const categories = [
  { name: "Baby", slug: "baby", icon: "🍼", color: "bg-pink-50 border-pink-200" },
  { name: "Beverages", slug: "beverages", icon: "🥤", color: "bg-blue-50 border-blue-200" },
  { name: "Household", slug: "household", icon: "🧹", color: "bg-yellow-50 border-yellow-200" },
  { name: "Fresh", slug: "fresh", icon: "🥬", color: "bg-green-50 border-green-200" },
  { name: "Meat & Seafood", slug: "meat-seafood", icon: "🥩", color: "bg-red-50 border-red-200" },
  { name: "Deli", slug: "deli", icon: "🧀", color: "bg-amber-50 border-amber-200" },
];

const dealHighlights = [
  { type: "BOGO", label: "Buy One Get One", count: "200+", color: "from-red-600 to-red-700" },
  { type: "weekly", label: "Weekly Deals", count: "150+", color: "from-amber-500 to-amber-600" },
  { type: "daily", label: "Daily Deals", count: "15", color: "from-emerald-600 to-emerald-700" },
];

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-primary to-primary-dark text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 text-8xl">🥑</div>
          <div className="absolute top-20 right-20 text-7xl">🍎</div>
          <div className="absolute bottom-10 left-1/3 text-6xl">🥖</div>
          <div className="absolute bottom-20 right-10 text-8xl">🧃</div>
        </div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 bg-white/15 rounded-full px-4 py-1.5 text-sm mb-6 backdrop-blur-sm">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              9 Stores in Lakeland, FL
            </div>
            <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
              Fresh groceries,<br />
              <span className="text-green-200">delivered smart.</span>
            </h1>
            <p className="text-lg text-green-100 mb-8 max-w-lg">
              3,000+ products across 6 categories. BOGO deals, weekly savings, and an
              AI assistant that knows exactly what you need.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                href="/products"
                className="px-8 py-3 bg-white text-primary font-semibold rounded-lg hover:bg-green-50 transition-colors"
              >
                Shop Now
              </Link>
              <Link
                href="/chat"
                className="px-8 py-3 bg-white/15 text-white font-semibold rounded-lg hover:bg-white/25 transition-colors backdrop-blur-sm border border-white/20"
              >
                💬 Ask AI Assistant
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Deals Banner */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {dealHighlights.map((deal) => (
            <Link
              key={deal.type}
              href={`/deals?type=${deal.type}`}
              className={`bg-gradient-to-r ${deal.color} rounded-xl p-5 text-white shadow-lg hover:shadow-xl transition-shadow`}
            >
              <div className="text-sm font-medium opacity-90">{deal.count} Products</div>
              <div className="text-xl font-bold mt-1">{deal.label}</div>
              <div className="text-sm mt-2 opacity-80">Shop deals &rarr;</div>
            </Link>
          ))}
        </div>
      </section>

      {/* Categories */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Shop by Category</h2>
            <p className="text-muted text-sm mt-1">Browse our 6 departments</p>
          </div>
          <Link href="/categories" className="text-sm font-medium text-primary hover:text-primary-dark">
            View all &rarr;
          </Link>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map((cat) => (
            <Link
              key={cat.slug}
              href={`/categories/${cat.slug}`}
              className={`${cat.color} border rounded-xl p-6 text-center hover:shadow-md transition-all group`}
            >
              <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">{cat.icon}</div>
              <div className="font-semibold text-foreground text-sm">{cat.name}</div>
            </Link>
          ))}
        </div>
      </section>

      {/* AI Assistant CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="bg-gradient-to-r from-gray-900 to-gray-800 rounded-2xl p-8 md:p-12 text-white">
          <div className="max-w-xl">
            <div className="text-3xl mb-2">💬</div>
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Need help finding something?
            </h2>
            <p className="text-gray-300 mb-6">
              Our AI shopping assistant can search products, find deals, recommend meals,
              and answer questions about our 9 store locations — all powered by RAG.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/chat"
                className="px-6 py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-dark transition-colors"
              >
                Start Chatting
              </Link>
              <div className="flex gap-2 items-center">
                {["What baby products are on BOGO?", "Find organic milk", "Store hours"].map((q) => (
                  <span key={q} className="text-xs bg-white/10 px-3 py-1.5 rounded-full text-gray-300">
                    {q}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-surface border-t border-border py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { value: "3,300+", label: "Products" },
              { value: "365", label: "Active Deals" },
              { value: "9", label: "Store Locations" },
              { value: "6", label: "Categories" },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-3xl font-bold text-primary">{stat.value}</div>
                <div className="text-sm text-muted mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
