from typing import Union, Optional, Callable

from autobahn import wamp
from autobahn.wamp import RegisterOptions

from mdstudio.api.schema import ISchema, validate_input, validate_output
from mdstudio.application_session import BaseApplicationSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

SchemaType = Union[str, dict, ISchema]

def register(uri, input_schema, output_schema, meta_schema=None, match=None, options=None, scope=None):
    # type: (str, SchemaType, SchemaType, bool, Optional[str], Optional[RegisterOptions], Optional[str]) -> Callable
    """
    Decorator for more complete WAMP uri registration

    Besides registering the uri, also wrap the function to validate json schemas on input and output.
    Store the schema definition and custom scopes in attributes of the function for later processing.

    :param uri:             WAMP uri to register on
    :type uri:              str
    :param input_schema:    JSON schema to check the input.
    :type input_schema:     ISchema
    :param output_schema:   JSON schema to check the output.
    :type output_schema:    ISchema
    :param details_arg:     Boolean indicating whether the wrapped function expects a details argument
                            (will be set in the RegisterOptions).
    :type details_arg:      bool
    :param match:           Matching approach for the uri. Defaults to 'exact' in crossbar.
    :type match:            str
    :param options:         Options for registration. Created if not provided.
    :type options:          wamp.RegisterOptions
    :param scope:           Custom scope name within this namespace. If none is provided, only exact uri permission grants access.
    :type scope:            str
    :return:                Wrapped function with extra attributes
    :rtype:                 function
    """

    if options is None:
        # If options is not given but required for match or details, create it
        options = RegisterOptions()

    if not options.details_arg:
        options.details_arg = 'details'

    if match:
        options.match = match

    def wrap_f(f):
        @wamp.register(uri, options)
        @validate_input(input_schema)
        @validate_output(output_schema)
        @chainable
        def wrapped_f(self, request, *args, signed_meta=None, **kwargs):
            auth_meta = yield super(BaseApplicationSession, self).call('mdstudio.auth.endpoint.verify', signed_meta)

            if 'error' in auth_meta:
                res = {'error': auth_meta['error']}
            elif 'expired' in auth_meta:
                res = {'expired': auth_meta['expired']}
            else:
                auth_meta = auth_meta['authMeta']

                # @todo: check auth_meta using schema

                if not self.authorize_request(uri, auth_meta):
                    self.log.warn("Unauthorized call to {uri}", uri=uri)
                    res = {'error': 'Unauthorized call to {}'.format(uri)}
                else:
                    # @todo: catch exceptions and add error
                    # @todo: support warnings
                    res = {'result': (yield f(self, request, *args, auth_meta=auth_meta, **kwargs))}

            return_value(res)

        wrapped_f.input_schema = input_schema
        wrapped_f.output_schema = output_schema

        wrapped_f.wrapped = f

        if scope:
            wrapped_f.uri = uri
            wrapped_f.scope = scope

        return wrapped_f

    return wrap_f
