output "vnet_id" {
  value = azurerm_virtual_network.main.id
}

output "app_subnet_id" {
  value = azurerm_subnet.app.id
}

output "db_subnet_id" {
  value = azurerm_subnet.db.id
}

output "functions_subnet_id" {
  value = azurerm_subnet.functions.id
}

output "frontdoor_profile_id" {
  value = azurerm_cdn_frontdoor_profile.main.id
}

output "frontdoor_endpoint" {
  value = azurerm_cdn_frontdoor_profile.main.resource_guid
}
