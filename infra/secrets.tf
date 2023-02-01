data "aws_ssm_parameter" "code" {
  name = "/tda/code"
}

data "aws_ssm_parameter" "client_id" {
  name = "/tda/client_id"
}

data "aws_ssm_parameter" "newrelic_account_id" {
  name = "/newrelic/account_id"
}
