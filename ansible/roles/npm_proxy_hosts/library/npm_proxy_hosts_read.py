"""Read the token-visible NPM proxy-host list using GET only."""
import ipaddress
import json
import socket
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, HTTPSHandler, ProxyHandler, build_opener

MAX_BYTES = 4 * 1024 * 1024
FIELDS = ('id', 'domain_names', 'forward_scheme', 'forward_host', 'forward_port',
          'enabled', 'allow_websocket_upgrade')


class ReadError(Exception):
    """Only fixed diagnostic codes may leave the adapter."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ReadError('REDIRECT_REJECTED')


def validate_settings(url, token, timeout, contract_verified):
    if contract_verified is not True:
        raise ReadError('API_CONTRACT_NOT_VERIFIED')
    if not isinstance(url, str) or any(c.isspace() or ord(c) < 32 for c in url):
        raise ReadError('INVALID_URL')
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        raise ReadError('INVALID_URL') from None
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path != '/api/nginx/proxy-hosts'
            or (port is not None and not 1 <= port <= 65535)):
        raise ReadError('INVALID_URL')
    if parsed.scheme == 'http':
        try:
            loopback = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            raise ReadError('HTTPS_OR_LOOPBACK_REQUIRED')
    if (not isinstance(token, str) or not token.strip()
            or any(c.isspace() or ord(c) < 33 or ord(c) > 126 for c in token)):
        raise ReadError('INVALID_TOKEN')
    if type(timeout) is not int or not 1 <= timeout <= 120:
        raise ReadError('INVALID_TIMEOUT')


def unique_mapping(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReadError('INVALID_RESPONSE')
        result[key] = value
    return result


def reject_constant(value):
    raise ReadError('INVALID_RESPONSE')


def normalize(payload):
    # Confirmed direct-list contract; permissions can still limit visibility.
    if not isinstance(payload, list):
        raise ReadError('UNSUPPORTED_RESPONSE_CONTRACT')
    snapshot, ids = [], set()
    for host in payload:
        if not isinstance(host, dict) or not all(field in host for field in FIELDS):
            raise ReadError('INVALID_RESPONSE')
        if type(host['id']) is not int or host['id'] <= 0 or host['id'] in ids:
            raise ReadError('INVALID_RESPONSE')
        ids.add(host['id'])
        if (not isinstance(host['domain_names'], list) or not host['domain_names']
                or any(not isinstance(d, str) or not d.strip()
                       or any(c.isspace() or ord(c) < 32 for c in d)
                       for d in host['domain_names'])
                or host['forward_scheme'] not in ('http', 'https')
                or not isinstance(host['forward_host'], str) or not host['forward_host'].strip()
                or type(host['forward_port']) is not int or not 1 <= host['forward_port'] <= 65535
                or type(host['enabled']) is not bool
                or type(host['allow_websocket_upgrade']) is not bool):
            raise ReadError('INVALID_RESPONSE')
        # TLS fields are outside route comparison, but reject malformed values
        # when supplied rather than silently accepting an invalid API object.
        if (('certificate_id' in host and (type(host['certificate_id']) is not int
                                          or host['certificate_id'] < 0))
                or ('ssl_forced' in host and type(host['ssl_forced']) is not bool)):
            raise ReadError('INVALID_RESPONSE')
        snapshot.append({field: host[field] for field in FIELDS})
    return snapshot


def read_snapshot(url, token, timeout=30, contract_verified=False, opener=None):
    validate_settings(url, token, timeout, contract_verified)
    if opener is None:
        # No environment proxies, no redirects, normal TLS trust and hostname checks.
        opener = build_opener(ProxyHandler({}), NoRedirect(),
                              HTTPSHandler(context=ssl.create_default_context()))
    request = Request(url, headers={'Authorization': 'Bearer ' + token,
                                   'Accept': 'application/json'}, method='GET')
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status in (401, 403):
                raise ReadError('AUTHORIZATION_FAILED')
            if response.status != 200:
                raise ReadError('HTTP_ERROR')
            content_type = response.headers.get('Content-Type', '').split(';')[0].strip().lower()
            if content_type != 'application/json':
                raise ReadError('INVALID_CONTENT_TYPE')
            # This stage supports only the explicitly verified, unpaginated list contract.
            if any(response.headers.get(header) for header in ('Link', 'X-Next-Page', 'Content-Range')):
                raise ReadError('PAGINATION_NOT_SUPPORTED')
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ReadError('RESPONSE_TOO_LARGE')
            payload = json.loads(body.decode('utf-8'), object_pairs_hook=unique_mapping,
                                 parse_constant=reject_constant)
            snapshot = normalize(payload)
            total = response.headers.get('X-Total-Count')
            if total is not None and (not total.isdecimal() or int(total) != len(snapshot)):
                raise ReadError('INCOMPLETE_RESPONSE')
            return snapshot
    except ReadError:
        raise
    except HTTPError as exc:
        if exc.code in (401, 403):
            raise ReadError('AUTHORIZATION_FAILED') from None
        if 300 <= exc.code < 400:
            raise ReadError('REDIRECT_REJECTED') from None
        raise ReadError('HTTP_ERROR') from None
    except (URLError, OSError, TimeoutError):
        raise ReadError('CONNECTION_FAILED') from None
    except (ValueError, UnicodeError, TypeError):
        raise ReadError('INVALID_RESPONSE') from None


def main():
    from ansible.module_utils.basic import AnsibleModule
    module = AnsibleModule(argument_spec=dict(
        url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
        contract_verified=dict(type='bool', default=False),
    ), supports_check_mode=True)
    try:
        if socket.gethostname().split('.')[0] != 'iza':
            raise ReadError('EXECUTION_HOST_MUST_BE_IZA')
        validate_settings(**{key: module.params[key] for key in ('url', 'token', 'timeout', 'contract_verified')})
        if module.check_mode:
            module.exit_json(changed=False, skipped=True, msg='Check mode: API read skipped')
        snapshot = read_snapshot(**module.params)
        module.exit_json(changed=False, snapshot=snapshot,
                         snapshot_scope='token_visible', completeness='unverified')
    except ReadError as exc:
        module.fail_json(changed=False, msg='NPM read failed', code=str(exc))
    except Exception:
        module.fail_json(changed=False, msg='NPM read failed', code='UNEXPECTED_ERROR')


if __name__ == '__main__':
    main()
