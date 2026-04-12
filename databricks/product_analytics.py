# Databricks notebook source
# MAGIC %md
# MAGIC # Product Catalog Analytics
# MAGIC Analyze product distribution, pricing trends, and brand frequency across the 3,300+ product catalog.
# MAGIC Reads from PostgreSQL via JDBC, writes results to Delta table.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

jdbc_url = dbutils.widgets.get("jdbc_url") if "dbutils" in dir() else "jdbc:postgresql://localhost:5436/groceryshop"
jdbc_props = {
    "user": dbutils.widgets.get("db_user") if "dbutils" in dir() else "grocery",
    "password": dbutils.widgets.get("db_password") if "dbutils" in dir() else "changeme",
    "driver": "org.postgresql.Driver"
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Load Data from PostgreSQL

# COMMAND ----------

products_df = (
    spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", '"Products"')
    .option("user", jdbc_props["user"])
    .option("password", jdbc_props["password"])
    .option("driver", jdbc_props["driver"])
    .load()
)

categories_df = (
    spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", '"Categories"')
    .option("user", jdbc_props["user"])
    .option("password", jdbc_props["password"])
    .option("driver", jdbc_props["driver"])
    .load()
)

print(f"Products: {products_df.count()}, Categories: {categories_df.count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Product Distribution by Category

# COMMAND ----------

from pyspark.sql import functions as F

category_stats = (
    products_df.join(categories_df, products_df.CategoryId == categories_df.Id, "inner")
    .groupBy(categories_df.Name.alias("category"))
    .agg(
        F.count("*").alias("product_count"),
        F.round(F.avg("Price"), 2).alias("avg_price"),
        F.round(F.min("Price"), 2).alias("min_price"),
        F.round(F.max("Price"), 2).alias("max_price"),
        F.round(F.stddev("Price"), 2).alias("price_stddev"),
        F.sum(F.when(F.col("IsOrganic") == True, 1).otherwise(0)).alias("organic_count"),
        F.sum(F.when(F.col("IsStoreBrand") == True, 1).otherwise(0)).alias("store_brand_count"),
    )
    .orderBy("category")
)

display(category_stats) if "display" in dir() else category_stats.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Brand Frequency Analysis

# COMMAND ----------

brand_frequency = (
    products_df
    .filter(F.col("Brand").isNotNull())
    .groupBy("Brand")
    .agg(
        F.count("*").alias("product_count"),
        F.round(F.avg("Price"), 2).alias("avg_price"),
    )
    .orderBy(F.desc("product_count"))
    .limit(30)
)

display(brand_frequency) if "display" in dir() else brand_frequency.show(30)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Price Distribution Histogram

# COMMAND ----------

price_buckets = (
    products_df
    .withColumn("price_bucket", F.floor(F.col("Price") / 5) * 5)
    .groupBy("price_bucket")
    .count()
    .orderBy("price_bucket")
)

display(price_buckets) if "display" in dir() else price_buckets.show(30)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write Analytics to Delta Table

# COMMAND ----------

output_path = "/mnt/grocery-analytics/category_stats"

try:
    category_stats.write.format("delta").mode("overwrite").save(output_path)
    print(f"Category stats written to {output_path}")
except Exception as e:
    # Fallback for local execution (no Delta Lake)
    print(f"Delta write skipped (local mode): {e}")
    category_stats.write.mode("overwrite").parquet("/tmp/grocery_category_stats")
    print("Written to /tmp/grocery_category_stats as Parquet")
