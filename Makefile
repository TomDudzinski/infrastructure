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

.PHONY: server-status

server-status:
	@./scripts/server-status.sh
