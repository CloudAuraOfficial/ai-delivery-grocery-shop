"""
Qdrant Vector Indexer for AIDeliveryGroceryShop.
Embeds products, stores, and deals into Qdrant collections using Ollama.
"""

import json
import os
import time
from pathlib import Path

import httpx
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
VECTOR_DIM = 768  # nomic-embed-text dimension
BATCH_SIZE = 50


def get_embedding(text: str, client: httpx.Client) -> list[float]:
    """Get embedding from Ollama."""
    resp = client.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def build_product_text(product: dict) -> str:
    """Build a rich text document from product fields for embedding."""
    parts = [
        f"Product: {product['name']}",
        f"Category: {product['category']}",
        f"Subcategory: {product.get('subcategory', '')}",
        f"Brand: {product.get('brand', 'Unknown')}",
        f"Price: ${product['price']:.2f}",
        f"Description: {product['description']}",
    ]
    if product.get("tags"):
        parts.append(f"Tags: {product['tags']}")
    if product.get("is_organic"):
        parts.append("This is an organic product.")
    if product.get("is_store_brand"):
        parts.append("This is a GreenWise store brand product.")
    return "\n".join(parts)


def build_store_text(store: dict) -> str:
    """Build text for store embedding."""
    return (
        f"Store: {store['name']}\n"
        f"Address: {store['address']}, {store['city']}, {store['state']} {store['zipCode']}\n"
        f"Phone: {store['phone']}\n"
        f"Store Number: {store['storeNumber']}"
    )


def build_deal_text(deal: dict, products_by_sku: dict) -> str:
    """Build text for deal embedding."""
    product = products_by_sku.get(deal["product_sku"], {})
    return (
        f"Deal: {deal['title']}\n"
        f"Type: {deal['deal_type']}\n"
        f"Product: {product.get('name', 'Unknown')}\n"
        f"Category: {product.get('category', 'Unknown')}\n"
        f"Price: ${product.get('price', 0):.2f}\n"
        f"Description: {deal.get('description', '')}"
    )


