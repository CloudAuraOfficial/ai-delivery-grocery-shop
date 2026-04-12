"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCategories } from "@/lib/api";
import { categoryIcon } from "@/lib/utils";
import type { Category } from "@/lib/types";

const categoryColors: Record<string, string> = {
  baby: "from-pink-500 to-rose-500",
  beverages: "from-blue-500 to-cyan-500",
  household: "from-yellow-500 to-amber-500",
  fresh: "from-green-500 to-emerald-500",
  "meat-seafood": "from-red-500 to-orange-500",
  deli: "from-amber-500 to-yellow-500",
};

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    getCategories().then(setCategories).catch(console.error);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-2">Categories</h1>
      <p className="text-muted text-sm mb-8">Browse our 6 departments</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map((cat) => (
          <Link
            key={cat.slug}
            href={`/categories/${cat.slug}`}
            className="group relative overflow-hidden rounded-2xl h-48"
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${categoryColors[cat.slug] || "from-gray-500 to-gray-600"} opacity-90 group-hover:opacity-100 transition-opacity`} />
            <div className="relative h-full flex flex-col justify-between p-6 text-white">
              <div className="text-5xl">{categoryIcon(cat.slug)}</div>
              <div>
                <h2 className="text-xl font-bold">{cat.name}</h2>
                <p className="text-sm text-white/80 mt-1">{cat.description}</p>
                <div className="text-sm font-medium mt-2">{cat.productCount} products &rarr;</div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
