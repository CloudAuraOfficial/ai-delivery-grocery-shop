output "server_fqdn" {
  value = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "database_name" {
  value = azurerm_mssql_database.main.name
}

output "connection_string" {
  value     = "Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Database=${azurerm_mssql_database.main.name};User ID=${var.admin_login};Password=${var.admin_password};Encrypt=true;TrustServerCertificate=false;"
  sensitive = true
}

output "server_id" {
  value = azurerm_mssql_server.main.id
}
