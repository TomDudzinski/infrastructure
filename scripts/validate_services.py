"""Validate the passive Ansible service catalogue locally; no network or Ansible."""
import argparse
import ipaddress
import json
from pathlib import Path
import re

DEFAULT_PATH = Path(__file__).resolve().parents[1] / 'ansible/inventories/production/group_vars/all/services.yml'


def unique_mapping(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate key: {key}')
        result[key] = value
    return result


def load_catalogue(path=DEFAULT_PATH):
    # JSON is a YAML subset, avoiding a PyYAML dependency for offline checks.
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_mapping)


def validate_catalogue(data):
    if not isinstance(data, dict) or set(data) != {'infrastructure_services'}:
        raise ValueError('Expected only infrastructure_services at the top level')
    services = data['infrastructure_services']
    if not isinstance(services, dict) or not services:
        raise ValueError('Expected a nonempty service mapping')
    domains = set()
    required = {'name', 'host', 'domain', 'ip', 'port', 'protocol', 'npm_enabled', 'source'}
    optional = {'websocket'}
    for key, service in services.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]*', key):
            raise ValueError(f'Invalid service identifier: {key}')
        if key == 'grafana':
            raise ValueError('Grafana must remain outside this NPM catalogue')
        if not isinstance(service, dict) or not required <= set(service) or set(service) - required - optional:
            raise ValueError(f'{key}: unexpected or missing fields')
        for field in ('name', 'host', 'source'):
            if not isinstance(service[field], str) or not service[field].strip():
                raise ValueError(f'{key}: invalid {field}')
        if type(service['npm_enabled']) is not bool:
            raise ValueError(f'{key}: npm_enabled must be boolean')
        if 'websocket' in service and type(service['websocket']) is not bool:
            raise ValueError(f'{key}: websocket must be boolean')
        domain = service['domain']
        if domain is not None:
            if not isinstance(domain, str):
                raise ValueError(f'{key}: invalid domain')
            normalized = domain.rstrip('.').lower()
            if len(normalized) > 253 or '.' not in normalized or any(
                not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                for label in normalized.split('.')
            ):
                raise ValueError(f'{key}: invalid domain')
            if normalized in domains:
                raise ValueError(f'{key}: duplicate domain {domain}')
            domains.add(normalized)
        if service['ip'] is not None:
            if not isinstance(service['ip'], str):
                raise ValueError(f'{key}: IP must be a string')
            try:
                ipaddress.ip_address(service['ip'])
            except ValueError as exc:
                raise ValueError(f'{key}: invalid IP') from exc
        port = service['port']
        if port is not None and (type(port) is not int or not 1 <= port <= 65535):
            raise ValueError(f'{key}: port must be an integer in 1..65535')
        if service['protocol'] not in (None, 'http', 'https'):
            raise ValueError(f'{key}: protocol must be http, https or null')
        if service['npm_enabled']:
            if any(service[field] is None for field in ('domain', 'ip', 'port', 'protocol')):
                raise ValueError(f'{key}: NPM requires a complete endpoint')
            if key == 'zabbix':
                raise ValueError('Zabbix NPM ownership belongs to zabbix_local_access')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    try:
        data = load_catalogue(args.path)
        validate_catalogue(data)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Invalid service catalogue: {exc}\n')
    print(f'Valid service catalogue: {len(data["infrastructure_services"])} services (offline)')


if __name__ == '__main__':
    main()
