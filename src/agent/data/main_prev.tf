resource "aws_lambda_function" "example" {
  function_name = "example_lambda"
  handler       = "app.handler"
  runtime       = "python3.11"
  memory_size   = 512
  timeout       = 30

  environment {
    variables = {
      LOG_LEVEL = "INFO"
      DB_HOST   = "db.example.com"
    }
  }
}
