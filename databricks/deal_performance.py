# Databricks notebook source
# MAGIC %md
# MAGIC # Deal Performance Analysis
# MAGIC Analyze deal effectiveness by type, category, and conversion rates.
# MAGIC Joins deals with order data to compute revenue impact.

# COMMAND ----------

jdbc_url = dbutils.widgets.get("jdbc_url") if "dbutils" in dir() else "jdbc:postgresql://localhost:5436/groceryshop"
jdbc_props = {
    "user": dbutils.widgets.get("db_user") if "dbutils" in dir() else "grocery",
    "password": dbutils.widgets.get("db_password") if "dbutils" in dir() else "changeme",
    "driver": "org.postgresql.Driver"
}

def load_table(table_name):
    return (
        spark.read.format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", f'"{table_name}"')
        .option("user", jdbc_props["user"])
        .option("password", jdbc_props["password"])
        .option("driver", jdbc_props["driver"])
        .load()
    )

# COMMAND ----------

from pyspark.sql import functions as F

deals_df = load_table("Deals")
products_df = load_table("Products")
categories_df = load_table("Categories")
order_items_df = load_table("OrderItems")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deal Distribution by Type

# COMMAND ----------

deal_stats = (
    deals_df
    .filter(F.col("IsActive") == True)
    .groupBy("DealType")
    .agg(
        F.count("*").alias("deal_count"),
        F.round(F.avg("DiscountPercent"), 1).alias("avg_discount_pct"),
    )
    .orderBy("DealType")
)

display(deal_stats) if "display" in dir() else deal_stats.show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deals by Category

# COMMAND ----------

deals_by_category = (
    deals_df
    .join(products_df.select("Id", "CategoryId", "Price"), deals_df.ProductId == products_df.Id, "inner")
    .join(categories_df.select(categories_df.Id.alias("CatId"), "Name"), F.col("CategoryId") == F.col("CatId"), "inner")
    .groupBy("Name", "DealType")
    .agg(
        F.count("*").alias("deal_count"),
        F.round(F.avg("Price"), 2).alias("avg_product_price"),
        F.round(F.avg("DiscountPercent"), 1).alias("avg_discount"),
    )
    .orderBy("Name", "DealType")
)

display(deals_by_category) if "display" in dir() else deals_by_category.show(30)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deal Conversion Rate (Orders with Deals)

# COMMAND ----------

total_order_items = order_items_df.count()
deal_order_items = order_items_df.filter(F.col("DealId").isNotNull()).count()

if total_order_items > 0:
    conversion_rate = deal_order_items / total_order_items * 100
    print(f"Total order items: {total_order_items}")
    print(f"Items with deals: {deal_order_items}")
    print(f"Deal conversion rate: {conversion_rate:.1f}%")
else:
    print("No order data yet — conversion metrics will populate after orders are placed.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Revenue Impact Estimate

# COMMAND ----------

if total_order_items > 0:
    revenue_impact = (
        order_items_df
        .join(deals_df.select("Id", "DealType", "DiscountPercent"),
              order_items_df.DealId == deals_df.Id, "left")
        .groupBy("DealType")
        .agg(
            F.count("*").alias("items_sold"),
            F.round(F.sum("LineTotal"), 2).alias("total_revenue"),
            F.round(F.avg("LineTotal"), 2).alias("avg_item_revenue"),
        )
        .orderBy("DealType")
    )
    display(revenue_impact) if "display" in dir() else revenue_impact.show()
else:
    print("No order data available for revenue analysis.")
