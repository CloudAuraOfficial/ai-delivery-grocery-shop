"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getProductById } from "@/lib/api";
import { formatPrice, formatDealBadge, dealBadgeColor } from "@/lib/utils";
import type { Product } from "@/lib/types";

export default function ProductDetailPage() {
  const params = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      getProductById(params.id as string)
        .then(setProduct)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="animate-pulse bg-gray-100 rounded-xl h-96" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold mb-4">Product Not Found</h1>
        <Link href="/products" className="text-primary hover:underline">Back to products</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <nav className="text-sm text-muted mb-6">
        <Link href="/products" className="hover:text-primary">Products</Link>
        <span className="mx-2">/</span>
        <Link href={`/categories/${product.categoryName.toLowerCase().replace(/ & /g, "-").replace(/ /g, "-")}`} className="hover:text-primary">
          {product.categoryName}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{product.name}</span>
      </nav>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Image */}
        <div className="aspect-square bg-gray-100 rounded-xl flex items-center justify-center text-8xl relative">
          <span className="opacity-30">🛒</span>
          {product.activeDeal && (
            <span className={`absolute top-4 left-4 ${dealBadgeColor(product.activeDeal.dealType)} text-white text-sm font-bold px-3 py-1.5 rounded-lg`}>
              {formatDealBadge(product.activeDeal.dealType)}
            </span>
          )}
        </div>

        {/* Details */}
        <div>
          <div className="flex flex-wrap gap-2 mb-3">
            {product.isOrganic && (
              <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">Organic</span>
            )}
            {product.isStoreBrand && (
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">GreenWise</span>
            )}
          </div>

          <h1 className="text-2xl font-bold text-foreground mb-2">{product.name}</h1>
          {product.brand && <div className="text-muted text-sm mb-4">by {product.brand}</div>}

          <div className="flex items-baseline gap-2 mb-4">
            <span className="text-3xl font-bold text-foreground">{formatPrice(product.price)}</span>
            <span className="text-muted">/ {product.unit}</span>
          </div>

          {product.activeDeal && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="font-semibold text-red-700">{product.activeDeal.title}</div>
              {product.activeDeal.discountPercent && (
                <div className="text-sm text-red-600">Save {product.activeDeal.discountPercent}%</div>
              )}
            </div>
          )}

          <p className="text-muted text-sm mb-6">{product.description}</p>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted">SKU</span>
              <span className="font-mono text-foreground">{product.sku}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted">Category</span>
              <span className="text-foreground">{product.categoryName}</span>
            </div>
            {product.weight && (
              <div className="flex justify-between py-2 border-b border-border">
                <span className="text-muted">Size</span>
                <span className="text-foreground">{product.weight}</span>
              </div>
            )}
            {product.tags && (
              <div className="flex justify-between py-2">
                <span className="text-muted">Tags</span>
                <div className="flex flex-wrap gap-1 justify-end">
                  {product.tags.split(",").map((tag) => (
                    <span key={tag} className="bg-gray-100 text-muted text-xs px-2 py-0.5 rounded">{tag.trim()}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <button className="mt-6 w-full py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary-dark transition-colors">
            Add to Cart
          </button>
        </div>
      </div>
    </div>
  );
}
