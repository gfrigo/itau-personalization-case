output "app_url" {
  description = "URL para testar a API"
  value       = "http://${aws_lb.this.dns_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.this.repository_url
}
