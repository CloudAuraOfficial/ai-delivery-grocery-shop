"""Staff service — direct PostgreSQL queries for structured store associate questions.
Skips LLM when a query can be answered from the database alone."""

import re
from datetime import datetime, timezone

import structlog
import psycopg2
import psycopg2.extras

from app.config import settings

logger = structlog.get_logger()


def get_connection():
    return psycopg2.connect(settings.postgres_dsn)


def classify_staff_query(query: str) -> dict:
    """Classify a staff query into a structured DB query or pass to RAG.

    Returns:
        {"type": "db_query", "action": str, "params": dict}  — answerable from DB
        {"type": "rag"}  — needs LLM reasoning
    """
    q = query.lower().strip()

    # Count queries: "how many X", "count of X", "total X"
    count_match = re.search(
        r"(?:how many|count|total|number of)\s+(.+?)(?:\s+do we|\s+are there|\s+in|\?|$)", q
    )
    if count_match:
        subject = count_match.group(1).strip()
        return _parse_count_query(subject, q)

    # Expiring deals: "deals expiring today/this week/tomorrow"
    if any(kw in q for kw in ["expir", "ending soon", "ends today", "about to end"]):
        return {"type": "db_query", "action": "expiring_deals", "params": {}}

    # Category listing: "list categories", "show categories", "what categories"
    if any(kw in q for kw in ["list categor", "show categor", "what categor", "all categor"]):
        return {"type": "db_query", "action": "list_categories", "params": {}}

    # Top/cheapest/most expensive: "cheapest X", "most expensive X", "top selling"
    if "cheapest" in q or "lowest price" in q:
        category = _detect_category(q)
        return {"type": "db_query", "action": "cheapest_products", "params": {"category": category, "limit": 5}}

    if "most expensive" in q or "highest price" in q or "priciest" in q:
        category = _detect_category(q)
        return {"type": "db_query", "action": "most_expensive_products", "params": {"category": category, "limit": 5}}

    # Store brand: "store brand products", "greenwise products" (check BEFORE generic brand)
    if "store brand" in q or "greenwise" in q or "private label" in q:
        category = _detect_category(q)
        return {"type": "db_query", "action": "store_brand_products", "params": {"category": category, "limit": 10}}

    # Brand lookup: "what brands", "which brands", "brands we carry"
    if "brand" in q and any(kw in q for kw in ["what", "which", "list", "show", "carry", "do we"]):
        category = _detect_category(q)
        return {"type": "db_query", "action": "list_brands", "params": {"category": category}}

    # Deal summary: "deal summary", "active deals", "deal breakdown"
    if any(kw in q for kw in ["deal summary", "deal breakdown", "active deals", "deal stats"]):
        return {"type": "db_query", "action": "deal_summary", "params": {}}

    # Price range: "products under $5", "products between $10 and $20"
    price_under = re.search(r"(?:under|below|less than|cheaper than)\s*\$?(\d+(?:\.\d+)?)", q)
    if price_under:
        category = _detect_category(q)
        return {"type": "db_query", "action": "products_under_price",
                "params": {"max_price": float(price_under.group(1)), "category": category, "limit": 10}}

    # Subcategory listing: "subcategories in X"
    if "subcategor" in q:
        category = _detect_category(q)
        return {"type": "db_query", "action": "list_subcategories", "params": {"category": category}}

    # Fall through to RAG
    return {"type": "rag"}


def execute_staff_query(action: str, params: dict) -> dict:
    """Execute a structured staff query against PostgreSQL.

    Returns:
        {"answer": str, "data": list[dict]}
    """
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        result = _QUERY_HANDLERS[action](cur, params)

        conn.close()
        return result

    except Exception as e:
        logger.error("staff_query_failed", action=action, error=str(e))
        return {"answer": f"Sorry, I couldn't fetch that data: {str(e)}", "data": []}


# ─── Query Handlers ──────────────────────────────────────────

