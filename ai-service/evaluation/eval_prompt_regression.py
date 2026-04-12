"""Prompt Regression Tests.
Golden question/answer pairs to ensure chatbot quality doesn't degrade.
"""

import asyncio
from pathlib import Path

# Golden test cases: question + expected keywords in response
GOLDEN_TESTS = [
    {
        "question": "What baby products are on BOGO?",
        "must_contain": ["bogo", "buy one", "baby"],
        "must_not_contain": ["store location", "hours"],
    },
    {
        "question": "Where is the nearest store?",
        "must_contain": ["store", "lakeland"],
        "must_not_contain": [],
    },
    {
        "question": "What are today's daily deals?",
        "must_contain": ["deal", "today", "%"],
        "must_not_contain": [],
    },
    {
        "question": "Do you have organic milk?",
        "must_contain": ["organic", "$"],
        "must_not_contain": [],
    },
    {
        "question": "How much is ground beef?",
        "must_contain": ["beef", "$"],
        "must_not_contain": ["store", "location"],
    },
    {
        "question": "What's the weather like today?",
        "must_contain": ["grocer"],  # Should redirect to grocery topics
        "must_not_contain": ["temperature", "forecast"],
    },
]


async def evaluate():
    """Run prompt regression tests."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from app.services import retriever, generator

    print(f"Running {len(GOLDEN_TESTS)} prompt regression tests...")
    print("-" * 70)

    passed = 0
    failed = 0

    for tc in GOLDEN_TESTS:
        try:
            intent = retriever.classify_intent(tc["question"])
            products = await retriever.retrieve_products(tc["question"], top_k=5)
            deals = await retriever.retrieve_deals(tc["question"], top_k=3)
            stores = await retriever.retrieve_stores(tc["question"], top_k=3) if intent == "store_info" else []

            context = generator.build_context(products, deals, stores)
            response, latency, model = await generator.generate(tc["question"], context)

            response_lower = response.lower()

            # Check must_contain
            missing = [kw for kw in tc["must_contain"] if kw.lower() not in response_lower]
            # Check must_not_contain
            present = [kw for kw in tc["must_not_contain"] if kw.lower() in response_lower]

            if not missing and not present:
                print(f"  PASS: {tc['question'][:50]:<50} ({latency:.0f}ms)")
                passed += 1
            else:
                reasons = []
                if missing:
                    reasons.append(f"missing: {missing}")
                if present:
                    reasons.append(f"unwanted: {present}")
                print(f"  FAIL: {tc['question'][:50]:<50} {', '.join(reasons)}")
                failed += 1

        except Exception as e:
            print(f"  ERROR: {tc['question'][:50]:<50} {e}")
            failed += 1

    print("-" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(GOLDEN_TESTS)}")

    assert failed == 0, f"{failed} prompt regression tests failed"
    print("\nAll prompt regression tests passed!")


if __name__ == "__main__":
    asyncio.run(evaluate())
