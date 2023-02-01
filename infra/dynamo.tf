data "aws_dynamodb_table" "constituents" {
  name = "constituents"
}

resource "aws_dynamodb_table" "config" {
  name     = "${local.project_name}_config"
  hash_key = "indicator"

  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "indicator"
    type = "S"
  }

}

resource "aws_dynamodb_table" "primary" {
  name      = local.project_name
  hash_key  = "indicator"
  range_key = "date"

  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "indicator"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }
}
