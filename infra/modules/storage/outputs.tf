output "account_name" {
  value = azurerm_storage_account.media.name
}

output "primary_blob_endpoint" {
  value = azurerm_storage_account.media.primary_blob_endpoint
}

output "primary_access_key" {
  value     = azurerm_storage_account.media.primary_access_key
  sensitive = true
}

output "primary_connection_string" {
  value     = azurerm_storage_account.media.primary_connection_string
  sensitive = true
}

output "product_images_url" {
  value = "${azurerm_storage_account.media.primary_blob_endpoint}${azurerm_storage_container.product_images.name}"
}

output "category_images_url" {
  value = "${azurerm_storage_account.media.primary_blob_endpoint}${azurerm_storage_container.category_images.name}"
}
