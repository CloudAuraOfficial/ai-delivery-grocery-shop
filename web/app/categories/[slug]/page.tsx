"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getProductsByCategory, getCategoryBySlug } from "@/lib/api";
import type { Product, Category, PagedResult } from "@/lib/types";
import ProductCard from "@/components/products/ProductCard";
import Pagination from "@/components/shared/Pagination";

export default function CategoryProductsPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [category, setCategory] = useState<Category | null>(null);
  const [data, setData] = useState<PagedResult<Product> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCategoryBySlug(slug).then(setCategory).catch(console.error);
  }, [slug]);

  useEffect(() => {
    setLoading(true);
    getProductsByCategory(slug, page)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [slug, page]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <nav className="text-sm text-muted mb-6">
        <Link href="/categories" className="hover:text-primary">Categories</Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{category?.name || slug}</span>
      </nav>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">{category?.name || slug}</h1>
        {category && <p className="text-muted text-sm mt-1">{category.description}</p>}
        {data && <p className="text-muted text-sm mt-1">{data.totalCount} products</p>}
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
        <div className="text-center py-16 text-muted">No products in this category.</div>
      )}
    </div>
  );
}
