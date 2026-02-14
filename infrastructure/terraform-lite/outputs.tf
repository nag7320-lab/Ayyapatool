# =============================================================================
# Aypa TaxAI - Outputs
# =============================================================================

output "public_ip" {
  description = "Public IP of the server"
  value       = aws_eip.aypa.public_ip
}

output "app_url" {
  description = "URL to access the application"
  value       = var.app_domain != "" ? "http://${var.app_domain}" : "http://${aws_eip.aypa.public_ip}"
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh -i aypa-key.pem ec2-user@${aws_eip.aypa.public_ip}"
}

output "ssh_key_file" {
  description = "Path to the SSH private key"
  value       = local_file.ssh_private_key.filename
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost"
  value       = "~$10-15/month (t3.small in ap-south-1)"
}
