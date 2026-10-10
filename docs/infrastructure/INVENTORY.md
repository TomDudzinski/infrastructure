# Inventory

Snapshot: 2026-10-10T00:00:00+02:00

confirmed = dated observation; unverified = code/documentation only; planned = explicit future intent.

Confirmation applies only to recorded fields at observation time, not service health or deployment.

| id | name | host | kind | vm_id | status | source | observed_at | cores | memory_bytes | disk_bytes | state | image |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| container/iza/code-server | code-server | iza | container | — | unverified | compose/code-server/compose.yaml | — | — | — | — | — | lscr.io/linuxserver/code-server:latest |
| container/iza/jupyter | jupyter | iza | container | — | unverified | compose/jupyter/compose.yaml | — | — | — | — | — | iza-jupyter:latest |
| container/iza/ollama | ollama | iza | container | — | unverified | compose/ollama/compose.yaml | — | — | — | — | — | ollama/ollama:latest |
| container/iza/open-webui | open-webui | iza | container | — | unverified | compose/open-webui/compose.yaml | — | — | — | — | — | ghcr.io/open-webui/open-webui:v0.11.0 |
| guest/dom/201 | mysql01 | dom | vm | 201 | unverified | terraform/dom_mysql01.tf | — | 2 | 4294967296 | 68719476736 | — | — |
| guest/dom/202 | qdrant01 | dom | vm | 202 | unverified | terraform/dom_qdrant01.tf | — | 2 | 2147483648 | 21474836480 | — | — |
| guest/dom/203 | langfuse01 | dom | vm | 203 | unverified | terraform/dom_langfuse01.tf | — | 4 | 17179869184 | 107374182400 | — | — |
| guest/dom/204 | grafana01 | dom | vm | 204 | unverified | terraform/dom_grafana01.tf | — | 2 | 4294967296 | 32212254720 | — | — |
| guest/dom/205 | cloudflare01 | dom | vm | 205 | unverified | terraform/dom_cloudflare01.tf | — | 1 | 1073741824 | 10737418240 | — | — |
| guest/dtcode/102 | dns01 | dtcode | lxc | 102 | unverified | terraform/dtcode_dns01.tf | — | 2 | 2147483648 | 21474836480 | — | — |
| guest/dtcode/103 | home01 | dtcode | vm | 103 | unverified | terraform/dtcode_home01.tf | — | 1 | 1073741824 | 34359738368 | — | — |
| guest/dtcode/104 | bao01 | dtcode | vm | 104 | unverified | terraform/dtcode_bao01.tf | — | 2 | 2147483648 | 34359738368 | — | — |
| guest/dtcode/105 | forgejo01 | dtcode | vm | 105 | unverified | terraform/dtcode_forgejo01.tf | — | 1 | 1073741824 | 34359738368 | — | — |
| guest/dtcode/106 | npm01 | dtcode | vm | 106 | unverified | terraform/dtcode_npm01.tf | — | 1 | 1073741824 | 34359738368 | — | — |
| guest/dtcode/107 | tailscale-router | dtcode | vm | 107 | unverified | terraform/dtcode_tailscale_router.tf | — | 1 | 536870912 | 34359738368 | — | — |
| host/dom | dom | dom | host | — | unverified | docs/network/NETWORK.md | — | — | — | — | — | — |
| host/dtcode | dtcode | dtcode | host | — | unverified | docs/network/NETWORK.md | — | — | — | — | — | — |
| host/iza | iza | iza | host | — | unverified | docs/network/NETWORK.md | — | — | — | — | — | — |
| host/qnap | qnap | qnap | host | — | unverified | docs/network/NETWORK.md | — | — | — | — | — | — |
