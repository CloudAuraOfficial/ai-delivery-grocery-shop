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


def seed_user_and_orders(conn):
    """Seed a demo customer (Roger) with a few sample orders."""
    cur = conn.cursor()

    # Check if user already exists
    cur.execute('SELECT COUNT(*) FROM "Users" WHERE "Email" = %s', ("roger@cloudaura.cloud",))
    if cur.fetchone()[0] > 0:
        print("  User 'Roger' already exists, skipping")
        return

    # Get first store
    cur.execute('SELECT "Id" FROM "Stores" ORDER BY "StoreNumber" LIMIT 1')
    store_row = cur.fetchone()
    if not store_row:
        print("  No stores found, skipping user/orders")
        return
    store_id = store_row[0]

    # Get a few random products
    cur.execute('SELECT "Id", "Name", "Price" FROM "Products" WHERE "IsAvailable" = true ORDER BY random() LIMIT 8')
    products = cur.fetchall()
    if len(products) < 8:
        print("  Not enough products, skipping orders")
        return

    now = datetime.utcnow()
    user_id = str(uuid.uuid4())

    # Insert user
    cur.execute('''
        INSERT INTO "Users" ("Id", "Email", "DisplayName", "PasswordHash", "PreferredStoreId", "CreatedAt", "UpdatedAt")
        VALUES (%s, %s, %s, %s, %s, %s, NULL)
    ''', (user_id, "roger@cloudaura.cloud", "Roger", "hashed_placeholder", store_id, now))

    # Create 3 orders at different times
    orders = [
        ("ORD-20260415-R001", "Delivered",  15, "3501 S Florida Ave, Lakeland FL 33803", "Leave at front door"),
        ("ORD-20260419-R002", "Delivered",   7, "3501 S Florida Ave, Lakeland FL 33803", None),
        ("ORD-20260422-R003", "Preparing",   1, "3501 S Florida Ave, Lakeland FL 33803", "Ring doorbell"),
    ]

    product_idx = 0
    for order_num, status, days_ago, address, notes in orders:
        order_id = str(uuid.uuid4())
        order_time = datetime(2026, 4, 22 - days_ago, 10, 30, 0)

        # Pick 2-3 products per order
        item_count = 3 if product_idx + 3 <= len(products) else 2
        order_products = products[product_idx:product_idx + item_count]
        product_idx += item_count

        sub_total = sum(float(p[2]) * 2 for p in order_products)  # qty 2 each
        tax = round(sub_total * 0.07, 2)
        delivery_fee = 0 if sub_total >= 35 else 5.99
        total = round(sub_total + tax + delivery_fee, 2)

        cur.execute('''
            INSERT INTO "Orders" (
                "Id", "UserId", "StoreId", "OrderNumber", "Status",
                "SubTotal", "Tax", "DeliveryFee", "Total",
                "DeliveryAddress", "Notes", "EstimatedDelivery", "CreatedAt", "UpdatedAt"
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)
        ''', (
            order_id, user_id, str(store_id), order_num, status,
            sub_total, tax, delivery_fee, total,
            address, notes, order_time + __import__("datetime").timedelta(minutes=45),
            order_time
        ))

        # Insert order items
        for prod_id, prod_name, prod_price in order_products:
            cur.execute('''
                INSERT INTO "OrderItems" (
                    "Id", "OrderId", "ProductId", "Quantity", "UnitPrice", "DealId", "LineTotal", "CreatedAt", "UpdatedAt"
                ) VALUES (%s, %s, %s, %s, %s, NULL, %s, %s, NULL)
            ''', (
                str(uuid.uuid4()), order_id, str(prod_id), 2, float(prod_price),
                float(prod_price) * 2, order_time
            ))

    conn.commit()
    print(f"  Created user 'Roger' with 3 orders")


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

        print("Seeding user and orders...")
        seed_user_and_orders(conn)

        # Report final counts
        cur = conn.cursor()
        for table in ["Categories", "Products", "Deals", "Stores", "StoreHours", "Users", "Orders", "OrderItems"]:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"  {table}: {count} rows")

    finally:
        conn.close()

    print("\nDatabase seeding complete!")


if __name__ == "__main__":
    main()
