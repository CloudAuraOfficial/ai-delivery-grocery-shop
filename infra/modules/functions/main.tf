resource "azurerm_storage_account" "func" {
  name                     = "st${replace(var.project_name, "-", "")}func"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
}

resource "azurerm_storage_queue" "order_processing" {
  name                 = "order-processing"
  storage_account_name = azurerm_storage_account.func.name
}

resource "azurerm_storage_queue" "delivery_updates" {
  name                 = "delivery-updates"
  storage_account_name = azurerm_storage_account.func.name
}

resource "azurerm_service_plan" "func" {
  name                = "plan-${var.project_name}-func"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "main" {
  name                       = "func-${var.project_name}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  service_plan_id            = azurerm_service_plan.func.id
  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key

  site_config {
    application_stack {
      dotnet_version              = "8.0"
      use_dotnet_isolated_runtime = true
    }
  }

  app_settings = {
    "ConnectionStrings__DefaultConnection"       = var.db_connection_string
    "APPLICATIONINSIGHTS_CONNECTION_STRING"       = var.appinsights_connection_string
    "OrderQueueConnection"                       = azurerm_storage_account.func.primary_connection_string
  }
}
