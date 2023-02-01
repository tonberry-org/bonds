resource "aws_cloudwatch_event_rule" "evnet_rule" {
  name                = local.project_name
  schedule_expression = "cron(0/5 13-23 ? * MON-FRI *)"
}


resource "aws_cloudwatch_event_target" "event_target" {
  rule      = aws_cloudwatch_event_rule.evnet_rule.name
  target_id = local.project_name

  input = <<DOC
{
}
DOC
  arn   = aws_lambda_function.coordinator.arn
}


resource "aws_lambda_permission" "coordinator_event_permission" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.coordinator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.evnet_rule.arn

}

resource "aws_cloudwatch_log_group" "coordinator_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.coordinator.function_name}"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "child_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.child.function_name}"
  retention_in_days = 7
}
