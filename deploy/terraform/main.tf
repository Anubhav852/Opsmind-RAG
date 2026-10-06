terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
provider "aws" { region = "ap-south-1" }

variable "db_password" {
  type      = string
  sensitive = true
}

resource "aws_ecr_repository" "api" {
  name                 = "opsmind-api"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_db_instance" "pg" {
  identifier          = "opsmind"
  engine              = "postgres"
  engine_version      = "16"
  instance_class      = "db.t4g.micro"
  allocated_storage   = 20
  db_name             = "opsmind"
  username            = "opsmind"
  password            = var.db_password
  skip_final_snapshot = true
  storage_encrypted   = true
}
