"""
Product Catalog Generator for AIDeliveryGroceryShop.
Generates 500+ products per category (3,000+ total) using template-based generation
with optional Ollama-powered descriptions.
"""

import json
import random
import hashlib
import os
import sys
from pathlib import Path

# Product name templates per subcategory type
PRODUCT_TEMPLATES = {
    "Diapers & Wipes": [
        "{brand} Diapers Size {size} ({count}ct)", "{brand} Baby Wipes {scent} ({count}ct)",
        "{brand} Overnight Diapers Size {size} ({count}ct)", "{brand} Training Pants Size {size} ({count}ct)",
        "{brand} Sensitive Wipes Refill ({count}ct)", "{brand} Swim Diapers Size {size} ({count}ct)",
    ],
    "Baby Formula": [
        "{brand} Infant Formula Powder ({weight}oz)", "{brand} Sensitive Formula ({weight}oz)",
        "{brand} Gentle Formula Ready-to-Feed ({weight}fl oz)", "{brand} Toddler Drink ({weight}oz)",
        "{brand} Organic Infant Formula ({weight}oz)", "{brand} Soy Formula ({weight}oz)",
    ],
    "Baby Food": [
        "{brand} Stage {stage} {flavor} ({weight}oz)", "{brand} Organic {flavor} Puree ({weight}oz)",
        "{brand} {flavor} Baby Food Pouch ({weight}oz)", "{brand} Stage {stage} {flavor} Jar ({weight}oz)",
    ],
    "Water": [
        "{brand} Purified Water ({count}pk {weight}fl oz)", "{brand} Spring Water ({weight}fl oz)",
        "{brand} Alkaline Water ({count}pk)", "{brand} Sparkling Mineral Water ({weight}fl oz)",
        "{brand} Distilled Water (1 gal)", "{brand} Water ({count}pk {weight}fl oz)",
    ],
    "Soda & Pop": [
        "{brand} {flavor} ({count}pk {weight}fl oz)", "{brand} {flavor} 2-Liter",
        "{brand} {flavor} Mini Cans ({count}pk)", "{brand} Zero Sugar {flavor} ({count}pk {weight}fl oz)",
        "{brand} Diet {flavor} ({count}pk)", "{brand} {flavor} ({weight}fl oz)",
    ],
    "Coffee": [
        "{brand} {roast} Ground Coffee ({weight}oz)", "{brand} {roast} Whole Bean ({weight}oz)",
        "{brand} K-Cups {flavor} ({count}ct)", "{brand} Cold Brew Concentrate ({weight}fl oz)",
        "{brand} Espresso {roast} ({weight}oz)", "{brand} Instant Coffee ({count}ct)",
    ],
    "Cleaning Supplies": [
        "{brand} {surface} Cleaner ({weight}fl oz)", "{brand} Disinfecting Wipes ({count}ct)",
        "{brand} Bleach ({weight}fl oz)", "{brand} Multi-Surface Spray ({weight}fl oz)",
        "{brand} {surface} Scrub ({weight}oz)", "{brand} Glass Cleaner ({weight}fl oz)",
    ],
    "Paper Products": [
        "{brand} Paper Towels ({count} Rolls)", "{brand} Toilet Paper ({count} Rolls)",
        "{brand} Facial Tissues ({count}ct)", "{brand} Napkins ({count}ct)",
        "{brand} Paper Plates ({count}ct)", "{brand} Ultra Strong TP ({count} Mega Rolls)",
    ],
    "Fruits": [
        "{brand} {variety} Apples ({weight}lb bag)", "{brand} Bananas (per lb)",
        "{brand} {variety} Oranges ({count}ct)", "{brand} Strawberries ({weight}oz)",
        "{brand} Blueberries ({weight}oz)", "{brand} Grapes {variety} (per lb)",
        "{brand} Avocados ({count}ct)", "{brand} Lemons ({count}ct)",
    ],
    "Vegetables": [
        "{brand} {variety} ({weight}oz bag)", "{brand} {variety} (per lb)",
        "{brand} Organic {variety} ({weight}oz)", "{brand} {variety} ({count}ct)",
        "{brand} Baby Carrots ({weight}oz)", "{brand} Sweet Potatoes (per lb)",
    ],
    "Beef": [
        "{brand} Ground Beef {lean}% Lean ({weight}lb)", "{brand} Ribeye Steak ({weight}lb)",
        "{brand} NY Strip Steak ({weight}lb)", "{brand} Sirloin Steak ({weight}lb)",
        "{brand} Beef Chuck Roast ({weight}lb)", "{brand} Stew Meat ({weight}lb)",
        "{brand} Filet Mignon ({weight}lb)", "{brand} Beef Short Ribs ({weight}lb)",
    ],
    "Chicken": [
        "{brand} Chicken Breast Boneless Skinless ({weight}lb)", "{brand} Chicken Thighs ({weight}lb)",
        "{brand} Whole Chicken ({weight}lb)", "{brand} Chicken Wings ({weight}lb)",
        "{brand} Chicken Tenders ({weight}lb)", "{brand} Ground Chicken ({weight}lb)",
        "{brand} Chicken Drumsticks ({weight}lb)", "{brand} Rotisserie Seasoned Chicken ({weight}lb)",
    ],
    "Sliced Meats": [
        "{brand} {variety} Turkey Breast ({weight}oz)", "{brand} {variety} Ham ({weight}oz)",
        "{brand} Roast Beef ({weight}oz)", "{brand} {variety} Salami ({weight}oz)",
        "{brand} Pepperoni ({weight}oz)", "{brand} Bologna ({weight}oz)",
        "{brand} {variety} Chicken Breast ({weight}oz)", "{brand} Prosciutto ({weight}oz)",
    ],
    "Cheese": [
        "{brand} {variety} Cheese ({weight}oz)", "{brand} Shredded {variety} ({weight}oz)",
        "{brand} Sliced {variety} ({weight}oz)", "{brand} {variety} Cheese Block ({weight}oz)",
        "{brand} Cream Cheese ({weight}oz)", "{brand} {variety} Crumbles ({weight}oz)",
    ],
}

