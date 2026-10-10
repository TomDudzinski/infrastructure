#!/usr/bin/env python3
"""Read-only, host-local collectors and offline Markdown inventory reports."""
import argparse
import datetime as dt
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import subprocess

STATUSES = {'confirmed', 'unverified', 'planned'}
FIELDS = {'id', 'kind', 'name', 'host', 'source', 'status', 'observed_at',
          'vm_id', 'address', 'bridge', 'cores', 'memory_bytes', 'disk_bytes',
          'state', 'image', 'ports'}
TEXT = re.compile(r'^[A-Za-z0-9_./:@+ -]{1,200}$')
SENSITIVE = re.compile(r'(?i)(password|passwd|token|secret|private|credential|bearer|ssh-rsa|ssh-ed25519)')


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def date(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    return parsed


def validate(data):
    if set(data) != {'schema_version', 'collected_at', 'coverage', 'records'} or data['schema_version'] != 1:
        raise ValueError('Unsupported snapshot schema')
    date(data['collected_at'])
    if not isinstance(data['coverage'], dict) or not isinstance(data['records'], list):
        raise ValueError('Invalid snapshot containers')
    for key, value in data['coverage'].items():
        if not TEXT.fullmatch(key) or SENSITIVE.search(key) or value not in {'complete', 'partial', 'unavailable', 'static'}:
            raise ValueError('Invalid coverage')
    seen = set()
    for row in data['records']:
        if not isinstance(row, dict) or set(row) - FIELDS:
            raise ValueError('Unknown record fields (secrets and raw payloads are prohibited)')
        if not {'id', 'kind', 'name', 'host', 'source', 'status'} <= set(row):
            raise ValueError('Missing record fields')
        if row['status'] not in STATUSES or row['kind'] not in {'host', 'vm', 'lxc', 'container', 'interface'}:
            raise ValueError('Invalid status or kind')
        if row['id'] in seen:
            raise ValueError('Duplicate record identity')
        seen.add(row['id'])
        for key, value in row.items():
            if key in {'vm_id', 'cores', 'memory_bytes', 'disk_bytes'}:
                if type(value) is not int or value < 0:
                    raise ValueError('Invalid numeric field')
            elif key == 'address':
                ipaddress.ip_interface(value)
            elif key == 'observed_at':
                if date(value) > date(data['collected_at']):
                    raise ValueError('Observation newer than snapshot')
            elif not isinstance(value, str) or not TEXT.fullmatch(value) or SENSITIVE.search(value):
                raise ValueError('Unsafe text field; review and sanitize input')
        if row['status'] == 'confirmed' and 'observed_at' not in row:
            raise ValueError('Confirmed observation requires timestamp')
    return data


def read(path):
    return validate(json.loads(Path(path).read_text()))


def write_json(path, data):
    validate(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves history and prevents symlink overwrites.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write('\n')


def run(args):
    # Never persist stderr, environments, or raw command responses.
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=30).stdout


def collect(mode, node=None):
    now, host = timestamp(), socket.gethostname()
    records, coverage = [], {}

    def record(kind, name, identity, **attrs):
        records.append(dict(id=identity, kind=kind, name=name, host=host,
                            source=mode, status='confirmed', observed_at=now, **attrs))

    if mode == 'linux':
        memory = next(int(line.split()[1]) * 1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:'))
        record('host', host, f'host/{host}', cores=os.cpu_count() or 0, memory_bytes=memory)
        coverage[f'{host}/linux'] = 'complete'
        try:
            for interface in json.loads(run(['ip', '-j', 'address', 'show'])):
                for addr in interface.get('addr_info', []):
                    if addr.get('family') in {'inet', 'inet6'}:
                        address = f"{addr['local']}/{addr['prefixlen']}"
                        record('interface', interface['ifname'], f"interface/{host}/{interface['ifname']}/{addr['local']}", address=address)
            coverage[f'{host}/network'] = 'complete'
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            coverage[f'{host}/network'] = 'unavailable'
    elif mode == 'proxmox':
        coverage[f'{host}/proxmox'] = 'unavailable'
        try:
            # pvesh executes on the Proxmox node; no HTTP/SSH client or token.
            rows = json.loads(run(['pvesh', 'get', '/cluster/resources', '--type', 'vm', '--output-format', 'json']))
            for row in rows:
                if row.get('type') not in {'qemu', 'lxc'} or (node and row.get('node') != node):
                    continue
                kind = 'vm' if row['type'] == 'qemu' else 'lxc'
                resource_node, vmid = row['node'], int(row['vmid'])
                record(kind, row.get('name') or f'{kind}-{vmid}', f"guest/{resource_node}/{vmid}", vm_id=vmid,
                       state=row['status'], cores=int(row.get('maxcpu', 0)),
                       memory_bytes=int(row.get('maxmem', 0)), disk_bytes=int(row.get('maxdisk', 0)))
                records[-1]['host'] = resource_node
            coverage[f'{host}/proxmox'] = 'complete'
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
            records.clear()
    elif mode == 'docker':
        coverage[f'{host}/docker'] = 'unavailable'
        try:
            # Explicit socket bypasses DOCKER_HOST/context and prevents remote connections.
            output = run(['docker', '--host', 'unix:///var/run/docker.sock', 'container', 'ls', '-a',
                          '--format', '{{json .}}'])
            for line in output.splitlines():
                row = json.loads(line)
                # Omit Command, Labels, environment, mounts, logs and inspect payloads.
                record('container', row['Names'], f"container/{host}/{row['Names']}",
                       image=row['Image'], state=row['State'])
            coverage[f'{host}/docker'] = 'complete'
        except (OSError, subprocess.SubprocessError, ValueError, KeyError):
            records.clear()
    return validate(dict(schema_version=1, collected_at=now, coverage=coverage, records=records))


def compare(current, previous):
    before = {row['id']: row for row in previous['records']} if previous else {}
    after = {row['id']: row for row in current['records']}
    changes = []
    for identity in sorted(before.keys() | after.keys()):
        if identity not in before:
            changes.append(f'Added observation: {identity}')
        elif identity not in after:
            changes.append(f'Absent from new snapshot (removal unverified): {identity}')
        else:
            keys = (before[identity].keys() | after[identity].keys()) - {'observed_at'}
            changed = sorted(key for key in keys if before[identity].get(key) != after[identity].get(key))
            if changed:
                changes.append(f'Changed {identity}: ' + ', '.join(changed))
    return changes


def table(rows, fields):
    lines = ['| ' + ' | '.join(fields) + ' |', '| ' + ' | '.join('---' for _ in fields) + ' |']
    for row in sorted(rows, key=lambda item: item['id']):
        lines.append('| ' + ' | '.join(str(row.get(field, '—')) for field in fields) + ' |')
    return '\n'.join(lines) + '\n'


def report(data, previous, output):
    validate(data)
    if previous:
        validate(previous)
        if date(previous['collected_at']) >= date(data['collected_at']):
            raise ValueError('Previous snapshot must be older')
    output = Path(output)
    history = output / 'history'
    history.mkdir(parents=True, exist_ok=True)
    identity = date(data['collected_at']).astimezone(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    snapshot = history / f'{identity}.json'
    if snapshot.exists():
        if read(snapshot) != data:
            raise ValueError('History timestamp collision')
    else:
        write_json(snapshot, data)
    changes = compare(data, previous)
    header = f"Snapshot: {data['collected_at']}\n\nconfirmed = dated observation; unverified = code/documentation only; planned = explicit future intent.\n\nConfirmation applies only to recorded fields at observation time, not service health or deployment.\n\n"
    files = {
        'CURRENT_STATE.md': '# Current state\n\n' + header + '## Collection coverage\n\n' + '\n'.join(f'- {key}: {value}' for key, value in sorted(data['coverage'].items())) + '\n\n## Counts\n\n' + '\n'.join(f"- {status}: {sum(row['status'] == status for row in data['records'])}" for status in sorted(STATUSES)) + '\n',
        'INVENTORY.md': '# Inventory\n\n' + header + table(data['records'], ['id', 'name', 'host', 'kind', 'vm_id', 'status', 'source', 'observed_at', 'cores', 'memory_bytes', 'disk_bytes', 'state', 'image']),
        'NETWORK.md': '# Network observations\n\n' + header + 'Addresses and ports from static sources do not confirm listeners, DNS, routes or firewall rules. Missing fields mean not collected.\n\n' + table([row for row in data['records'] if any(key in row for key in ('address', 'bridge', 'ports'))], ['id', 'address', 'bridge', 'ports', 'status', 'source']),
    }
    entry = '# Snapshot changes\n\n' + header + f"Previous: {previous['collected_at'] if previous else 'none (baseline)'}\n\n" + '\n'.join('- ' + change for change in changes) + ('\n' if changes else 'No inventory field changes.\n')
    entry_path = history / f'{identity}.md'
    if entry_path.exists() and entry_path.read_text() != entry:
        raise ValueError('History comparison collision')
    entry_path.write_text(entry)
    files['CHANGELOG.md'] = '# Inventory history\n\nMissing observations do not prove resource removal. Collection coverage must be reviewed before interpreting differences.\n\n' + '\n'.join(f'- [{path.stem}](history/{path.name})' for path in sorted(history.glob('*.md'))) + '\n'
    for name, contents in files.items():
        (output / name).write_text(contents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    collector = commands.add_parser('collect')
    collector.add_argument('source', choices=['linux', 'proxmox', 'docker'])
    collector.add_argument('--output', required=True)
    collector.add_argument('--node', help='Restrict Proxmox observations to one node')
    generator = commands.add_parser('report')
    generator.add_argument('inputs', nargs='+')
    generator.add_argument('--previous')
    generator.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'collect':
        if args.node and args.source != 'proxmox':
            raise ValueError('--node requires the Proxmox collector')
        data = collect(args.source, args.node)
        write_json(args.output, data)
        return 0 if all(value == 'complete' for value in data['coverage'].values()) else 2
    snapshots = [read(path) for path in args.inputs]
    coverage, records = {}, []
    for snapshot in snapshots:
        if coverage.keys() & snapshot['coverage'].keys():
            raise ValueError('Duplicate collection scope')
        coverage.update(snapshot['coverage'])
        records.extend(snapshot['records'])
    data = dict(schema_version=1, collected_at=max((item['collected_at'] for item in snapshots), key=date), coverage=coverage, records=records)
    report(data, read(args.previous) if args.previous else None, args.output)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, TypeError, KeyError):
        raise SystemExit('Inventory rejected or I/O failed; review schema, permissions and existing history. Raw data omitted.')
