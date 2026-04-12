output "api_url" {
  value = "https://${azurerm_linux_web_app.api.default_hostname}"
}

output "web_url" {
  value = "https://${azurerm_linux_web_app.web.default_hostname}"
}

output "ai_url" {
  value = "https://${azurerm_linux_web_app.ai.default_hostname}"
}

output "service_plan_id" {
  value = azurerm_service_plan.main.id
}

output "api_principal_id" {
  value = azurerm_linux_web_app.api.identity != null ? try(azurerm_linux_web_app.api.identity[0].principal_id, "") : ""
}
