resource "azurerm_mssql_server" "main" {
  name                         = "sql-${var.project_name}"
  resource_group_name          = var.resource_group_name
  location                     = var.location
  version                      = "12.0"
  administrator_login          = var.admin_login
  administrator_login_password = var.admin_password
  minimum_tls_version          = "1.2"
}

resource "azurerm_mssql_database" "main" {
  name      = "sqldb-${var.project_name}"
  server_id = azurerm_mssql_server.main.id
  sku_name  = var.db_sku
  collation = "SQL_Latin1_General_CP1_CI_AS"

  short_term_retention_policy {
    retention_days = 7
  }
}

resource "azurerm_mssql_firewall_rule" "allow_azure" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
