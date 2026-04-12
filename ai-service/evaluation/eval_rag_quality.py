"""RAG Retrieval Quality Evaluation.
Measures retrieval precision and recall against a labeled test set.
"""

import asyncio
import json
from pathlib import Path

# Test cases: query -> expected product SKUs that should appear in top-5
TEST_CASES = [
    {"query": "organic baby formula", "expected_skus": ["BAB-"], "category": "Baby"},
    {"query": "BOGO diapers", "expected_skus": ["BAB-"], "category": "Baby"},
    {"query": "sparkling water LaCroix", "expected_skus": ["BEV-"], "category": "Beverages"},
    {"query": "ground beef 90% lean", "expected_skus": ["MEA-"], "category": "Meat & Seafood"},
    {"query": "Boar's Head turkey breast", "expected_skus": ["DEL-"], "category": "Deli"},
    {"query": "fresh organic spinach", "expected_skus": ["FRE-"], "category": "Fresh"},
    {"query": "Tide laundry detergent", "expected_skus": ["HOU-"], "category": "Household"},
    {"query": "coffee K-Cups", "expected_skus": ["BEV-"], "category": "Beverages"},
    {"query": "chicken breast boneless", "expected_skus": ["MEA-"], "category": "Meat & Seafood"},
    {"query": "Clorox disinfecting wipes", "expected_skus": ["HOU-"], "category": "Household"},
    {"query": "mozzarella cheese shredded", "expected_skus": ["DEL-"], "category": "Deli"},
    {"query": "avocados fresh", "expected_skus": ["FRE-"], "category": "Fresh"},
    {"query": "Pampers size 3", "expected_skus": ["BAB-"], "category": "Baby"},
    {"query": "energy drinks Monster", "expected_skus": ["BEV-"], "category": "Beverages"},
    {"query": "paper towels Bounty", "expected_skus": ["HOU-"], "category": "Household"},
]


async def evaluate():
    """Run retrieval quality evaluation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from app.services.retriever import retrieve_products

    results = []
    total_precision = 0
    total_recall = 0
    total_category_match = 0

    print(f"Running {len(TEST_CASES)} retrieval quality tests...")
    print("-" * 70)

    for tc in TEST_CASES:
        try:
            products = await retrieve_products(tc["query"], top_k=5)
        except Exception as e:
            print(f"  FAIL: {tc['query'][:40]} — {e}")
            results.append({"query": tc["query"], "status": "error", "error": str(e)})
            continue

        # Check if any retrieved SKU matches expected prefix
        retrieved_skus = [p["sku"] for p in products]
        retrieved_categories = [p["category"] for p in products]

        # Precision: what fraction of retrieved items are relevant (correct category)
        relevant_retrieved = sum(1 for cat in retrieved_categories if cat == tc["category"])
        precision = relevant_retrieved / len(products) if products else 0

        # Category match: did we get at least one result from the right category?
        category_hit = tc["category"] in retrieved_categories

        # SKU prefix match
        sku_hit = any(
            any(sku.startswith(prefix) for prefix in tc["expected_skus"])
            for sku in retrieved_skus
        )

        total_precision += precision
        total_category_match += int(category_hit)

        status = "PASS" if category_hit and sku_hit else "FAIL"
        print(f"  {status}: {tc['query'][:40]:<40} precision={precision:.2f} cat={category_hit} sku={sku_hit}")

        results.append({
            "query": tc["query"],
            "status": status,
            "precision": precision,
            "category_hit": category_hit,
            "sku_hit": sku_hit,
            "retrieved_count": len(products),
        })

    # Aggregate metrics
    n = len(TEST_CASES)
    avg_precision = total_precision / n
    category_accuracy = total_category_match / n

    print("-" * 70)
    print(f"Avg Precision:     {avg_precision:.3f} (threshold: >= 0.7)")
    print(f"Category Accuracy: {category_accuracy:.3f} (threshold: >= 0.8)")
    print(f"Pass Rate:         {sum(1 for r in results if r.get('status') == 'PASS')}/{n}")

    # Assert thresholds
    assert avg_precision >= 0.7, f"Precision {avg_precision:.3f} below threshold 0.7"
    assert category_accuracy >= 0.8, f"Category accuracy {category_accuracy:.3f} below threshold 0.8"
    print("\nAll quality thresholds passed!")


if __name__ == "__main__":
    asyncio.run(evaluate())
