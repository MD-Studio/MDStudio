import itertools
import re

class ActionRule(object):
    def __init__(self, actions):
        self.actions = actions

    def match(self, uri, action, **kw):
        return any(a in self.actions for a in ('*', action))

class PrefixRule(ActionRule):
    def __init__(self, prefix, actions=['call']):
        self.prefix = prefix
        super(PrefixRule, self).__init__(actions)

    def match(self, uri, action, **kw):
        return uri.startswith(self.prefix.format(uri=uri, **kw)) and super(PrefixRule, self).match(uri, action, **kw)

class RegexRule(ActionRule):
    def __init__(self, pattern, actions=['call']):
        self.pattern = pattern
        self.actions = actions

    def match(self, uri, action, **kw):
        return super(RegexRule, self).match(uri, action, **kw) and re.match(self.pattern.format(uri=uri, **kw), uri)

class ExactRule(ActionRule):
    def __init__(self, uri, actions=['call']):
        self.uri = uri
        super(ExactRule, self).__init__(actions)

    def match(self, uri, action, **kw):
        return self.uri.format(uri=uri, **kw) == uri and super(ExactRule, self).match(uri, action, **kw)

class Authorizer(object):
    def __init__(self):
        # Build ruleset for communication inside ring0
        self.ring0_rules = [
            PrefixRule('mdstudio.{role}.', ['*']),
            PrefixRule('mdstudio.auth.endpoint.oauth.registerscopes.{role}'),
            RegexRule('mdstudio\\.\\w+\\.endpoint\\.events\\.\\w+', ['subscribe']),
            RegexRule('mdstudio\\.db\\.endpoint\\.\\w+'),
            ExactRule('mdstudio.auth.endpoint.oauth.client.getusername'),
            ExactRule('mdstudio.auth.endpoint.sign'),
            ExactRule('mdstudio.auth.endpoint.verify'),
            ExactRule('mdstudio.schema.endpoint.upload'),
            ExactRule('mdstudio.schema.endpoint.get'),
            ExactRule('mdstudio.logger.endpoint.log'),
            ExactRule('mdstudio.auth.endpoint.ring0.get-status'),
            ExactRule('mdstudio.auth.endpoint.ring0.set-status')
        ]
    
    def authorize_ring0(self, uri, action, role):
        if any(rule.match(uri, action, role=role) for rule in self.ring0_rules):
            return {'allow': True, 'disclose': True}

        return False

    def oauthclient_scopes(self, uri, action, authid):
        # Generator for multiple scopes with this pattern
        def iter_scopes(pattern, **kw):
            yield pattern.format(action=action, **kw)
            yield pattern.format(action='*', **kw)
        
        match = re.match('(.*?)\\.(.*?)\\..+', uri)
        vendor = match.group(1)
        ns = match.group(2)

        # Check for scopes that match the exact uri or the entire namespace the uri is registered in
        scopes = itertools.chain(iter_scopes('{uri}:{action}', uri=uri), iter_scopes('ns.{vendor}.{ns}:{action}', ns=ns, vendor=vendor))

        # TODO: check custom scope name on uri
        scope_name = None

        if scope_name:
            scopes = itertools.chain(scopes, iter_scopes('ns.{vendor}.{ns}.{scope}:{action}', ns=ns, scope=scope_name))

        return scopes
