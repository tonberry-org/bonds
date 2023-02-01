terraform {
  backend "s3" {
    bucket         = "tonberry-terraform-backend"
    key            = "bonds.tfstate"
    region         = "us-west-2"
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region              = "us-west-2"
  allowed_account_ids = ["536213556125"]
}