def ensure_collection(qdrant: QdrantClient, name: str):
    """Create collection if it doesn't exist."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if name in collections:
        print(f"  Collection '{name}' exists, recreating...")
        qdrant.delete_collection(name)

    qdrant.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )
    print(f"  Created collection '{name}' (dim={VECTOR_DIM}, cosine)")


def index_products(qdrant: QdrantClient, http_client: httpx.Client, products: list[dict]):
    """Index all products into Qdrant."""
    collection = "grocery_products"
    ensure_collection(qdrant, collection)

    total = len(products)
    indexed = 0
    start = time.time()

    for batch_start in range(0, total, BATCH_SIZE):
        batch = products[batch_start:batch_start + BATCH_SIZE]
        points = []

        for i, p in enumerate(batch):
            text = build_product_text(p)
            try:
                embedding = get_embedding(text, http_client)
            except Exception as e:
                print(f"  WARNING: Failed to embed {p['sku']}: {e}")
                continue

            points.append(PointStruct(
                id=batch_start + i,
                vector=embedding,
                payload={
                    "sku": p["sku"],
                    "name": p["name"],
                    "category": p["category"],
                    "subcategory": p.get("subcategory", ""),
                    "brand": p.get("brand", ""),
                    "price": p["price"],
                    "unit": p["unit"],
                    "is_organic": p.get("is_organic", False),
                    "is_store_brand": p.get("is_store_brand", False),
                    "tags": p.get("tags", ""),
                },
            ))

        if points:
            qdrant.upsert(collection_name=collection, points=points)
            indexed += len(points)

        elapsed = time.time() - start
        rate = indexed / elapsed if elapsed > 0 else 0
        print(f"  Products: {indexed}/{total} ({rate:.1f}/sec)", end="\r")

    print(f"\n  Indexed {indexed} products into '{collection}'")


def index_stores(qdrant: QdrantClient, http_client: httpx.Client):
    """Index 9 stores into Qdrant."""
    collection = "grocery_stores"
    ensure_collection(qdrant, collection)

    stores_path = Path(__file__).parent / "templates" / "stores.json"
    if not stores_path.exists():
        # Build from the seed data template
        stores = [
            {"name": "AI Grocery - Lakeland South", "storeNumber": "1001", "address": "3501 S Florida Ave", "city": "Lakeland", "state": "FL", "zipCode": "33803", "phone": "(863) 555-0101"},
            {"name": "AI Grocery - Lakeland North", "storeNumber": "1002", "address": "4730 N Socrum Loop Rd", "city": "Lakeland", "state": "FL", "zipCode": "33809", "phone": "(863) 555-0102"},
            {"name": "AI Grocery - Winter Haven", "storeNumber": "1003", "address": "200 Cypress Gardens Blvd", "city": "Winter Haven", "state": "FL", "zipCode": "33880", "phone": "(863) 555-0103"},
            {"name": "AI Grocery - Plant City", "storeNumber": "1004", "address": "2602 James L Redman Pkwy", "city": "Plant City", "state": "FL", "zipCode": "33566", "phone": "(813) 555-0104"},
            {"name": "AI Grocery - Bartow", "storeNumber": "1005", "address": "1050 N Broadway Ave", "city": "Bartow", "state": "FL", "zipCode": "33830", "phone": "(863) 555-0105"},
            {"name": "AI Grocery - Auburndale", "storeNumber": "1006", "address": "508 Havendale Blvd", "city": "Auburndale", "state": "FL", "zipCode": "33823", "phone": "(863) 555-0106"},
            {"name": "AI Grocery - Haines City", "storeNumber": "1007", "address": "36000 US Hwy 27", "city": "Haines City", "state": "FL", "zipCode": "33844", "phone": "(863) 555-0107"},
            {"name": "AI Grocery - Mulberry", "storeNumber": "1008", "address": "901 N Church Ave", "city": "Mulberry", "state": "FL", "zipCode": "33860", "phone": "(863) 555-0108"},
            {"name": "AI Grocery - Davenport", "storeNumber": "1009", "address": "2400 Posner Blvd", "city": "Davenport", "state": "FL", "zipCode": "33837", "phone": "(863) 555-0109"},
        ]
    else:
        with open(stores_path) as f:
            stores = json.load(f)

    points = []
    for i, store in enumerate(stores):
        text = build_store_text(store)
        embedding = get_embedding(text, http_client)
        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload=store,
        ))

    qdrant.upsert(collection_name=collection, points=points)
    print(f"  Indexed {len(points)} stores into '{collection}'")


def index_deals(qdrant: QdrantClient, http_client: httpx.Client, deals: list[dict], products: list[dict]):
    """Index active deals into Qdrant."""
    collection = "grocery_deals"
    ensure_collection(qdrant, collection)

    products_by_sku = {p["sku"]: p for p in products}
    points = []

    for i, deal in enumerate(deals):
        text = build_deal_text(deal, products_by_sku)
        try:
            embedding = get_embedding(text, http_client)
        except Exception as e:
            print(f"  WARNING: Failed to embed deal {i}: {e}")
            continue

        points.append(PointStruct(
            id=i,
            vector=embedding,
            payload={
                "deal_type": deal["deal_type"],
                "title": deal["title"],
                "product_sku": deal["product_sku"],
                "product_name": products_by_sku.get(deal["product_sku"], {}).get("name", ""),
                "category": products_by_sku.get(deal["product_sku"], {}).get("category", ""),
                "discount_percent": deal.get("discount_percent"),
            },
        ))

    if points:
        qdrant.upsert(collection_name=collection, points=points)
    print(f"  Indexed {len(points)} deals into '{collection}'")


def main():
    output_dir = Path(__file__).parent / "output"
    products_path = output_dir / "products.json"
    deals_path = output_dir / "deals.json"

    if not products_path.exists():
        print("ERROR: Run generate_products.py first")
        return

    with open(products_path) as f:
        products = json.load(f)

    deals = []
    if deals_path.exists():
        with open(deals_path) as f:
            deals = json.load(f)

    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    qdrant = QdrantClient(url=QDRANT_URL)

    print(f"Using Ollama at {OLLAMA_URL} with model {EMBED_MODEL}...")
    http_client = httpx.Client()

    # Verify Ollama is accessible
    try:
        resp = http_client.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        models = [m["name"] for m in resp.json().get("models", [])]
        if not any(EMBED_MODEL in m for m in models):
            print(f"  WARNING: Model '{EMBED_MODEL}' not found. Available: {models}")
            print(f"  Pull it with: ollama pull {EMBED_MODEL}")
            return
        print(f"  Model '{EMBED_MODEL}' available")
    except Exception as e:
        print(f"  ERROR: Cannot reach Ollama: {e}")
        return

    print("\nIndexing products...")
    index_products(qdrant, http_client, products)

    print("\nIndexing stores...")
    index_stores(qdrant, http_client)

    if deals:
        print("\nIndexing deals...")
        index_deals(qdrant, http_client, deals, products)

    # Report collection sizes
    print("\n=== Index Summary ===")
    for name in ["grocery_products", "grocery_stores", "grocery_deals"]:
        try:
            info = qdrant.get_collection(name)
            print(f"  {name}: {info.points_count} vectors ({info.vectors_count} total)")
        except Exception:
            print(f"  {name}: not found")

    http_client.close()
    print("\nVector indexing complete!")


if __name__ == "__main__":
    main()