FLAVORS = {
    "soda": ["Original", "Cherry", "Vanilla", "Lemon Lime", "Orange", "Grape", "Ginger Ale", "Root Beer", "Cream Soda"],
    "coffee_roast": ["Medium Roast", "Dark Roast", "Light Roast", "French Roast", "Italian Roast", "Breakfast Blend"],
    "coffee_flavor": ["Classic", "Hazelnut", "French Vanilla", "Caramel", "Mocha", "Colombian"],
    "baby_food": ["Banana", "Apple", "Sweet Potato", "Pear", "Carrot", "Mango", "Peach", "Squash", "Pea", "Green Bean"],
    "apple_variety": ["Gala", "Fuji", "Honeycrisp", "Granny Smith", "Pink Lady", "Red Delicious"],
    "grape_variety": ["Red", "Green", "Black", "Cotton Candy"],
    "veggie_variety": ["Broccoli", "Cauliflower", "Spinach", "Kale", "Zucchini", "Bell Peppers", "Tomatoes", "Cucumber", "Celery", "Corn", "Green Beans", "Asparagus", "Brussels Sprouts", "Mushrooms"],
    "cheese_variety": ["Cheddar", "Mozzarella", "Swiss", "Provolone", "Pepper Jack", "Colby Jack", "Gouda", "Parmesan", "Brie", "Havarti"],
    "deli_meat": ["Oven Roasted", "Smoked", "Honey", "Peppered", "Cajun", "Mesquite"],
    "surface": ["All-Purpose", "Bathroom", "Kitchen", "Floor", "Toilet", "Oven"],
    "scent": ["Unscented", "Lavender", "Fresh", "Sensitive", "Aloe"],
}

UNITS_MAP = {
    "Baby": "each", "Beverages": "each", "Household": "each",
    "Fresh": "lb", "Meat & Seafood": "lb", "Deli": "lb",
}


def generate_slug(name: str) -> str:
    return name.lower().replace("&", "and").replace("'", "").replace("(", "").replace(")", "").replace("/", "-").replace(",", "").replace("  ", " ").replace(" ", "-").replace("--", "-").strip("-")


def generate_sku(category_slug: str, index: int) -> str:
    prefix = category_slug.upper()[:3]
    return f"{prefix}-{index:04d}"


def generate_description(product_name: str, category: str, brand: str) -> str:
    templates = [
        f"Premium quality {product_name.lower()} from {brand}. Perfect for your everyday needs.",
        f"{brand} brings you {product_name.lower()}, made with care for the best quality.",
        f"Trust {brand} for premium {category.lower()} products. {product_name} delivers on taste and value.",
        f"Stock up on {product_name.lower()} from {brand}. Great quality at an everyday price.",
        f"{product_name} by {brand}. A trusted choice for families across Florida.",
    ]
    return random.choice(templates)


def generate_tags(category: str, subcategory: str, is_organic: bool, is_store_brand: bool) -> str:
    tags = [category.lower(), subcategory.lower().replace(" & ", ",").replace(" ", "-")]
    if is_organic:
        tags.append("organic")
    if is_store_brand:
        tags.append("store-brand")
    return ",".join(tags)


