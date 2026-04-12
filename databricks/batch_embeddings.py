# Databricks notebook source
# MAGIC %md
# MAGIC # Batch Embedding Pipeline
# MAGIC Generate embeddings for all products using a Spark UDF.
# MAGIC Runs on Databricks cluster for parallel processing, upserts to Qdrant.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import os

jdbc_url = dbutils.widgets.get("jdbc_url") if "dbutils" in dir() else "jdbc:postgresql://localhost:5436/groceryshop"
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
embed_model = os.environ.get("EMBED_MODEL", "nomic-embed-text")

jdbc_props = {
    "user": dbutils.widgets.get("db_user") if "dbutils" in dir() else "grocery",
    "password": dbutils.widgets.get("db_password") if "dbutils" in dir() else "changeme",
    "driver": "org.postgresql.Driver"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Products

# COMMAND ----------

products_df = (
    spark.read.format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", '"Products"')
    .option("user", jdbc_props["user"])
    .option("password", jdbc_props["password"])
    .option("driver", jdbc_props["driver"])
    .load()
)

categories_df = (
    spark.read.format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", '"Categories"')
    .option("user", jdbc_props["user"])
    .option("password", jdbc_props["password"])
    .option("driver", jdbc_props["driver"])
    .load()
)

joined_df = products_df.join(
    categories_df.select("Id", "Name"),
    products_df.CategoryId == categories_df.Id,
    "inner"
).select(
    products_df["*"],
    categories_df.Name.alias("CategoryName")
)

print(f"Total products to embed: {joined_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Embedding UDF

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType
import requests
import json


def build_text(name, category, brand, price, description, is_organic, tags):
    parts = [
        f"Product: {name}",
        f"Category: {category}",
        f"Brand: {brand or 'Unknown'}",
        f"Price: ${price:.2f}",
        f"Description: {description}",
    ]
    if is_organic:
        parts.append("This is an organic product.")
    if tags:
        parts.append(f"Tags: {tags}")
    return "\n".join(parts)


def get_embedding_batch(texts):
    """Get embeddings for a batch of texts via Ollama."""
    embeddings = []
    for text in texts:
        try:
            resp = requests.post(
                f"{ollama_url}/api/embeddings",
                json={"model": embed_model, "prompt": text},
                timeout=30,
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
        except Exception as e:
            print(f"Embedding error: {e}")
            embeddings.append([0.0] * 768)  # Fallback zero vector
    return embeddings


# Register as Pandas UDF for efficient batch processing
@F.pandas_udf(ArrayType(FloatType()))
def embed_udf(texts):
    import pandas as pd
    results = []
    batch_size = 10
    text_list = texts.tolist()
    for i in range(0, len(text_list), batch_size):
        batch = text_list[i:i + batch_size]
        results.extend(get_embedding_batch(batch))
    return pd.Series(results)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Embeddings

# COMMAND ----------

from pyspark.sql.functions import concat_ws, lit, when, col

embedded_df = joined_df.withColumn(
    "embed_text",
    concat_ws(
        "\n",
        concat_ws(": ", lit("Product"), col("Name")),
        concat_ws(": ", lit("Category"), col("CategoryName")),
        concat_ws(": ", lit("Brand"), F.coalesce(col("Brand"), lit("Unknown"))),
        concat_ws(": ", lit("Price"), F.format_number(col("Price"), 2)),
        concat_ws(": ", lit("Description"), col("Description")),
        when(col("IsOrganic") == True, lit("This is an organic product.")).otherwise(lit("")),
    )
).withColumn("embedding", embed_udf(col("embed_text")))

print(f"Generated embeddings for {embedded_df.count()} products")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Upsert to Qdrant

# COMMAND ----------

def upsert_to_qdrant(partition):
    """Upsert a partition of products to Qdrant."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import PointStruct

    client = QdrantClient(url=qdrant_url)
    points = []

    for idx, row in enumerate(partition):
        points.append(PointStruct(
            id=hash(row["Sku"]) % (2**63),
            vector=row["embedding"],
            payload={
                "sku": row["Sku"],
                "name": row["Name"],
                "category": row["CategoryName"],
                "brand": row["Brand"] or "",
                "price": float(row["Price"]),
                "is_organic": bool(row["IsOrganic"]),
                "is_store_brand": bool(row["IsStoreBrand"]),
                "tags": row["Tags"] or "",
            }
        ))

        if len(points) >= 100:
            client.upsert(collection_name="grocery_products", points=points)
            points = []

    if points:
        client.upsert(collection_name="grocery_products", points=points)


# Execute across partitions
embedded_df.foreachPartition(upsert_to_qdrant)
print("Qdrant upsert complete!")
