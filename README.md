# Iza AI Infrastructure

Infrastructure configuration for the dedicated local LLM server.

## Services

- Ollama
- Open WebUI
- code-server

## Data locations

Persistent data is stored outside the Git repository:

- `/opt/ai/data`
- `/opt/ai/models`
- `/opt/ai/cache`
- `/opt/ai/notebooks`
- `/opt/ai/datasets`

## Common commands

```bash
make help
make up
make down
make restart
make status
make logs
make pull
make update
make health
