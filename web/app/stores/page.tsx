import Link from "next/link";
import type { Store } from "@/lib/types";

export const dynamic = "force-dynamic";

const INTERNAL_API = process.env.INTERNAL_API_URL || "http://grocery-api:8000/api/v1";

async function getStoresServer(): Promise<Store[]> {
  const res = await fetch(`${INTERNAL_API}/stores`, { cache: "no-store" });
  if (!res.ok) throw new Error(`stores fetch failed: ${res.status}`);
  return res.json();
}

export default async function StoresPage() {
  let stores: Store[] = [];
  let error: string | null = null;
  try {
    stores = await getStoresServer();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unable to load store list";
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-foreground mb-2">Store Locations</h1>
      <p className="text-muted text-sm mb-8">
        {stores.length} locations in the Lakeland, Florida area
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {stores.map((store) => (
          <article
            key={store.id}
            itemScope
            itemType="https://schema.org/GroceryStore"
            className="bg-white border border-border rounded-xl p-6 hover:shadow-lg transition-all"
          >
            <Link href={`/stores/${store.id}`} className="block group">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                  #{store.storeNumber}
                </div>
                <div>
                  <h2
                    itemProp="name"
                    className="font-semibold text-foreground group-hover:text-primary transition-colors"
                  >
                    {store.name}
                  </h2>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        store.isOpen ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <span className="text-xs text-muted">
                      {store.isOpen ? "Open now" : "Closed"}
                    </span>
                  </div>
                </div>
              </div>
            </Link>

            <address
              itemProp="address"
              itemScope
              itemType="https://schema.org/PostalAddress"
              className="not-italic text-sm text-muted space-y-1.5"
            >
              <div>
                <span itemProp="streetAddress">{store.address}</span>
              </div>
              <div>
                <span itemProp="addressLocality">{store.city}</span>,{" "}
                <span itemProp="addressRegion">{store.state}</span>{" "}
                <span itemProp="postalCode">{store.zipCode}</span>
              </div>
              <div>
                <span className="text-muted">Phone: </span>
                <a
                  itemProp="telephone"
                  href={`tel:${store.phone.replace(/[^\d+]/g, "")}`}
                  className="text-primary hover:underline"
                >
                  {store.phone}
                </a>
              </div>
            </address>

            {store.hours && store.hours.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <div className="text-xs font-semibold text-foreground mb-2">Hours</div>
                <dl className="text-xs text-muted space-y-0.5">
                  {store.hours.map((h) => (
                    <div
                      key={h.dayOfWeek}
                      itemProp="openingHoursSpecification"
                      itemScope
                      itemType="https://schema.org/OpeningHoursSpecification"
                      className="flex justify-between"
                    >
                      <dt itemProp="dayOfWeek">{h.dayName}</dt>
                      <dd>
                        <span itemProp="opens">{h.openTime}</span>
                        {" – "}
                        <span itemProp="closes">{h.closeTime}</span>
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
