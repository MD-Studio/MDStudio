import re
from typing import Union, Optional, Callable

from autobahn import wamp
from autobahn.wamp import RegisterOptions

from mdstudio.api.schema import ISchema, validate_input, validate_output, EndpointSchema
from mdstudio.component.impl.common import CommonSession
from mdstudio.deferred.chainable import chainable
from mdstudio.deferred.return_value import return_value

SchemaType = Union[str, dict, ISchema]


def register(uri, input_schema, output_schema, meta_schema=None, options=None, scope=None):
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

    if not input_schema:
        #print('Input on {uri} is not checked'.format(uri=uri))
        pass
    elif isinstance(input_schema, str):
        if not re.match('\\w+://.*', input_schema):
            input_schema = 'endpoint://{}'.format(input_schema)

        input_schema = EndpointSchema(input_schema)

    if not output_schema:
        #print('Output on {uri} is not checked'.format(uri=uri))
        pass
    if isinstance(output_schema, str):
        if not re.match('\\w+://.*', output_schema):
            output_schema = 'endpoint://{}'.format(output_schema)

        output_schema = EndpointSchema(output_schema)

    def wrap_f(f):
        @wamp.register(uri, options)
        @validate_input(input_schema)
        @validate_output(output_schema)
        @chainable
        def wrapped_f(self, request, *args, signed_claims=None, **kwargs):
            claims = yield super(CommonSession, self).call('mdstudio.auth.endpoint.verify', signed_claims)

            if 'error' in claims:
                res = {'error': claims['error']}
            elif 'expired' in claims:
                res = {'expired': claims['expired']}
            else:
                claims = claims['claims']

                # @todo: check claims using schema

                if not self.authorize_request(uri, claims):
                    self.log.warn("Unauthorized call to {uri}", uri=uri)
                    res = {'error': 'Unauthorized call to {}'.format(uri)}
                else:
                    # @todo: catch exceptions and add error
                    # @todo: support warnings
                    res = {'result': (yield f(self, request, *args, claims=claims, **kwargs))}

            return_value(res)

        wrapped_f.input_schema = input_schema
        wrapped_f.output_schema = output_schema

        wrapped_f.wrapped = f

        if scope:
            wrapped_f.uri = uri
            wrapped_f.scope = scope

        return wrapped_f

    return wrap_f
