resource "azurerm_storage_account" "media" {
  name                     = "st${replace(var.project_name, "-", "")}media"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type = var.replication_type
  min_tls_version          = "TLS1_2"

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["GET", "HEAD"]
      allowed_origins    = ["*"]
      exposed_headers    = ["Content-Length"]
      max_age_in_seconds = 3600
    }
  }
}

resource "azurerm_storage_container" "product_images" {
  name                  = "product-images"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "blob"
}

resource "azurerm_storage_container" "category_images" {
  name                  = "category-images"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "blob"
}