def fill_template(template: str, brand: str, subcategory: str) -> tuple[str, str, str]:
    """Fill a product name template with random values. Returns (name, unit, weight)."""
    params = {"brand": brand}
    weight_str = ""
    unit = "each"

    # Common fill values
    params["count"] = random.choice([4, 6, 8, 10, 12, 16, 20, 24, 30, 36, 48])
    params["weight"] = random.choice([4, 6, 8, 10, 12, 16, 20, 24, 32, 48, 64])
    params["size"] = random.choice(["N", "1", "2", "3", "4", "5", "6"])
    params["stage"] = random.choice([1, 2, 3])
    params["lean"] = random.choice([73, 80, 85, 90, 93, 96])

    # Context-specific fills
    if "flavor" in template and "Soda" in subcategory:
        params["flavor"] = random.choice(FLAVORS["soda"])
    elif "flavor" in template and "Coffee" in subcategory:
        params["flavor"] = random.choice(FLAVORS["coffee_flavor"])
    elif "flavor" in template and "Baby" in subcategory:
        params["flavor"] = random.choice(FLAVORS["baby_food"])
    elif "flavor" in template:
        params["flavor"] = random.choice(["Original", "Classic", "Natural"])

    if "roast" in template:
        params["roast"] = random.choice(FLAVORS["coffee_roast"])
    if "variety" in template:
        if "Apple" in subcategory or "Fruit" in subcategory:
            params["variety"] = random.choice(FLAVORS["apple_variety"])
        elif "Grape" in subcategory or "Fruit" in subcategory:
            params["variety"] = random.choice(FLAVORS["grape_variety"])
        elif "Vegetable" in subcategory or "Fresh" in subcategory:
            params["variety"] = random.choice(FLAVORS["veggie_variety"])
        elif "Cheese" in subcategory:
            params["variety"] = random.choice(FLAVORS["cheese_variety"])
        elif "Sliced" in subcategory or "Deli" in subcategory:
            params["variety"] = random.choice(FLAVORS["deli_meat"])
        else:
            params["variety"] = random.choice(["Classic", "Premium", "Select"])

    if "surface" in template:
        params["surface"] = random.choice(FLAVORS["surface"])
    if "scent" in template:
        params["scent"] = random.choice(FLAVORS["scent"])

    name = template.format(**params)

    # Determine weight string and unit
    if "lb" in name or "per lb" in name.lower():
        unit = "lb"
        weight_str = f"{params.get('weight', 1)} lb"
    elif "oz" in name:
        unit = "oz"
        weight_str = f"{params.get('weight', 12)} oz"
    elif "gal" in name.lower():
        unit = "gallon"
        weight_str = "1 gallon"
    elif "ct" in name or "pk" in name or "Roll" in name:
        unit = "each"
        weight_str = f"{params.get('count', 1)} ct"
    else:
        unit = "each"
        weight_str = "1 each"

    return name, unit, weight_str


def generate_products_for_category(category_data: dict, start_sku: int) -> list[dict]:
    """Generate 500+ products for a single category."""
    products = []
    sku_counter = start_sku
    seen_names = set()

    target_per_subcategory = 55  # 55 * ~10 subcategories ≈ 550 per category

    for sub in category_data["subcategories"]:
        sub_name = sub["name"]
        brands = sub["brands"]
        price_min, price_max = sub["priceRange"]

        # Get templates or use generic ones
        templates = PRODUCT_TEMPLATES.get(sub_name, [
            "{brand} " + sub_name + " {variety} ({weight}oz)",
            "{brand} Premium " + sub_name + " ({weight}oz)",
            "{brand} " + sub_name + " Value Pack ({count}ct)",
            "{brand} Organic " + sub_name + " ({weight}oz)",
            "{brand} " + sub_name + " Family Size ({weight}oz)",
            "{brand} " + sub_name + " ({count}ct)",
        ])

        generated = 0
        attempts = 0
        max_attempts = target_per_subcategory * 5

        while generated < target_per_subcategory and attempts < max_attempts:
            attempts += 1
            brand = random.choice(brands)
            template = random.choice(templates)

            name, unit, weight = fill_template(template, brand, sub_name)

            # Deduplicate
            name_key = name.lower().strip()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            is_store_brand = brand == "GreenWise"
            is_organic = is_store_brand or random.random() < 0.12
            price = round(random.uniform(price_min, price_max), 2)

            if is_store_brand:
                price = round(price * 0.85, 2)  # Store brand discount

            product = {
                "name": name,
                "slug": generate_slug(name),
                "category": category_data["name"],
                "category_slug": category_data["slug"],
                "subcategory": sub_name,
                "brand": brand,
                "price": price,
                "unit": unit,
                "weight": weight,
                "sku": generate_sku(category_data["slug"], sku_counter),
                "is_organic": is_organic,
                "is_store_brand": is_store_brand,
                "is_available": True,
                "description": generate_description(name, category_data["name"], brand),
                "tags": generate_tags(category_data["name"], sub_name, is_organic, is_store_brand),
            }

            products.append(product)
            sku_counter += 1
            generated += 1

    return products


def main():
    random.seed(42)  # Reproducible output

    templates_path = Path(__file__).parent / "templates" / "categories.json"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    with open(templates_path) as f:
        categories = json.load(f)

    all_products = []
    sku_offset = 1

    for cat in categories:
        products = generate_products_for_category(cat, sku_offset)
        all_products.extend(products)
        sku_offset += len(products)
        print(f"  {cat['name']}: {len(products)} products")

    output_path = output_dir / "products.json"
    with open(output_path, "w") as f:
        json.dump(all_products, f, indent=2)

    print(f"\nTotal: {len(all_products)} products written to {output_path}")

    # Summary by category
    from collections import Counter
    cat_counts = Counter(p["category"] for p in all_products)
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
