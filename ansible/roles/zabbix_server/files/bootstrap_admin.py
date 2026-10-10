"""Bootstrap Admin through loopback; emit only fixed diagnostic codes."""
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, ProxyHandler, build_opener

# Never use environment proxies for credentials sent to loopback.
urlopen = build_opener(ProxyHandler({})).open


class BootstrapError(ValueError):
    def __init__(self, stage, code):
        self.stage = stage
        self.code = code
        super().__init__(stage + ':' + code)

    def diagnostic(self):
        return {'stage': self.stage, 'code': self.code}


def call(stage, method, params, token=None):
    headers = {'Content-Type': 'application/json-rpc'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = json.dumps(dict(jsonrpc='2.0', method=method, params=params, id=1)).encode()
    try:
        with urlopen(Request('http://127.0.0.1:8080/api_jsonrpc.php', body, headers), timeout=30) as response:
            result = json.load(response)
    except HTTPError:
        raise BootstrapError(stage, 'HTTP_ERROR') from None
    except (URLError, OSError):
        raise BootstrapError(stage, 'TRANSPORT_ERROR') from None
    except (ValueError, UnicodeError):
        raise BootstrapError(stage, 'INVALID_JSON') from None
    except Exception:
        raise BootstrapError(stage, 'UNEXPECTED_ERROR') from None
    if not isinstance(result, dict):
        raise BootstrapError(stage, 'INVALID_RESPONSE')
    if 'error' in result:
        raise BootstrapError(stage, 'RPC_ERROR')
    if 'result' not in result:
        raise BootstrapError(stage, 'MISSING_RESULT')
    return result['result']


def login(stage, password):
    token = call(stage, 'user.login', {'username': 'Admin', 'password': password})
    if not isinstance(token, str) or not token:
        raise BootstrapError(stage, 'INVALID_TOKEN')
    return token


def logout(token, warnings):
    try:
        if call('logout', 'user.logout', [], token) is not True:
            raise BootstrapError('logout', 'INVALID_RESULT')
    except BootstrapError as error:
        warnings.append(error.diagnostic())


def main(settings, warnings=None):
    warnings = warnings if warnings is not None else []
    if (not isinstance(settings, dict) or not isinstance(settings.get('password'), str)
            or not settings['password'] or type(settings.get('allow_initial_password')) is not bool):
        raise BootstrapError('input', 'INVALID_SETTINGS')
    try:
        token = login('target_login', settings['password'])
    except BootstrapError as error:
        # Only an API rejection permits the approved initial-password attempt.
        # Network/protocol failures do not imply that the target password is wrong.
        if error.code != 'RPC_ERROR':
            raise
        if not settings['allow_initial_password']:
            raise BootstrapError('target_login', 'INITIAL_PASSWORD_NOT_APPROVED') from None
    else:
        logout(token, warnings)
        return False

    token = login('initial_login', 'zabbix')
    try:
        users = call('user_read', 'user.get',
                     {'output': ['userid'], 'filter': {'username': 'Admin'}}, token)
        if (not isinstance(users, list) or len(users) != 1
                or not isinstance(users[0], dict)
                or not isinstance(users[0].get('userid'), str)
                or not users[0]['userid'].isdigit()):
            raise BootstrapError('user_read', 'INVALID_ADMIN_RESULT')
        user_id = users[0]['userid']
        result = call('password_update', 'user.update',
                      {'userid': user_id, 'passwd': settings['password']}, token)
        if not isinstance(result, dict) or result.get('userids') != [user_id]:
            raise BootstrapError('password_update', 'UPDATE_NOT_CONFIRMED')
    finally:
        # Cleanup must not mask the primary error or a confirmed update.
        logout(token, warnings)
    return True


def run(settings):
    warnings = []
    try:
        changed = main(settings, warnings)
    except BootstrapError as error:
        return {'changed': False, 'failed': True, **error.diagnostic(), 'warnings': warnings}
    except Exception:
        return {'changed': False, 'failed': True, 'stage': 'input',
                'code': 'UNEXPECTED_ERROR', 'warnings': warnings}
    return {'changed': changed, 'failed': False, 'warnings': warnings}


def cli():
    try:
        settings = json.load(sys.stdin)
    except Exception:
        result = {'changed': False, 'failed': True, 'stage': 'input',
                  'code': 'INVALID_JSON', 'warnings': []}
    else:
        result = run(settings)
    print(json.dumps(result))
    return 1 if result['failed'] else 0


if __name__ == '__main__':
    sys.exit(cli())
