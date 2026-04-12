"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getStores } from "@/lib/api";
import type { Store } from "@/lib/types";

export default function StoresPage() {
  const [stores, setStores] = useState<Store[]>([]);

  useEffect(() => {
    getStores().then(setStores).catch(console.error);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-2">Store Locations</h1>
      <p className="text-muted text-sm mb-8">9 locations in the Lakeland, Florida area</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stores.map((store) => (
          <Link
            key={store.id}
            href={`/stores/${store.id}`}
            className="bg-white border border-border rounded-xl p-6 hover:shadow-lg transition-all group"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                #{store.storeNumber}
              </div>
              <div>
                <h2 className="font-semibold text-foreground group-hover:text-primary transition-colors">
                  {store.name}
                </h2>
                <div className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${store.isOpen ? "bg-green-500" : "bg-red-500"}`} />
                  <span className="text-xs text-muted">{store.isOpen ? "Open" : "Closed"}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2 text-sm text-muted">
              <div className="flex items-start gap-2">
                <span className="shrink-0">📍</span>
                <span>{store.address}, {store.city}, {store.state} {store.zipCode}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>📞</span>
                <span>{store.phone}</span>
              </div>
            </div>

            {store.hours.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="text-xs text-muted">
                  Today: {store.hours[new Date().getDay()]?.openTime} - {store.hours[new Date().getDay()]?.closeTime}
                </div>
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
