variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "project_name" {
  type = string
}

variable "sku_name" {
  type    = string
  default = "B1"
}

variable "db_connection_string" {
  type      = string
  sensitive = true
}

variable "ai_endpoint" {
  type      = string
  sensitive = true
}

variable "ai_api_key" {
  type      = string
  sensitive = true
}

variable "appinsights_connection_string" {
  type      = string
  sensitive = true
}