def _count_products(cur, params: dict) -> dict:
    category = params.get("category")
    brand = params.get("brand")
    organic_only = params.get("organic_only", False)

    sql = 'SELECT COUNT(*) as cnt FROM "Products" p JOIN "Categories" c ON p."CategoryId" = c."Id" WHERE p."IsAvailable" = true'
    bind = []

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)
    if brand:
        sql += ' AND LOWER(p."Brand") LIKE %s'
        bind.append(f"%{brand.lower()}%")
    if organic_only:
        sql += ' AND p."IsOrganic" = true'

    cur.execute(sql, bind)
    count = cur.fetchone()["cnt"]

    desc_parts = []
    if organic_only:
        desc_parts.append("organic")
    if category:
        desc_parts.append(f"in {category}")
    if brand:
        desc_parts.append(f"from {brand}")
    desc = " ".join(desc_parts) if desc_parts else "total"

    return {"answer": f"We carry **{count}** {desc} products.", "data": [{"count": count}]}


def _count_deals(cur, params: dict) -> dict:
    deal_type = params.get("deal_type")
    now = datetime.now(timezone.utc)

    sql = 'SELECT COUNT(*) as cnt FROM "Deals" WHERE "IsActive" = true AND "EndDate" > %s'
    bind = [now]

    if deal_type:
        sql += ' AND "DealType" = %s'
        bind.append(deal_type)

    cur.execute(sql, bind)
    count = cur.fetchone()["cnt"]
    label = deal_type if deal_type else "active"

    return {"answer": f"We have **{count}** {label} deals right now.", "data": [{"count": count}]}


def _expiring_deals(cur, params: dict) -> dict:
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=23, minute=59, second=59)

    cur.execute('''
        SELECT d."Title", d."DealType", d."EndDate", p."Name" as product_name, p."Sku"
        FROM "Deals" d
        JOIN "Products" p ON d."ProductId" = p."Id"
        WHERE d."IsActive" = true AND d."EndDate" BETWEEN %s AND %s
        ORDER BY d."EndDate"
        LIMIT 20
    ''', (now, tomorrow))

    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        r["EndDate"] = r["EndDate"].isoformat() if r.get("EndDate") else None

    if not rows:
        return {"answer": "No deals expiring today.", "data": []}

    lines = [f"**{len(rows)} deals expiring today:**"]
    for r in rows:
        lines.append(f"- {r['product_name']} ({r['sku']}) — {r['Title']} ({r['DealType']})")

    return {"answer": "\n".join(lines), "data": rows}


def _list_categories(cur, params: dict) -> dict:
    cur.execute('''
        SELECT c."Name", c."Slug", COUNT(p."Id") as product_count
        FROM "Categories" c
        LEFT JOIN "Products" p ON c."Id" = p."CategoryId" AND p."IsAvailable" = true
        WHERE c."IsActive" = true
        GROUP BY c."Id", c."Name", c."Slug"
        ORDER BY c."DisplayOrder"
    ''')
    rows = [dict(r) for r in cur.fetchall()]
    lines = ["**Categories:**"]
    for r in rows:
        lines.append(f"- {r['Name']} — {r['product_count']} products")

    return {"answer": "\n".join(lines), "data": rows}


def _cheapest_products(cur, params: dict) -> dict:
    return _price_sorted_products(cur, params, "ASC", "cheapest")


def _most_expensive_products(cur, params: dict) -> dict:
    return _price_sorted_products(cur, params, "DESC", "most expensive")


def _price_sorted_products(cur, params: dict, order: str, label: str) -> dict:
    category = params.get("category")
    limit = params.get("limit", 5)

    sql = f'''
        SELECT p."Name", p."Sku", p."Price", p."Unit", c."Name" as category, p."Brand"
        FROM "Products" p
        JOIN "Categories" c ON p."CategoryId" = c."Id"
        WHERE p."IsAvailable" = true
    '''
    bind = []

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)

    sql += f' ORDER BY p."Price" {order} LIMIT %s'
    bind.append(limit)

    cur.execute(sql, bind)
    rows = [dict(r) for r in cur.fetchall()]

    cat_label = f" in {category}" if category else ""
    lines = [f"**{label.title()} products{cat_label}:**"]
    for r in rows:
        brand = f" ({r['Brand']})" if r.get("Brand") else ""
        lines.append(f"- {r['Name']}{brand} — ${r['Price']:.2f}/{r['Unit']} [{r['Sku']}]")

    return {"answer": "\n".join(lines), "data": rows}


