"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getStoreById } from "@/lib/api";
import type { Store } from "@/lib/types";

export default function StoreDetailPage() {
  const params = useParams();
  const [store, setStore] = useState<Store | null>(null);

  useEffect(() => {
    if (params.id) {
      getStoreById(params.id as string).then(setStore).catch(console.error);
    }
  }, [params.id]);

  if (!store) {
    return <div className="max-w-4xl mx-auto px-4 py-16"><div className="animate-pulse bg-gray-100 rounded-xl h-96" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <nav className="text-sm text-muted mb-6">
        <Link href="/stores" className="hover:text-primary">Stores</Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{store.name}</span>
      </nav>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Map placeholder */}
        <div className="bg-gray-100 rounded-xl h-80 flex items-center justify-center">
          <div className="text-center text-muted">
            <div className="text-4xl mb-2">🗺️</div>
            <div className="text-sm">Map: {store.latitude}, {store.longitude}</div>
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${store.latitude},${store.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary text-sm hover:underline mt-2 inline-block"
            >
              Open in Google Maps
            </a>
          </div>
        </div>

        {/* Info */}
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-2">{store.name}</h1>
          <div className="flex items-center gap-2 mb-6">
            <span className={`w-2.5 h-2.5 rounded-full ${store.isOpen ? "bg-green-500" : "bg-red-500"}`} />
            <span className="text-sm font-medium">{store.isOpen ? "Open Now" : "Closed"}</span>
            <span className="text-muted text-sm">Store #{store.storeNumber}</span>
          </div>

          <div className="space-y-3 text-sm mb-8">
            <div className="flex gap-3">
              <span className="text-muted w-16 shrink-0">Address</span>
              <span>{store.address}, {store.city}, {store.state} {store.zipCode}</span>
            </div>
            <div className="flex gap-3">
              <span className="text-muted w-16 shrink-0">Phone</span>
              <a href={`tel:${store.phone}`} className="text-primary hover:underline">{store.phone}</a>
            </div>
          </div>

          {/* Hours */}
          <h2 className="font-semibold text-foreground mb-3">Store Hours</h2>
          <div className="bg-surface rounded-lg overflow-hidden border border-border">
            {store.hours.map((h) => (
              <div
                key={h.dayOfWeek}
                className={`flex justify-between px-4 py-2.5 text-sm ${
                  h.dayOfWeek === new Date().getDay()
                    ? "bg-primary/5 font-medium text-primary"
                    : "text-foreground"
                } ${h.dayOfWeek < store.hours.length - 1 ? "border-b border-border" : ""}`}
              >
                <span>{h.dayName}</span>
                <span>{h.openTime} - {h.closeTime}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
