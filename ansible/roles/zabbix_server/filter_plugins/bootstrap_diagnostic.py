"""Project bootstrap output onto a closed, secret-free diagnostic contract."""
import json


STAGES = frozenset({'input', 'target_login', 'initial_login', 'user_read',
                    'password_update', 'logout'})
CODES = frozenset({'HTTP_ERROR', 'TRANSPORT_ERROR', 'INVALID_JSON',
                   'UNEXPECTED_ERROR', 'INVALID_RESPONSE', 'RPC_ERROR',
                   'MISSING_RESULT', 'INVALID_TOKEN', 'INVALID_RESULT',
                   'INVALID_SETTINGS', 'INITIAL_PASSWORD_NOT_APPROVED',
                   'INVALID_ADMIN_RESULT', 'UPDATE_NOT_CONFIRMED'})


def bootstrap_diagnostic(result):
    unavailable = {'failed': True, 'changed': False, 'stage': 'input',
                   'code': 'DIAGNOSTIC_UNAVAILABLE'}
    try:
        payload = json.loads(result['stdout'])
        rc = result['rc']
        if (not isinstance(payload, dict) or type(rc) is not int
                or type(payload.get('failed')) is not bool
                or type(payload.get('changed')) is not bool):
            return unavailable
        # Success normally omits stage/code; supplied values still need validation.
        for field, allowed in (('stage', STAGES), ('code', CODES)):
            if field in payload and (not isinstance(payload[field], str)
                                     or payload[field] not in allowed):
                return unavailable
        if payload['failed']:
            if 'stage' not in payload or 'code' not in payload or payload['changed']:
                return unavailable
            return {'failed': True, 'changed': False,
                    'stage': payload['stage'], 'code': payload['code']}
        if rc != 0:
            return unavailable
        return {'failed': False, 'changed': payload['changed'],
                'stage': 'input', 'code': 'DIAGNOSTIC_UNAVAILABLE'}
    except Exception:
        # Never propagate parser exceptions containing untrusted output.
        return unavailable


class FilterModule:
    def filters(self):
        return {'zabbix_bootstrap_diagnostic': bootstrap_diagnostic}
