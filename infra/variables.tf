variable "project_name" {
  type    = string
  default = "grocery"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "ai_location" {
  type    = string
  default = "eastus2"
  description = "Azure OpenAI has regional availability constraints"
}

variable "db_admin_login" {
  type      = string
  sensitive = true
}

variable "db_admin_password" {
  type      = string
  sensitive = true
}
