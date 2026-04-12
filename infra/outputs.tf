output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "api_url" {
  value = module.compute.api_url
}

output "ai_endpoint" {
  value     = module.ai.endpoint
  sensitive = true
}

output "db_connection_string" {
  value     = module.database.connection_string
  sensitive = true
}

output "appinsights_connection_string" {
  value     = module.observability.connection_string
  sensitive = true
}

output "databricks_workspace_url" {
  value = module.databricks.workspace_url
}
