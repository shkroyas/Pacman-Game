# Import the existing EC2 instance exactly as it is now.
# After import succeeds, we'll add IAM role, EIP, and update user_data.
resource "aws_instance" "app" {
  ami                    = "ami-0b5358cc8c5df0b02"
  instance_type          = "t3.micro"
  key_name               = "pacman-ai-key"
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = "subnet-044e41a36308e8398"

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }

  tags = {
    Name = "pacman-ai-server"
  }
}

# New: Elastic IP (will be created on apply, not imported)
resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = {
    Name = "pacman-game-eip"
  }

  depends_on = [aws_instance.app]
}
