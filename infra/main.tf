resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
}

module "networking" {
  source              = "./modules/networking"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = var.project_name
  environment         = var.environment
}

module "database" {
  source              = "./modules/database"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = var.project_name
  admin_login         = var.db_admin_login
  admin_password      = var.db_admin_password
}

module "observability" {
  source              = "./modules/observability"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = var.project_name
}

module "ai" {
  source              = "./modules/ai"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.ai_location
  project_name        = var.project_name
}

module "storage" {
  source              = "./modules/storage"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = var.project_name
}

module "compute" {
  source                       = "./modules/compute"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  project_name                 = var.project_name
  db_connection_string         = module.database.connection_string
  ai_endpoint                  = module.ai.endpoint
  ai_api_key                   = module.ai.api_key
  appinsights_connection_string = module.observability.connection_string
}

module "functions" {
  source                       = "./modules/functions"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  project_name                 = var.project_name
  db_connection_string         = module.database.connection_string
  appinsights_connection_string = module.observability.connection_string
}

module "databricks" {
  source              = "./modules/databricks"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  project_name        = var.project_name
}
