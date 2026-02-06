resource "aws_lambda_function" "example" {
  function_name = "example_lambda"
  handler       = "app.handler"
  runtime       = "python3.11"
  memory_size   = 128  # Reduced memory might be the cause
  timeout       = 30

  environment {
    variables = {
      LOG_LEVEL = "DEBUG"
      DB_HOST   = "db.example.com"
      # MISSING_VAR = "was_here_before"
    }
  }
}
