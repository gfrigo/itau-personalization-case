resource "aws_ecr_repository" "this" {
  name         = var.project_name
  force_delete = true
}
