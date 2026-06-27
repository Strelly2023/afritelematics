terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.name}"
  retention_in_days = 30
}

resource "aws_kms_key" "novatrust_signing" {
  description             = "NovaTrust audit signing key"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "aws_kms_alias" "novatrust_signing" {
  name          = "alias/${var.name}-novatrust-signing"
  target_key_id = aws_kms_key.novatrust_signing.key_id
}

resource "aws_security_group" "alb" {
  name        = "${var.name}-alb"
  description = "ALB ingress"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service" {
  name        = "${var.name}-service"
  description = "ECS service access"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name        = "${var.name}-db"
  description = "RDS access from ECS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.service.id]
  }
}

resource "aws_db_subnet_group" "db" {
  name       = "${var.name}-db"
  subnet_ids = var.private_subnet_ids
}

resource "aws_db_instance" "postgres" {
  identifier             = var.name
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  db_name                = "novatech"
  username               = "novatech"
  password               = var.database_password
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true
}

resource "aws_lb" "api" {
  name               = var.name
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "api" {
  name        = var.name
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    path = "/health"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_ecs_cluster" "main" {
  name = var.name
}

resource "aws_iam_role" "task_execution" {
  name = "${var.name}-task-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role" "task" {
  name = "${var.name}-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "task_kms" {
  name = "${var.name}-task-kms"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kms:Sign",
          "kms:GetPublicKey",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.novatrust_signing.arn
      }
    ]
  })
}

resource "aws_ecs_task_definition" "api" {
  family                   = var.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn             = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.container_image
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = concat([
        { name = "STRIPE_LIVE_MODE", value = "true" },
        { name = "NOVAPAY_EVENT_BUS_BACKEND", value = var.event_bus_backend },
        { name = "NOVAPAY_EVENT_BUS_KAFKA_BROKERS", value = var.event_bus_kafka_brokers },
        { name = "NOVAPAY_REGION", value = var.novapay_region },
        { name = "NOVATRUST_SIGNING_PROVIDER", value = var.novatrust_signing_provider },
        {
          name  = "NOVATRUST_KMS_SIGNING_ENABLED"
          value = tostring(var.novatrust_kms_signing_enabled)
        },
        {
          name  = "NOVATRUST_KMS_SIGNING_ALGORITHM"
          value = var.novatrust_kms_signing_algorithm
        },
        { name = "NOVATRUST_KMS_KEY_ID", value = aws_kms_key.novatrust_signing.key_id },
        { name = "NOVATRUST_KEY_ROTATION_ENABLED", value = "true" },
        {
          name  = "NOVAPAY_CBDC_LIVE_ENABLED"
          value = tostring(var.novapay_cbdc_live_enabled)
        },
        { name = "NOVAPAY_CBDC_NETWORK", value = var.novapay_cbdc_network },
        { name = "NOVAPAY_ROLLOUT_MODE", value = var.novapay_rollout_mode },
        { name = "NOVAPAY_PRIMARY_CORRIDOR", value = var.novapay_primary_corridor },
        {
          name  = "NOVAPAY_CORRIDORS"
          value = join(",", var.novapay_corridors)
        },
        { name = "NOVAPAY_SETTLEMENT_MODE", value = var.novapay_settlement_mode },
        {
          name  = "NOVAPAY_MOBILE_MONEY_LIVE_ENABLED"
          value = tostring(var.novapay_mobile_money_live_enabled)
        },
        { name = "NOVAPAY_COMPLIANCE_PROVIDER", value = var.novapay_compliance_provider },
        {
          name  = "NOVAPAY_COMPLIANCE_LIVE_ENABLED"
          value = tostring(var.novapay_compliance_live_enabled)
        },
        {
          name  = "DATABASE_URL"
          value = "postgresql://novatech:${var.database_password}@${aws_db_instance.postgres.address}:5432/novatech"
        }
      ], [
        for key, value in var.novapay_env_vars : {
          name  = key
          value = value
        }
      ])
      secrets = concat(
        [
          { name = "STRIPE_API_KEY", valueFrom = var.stripe_api_key_secret_arn }
        ],
        [
          for key, value in var.novapay_secret_arns : {
            name      = key
            valueFrom = value
          }
        ]
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = var.name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [aws_security_group.service.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
}
