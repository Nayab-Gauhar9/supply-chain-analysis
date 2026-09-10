resource "aws_iam_role" "etl_server" {
  name = "supply-chain-etl-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ec2.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })
}
resource "aws_iam_policy" "etl_s3_access" {
  name        = "supply-chain-etl-s3-access"
  description = "Allow the ETL server to access raw data in the supply chain S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:ListBucket"
        ]

        Resource = aws_s3_bucket.raw_data.arn
      },
      {
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = "${aws_s3_bucket.raw_data.arn}/*"
      }
    ]
  })
}
resource "aws_iam_role_policy_attachment" "etl_s3_access" {
  role       = aws_iam_role.etl_server.name
  policy_arn = aws_iam_policy.etl_s3_access.arn
}