resource "aws_key_pair" "etl_server" {
  key_name   = "supply-chain-etl"
  public_key = file("C:/Users/Nayab/.ssh/supply-chain-etl.pub")
}

resource "aws_instance" "etl_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name = aws_key_pair.etl_server.key_name
  vpc_security_group_ids = [aws_security_group.etl_server.id]
  iam_instance_profile = aws_iam_instance_profile.etl_server.name

  tags = {
    Name = "supply-chain-etl"
  }
}
resource "aws_security_group" "etl_server" {
  name        = "supply-chain-etl-sg"
  description = "Security group for supply chain ETL server"

  ingress {
    description = "SSH from my IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["150.129.132.30/32"]
  }

  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "supply-chain-etl-sg"
  }
}
resource "aws_iam_instance_profile" "etl_server" {
  name = "supply-chain-etl-profile"
  role = aws_iam_role.etl_server.name
}