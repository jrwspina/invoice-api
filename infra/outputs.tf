output "alb_url" {
    value = "http://${aws_lb.alb.dns_name}"
}