variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = "morpheus:latest"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "morpheus"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "morpheus"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}