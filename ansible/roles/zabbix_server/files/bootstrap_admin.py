"""Set the initial Admin password through loopback API, without persisting a token."""
import json
import sys
from urllib.request import Request, urlopen


def main(settings):
    def call(method, params, token=None):
        headers = {'Content-Type': 'application/json-rpc'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        body = json.dumps(dict(jsonrpc='2.0', method=method, params=params, id=1)).encode()
        with urlopen(Request('http://127.0.0.1:8080/api_jsonrpc.php', body, headers), timeout=30) as response:
            result = json.load(response)
        return result
    login = call('user.login', {'username': 'Admin', 'password': settings['password']})
    if 'result' in login:
        call('user.logout', [], login['result'])
        return False
    if not settings['allow_initial_password']:
        raise ValueError('Initial password bootstrap has not been approved')
    login = call('user.login', {'username': 'Admin', 'password': 'zabbix'})
    token = login['result']
    users = call('user.get', {'output': ['userid'], 'filter': {'username': 'Admin'}}, token)['result']
    result = call('user.update', {'userid': users[0]['userid'], 'passwd': settings['password']}, token)
    if 'error' in result:
        raise ValueError('Password update failed')
    call('user.logout', [], token)
    return True


if __name__ == '__main__':
    try:
        print(json.dumps({'changed': main(json.load(sys.stdin))}))
    except Exception:
        sys.exit('Admin bootstrap failed; credentials are not logged.')
