resource "aws_dynamodb_table" "config" {
  name     = "${local.project_name}_config"
  hash_key = "bond"

  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "bond"
    type = "S"
  }

}
