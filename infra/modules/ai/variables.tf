variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "project_name" {
  type = string
}

variable "gpt4o_capacity" {
  type    = number
  default = 10
}

variable "embedding_capacity" {
  type    = number
  default = 10
}