def _list_brands(cur, params: dict) -> dict:
    category = params.get("category")

    sql = '''
        SELECT p."Brand", COUNT(*) as product_count
        FROM "Products" p
        JOIN "Categories" c ON p."CategoryId" = c."Id"
        WHERE p."IsAvailable" = true AND p."Brand" IS NOT NULL
    '''
    bind = []

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)

    sql += ' GROUP BY p."Brand" ORDER BY product_count DESC'

    cur.execute(sql, bind)
    rows = [dict(r) for r in cur.fetchall()]

    cat_label = f" in {category}" if category else ""
    lines = [f"**{len(rows)} brands{cat_label}:**"]
    for r in rows[:15]:
        lines.append(f"- {r['Brand']} — {r['product_count']} products")
    if len(rows) > 15:
        lines.append(f"  ...and {len(rows) - 15} more")

    return {"answer": "\n".join(lines), "data": rows}


def _store_brand_products(cur, params: dict) -> dict:
    category = params.get("category")
    limit = params.get("limit", 10)

    sql = '''
        SELECT p."Name", p."Sku", p."Price", p."Unit", p."Brand", c."Name" as category
        FROM "Products" p
        JOIN "Categories" c ON p."CategoryId" = c."Id"
        WHERE p."IsAvailable" = true AND p."IsStoreBrand" = true
    '''
    bind = []

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)

    sql += ' ORDER BY p."Name" LIMIT %s'
    bind.append(limit)

    cur.execute(sql, bind)
    rows = [dict(r) for r in cur.fetchall()]

    cur.execute('SELECT COUNT(*) as cnt FROM "Products" WHERE "IsAvailable" = true AND "IsStoreBrand" = true')
    total = cur.fetchone()["cnt"]

    cat_label = f" in {category}" if category else ""
    lines = [f"**Store brand products{cat_label} ({total} total, showing {len(rows)}):**"]
    for r in rows:
        lines.append(f"- {r['Name']} — ${r['Price']:.2f}/{r['Unit']} [{r['Sku']}]")

    return {"answer": "\n".join(lines), "data": rows}


def _deal_summary(cur, params: dict) -> dict:
    now = datetime.now(timezone.utc)

    cur.execute('''
        SELECT "DealType", COUNT(*) as cnt,
               ROUND(AVG("DiscountPercent")::numeric, 1) as avg_discount
        FROM "Deals"
        WHERE "IsActive" = true AND "EndDate" > %s
        GROUP BY "DealType"
        ORDER BY cnt DESC
    ''', (now,))
    rows = [dict(r) for r in cur.fetchall()]

    total = sum(r["cnt"] for r in rows)
    lines = [f"**Active deals: {total} total**"]
    for r in rows:
        avg = f", avg {r['avg_discount']}% off" if r.get("avg_discount") else ""
        lines.append(f"- {r['DealType']}: {r['cnt']} deals{avg}")

    return {"answer": "\n".join(lines), "data": rows}


def _products_under_price(cur, params: dict) -> dict:
    max_price = params["max_price"]
    category = params.get("category")
    limit = params.get("limit", 10)

    sql = '''
        SELECT p."Name", p."Sku", p."Price", p."Unit", p."Brand", c."Name" as category
        FROM "Products" p
        JOIN "Categories" c ON p."CategoryId" = c."Id"
        WHERE p."IsAvailable" = true AND p."Price" < %s
    '''
    bind = [max_price]

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)

    sql += ' ORDER BY p."Price" ASC LIMIT %s'
    bind.append(limit)

    cur.execute(sql, bind)
    rows = [dict(r) for r in cur.fetchall()]

    # Get total count
    count_sql = 'SELECT COUNT(*) as cnt FROM "Products" p JOIN "Categories" c ON p."CategoryId" = c."Id" WHERE p."IsAvailable" = true AND p."Price" < %s'
    count_bind = [max_price]
    if category:
        count_sql += ' AND c."Name" = %s'
        count_bind.append(category)
    cur.execute(count_sql, count_bind)
    total = cur.fetchone()["cnt"]

    cat_label = f" in {category}" if category else ""
    lines = [f"**{total} products under ${max_price:.2f}{cat_label} (showing {len(rows)}):**"]
    for r in rows:
        brand = f" ({r['Brand']})" if r.get("Brand") else ""
        lines.append(f"- {r['Name']}{brand} — ${r['Price']:.2f}/{r['Unit']} [{r['Sku']}]")

    return {"answer": "\n".join(lines), "data": rows}


