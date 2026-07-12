terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_ecr_repository" "api" {
  name = "invoice-api"
  force_delete = true
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/invoice-api-task"
  retention_in_days = 7
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "app" {
  name        = "invoice-api-app-sg"
  vpc_id      = data.aws_vpc.default.id
  description = "APP: accepts HTTP from the ALB"
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  from_port                    = 8000
  to_port                      = 8000
  ip_protocol                  = "tcp"
  referenced_security_group_id = aws_security_group.alb.id
}

resource "aws_vpc_security_group_egress_rule" "app_all" {
  security_group_id = aws_security_group.app.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "alb" {
  name        = "invoice-api-alb-sg"
  vpc_id      = data.aws_vpc.default.id
  description = "ALB: accepts HTTP from the internet"
}

resource "aws_vpc_security_group_ingress_rule" "alb_from_all" {
  security_group_id = aws_security_group.alb.id
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_egress_rule" "alb_all" {
  security_group_id = aws_security_group.alb.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_security_group" "rds" {
  name        = "invoice-api-rds-sg"
  vpc_id      = data.aws_vpc.default.id
  description = "RDS: accepts PostgreSQL traffic from the app"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_app" {
  security_group_id            = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.app.id
}

resource "aws_vpc_security_group_egress_rule" "rds_all" {
  security_group_id = aws_security_group.rds.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_db_instance" "rds_db" {
  allocated_storage      = 20
  db_name                = "invoiceapi"
  identifier             = "invoice-api-db"
  engine                 = "postgres"
  engine_version         = "17"
  instance_class         = "db.t4g.micro"
  username               = "invoiceapi"
  password               = var.db_password
  skip_final_snapshot    = true
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false
  multi_az               = false
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_lb" "alb" {
  name               = "invoice-api-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids
}

resource "aws_lb_target_group" "api" {
  name        = "invoice-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"
  health_check {
    enabled             = true
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    protocol            = "HTTP"
    path                = "/health"
  }
}

resource "aws_lb_listener" "listener" {
  port              = 80
  load_balancer_arn = aws_lb.alb.arn
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

data "aws_iam_role" "ecs_execution" {
  name = "ecsTaskExecutionRole"
}

resource "aws_ecs_cluster" "cluster" {
  name = "invoice-api-cluster"
}

resource "aws_ecs_task_definition" "app" {
  family                   = "invoice-api-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = data.aws_iam_role.ecs_execution.arn
  container_definitions = jsonencode([
    {
      name         = "app"
      image        = "${aws_ecr_repository.api.repository_url}:latest"
      portMappings = [{ containerPort = 8000 }]
      essential    = true
      environment = [
        {
          name  = "POSTGRES_URL"
          value = "postgresql+asyncpg://${aws_db_instance.rds_db.username}:${var.db_password}@${aws_db_instance.rds_db.address}:5432/${aws_db_instance.rds_db.db_name}"
        },
        {
          name  = "SECRET_KEY"
          value = var.secret_key
        },
        {
          name  = "REDIS_URL"
          value = "redis://localhost:6379/0"
        },
        {
          name  = "MAIL_SERVER"
          value = "mailserver"
        },
        {
          name  = "MAIL_PORT"
          value = "1025"
        },
        {
          name  = "EMAIL_FROM"
          value = "email@test.com"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    },
    {
      name         = "redis"
      image        = "redis:7-alpine"
      portMappings = [{ containerPort = 6379 }]
      essential    = true
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "invoice-api-task-service"
  cluster         = aws_ecs_cluster.cluster.id
  task_definition = aws_ecs_task_definition.app.id
  desired_count   = 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = true
  }
  load_balancer {
    container_name   = "app"
    container_port   = 8000
    target_group_arn = aws_lb_target_group.api.arn
  }
}