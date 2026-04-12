#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PIPELINE_DIR="$PROJECT_DIR/data-pipeline"

echo "=== AIDeliveryGroceryShop Data Pipeline ==="
echo ""

echo "[1/3] Generating products..."
python3 "$PIPELINE_DIR/generate_products.py"
echo ""

echo "[2/3] Generating deals..."
python3 "$PIPELINE_DIR/generate_deals.py"
echo ""

echo "[3/3] Seeding database..."
python3 "$PIPELINE_DIR/seed_database.py"
echo ""

echo "=== Pipeline complete ==="
