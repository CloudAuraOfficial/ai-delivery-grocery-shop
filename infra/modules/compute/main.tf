resource "azurerm_service_plan" "main" {
  name                = "plan-${var.project_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  os_type             = "Linux"
  sku_name            = var.sku_name
}

resource "azurerm_linux_web_app" "api" {
  name                = "app-${var.project_name}-api"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      dotnet_version = "8.0"
    }
    always_on = false
  }

  app_settings = {
    "ConnectionStrings__DefaultConnection"       = var.db_connection_string
    "AzureOpenAI__Endpoint"                      = var.ai_endpoint
    "AzureOpenAI__ApiKey"                        = var.ai_api_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING"       = var.appinsights_connection_string
  }
}

resource "azurerm_linux_web_app" "web" {
  name                = "app-${var.project_name}-web"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      dotnet_version = "8.0"
    }
    always_on = false
  }

  app_settings = {
    "ApiBaseUrl"                                 = "https://${azurerm_linux_web_app.api.default_hostname}"
    "APPLICATIONINSIGHTS_CONNECTION_STRING"       = var.appinsights_connection_string
  }
}

resource "azurerm_linux_web_app" "ai" {
  name                = "app-${var.project_name}-ai"
  location            = var.location
  resource_group_name = var.resource_group_name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
    always_on = false
  }

  app_settings = {
    "AZURE_OPENAI_ENDPOINT"                      = var.ai_endpoint
    "AZURE_OPENAI_API_KEY"                       = var.ai_api_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING"       = var.appinsights_connection_string
  }
}
