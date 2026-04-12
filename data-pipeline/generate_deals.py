"""
Deal Assignment for AIDeliveryGroceryShop.
Assigns BOGO, Weekly, and Daily deals to generated products.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def main():
    random.seed(42)

    output_dir = Path(__file__).parent / "output"
    products_path = output_dir / "products.json"

    if not products_path.exists():
        print("ERROR: Run generate_products.py first")
        return

    with open(products_path) as f:
        products = json.load(f)

    now = datetime.utcnow()
    deals = []

    # Shuffle for random selection
    shuffled = list(range(len(products)))
    random.shuffle(shuffled)

    idx = 0

    # BOGO deals: ~200 products across categories
    bogo_count = 200
    for i in range(bogo_count):
        p = products[shuffled[idx]]
        deals.append({
            "product_sku": p["sku"],
            "deal_type": "BOGO",
            "title": "Buy One Get One Free",
            "description": f"Buy one {p['name']} and get one free!",
            "discount_percent": None,
            "discount_amount": None,
            "buy_quantity": 1,
            "get_quantity": 1,
            "start_date": (now - timedelta(days=2)).isoformat(),
            "end_date": (now + timedelta(days=12)).isoformat(),
            "is_active": True,
        })
        idx += 1

    # Weekly deals: ~150 products, 20-40% off
    weekly_count = 150
    for i in range(weekly_count):
        p = products[shuffled[idx]]
        pct = random.choice([20, 25, 30, 35, 40])
        deals.append({
            "product_sku": p["sku"],
            "deal_type": "WeeklyDeal",
            "title": f"{pct}% Off This Week",
            "description": f"Save {pct}% on {p['name']} this week only!",
            "discount_percent": pct,
            "discount_amount": None,
            "buy_quantity": None,
            "get_quantity": None,
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": (now + timedelta(days=6)).isoformat(),
            "is_active": True,
        })
        idx += 1

    # Daily deals: 15 products, 25-50% off
    daily_count = 15
    for i in range(daily_count):
        p = products[shuffled[idx]]
        pct = random.choice([25, 30, 35, 40, 45, 50])
        deals.append({
            "product_sku": p["sku"],
            "deal_type": "DailyDeal",
            "title": f"Today Only: {pct}% Off",
            "description": f"Flash deal! Save {pct}% on {p['name']} today only.",
            "discount_percent": pct,
            "discount_amount": None,
            "buy_quantity": None,
            "get_quantity": None,
            "start_date": now.replace(hour=0, minute=0, second=0).isoformat(),
            "end_date": (now.replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat(),
            "is_active": True,
        })
        idx += 1

    deals_path = output_dir / "deals.json"
    with open(deals_path, "w") as f:
        json.dump(deals, f, indent=2)

    print(f"Generated {len(deals)} deals:")
    print(f"  BOGO: {bogo_count}")
    print(f"  Weekly: {weekly_count}")
    print(f"  Daily: {daily_count}")
    print(f"Written to {deals_path}")


if __name__ == "__main__":
    main()
