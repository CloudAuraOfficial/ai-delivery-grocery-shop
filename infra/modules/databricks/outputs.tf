output "workspace_url" {
  value = azurerm_databricks_workspace.main.workspace_url
}

output "workspace_id" {
  value = azurerm_databricks_workspace.main.id
}

output "managed_resource_group_id" {
  value = azurerm_databricks_workspace.main.managed_resource_group_id
}
