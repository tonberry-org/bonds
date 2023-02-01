resource "aws_lambda_function" "coordinator" {
  function_name    = "${local.project_name}_coordinator"
  role             = aws_iam_role.lambda.arn
  filename         = "../dist/${local.project_name}.zip"
  source_code_hash = filebase64sha256("../dist/${local.project_name}.zip")
  handler          = "newrelic_lambda_wrapper.handler"
  runtime          = "python3.9"
  publish          = true
  timeout          = 60

  environment {
    variables = {
      QUEUE_NAME       = aws_sqs_queue.queue.name
      CONFIG_DDB_TABLE = aws_dynamodb_table.config.name
      # For the instrumentation handler to invoke your real handler, we need this value
      NEW_RELIC_LAMBDA_HANDLER = "${local.project_name}.coordinator_lambda_function.lambda_handler"
      NEW_RELIC_ACCOUNT_ID     = data.aws_ssm_parameter.newrelic_account_id.value
      # Enable NR Lambda extension if the telemetry data are ingested via lambda extension
      NEW_RELIC_LAMBDA_EXTENSION_ENABLED = true
      # Enable Distributed tracing for in-depth monitoring of transactions in lambda (Optional)
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }

  layers = ["arn:aws:lambda:us-west-2:451483290750:layer:NewRelicPython39:36"]
}

resource "aws_lambda_function" "child" {
  function_name    = local.project_name
  role             = aws_iam_role.lambda.arn
  filename         = "../dist/${local.project_name}.zip"
  source_code_hash = filebase64sha256("../dist/${local.project_name}.zip")
  handler          = "newrelic_lambda_wrapper.handler"
  runtime          = "python3.9"
  publish          = true
  timeout          = 60

  environment {
    variables = {
      DDB_TABLE : aws_dynamodb_table.primary.name
      CLIENT_ID : data.aws_ssm_parameter.client_id.value
      # For the instrumentation handler to invoke your real handler, we need this value
      NEW_RELIC_LAMBDA_HANDLER = "${local.project_name}.child_lambda_function.lambda_handler"
      NEW_RELIC_ACCOUNT_ID     = data.aws_ssm_parameter.newrelic_account_id.value
      # Enable NR Lambda extension if the telemetry data are ingested via lambda extension
      NEW_RELIC_LAMBDA_EXTENSION_ENABLED = true
      # Enable Distributed tracing for in-depth monitoring of transactions in lambda (Optional)
      NEW_RELIC_DISTRIBUTED_TRACING_ENABLED = true
    }
  }

  layers = ["arn:aws:lambda:us-west-2:451483290750:layer:NewRelicPython39:36"]
}


resource "aws_lambda_event_source_mapping" "example" {
  event_source_arn = aws_sqs_queue.queue.arn
  function_name    = aws_lambda_function.child.arn
}


data "aws_lambda_function" "new_relic" {
  function_name = "newrelic-log-ingestion"
}
resource "aws_cloudwatch_log_subscription_filter" "coordinator_log_subscription_filter" {
  name            = "logdna-logfilter"
  log_group_name  = aws_cloudwatch_log_group.coordinator_log_group.name
  filter_pattern  = ""
  destination_arn = data.aws_lambda_function.new_relic.arn
}

resource "aws_cloudwatch_log_subscription_filter" "log_subscription_filter" {
  name            = "logdna-logfilter"
  log_group_name  = aws_cloudwatch_log_group.child_log_group.name
  filter_pattern  = ""
  destination_arn = data.aws_lambda_function.new_relic.arn
}
