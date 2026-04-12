"""Latency Evaluation.
Measures P50, P95, P99 response times for the chat pipeline.
"""

import asyncio
import statistics
import time
from pathlib import Path

TEST_QUERIES = [
    "organic baby formula",
    "What BOGO deals do you have?",
    "ground beef lean",
    "store near Lakeland",
    "coffee K-Cups",
    "today's daily deals",
    "fresh vegetables organic",
    "Boar's Head turkey",
    "cleaning supplies Clorox",
    "sparkling water",
]


async def evaluate():
    """Run latency evaluation."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from app.services import retriever, generator

    latencies = []
    retrieval_times = []
    generation_times = []

    print(f"Running latency evaluation with {len(TEST_QUERIES)} queries...")
    print("-" * 70)

    for query in TEST_QUERIES:
        # Retrieval
        t0 = time.time()
        products = await retriever.retrieve_products(query, top_k=5)
        deals = await retriever.retrieve_deals(query, top_k=3)
        t1 = time.time()
        retrieval_ms = (t1 - t0) * 1000
        retrieval_times.append(retrieval_ms)

        # Generation
        context = generator.build_context(products, deals, [])
        response, gen_latency, model = await generator.generate(query, context)
        generation_times.append(gen_latency)

        total_ms = retrieval_ms + gen_latency
        latencies.append(total_ms)

        print(f"  {query[:40]:<40} retrieval={retrieval_ms:.0f}ms gen={gen_latency:.0f}ms total={total_ms:.0f}ms")

    print("-" * 70)

    # Calculate percentiles
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    ret_avg = statistics.mean(retrieval_times)
    gen_avg = statistics.mean(generation_times)

    print(f"\nLatency Percentiles (end-to-end):")
    print(f"  P50: {p50:.0f}ms")
    print(f"  P95: {p95:.0f}ms")
    print(f"  P99: {p99:.0f}ms")
    print(f"\nBreakdown:")
    print(f"  Avg Retrieval: {ret_avg:.0f}ms")
    print(f"  Avg Generation: {gen_avg:.0f}ms")

    # Thresholds (Ollama local is slower)
    provider = "ollama"  # or "azure_openai"
    threshold_p95 = 30000 if provider == "ollama" else 3000

    print(f"\nThreshold (P95 < {threshold_p95}ms for {provider}): ", end="")
    if p95 < threshold_p95:
        print("PASS")
    else:
        print(f"FAIL (P95={p95:.0f}ms)")

    assert p95 < threshold_p95, f"P95 latency {p95:.0f}ms exceeds threshold {threshold_p95}ms"


if __name__ == "__main__":
    asyncio.run(evaluate())
