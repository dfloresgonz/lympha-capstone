terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "= 6.0.0"
    }
  }
  backend "s3" {}
}

provider "aws" {

  # default_tags {
  #   tags = {
  #     PROJECT     = upper(var.project_name)
  #     OWNER       = upper(var.owner)
  #     MODULE      = upper(var.module)
  #     ENVIRONMENT = upper(var.env)
  #     SERVICE     = format("%s-%s-%s-%s-%s-%s", var.project_name, var.repo_type, var.module, var.sub_module, var.service_type, var.version_project)
  #   }
  # }
}

provider "aws" {
  alias = "build"
}
