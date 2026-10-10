# Network observations

Snapshot: 2026-10-10T00:00:00+02:00

confirmed = dated observation; unverified = code/documentation only; planned = explicit future intent.

Confirmation applies only to recorded fields at observation time, not service health or deployment.

Addresses and ports from static sources do not confirm listeners, DNS, routes or firewall rules. Missing fields mean not collected.

| id | address | bridge | ports | status | source |
| --- | --- | --- | --- | --- | --- |
| container/iza/code-server | — | — | 8443/tcp | unverified | compose/code-server/compose.yaml |
| container/iza/jupyter | — | — | 8888/tcp | unverified | compose/jupyter/compose.yaml |
| container/iza/ollama | — | — | 11434/tcp | unverified | compose/ollama/compose.yaml |
| container/iza/open-webui | — | — | 3000/tcp | unverified | compose/open-webui/compose.yaml |
| guest/dom/201 | 192.168.55.21/24 | vmbr0 | — | unverified | terraform/dom_mysql01.tf |
| guest/dom/202 | 192.168.55.25/24 | vmbr0 | — | unverified | terraform/dom_qdrant01.tf |
| guest/dom/203 | 192.168.55.26/24 | vmbr0 | — | unverified | terraform/dom_langfuse01.tf |
| guest/dom/204 | 192.168.55.27/24 | vmbr0 | — | unverified | terraform/dom_grafana01.tf |
| guest/dom/205 | 192.168.55.28/24 | vmbr0 | — | unverified | terraform/dom_cloudflare01.tf |
| guest/dtcode/102 | 192.168.55.10/24 | vmbr0 | — | unverified | terraform/dtcode_dns01.tf |
| guest/dtcode/103 | 192.168.55.20/24 | vmbr0 | — | unverified | terraform/dtcode_home01.tf |
| guest/dtcode/104 | 192.168.55.24/24 | vmbr0 | — | unverified | terraform/dtcode_bao01.tf |
| guest/dtcode/105 | 192.168.55.22/24 | vmbr0 | — | unverified | terraform/dtcode_forgejo01.tf |
| guest/dtcode/106 | 192.168.55.23/24 | vmbr0 | — | unverified | terraform/dtcode_npm01.tf |
| guest/dtcode/107 | 192.168.55.4/24 | vmbr0 | — | unverified | terraform/dtcode_tailscale_router.tf |
| host/dom | 192.168.55.3/24 | — | — | unverified | docs/network/NETWORK.md |
| host/dtcode | 192.168.55.6/24 | — | — | unverified | docs/network/NETWORK.md |
| host/iza | 192.168.55.7/24 | — | — | unverified | docs/network/NETWORK.md |
| host/qnap | 192.168.55.5/24 | — | — | unverified | docs/network/NETWORK.md |
