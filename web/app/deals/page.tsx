"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getBogoDeals, getWeeklyDeals, getDailyDeals } from "@/lib/api";
import { formatPrice, timeUntil } from "@/lib/utils";
import type { Deal } from "@/lib/types";

type TabKey = "bogo" | "weekly" | "daily";

const tabs: { key: TabKey; label: string; color: string }[] = [
  { key: "bogo", label: "BOGO", color: "bg-red-600" },
  { key: "weekly", label: "Weekly Deals", color: "bg-amber-600" },
  { key: "daily", label: "Daily Deals", color: "bg-emerald-600" },
];

export default function DealsPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("bogo");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const fetcher = activeTab === "bogo" ? getBogoDeals : activeTab === "weekly" ? getWeeklyDeals : getDailyDeals;
    fetcher()
      .then(setDeals)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeTab]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-2">Deals & Savings</h1>
      <p className="text-muted text-sm mb-6">Save big on 365+ products across all categories</p>

      {/* Tabs */}
      <div className="flex gap-2 mb-8 border-b border-border pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-5 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.key
                ? `${tab.color} text-white`
                : "text-muted hover:text-foreground hover:bg-surface"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-gray-100 rounded-xl h-40 animate-pulse" />
          ))}
        </div>
      ) : deals.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {deals.map((deal) => (
            <div key={deal.id} className="bg-white border border-border rounded-xl p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <span className={`${tabs.find(t => t.key === activeTab)?.color} text-white text-xs font-bold px-2.5 py-1 rounded-md`}>
                  {deal.dealType === "BOGO" ? "BOGO" : deal.dealType === "WeeklyDeal" ? "Weekly" : "Daily"}
                </span>
                <span className="text-xs text-muted">Ends {timeUntil(deal.endDate)}</span>
              </div>
              <h3 className="font-semibold text-foreground text-sm mb-1">{deal.productName}</h3>
              <div className="text-xs text-muted mb-3">{deal.categoryName}</div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-lg text-foreground">{formatPrice(deal.productPrice)}</span>
                <span className="text-sm font-medium text-red-600">{deal.title}</span>
              </div>
              {deal.discountPercent && (
                <div className="mt-2 text-sm text-green-700 font-medium">Save {deal.discountPercent}%</div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-muted">No deals available in this category.</div>
      )}
    </div>
  );
}
