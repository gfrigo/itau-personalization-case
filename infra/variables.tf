variable "project_name" {
  description = "Nome usado no ECR, ECS, ALB e demais recursos"
  type        = string
  default     = "itau-purchase-propensity"
}

variable "image_tag" {
  description = "Tag da imagem no ECR a ser publicada (ex: SHA do commit)"
  type        = string
}