def _list_subcategories(cur, params: dict) -> dict:
    category = params.get("category")

    sql = '''
        SELECT p."Tags", COUNT(*) as cnt
        FROM "Products" p
        JOIN "Categories" c ON p."CategoryId" = c."Id"
        WHERE p."IsAvailable" = true AND p."Tags" IS NOT NULL
    '''
    bind = []

    if category:
        sql += ' AND c."Name" = %s'
        bind.append(category)

    sql += ' GROUP BY p."Tags" ORDER BY cnt DESC LIMIT 15'

    cur.execute(sql, bind)
    rows = [dict(r) for r in cur.fetchall()]

    cat_label = f" in {category}" if category else ""
    lines = [f"**Top product tags{cat_label}:**"]
    for r in rows:
        lines.append(f"- {r['Tags']} — {r['cnt']} products")

    return {"answer": "\n".join(lines), "data": rows}


# ─── Handler Registry ────────────────────────────────────────

_QUERY_HANDLERS = {
    "count_products": _count_products,
    "count_deals": _count_deals,
    "expiring_deals": _expiring_deals,
    "list_categories": _list_categories,
    "cheapest_products": _cheapest_products,
    "most_expensive_products": _most_expensive_products,
    "list_brands": _list_brands,
    "store_brand_products": _store_brand_products,
    "deal_summary": _deal_summary,
    "products_under_price": _products_under_price,
    "list_subcategories": _list_subcategories,
}


# ─── Helpers ─────────────────────────────────────────────────

def _detect_category(query: str) -> str | None:
    q = query.lower()
    categories = {
        "baby": "Baby", "diaper": "Baby", "formula": "Baby",
        "beverage": "Beverages", "drink": "Beverages", "water": "Beverages", "coffee": "Beverages",
        "household": "Household", "cleaning": "Household", "laundry": "Household",
        "fresh": "Fresh", "fruit": "Fresh", "vegetable": "Fresh", "produce": "Fresh",
        "meat": "Meat & Seafood", "seafood": "Meat & Seafood", "chicken": "Meat & Seafood",
        "fish": "Meat & Seafood",
        "deli": "Deli", "cheese": "Deli", "sandwich": "Deli",
    }
    for keyword, category in categories.items():
        if keyword in q:
            return category
    return None


def _parse_count_query(subject: str, full_query: str) -> dict:
    s = subject.lower()

    # Deal counts
    if "deal" in s or "bogo" in s or "sale" in s or "discount" in s:
        deal_type = None
        if "bogo" in s or "buy one" in s:
            deal_type = "BOGO"
        elif "weekly" in s:
            deal_type = "WeeklyDeal"
        elif "daily" in s:
            deal_type = "DailyDeal"
        return {"type": "db_query", "action": "count_deals", "params": {"deal_type": deal_type}}

    # Product counts
    category = _detect_category(full_query)
    brand = None
    organic = "organic" in s

    # Try to extract brand: "how many Pampers products"
    known_brands = ["pampers", "huggies", "greenwise", "boar's head", "cal-organic",
                    "crystal clear", "nature's best", "sabra", "smithfield"]
    for b in known_brands:
        if b in s:
            brand = b
            break

    return {"type": "db_query", "action": "count_products",
            "params": {"category": category, "brand": brand, "organic_only": organic}}
