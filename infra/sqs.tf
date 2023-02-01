resource "aws_sqs_queue" "queue" {
  name                       = local.project_name
  redrive_policy             = "{\"deadLetterTargetArn\":\"${aws_sqs_queue.dlq.arn}\",\"maxReceiveCount\":5}"
  visibility_timeout_seconds = 300
}

resource "aws_sqs_queue" "dlq" {
  name = "${local.project_name}-dlq"
}



resource "aws_sqs_queue_policy" "queue_policy" {
  queue_url = aws_sqs_queue.queue.id

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Id": "sqspolicy",
  "Statement": [
    {
      "Sid": "First",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "sqs:SendMessage",
      "Resource": "${aws_sqs_queue.queue.arn}",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "${aws_lambda_function.coordinator.arn}"
        }
      }
    }
  ]
}
POLICY
}
