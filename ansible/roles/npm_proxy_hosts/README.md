# npm_proxy_hosts — comparison and opt-in GET adapter

Pure, observational comparison of `infrastructure_services` with an explicit
`npm_proxy_hosts_snapshot` list. Offline comparison remains the default.
An opt-in GET adapter and a dedicated read playbook are prepared; there are no
create/update/delete actions or changes to existing deployment playbooks.
Offline assert, set_fact and debug actions run on the Ansible controller.
Use a localhost-only play with `gather_facts: false` for offline execution;
running an ordinary remote play could still contact hosts outside this role.

The production inventory supplies the catalogue via `group_vars/all/services.yml`.
A standalone localhost play must explicitly load that file through `vars_files`.
The snapshot defaults to `null` and must be explicitly provided in offline mode.
With `npm_proxy_hosts_read_api: true`, a successful API read supplies it instead. An explicit `[]`
means a successfully obtained empty snapshot, not an API failure. Missing or
malformed input raises an error; do not convert a failed read into an empty list.
The comparison filter is exposed as:

```jinja2
{{ infrastructure_services | npm_proxy_hosts_compare(npm_proxy_hosts_snapshot) }}
```

Required snapshot fields per proxy: positive unique integer `id`, nonempty
`domain_names` list, `forward_scheme`, `forward_host`, integer `forward_port`,
boolean `enabled` and boolean `allow_websocket_upgrade`. Other fields are ignored
and never copied into the report. Snapshot values must be normalized to this
contract by the adapter after verifying the installed NPM response format.

Catalogue mapping is explicit:

| Catalogue | NPM | Comparison |
|---|---|---|
| `domain` | each entry in `domain_names` | All domains, regardless of order |
| `protocol` | `forward_scheme` | Exact match |
| `ip` | `forward_host` | Normalized address |
| `port` | `forward_port` | Integer match |
| `websocket` | `allow_websocket_upgrade` | Compared only when specified |
| `npm_enabled` | no direct mapping | Catalogue intent; never changes NPM `enabled` |
| no field | `enabled` | Disabled hosts cause a conflict |
| no field | `certificate_id`, `ssl_forced` | TLS is outside route comparison |

The adapter validates `certificate_id` (nonnegative integer) and `ssl_forced`
(boolean) when present, then omits them from the routing snapshot. They are not
required by the offline routing snapshot contract.

`npm_proxy_hosts_report` contains `snapshot_visibility` metadata, four comparison
lists and an `observed_endpoints` list.
Completeness is always `unverified`: owner permissions may limit the provided
snapshot, even with HTTP 200, an empty array or a matching `X-Total-Count`.
`missing` means absent from the visible snapshot, not proven absent from NPM.
Its reason is `no_visible_proxy_host`; no deletion or creation follows.

`observed_endpoints` exposes every proxy in the provided snapshot, including
disabled and unmanaged hosts, in snapshot order. Each entry contains only
`proxy_host_id` (`id`), `domains` (`domain_names`), `protocol` (`forward_scheme`),
`host` (`forward_host`), `port` (`forward_port`), `enabled` and `websocket`
(`allow_websocket_upgrade`). Values retain their snapshot form, including domain
case and trailing dots. This section can inform a manual review of missing
catalogue protocols; it does not update the catalogue or NPM, change comparison
rules, perform additional API requests or certify complete/current visibility.
Credentials and other snapshot fields are omitted.


| Status | Meaning |
|---|---|
| `matching` | Exactly one proxy contains the catalogue domain and its enabled route matches known IP, port, protocol and explicitly specified websocket setting. |
| `missing` | No visible proxy covers a known catalogue domain. Informational even when `npm_enabled: false`. |
| `conflict` | Duplicate domain, overlapping wildcard, multiple proxies, routing mismatch, disabled proxy or incomplete endpoint prevents an unambiguous match. |
| `unmanaged` | Catalogue service has no known domain, or a proxy domain is outside the catalogue. Unknown aliases on otherwise matching hosts appear here too. |

Every domain in a multi-domain host is inspected, regardless of order. Multiple
catalogue services can match one proxy if they share its routing parameters.
Domains compare case-insensitively with trailing dots removed. Wildcard matches
are conservatively conflicts, never proof of an exact route. Duplicate unknown
domains are reported as conflicts as well as remaining unmanaged.

`npm_enabled: false` never means delete, disable, ignore, or transfer ownership.
All catalogue entries are compared. Absent `websocket` means unspecified, rather
than false. `matching` compares routing only; it does not certify TLS, ACL,
custom locations, advanced configuration or ownership. No action is proposed.
Zabbix entries explicitly report `owner: zabbix_local_access`; that existing role
remains independent and unchanged. An existing Zabbix route can match even when
its catalogue flag is false, and duplicate/wrong routes report conflicts.
Grafana remains outside catalogue management and appears as unmanaged.

## Local tests

Catalogue ports accept integers and metadata-carrying integer subclasses passed
by Ansible to Python filters. Exact `type(port) is int` checks reject these
subclasses even when Ansible's `type_debug` reports `int`. Booleans, strings
(including numeric strings), floats and ports outside 1–65535 remain invalid;
an absent or null port retains its existing unspecified-endpoint meaning.
Regression tests reproduce this behavior with an integer subclass offline and
verify unchanged comparison results and strict validation at the range limits.

