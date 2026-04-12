"""
Prompt Optimization — Systematic A/B Testing
Evaluates different system prompt variants across a standardized test set.
Measures answer relevance, product citation accuracy, and deal mention rate.
"""

import asyncio
import json
import time
from pathlib import Path

# Prompt variants to A/B test
PROMPT_VARIANTS = {
    "A_baseline": """You are a helpful AI shopping assistant for AI Delivery Grocery Shop.
Answer questions about products, deals, and stores. Be concise and helpful.""",

    "B_structured": """You are a helpful AI shopping assistant for AI Delivery Grocery Shop, a grocery delivery service with 9 stores in the Lakeland, Florida area.

Your capabilities:
- Search and recommend products from our catalog of 3,000+ items
- Inform customers about current deals (BOGO, Weekly Deals, Daily Deals)
- Provide store locations, hours, and contact information

Rules:
1. Only recommend products from the provided context.
2. Always mention deals when they apply.
3. Include prices in recommendations.
4. Format product names clearly.
5. Be friendly and concise.""",

    "C_persona": """You are Sam, a friendly and knowledgeable grocery store associate at AI Delivery Grocery Shop in Lakeland, Florida. You've worked here for years and know every aisle.

When helping customers:
- Recommend specific products with prices from the context provided
- Highlight any active deals (BOGO, weekly, daily)
- Suggest complementary items when appropriate
- Keep responses warm but efficient — customers are busy
- If you don't have info, say so honestly rather than guessing""",
}

TEST_QUERIES = [
    {"query": "What baby products are on BOGO?", "expected_keywords": ["bogo", "baby", "$"]},
    {"query": "Find me organic vegetables", "expected_keywords": ["organic", "vegetable", "$"]},
    {"query": "I need coffee for the week", "expected_keywords": ["coffee", "$"]},
    {"query": "What store is closest to Winter Haven?", "expected_keywords": ["winter haven", "store"]},
    {"query": "Recommend ingredients for tacos", "expected_keywords": ["$"]},
]


def score_response(response: str, expected_keywords: list[str]) -> dict:
    """Score a response based on keyword presence and quality metrics."""
    response_lower = response.lower()

    keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
    keyword_score = keyword_hits / len(expected_keywords) if expected_keywords else 1.0

    has_price = "$" in response
    has_deal = any(w in response_lower for w in ["bogo", "deal", "off", "save", "% off"])
    is_concise = len(response) < 1000
    has_product_names = response.count("$") >= 1  # At least one price = at least one product

    return {
        "keyword_score": keyword_score,
        "has_price": has_price,
        "has_deal": has_deal,
        "is_concise": is_concise,
        "has_products": has_product_names,
        "response_length": len(response),
        "composite_score": (
            keyword_score * 0.4 +
            (1 if has_price else 0) * 0.2 +
            (1 if has_deal else 0) * 0.15 +
            (1 if is_concise else 0) * 0.1 +
            (1 if has_product_names else 0) * 0.15
        ),
    }


async def run_ab_test():
    """Run A/B test across all prompt variants."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "ai-service"))

    from app.services import retriever, generator

    results = {}

    for variant_name, system_prompt in PROMPT_VARIANTS.items():
        print(f"\n{'='*60}")
        print(f"Testing variant: {variant_name}")
        print(f"{'='*60}")

        variant_scores = []

        for tc in TEST_QUERIES:
            products = await retriever.retrieve_products(tc["query"], top_k=5)
            deals = await retriever.retrieve_deals(tc["query"], top_k=3)
            context = generator.build_context(products, deals, [])

            # Override system prompt for this variant
            messages = [{"role": "system", "content": system_prompt}]
            augmented = f"Based on the following:\n\n{context}\n\nCustomer: {tc['query']}"
            messages.append({"role": "user", "content": augmented})

            start = time.time()
            response, latency, model = await generator.generate(tc["query"], context)
            elapsed = time.time() - start

            score = score_response(response, tc["expected_keywords"])
            variant_scores.append(score)

            print(f"  Q: {tc['query'][:40]:<40} score={score['composite_score']:.2f} len={score['response_length']} latency={latency:.0f}ms")

        # Aggregate
        avg_composite = sum(s["composite_score"] for s in variant_scores) / len(variant_scores)
        avg_keyword = sum(s["keyword_score"] for s in variant_scores) / len(variant_scores)
        price_rate = sum(1 for s in variant_scores if s["has_price"]) / len(variant_scores)
        deal_rate = sum(1 for s in variant_scores if s["has_deal"]) / len(variant_scores)

        results[variant_name] = {
            "avg_composite": avg_composite,
            "avg_keyword": avg_keyword,
            "price_mention_rate": price_rate,
            "deal_mention_rate": deal_rate,
        }

    # Summary
    print(f"\n{'='*60}")
    print("A/B TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"{'Variant':<20} {'Composite':>10} {'Keywords':>10} {'Prices':>10} {'Deals':>10}")
    print("-" * 60)

    best_variant = None
    best_score = 0

    for name, metrics in results.items():
        print(f"{name:<20} {metrics['avg_composite']:>10.3f} {metrics['avg_keyword']:>10.3f} {metrics['price_mention_rate']:>10.1%} {metrics['deal_mention_rate']:>10.1%}")
        if metrics["avg_composite"] > best_score:
            best_score = metrics["avg_composite"]
            best_variant = name

    print(f"\nWinner: {best_variant} (composite score: {best_score:.3f})")


if __name__ == "__main__":
    asyncio.run(run_ab_test())
