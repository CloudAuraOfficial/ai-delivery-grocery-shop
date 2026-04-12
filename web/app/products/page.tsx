"use client";

import { useEffect, useState } from "react";
import { getProducts } from "@/lib/api";
import type { Product, PagedResult } from "@/lib/types";
import ProductCard from "@/components/products/ProductCard";
import Pagination from "@/components/shared/Pagination";

export default function ProductsPage() {
  const [data, setData] = useState<PagedResult<Product> | null>(null);
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("name");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string> = { page: String(page), pageSize: "24", sortBy };
    if (search) params.q = search;

    const endpoint = search ? `search?q=${encodeURIComponent(search)}&page=${page}` : "";

    getProducts(params)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, sortBy, search]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">All Products</h1>
          <p className="text-muted text-sm mt-1">
            {data ? `${data.totalCount.toLocaleString()} products` : "Loading..."}
          </p>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="px-4 py-2 text-sm border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 text-sm border border-border rounded-lg bg-white focus:outline-none"
          >
            <option value="name">Name A-Z</option>
            <option value="price_asc">Price Low-High</option>
            <option value="price_desc">Price High-Low</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-64 animate-pulse" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {data.items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          <Pagination page={data.page} totalPages={data.totalPages} onPageChange={setPage} />
        </>
      ) : (
        <div className="text-center py-16 text-muted">No products found.</div>
      )}
    </div>
  );
}
