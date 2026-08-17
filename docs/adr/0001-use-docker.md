# ADR-0001: Docker as the primary deployment platform

## Status

Accepted

## Context

The AI infrastructure consists of multiple independent services:
- Ollama
- Open WebUI
- JupyterLab
- code-server
- future AI tools

The environment should be reproducible and easy to migrate.

## Decision

All services will be deployed using Docker Compose.

Persistent data will always be stored outside containers.

## Consequences

Pros:
- Easy upgrades
- Reproducible deployments
- Simple backups
- Service isolation

Cons:
- Additional Docker layer
