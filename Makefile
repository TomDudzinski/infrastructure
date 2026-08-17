SHELL := /bin/bash

COMPOSE_DIR := $(CURDIR)/compose
SERVICES := ollama open-webui code-server jupyter
DEFAULT_MODEL := llama3.2:1b

.PHONY: \
	help \
	up down restart status ps logs pull update \
	ollama open-webui code-server jupyter \
	health server-status gpu sensors disk docker-usage benchmark \
	backup backup-config backup-data backup-report \
	backup-list backup-check backup-check-full backup-retention \
	install-host-deps install-terraform

help:
	@echo "HomeLab Infrastructure commands"
	@echo ""
	@echo "Application lifecycle:"
	@echo "  make up                     Start all applications"
	@echo "  make down                   Stop all applications"
	@echo "  make restart                Restart all applications"
	@echo "  make status                 Show running container status"
	@echo "  make ps                     Alias for make status"
	@echo "  make logs                   Show recent logs for all applications"
	@echo "  make pull                   Pull the newest application images"
	@echo "  make update                 Pull images and recreate applications"
	@echo ""
	@echo "Individual applications:"
	@echo "  make ollama                 Start Ollama"
	@echo "  make open-webui             Start Open WebUI"
	@echo "  make code-server            Start code-server"
	@echo "  make jupyter                Start JupyterLab"
	@echo ""
	@echo "Health and diagnostics:"
	@echo "  make health                 Run application health checks"
	@echo "  make server-status          Show the AI server status"
	@echo "  make gpu                    Show NVIDIA GPU status"
	@echo "  make sensors                Show hardware sensor readings"
	@echo "  make disk                   Show disk usage"
	@echo "  make docker-usage           Show Docker disk usage"
	@echo "  make benchmark              Benchmark the default Ollama model"
	@echo "  make benchmark MODEL=name   Benchmark a selected Ollama model"
	@echo ""
	@echo "Backup:"
	@echo "  make backup                 Run the complete backup workflow"
	@echo "  make backup-config          Back up configuration"
	@echo "  make backup-data            Back up projects and application data"
	@echo "  make backup-report          Create a backup and system report"
	@echo "  make backup-list            List Restic snapshots"
	@echo "  make backup-check           Check the Restic repository"
	@echo "  make backup-check-full      Check all Restic repository data"
	@echo "  make backup-retention       Apply the Restic retention policy"
	@echo ""
	@echo "Host setup:"
	@echo "  make install-host-deps      Install required host packages"
	@echo "  make install-terraform      Install Terraform from the HashiCorp repository"

# Application lifecycle

up:
	@for service in $(SERVICES); do \
		echo "Starting $$service..."; \
		docker compose -f "$(COMPOSE_DIR)/$$service/compose.yaml" up -d || exit 1; \
	done

down:
	@for service in $(SERVICES); do \
		echo "Stopping $$service..."; \
		docker compose -f "$(COMPOSE_DIR)/$$service/compose.yaml" down || exit 1; \
	done

restart:
	@$(MAKE) down
	@$(MAKE) up

status:
	@docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"

ps: status

logs:
	@for service in $(SERVICES); do \
		echo ""; \
		echo "===== $$service ====="; \
		docker compose -f "$(COMPOSE_DIR)/$$service/compose.yaml" logs --tail=30; \
	done

pull:
	@for service in $(SERVICES); do \
		echo "Pulling $$service..."; \
		docker compose -f "$(COMPOSE_DIR)/$$service/compose.yaml" pull || exit 1; \
	done

update:
	@$(MAKE) pull
	@$(MAKE) up

# Individual applications

ollama:
	@docker compose -f "$(COMPOSE_DIR)/ollama/compose.yaml" up -d

open-webui:
	@docker compose -f "$(COMPOSE_DIR)/open-webui/compose.yaml" up -d

code-server:
	@docker compose -f "$(COMPOSE_DIR)/code-server/compose.yaml" up -d

jupyter:
	@docker compose -f "$(COMPOSE_DIR)/jupyter/compose.yaml" up -d

# Health and diagnostics

health:
	@./scripts/healthcheck.sh

server-status:
	@./scripts/server-status.sh

gpu:
	@nvidia-smi

sensors:
	@sensors

disk:
	@df -h / /opt/ai

docker-usage:
	@docker system df

benchmark:
	@./scripts/benchmark-ollama.sh "$(or $(MODEL),$(DEFAULT_MODEL))"

# Backup

backup:
	@./scripts/backup-all.sh

backup-config:
	@./scripts/backup-config.sh

backup-data:
	@./scripts/backup-data.sh

backup-report:
	@./scripts/backup-report.sh

backup-list:
	@bash -c 'source config/backup.env && restic snapshots'

backup-check:
	@bash -c 'source config/backup.env && restic check'

backup-check-full:
	@bash -c 'source config/backup.env && restic check --read-data'

backup-retention:
	@./scripts/backup-retention.sh

# Host setup

install-host-deps:
	@sudo ./scripts/install-host-dependencies.sh

install-terraform:
	@sudo ./scripts/install-terraform.sh
