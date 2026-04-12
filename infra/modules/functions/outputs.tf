output "function_app_name" {
  value = azurerm_linux_function_app.main.name
}

output "function_app_url" {
  value = "https://${azurerm_linux_function_app.main.default_hostname}"
}

output "storage_connection_string" {
  value     = azurerm_storage_account.func.primary_connection_string
  sensitive = true
}

output "order_queue_name" {
  value = azurerm_storage_queue.order_processing.name
}

output "delivery_queue_name" {
  value = azurerm_storage_queue.delivery_updates.name
}
