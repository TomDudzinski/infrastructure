SHELL := /bin/bash

COMPOSE_DIR := $(CURDIR)/compose
SERVICES := ollama open-webui code-server jupyter

.PHONY: help up down restart status logs pull update ps ollama open-webui code-server

help:
	@echo "Available commands:"
	@echo "  make up            Start all services"
	@echo "  make down          Stop all services"
	@echo "  make restart       Restart all services"
	@echo "  make status        Show container status"
	@echo "  make logs          Show recent logs"
	@echo "  make pull          Pull newest images"
	@echo "  make update        Pull and recreate services"
	@echo "  make ollama        Start Ollama"
	@echo "  make open-webui    Start Open WebUI"
	@echo "  make code-server   Start code-server"
	@echo "  make install-host-deps       Install required host packages"
	@echo "  make server-status           Show server status"
	@echo "  make gpu                     Show NVIDIA GPU status"
	@echo "  make sensors                 Show hardware sensor readings"
	@echo "  make disk                    Show disk usage"
	@echo "  make docker-usage            Show Docker disk usage"
	@echo "  make benchmark               Benchmark the default Ollama model"
	@echo "  make benchmark MODEL=name    Benchmark a selected Ollama model"

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

ollama:
	@docker compose -f "$(COMPOSE_DIR)/ollama/compose.yaml" up -d

open-webui:
	@docker compose -f "$(COMPOSE_DIR)/open-webui/compose.yaml" up -d

code-server:
	@docker compose -f "$(COMPOSE_DIR)/code-server/compose.yaml" up -d
jupyter:
	@docker compose -f "$(COMPOSE_DIR)/jupyter/compose.yaml" up -d

.PHONY: health

health:
	@./scripts/healthcheck.sh

.PHONY: install-host-deps

install-host-deps:
	@sudo ./scripts/install-host-dependencies.sh

.PHONY: server-status gpu benchmark sensors disk docker-usage

server-status:
	@./scripts/server-status.sh

gpu:
	@nvidia-smi

benchmark:
	@./scripts/benchmark-ollama.sh "$(or $(MODEL),llama3.2:1b)"

sensors:
	@sensors

disk:
	@df -h / /opt/ai

docker-usage:
	@docker system df

.PHONY: backup backup-config backup-data backup-report backup-list backup-check backup-check-full

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
