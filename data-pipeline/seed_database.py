"""
Database Seeder for AIDeliveryGroceryShop.
Bulk inserts generated products and deals into PostgreSQL.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5436"),
        dbname=os.environ.get("POSTGRES_DB", "groceryshop"),
        user=os.environ.get("POSTGRES_USER", "grocery"),
        password=os.environ.get("POSTGRES_PASSWORD", "changeme"),
    )


def seed_products(conn, products: list[dict]):
    """Bulk insert products, linking to existing categories."""
    cur = conn.cursor()

    # Get category slug -> id mapping
    cur.execute('SELECT "Slug", "Id" FROM "Categories"')
    cat_map = {row[0]: row[1] for row in cur.fetchall()}

    # Check existing product count
    cur.execute('SELECT COUNT(*) FROM "Products"')
    existing = cur.fetchone()[0]
    if existing > 100:
        print(f"  Products table already has {existing} rows, skipping")
        return {}

    now = datetime.utcnow()
    sku_to_id = {}
    rows = []

    for p in products:
        cat_id = cat_map.get(p["category_slug"])
        if not cat_id:
            continue

        product_id = str(uuid.uuid4())
        sku_to_id[p["sku"]] = product_id

        rows.append((
            product_id, cat_id, p["name"], p["slug"], p["description"],
            p.get("brand"), p["price"], p["unit"], p.get("weight"),
            None, p["sku"], p["is_available"], p["is_organic"],
            p["is_store_brand"], None, p.get("tags"),
            now, None
        ))

    sql = '''
        INSERT INTO "Products" (
            "Id", "CategoryId", "Name", "Slug", "Description",
            "Brand", "Price", "Unit", "Weight",
            "ImageUrl", "Sku", "IsAvailable", "IsOrganic",
            "IsStoreBrand", "NutritionInfo", "Tags",
            "CreatedAt", "UpdatedAt"
        ) VALUES %s
        ON CONFLICT ("Sku") DO NOTHING
    '''

    execute_values(cur, sql, rows, page_size=500)
    conn.commit()
    print(f"  Inserted {len(rows)} products")
    return sku_to_id


def seed_deals(conn, deals: list[dict], sku_to_id: dict):
    """Bulk insert deals linked to products by SKU."""
    cur = conn.cursor()

    # If sku_to_id is empty, rebuild from DB
    if not sku_to_id:
        cur.execute('SELECT "Sku", "Id" FROM "Products"')
        sku_to_id = {row[0]: str(row[1]) for row in cur.fetchall()}

    # Check existing deal count
    cur.execute('SELECT COUNT(*) FROM "Deals"')
    existing = cur.fetchone()[0]
    if existing > 10:
        print(f"  Deals table already has {existing} rows, skipping")
        return

    now = datetime.utcnow()
    rows = []

    for d in deals:
        product_id = sku_to_id.get(d["product_sku"])
        if not product_id:
            continue

        rows.append((
            str(uuid.uuid4()), product_id, d["deal_type"], d["title"],
            d.get("description"), d.get("discount_percent"), d.get("discount_amount"),
            d.get("buy_quantity"), d.get("get_quantity"),
            d["start_date"], d["end_date"], d["is_active"], now, None
        ))

    sql = '''
        INSERT INTO "Deals" (
            "Id", "ProductId", "DealType", "Title",
            "Description", "DiscountPercent", "DiscountAmount",
            "BuyQuantity", "GetQuantity",
            "StartDate", "EndDate", "IsActive", "CreatedAt", "UpdatedAt"
        ) VALUES %s
    '''

    execute_values(cur, sql, rows, page_size=500)
    conn.commit()
    print(f"  Inserted {len(rows)} deals")


def main():
    output_dir = Path(__file__).parent / "output"
    products_path = output_dir / "products.json"
    deals_path = output_dir / "deals.json"

    if not products_path.exists():
        print("ERROR: Run generate_products.py first")
        return
    if not deals_path.exists():
        print("ERROR: Run generate_deals.py first")
        return

    with open(products_path) as f:
        products = json.load(f)
    with open(deals_path) as f:
        deals = json.load(f)

    print("Connecting to PostgreSQL...")
    conn = get_connection()

    try:
        print("Seeding products...")
        sku_to_id = seed_products(conn, products)

        print("Seeding deals...")
        seed_deals(conn, deals, sku_to_id)

        # Report final counts
        cur = conn.cursor()
        for table in ["Categories", "Products", "Deals", "Stores", "StoreHours"]:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"  {table}: {count} rows")

    finally:
        conn.close()

    print("\nDatabase seeding complete!")


if __name__ == "__main__":
    main()
