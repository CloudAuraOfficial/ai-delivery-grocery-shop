"""Custom response handler for specific customer scenarios.
Returns a custom message if the query matches a known scenario, or None to proceed with RAG.
"""

import re


def check_custom_scenario(query: str) -> dict | None:
    """Check if the query matches a predefined scenario.
    Returns {"message": str, "skip_rag": bool} or None.
    """
    q = query.lower().strip()

    # 1. Order tracking / order history
    if any(kw in q for kw in ["track my order", "order status", "order history", "where is my order", "my orders", "track order"]):
        return {
            "message": (
                "I appreciate your interest in tracking your order! "
                "Order tracking is currently being developed as part of our 'customer-first' commitment. "
                "In the meantime, please check your email for order confirmation details, "
                "or visit our store directly for assistance.\n\n"
                "Is there anything else I can help you with? I'm great at finding products, deals, and store info!"
            ),
            "skip_rag": True,
        }

    # 2. Brand not carried
    not_carried_brands = ["whole foods", "trader joe", "aldi", "costco", "kirkland", "walmart", "great value", "sam's choice", "kroger", "365 by whole"]
    for brand in not_carried_brands:
        if brand in q:
            return {
                "message": (
                    f"I'm sorry, we don't currently carry that brand in our stores. "
                    f"However, I'd love to help you find a great alternative! "
                    f"We carry over 3,300 products including our premium GreenWise store brand "
                    f"and popular national brands.\n\n"
                    f"Would you like me to suggest similar products from the brands we do carry?"
                ),
                "skip_rag": False,  # Still run RAG to find alternatives
            }

    # 3. Delivery area / do you deliver to...
    if any(kw in q for kw in ["deliver to", "delivery area", "delivery zone", "do you deliver", "ship to"]):
        return {
            "message": (
                "We currently deliver to the greater Lakeland, Florida area, "
                "covering 9 store locations: Lakeland South, Lakeland North, Winter Haven, "
                "Plant City, Bartow, Auburndale, Haines City, Mulberry, and Davenport.\n\n"
                "Free delivery on orders over $35! Standard delivery fee is $5.99 for smaller orders.\n\n"
                "Would you like to see our store locations or start shopping?"
            ),
            "skip_rag": True,
        }

    # 4. Payment methods
    if any(kw in q for kw in ["payment", "pay with", "credit card", "debit card", "apple pay", "how to pay", "accept"]):
        return {
            "message": (
                "We're currently in demo mode, so no real payments are processed. "
                "In our production version, we would accept all major credit/debit cards, "
                "Apple Pay, Google Pay, and EBT/SNAP benefits — because grocery access matters.\n\n"
                "Feel free to explore the full shopping experience including cart and checkout!"
            ),
            "skip_rag": True,
        }

    # 5. Return / refund
    if any(kw in q for kw in ["return", "refund", "exchange", "money back", "damaged", "wrong item"]):
        return {
            "message": (
                "Customer satisfaction is our top priority! "
                "Our return and refund system is currently under development as part of our "
                "'customer-first' philosophy.\n\n"
                "In a production environment, we would offer:\n"
                "- Full refunds for damaged or incorrect items\n"
                "- Easy returns within 7 days of delivery\n"
                "- Instant credit for missing items\n\n"
                "Is there anything else I can help you find today?"
            ),
            "skip_rag": True,
        }

    # 6. Coupons / promo codes
    if any(kw in q for kw in ["coupon", "promo code", "discount code", "voucher", "promotion code"]):
        return {
            "message": (
                "We don't use promo codes — instead, our deals are applied automatically! "
                "Here's what's always available:\n\n"
                "- **BOGO**: 200+ Buy One Get One Free products\n"
                "- **Weekly Deals**: 150+ products at 20-40% off\n"
                "- **Daily Deals**: 15 products at 25-50% off (changes daily!)\n\n"
                "Would you like me to show you what's on sale right now?"
            ),
            "skip_rag": False,
        }

    # 7. Allergies / dietary restrictions
    if any(kw in q for kw in ["allergy", "allergic", "gluten free", "gluten-free", "nut free", "dairy free", "vegan", "vegetarian", "keto", "halal", "kosher"]):
        diet = "dietary needs"
        if "gluten" in q: diet = "gluten-free options"
        elif "vegan" in q: diet = "vegan products"
        elif "keto" in q: diet = "keto-friendly items"
        elif "dairy" in q: diet = "dairy-free alternatives"
        return {
            "message": (
                f"I understand how important {diet} are! "
                f"While our product labels include basic tags like 'organic', "
                f"detailed allergen information is something we're actively working on adding "
                f"to every product listing.\n\n"
                f"In the meantime, I can help you search for products tagged as organic "
                f"or from specific brands known for {diet}. "
                f"What specifically are you looking for?"
            ),
            "skip_rag": False,
        }

    # 8. Off-topic (weather, sports, news, etc.)
    off_topic_keywords = ["weather", "sports", "news", "politics", "movie", "music", "game score",
                          "stock market", "bitcoin", "crypto", "joke", "tell me a joke",
                          "who are you", "what are you", "how old are you"]
    if any(kw in q for kw in off_topic_keywords):
        return {
            "message": (
                "That's a great question, but I'm a grocery shopping specialist! "
                "I know everything about our 3,300+ products, 365 active deals, "
                "and 9 store locations — but that's where my expertise ends.\n\n"
                "Here are some things I can help with:\n"
                "- Find products by name, brand, or category\n"
                "- Show you BOGO, weekly, or daily deals\n"
                "- Store locations and hours\n"
                "- Meal ingredient suggestions\n\n"
                "What can I help you find?"
            ),
            "skip_rag": True,
        }

    # 9. Complaint / bad experience
    if any(kw in q for kw in ["complaint", "complain", "bad experience", "terrible", "worst", "horrible", "disgusting", "rude"]):
        return {
            "message": (
                "I'm truly sorry to hear about your experience. "
                "Customer satisfaction is at the heart of everything we do, "
                "and we take every concern seriously.\n\n"
                "While our feedback system is being built out, "
                "please know that your input helps us improve. "
                "For immediate assistance, you can contact any of our 9 store locations directly.\n\n"
                "Is there anything I can help you with right now to make things better?"
            ),
            "skip_rag": True,
        }

    # 10. Bulk / catering / large orders
    if any(kw in q for kw in ["bulk order", "catering", "party platter", "large order", "wholesale", "event", "party"]):
        return {
            "message": (
                "Great choice for planning an event! "
                "Our Deli department offers party platters starting at $14.99, "
                "and we have bulk options across many product categories.\n\n"
                "Bulk ordering and catering services are being expanded — "
                "for large orders (50+ items), we recommend contacting your nearest store directly "
                "for personalized assistance and potential volume discounts.\n\n"
                "Want me to show you our Deli platters and party food options?"
            ),
            "skip_rag": False,
        }

    return None
