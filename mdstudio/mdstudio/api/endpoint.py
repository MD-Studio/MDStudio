import json
from typing import Union

import six
from jsonschema import ValidationError

from mdstudio.api.api_result import APIResult
from mdstudio.api.converter import convert_obj_to_json
from mdstudio.api.request_hash import request_hash
from mdstudio.api.schema import ISchema, EndpointSchema, validate_json_schema, ClaimSchema, MDStudioClaimSchema, InlineSchema
from mdstudio.deferred.chainable import chainable, Chainable
from mdstudio.deferred.return_value import return_value

SchemaType = Union[str, dict, ISchema]


def validation_error(schema, instance, error, prefix, uri):
    return \
        '{prefix} validation on uri "{uri}" failed on "{property}": \n' \
        'Subschema:\n{subschema}\ndid not match actual value:\n{subproperty}'.format(
            prefix=prefix,
            uri=uri,
            property='.'.join(error.schema_path),
            subschema=json.dumps(error.schema, indent=2),
            subproperty=json.dumps(error.instance, indent=2)
        )


class WampEndpoint(object):
    def __init__(self, wrapped_f, uri, input_schema, output_schema, claim_schema=None, options=None, scope=None):
        self.uri = uri
        self.options = options
        self.scope = scope
        self.instance = None
        self.wrapped = wrapped_f
        self.input_schema = self._to_schema(input_schema, EndpointSchema)
        self.output_schema = self._to_schema(output_schema, EndpointSchema)

        from mdstudio.component.impl.common import CommonSession
        self.claim_schemas = [MDStudioClaimSchema(CommonSession)]

        claim_schema = self._to_schema(claim_schema, ClaimSchema, {})
        if claim_schema:
            self.claim_schemas.append(claim_schema)

    def set_instance(self, instance):
        self.instance = instance

    def __call__(self, request, signed_claims=None):
        result = self.execute(request, signed_claims)  # type: Chainable
        return result.transform(convert_obj_to_json)

    @chainable
    def execute(self, request, signed_claims):
        if not signed_claims:
            return_value(APIResult(error='Remote procedure was called without claims'))

        from mdstudio.component.impl.common import CommonSession

        claims = yield super(CommonSession, self.instance).call(u'mdstudio.auth.endpoint.verify', signed_claims)

        claim_errors = self.validate_claims(claims, request)
        if claim_errors:
            return_value(claim_errors)

        request_errors = self.validate_request(request)
        if request_errors:
            return_value(request_errors)

        result = yield self.wrapped(self.instance, request, claims['claims'])
        result = result if isinstance(result, APIResult) else APIResult(result)

        if 'error' in result:
            return_value(result)

        result_errors = self.validate_result(result.result)
        if result_errors:
            return_value(result_errors)

        return_value(result)

    def validate_claims(self, claims, request):
        if 'error' in claims:
            res = APIResult(error=claims['error'])
        elif 'expired' in claims:
            res = APIResult(expired=claims['expired'])
        else:
            claims = claims['claims']
            if claims['requestHash'] != request_hash(request):
                res = APIResult(error='Request did not match the signed request')
            elif claims['uri'] != self.uri:
                res = APIResult(error='Claims were obtained for a different endpoint')
            elif claims['action'] != 'call':
                res = APIResult(error='Claims were not obtained for the action "call"')
            else:
                s = None
                try:
                    for s in self.claim_schemas:
                        validate_json_schema(s.to_schema(), claims)
                except ValidationError as e:
                    res = {'error': validation_error(s.to_schema(), claims, e, 'Claims', self.uri)}
                    self.instance.log.error('{error_message}', error_message=res['error'])
                else:
                    if not self.instance.authorize_request(self.uri, claims):
                        res = APIResult(error='Unauthorized call to {}'.format(self.uri))
                        self.instance.log.error('{error_message}', error_message=res['error'])
                    else:
                        # Everything is OK, no errors
                        res = None

        return res

    def validate_request(self, request):
        schema = self.input_schema.to_schema()
        try:
            validate_json_schema(schema, request)
        except ValidationError as e:
            return APIResult(error=validation_error(schema, request, e, 'Input', self.uri))
        else:
            # No validation errors
            return None

    def validate_result(self, result):
        schema = self.output_schema.to_schema()

        try:
            validate_json_schema(schema, result)
        except ValidationError as e:
            res = APIResult(error=validation_error(schema, result, e, 'Output', self.uri))
        else:
            # No validation errors
            res = None

        return res

    @staticmethod
    def _to_schema(schema, schema_type, default_schema=None):
        if isinstance(schema, six.text_type):
            schema = schema_type(schema)
        elif isinstance(schema, dict):
            schema = InlineSchema(schema)
        elif isinstance(schema, schema_type):
            schema = schema
        elif not schema:
            schema = InlineSchema({} if default_schema == {} else default_schema or {'type': 'null'})
        else:
            raise NotImplementedError('{} of type {} is not supported'.format(schema_type.__name__, type(schema)))

        return schema


def endpoint(uri, input_schema, output_schema, claim_schema=None, options=None, scope=None):
    # type: (str, SchemaType, Optional[SchemaType], Optional[SchemaType], bool, Optional[str], Optional[RegisterOptions], Optional[str]) -> Callable
    def wrap_f(f):
        return WampEndpoint(f, uri, input_schema, output_schema, claim_schema, options, scope)

    return wrap_f
