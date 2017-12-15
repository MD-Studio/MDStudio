def whois(claims, extra=None):
    whois = {
        'username': claims.get('username'),
        'role': claims.get('role'),
        'group': claims.get('group')
    }

    if extra:
        whois[extra] = claims.get(extra)

    return dict([(k, v) for k, v in whois.items() if v])
