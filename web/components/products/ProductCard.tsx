"use client";

import Link from "next/link";
import { formatPrice, formatDealBadge, dealBadgeColor } from "@/lib/utils";
import type { Product } from "@/lib/types";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      href={`/products/${product.id}`}
      className="group bg-white border border-border rounded-xl overflow-hidden hover:shadow-lg transition-all"
    >
      {/* Image placeholder */}
      <div className="aspect-square bg-gray-100 flex items-center justify-center text-4xl relative">
        <span className="opacity-40 group-hover:opacity-60 transition-opacity">🛒</span>
        {product.activeDeal && (
          <span className={`absolute top-2 left-2 ${dealBadgeColor(product.activeDeal.dealType)} text-white text-xs font-bold px-2 py-1 rounded-md`}>
            {formatDealBadge(product.activeDeal.dealType)}
          </span>
        )}
        {product.isOrganic && (
          <span className="absolute top-2 right-2 bg-green-100 text-green-800 text-xs font-medium px-2 py-0.5 rounded-md">
            Organic
          </span>
        )}
      </div>

      <div className="p-4">
        <div className="text-xs text-muted mb-1">{product.categoryName}</div>
        <h3 className="font-medium text-foreground text-sm leading-tight mb-1 line-clamp-2 group-hover:text-primary transition-colors">
          {product.name}
        </h3>
        {product.brand && (
          <div className="text-xs text-muted mb-2">{product.brand}</div>
        )}
        <div className="flex items-center justify-between">
          <div className="font-bold text-foreground">{formatPrice(product.price)}</div>
          <div className="text-xs text-muted">/{product.unit}</div>
        </div>
        {product.activeDeal && (
          <div className="mt-2 text-xs text-red-600 font-medium">
            {product.activeDeal.title}
          </div>
        )}
      </div>
    </Link>
  );
}
