output "endpoint" {
  value     = azurerm_cognitive_account.openai.endpoint
  sensitive = true
}

output "api_key" {
  value     = azurerm_cognitive_account.openai.primary_access_key
  sensitive = true
}

output "account_id" {
  value = azurerm_cognitive_account.openai.id
}

output "gpt4o_deployment_name" {
  value = azurerm_cognitive_deployment.gpt4o.name
}

output "embedding_deployment_name" {
  value = azurerm_cognitive_deployment.embedding.name
}