`tests/fixtures/npm/proxy_hosts.json` is synthetic data, not an infrastructure
export. It includes a multi-domain Forgejo proxy, a Zabbix route with the existing
role's marker/ACL, and an unmanaged Grafana route. Tests mutate copies to exercise
conflicts and block network calls. From the repository root:

```bash
python3 -B -m unittest discover -s tests -p 'test_npm_proxy_hosts*.py' -v
python3 -B -m unittest discover -s tests -p 'test_services_catalogue.py' -v
python3 -B scripts/validate_services.py
```

No infrastructure was deployed or queried. Python tests exercise the filter;
they are not an Ansible execution or syntax check.

## GET adapter and repository evidence

The user-confirmed API contract is `GET /api/nginx/proxy-hosts`,
`Authorization: Bearer TOKEN`, a direct JSON array of objects, and the required
`proxy_hosts` permission. There is no pagination in the checked API code.
The API can restrict results by owner. This confirmation does not establish
that a particular token sees all hosts or that the installed instance was
queried from this development laptop.

`library/npm_proxy_hosts_read.py` performs one GET with an existing bearer token;
it neither logs in nor issues/refreshes tokens. The URL must use exactly the
confirmed collection path. The adapter rejects unknown wrappers, wrong types,
missing routing fields, duplicate IDs, authorization errors, non-200 status,
wrong Content-Type, invalid JSON and transport/TLS errors. Pagination hints are
rejected defensively; an advertised total must equal the list length.
Neither that total nor the contract flag proves visibility of all owners.
The module returns `snapshot_scope: token_visible`, `completeness: unverified`;
the comparison report retains a warning for offline and API snapshots alike.
Set `npm_proxy_hosts_api_contract_verified: true` only after checking the
installed contract and token's `proxy_hosts` permission on iza. Visibility needs
independent review; a filtered successful response cannot be detected from the
array alone. Do not coerce missing booleans, ports or lists into defaults.

`npm_proxy_hosts_api_url` has no default endpoint. It must be a full verified
collection URL without userinfo, query or fragment. HTTPS uses system CA trust
and hostname verification; plaintext HTTP is accepted only for a literal
loopback address (e.g. an SSH tunnel). Environment proxies and redirects are
blocked, request timeout defaults to 30 seconds, and response size is bounded.

Authentication comes exclusively from `vault_npm_proxy_hosts_read_token`.
Store an already issued token in an encrypted Ansible Vault file outside Git,
using the existing Vault workflow. This role does not need a username/password.
Secret input, fetch and snapshot assignment tasks have `no_log: true`; the
module's token parameter also has `no_log`. Only required routing fields are
retained from the response; advanced configuration and other fields are dropped.
Failures stop execution and never fall back to the previous snapshot or `[]`.

## First safe run — on iza only, not performed here

1. Confirm on `iza` the installed NPM version, collection URL, bearer-token
   validity/permissions, field types, `application/json` response, and that the
   token has `proxy_hosts` permission; independently review owner restrictions
   and visibility, including the Zabbix route. An unpaginated list can be partial.
   Review existing administrator information or an already authenticated session;
   this adapter cannot perform login. Do not enable the contract flag blindly.
2. Prepare an encrypted external Vault file with
   `vault_npm_proxy_hosts_read_token` using `ansible-vault create`/`edit`.
   Do not pass the token through CLI arguments, environment dumps or plaintext
   files. Prepare a separate nonsecret settings file containing the verified
   `npm_proxy_hosts_api_url` and `npm_proxy_hosts_api_contract_verified: true`.
3. If NPM offers only HTTP on port 81, use an explicitly authorized SSH tunnel
   from `iza` to `npm01` (with existing host-key checking). A possible command,
   after access/port verification, is:

   ```bash
   ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:18081:127.0.0.1:81 npm01
   ```

   The collection URL then becomes
   `http://127.0.0.1:18081/api/nginx/proxy-hosts`; verify it, do not assume it.
   Alternatively use verified HTTPS with a trusted certificate. No TLS bypass
   or plaintext HTTP request from iza to the LAN NPM address is implemented.
4. From the repository's `ansible` directory on `iza`, first perform a static
   check, then the read. Substitute the paths to your external settings/Vault:

   ```bash
   ansible-playbook playbooks/npm-proxy-hosts-read.yml \
     --limit iza --syntax-check
   ansible-playbook playbooks/npm-proxy-hosts-read.yml \
     --limit iza \
     -e @/path/to/npm-read-settings.yml \
     -e @/path/to/npm-read-vault.yml \
     --ask-vault-pass
   ```

   The playbook targets only `iza` with local connection, no facts or privilege
   escalation. Both role and module enforce iza execution. Check mode is rejected
   by the playbook/role before any API request; use syntax-check for static review.
5. Review the comparison report. `matching` is not TLS/ACL/ownership validation;
   `missing`, `conflict` and `unmanaged` cause no reconciliation. Leave Zabbix
   under `zabbix_local_access` and stop the tunnel afterwards if one was used.

No infrastructure/API connections or Ansible execution were performed locally.
The prepared GET behavior is tested with fake responses, not verified in NPM.
