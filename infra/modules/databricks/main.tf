resource "azurerm_databricks_workspace" "main" {
  name                = "dbw-${var.project_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku

  tags = {
    Purpose = "AI-powered grocery analytics"
  }
}
