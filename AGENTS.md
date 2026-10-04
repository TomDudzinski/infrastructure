Create an AGENTS.md file for this repository.

For this task:
- Create ONLY AGENTS.md.
- Do not modify any other files.
- Do not commit or push anything.
- Do not run or deploy any infrastructure.
- Do not connect to any remote hosts or services.

Important environment rule:
This laptop is ONLY a development environment for writing and reviewing infrastructure code.

Nothing is deployed or executed against the real infrastructure from this machine.

Codex may inspect, edit and statically validate code locally, but must never:
- run terraform apply or destroy
- run Ansible against real hosts
- SSH to infrastructure hosts
- connect to Proxmox or infrastructure services
- restart or modify services
- perform deployments

Communication:
- Communicate with me in Polish.
- Explain in Polish what you are doing and what you changed.
- Code, configuration, variable names and technical identifiers should be in English.
- Never claim something works in the real infrastructure if it was only checked locally.

General rules:
- Preserve existing working infrastructure.
- Prefer small incremental changes.
- Terraform manages VMs/infrastructure.
- Ansible manages host and service configuration.
- Never change existing VM IDs, IPs, hostnames or deployed resources without explicit approval.
- Never store plaintext secrets in Git.
- Use the existing Ansible Vault approach for secrets.
- Prefer reusable Ansible roles instead of duplicated configuration.
- Host-specific configuration should use inventory, host_vars or group_vars.
- Do not introduce unnecessary abstractions.

Documentation:
Documentation is part of every infrastructure change.

When relevant:
- update INVENTORY.md for hosts, VMs, IPs and services
- update STATUS.md for infrastructure status
- update README/docs when architecture or procedures change

Never describe something as deployed only because its code exists.

Expected workflow:

inspect
-> propose change
-> edit code
-> safe local/static validation
-> review diff
-> update documentation
-> report results in Polish
-> wait for approval

Do not commit or push unless I explicitly request it.

Create a concise and practical AGENTS.md containing these rules.

After creating it, show me its contents in Polish summary, but do nothing else.