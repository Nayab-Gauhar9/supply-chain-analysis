output "ec2_instance_id" {
  description = "ID of the Supply Chain ETL EC2 instance"
  value       = aws_instance.etl_server.id
}

output "ec2_public_ip" {
  description = "Public IP address of the Supply Chain ETL EC2 instance"
  value       = aws_instance.etl_server.public_ip
}

output "s3_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data.bucket
}