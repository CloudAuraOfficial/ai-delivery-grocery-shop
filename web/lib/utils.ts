export function formatPrice(price: number): string {
  return `$${price.toFixed(2)}`;
}

export function formatDealBadge(dealType: string): string {
  switch (dealType) {
    case "BOGO": return "BOGO";
    case "WeeklyDeal": return "Weekly Deal";
    case "DailyDeal": return "Daily Deal";
    default: return dealType;
  }
}

export function dealBadgeColor(dealType: string): string {
  switch (dealType) {
    case "BOGO": return "bg-red-600";
    case "WeeklyDeal": return "bg-amber-600";
    case "DailyDeal": return "bg-emerald-600";
    default: return "bg-gray-600";
  }
}

export function categoryIcon(slug: string): string {
  const icons: Record<string, string> = {
    baby: "🍼",
    beverages: "🥤",
    household: "🧹",
    fresh: "🥬",
    "meat-seafood": "🥩",
    deli: "🧀",
  };
  return icons[slug] || "🛒";
}

export function timeUntil(dateStr: string): string {
  const diff = new Date(dateStr).getTime() - Date.now();
  if (diff <= 0) return "Expired";
  const hours = Math.floor(diff / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  return `${hours}h ${minutes}m`;
}
