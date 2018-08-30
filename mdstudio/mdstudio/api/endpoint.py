import json
import uuid
from datetime import timedelta
from types import GeneratorType
from typing import Union, Optional, Callable

import six
from jsonschema import ValidationError
from twisted.internet.defer import _inlineCallbacks, Deferred

from mdstudio.api.api_result import APIResult
from mdstudio.api.converter import convert_obj_to_json
from mdstudio.api.request_hash import request_hash
from mdstudio.api.schema import ISchema, EndpointSchema, validate_json_schema, ClaimSchema, MDStudioClaimSchema, InlineSchema, \
    MDStudioSchema
from mdstudio.deferred.chainable import chainable
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
        from mdstudio.component.impl.common import CommonSession
        self.uri_suffix = uri
        self.uri = None
        self.options = options
        self.scope = scope
        self.instance = None  # type: CommonSession
        self.wrapped = wrapped_f
        self.input_schema = self._to_schema(input_schema, EndpointSchema)
        self.output_schema = self._to_schema(output_schema, EndpointSchema)

        self.claim_schemas = [MDStudioClaimSchema(CommonSession)]

        claim_schema = self._to_schema(claim_schema, ClaimSchema, {})
        if claim_schema:
            self.claim_schemas.append(claim_schema)

    def set_instance(self, instance):
        self.instance = instance
        self.uri = u'{}.{}.endpoint.{}'.format(
            self.instance.component_config.static.vendor,
            self.instance.component_config.static.component,
            self.uri_suffix
        )

    def register(self):
        return self.instance.register(self, self.uri, options=self.options)

    def __call__(self, request, signed_claims=None):
        return self.execute(request, signed_claims)  # type: Chainable

    @chainable
    def execute(self, request, signed_claims):
        if not signed_claims:
            return_value(APIResult(error='Remote procedure was called without claims'))

        from mdstudio.component.impl.common import CommonSession

        request = convert_obj_to_json(request)
        claims = yield super(CommonSession, self.instance).call(u'mdstudio.auth.endpoint.verify', signed_claims)

        claim_errors = self.validate_claims(claims, request)
        if claim_errors:
            return_value(claim_errors)

        request_errors = self.validate_request(request)
        if request_errors:
            return_value(request_errors)

        result = self.call_wrapped(request, claims['claims'])
        if isinstance(result, GeneratorType):
            result = _inlineCallbacks(None, result, Deferred())
        result = yield result

        result = convert_obj_to_json(result)
        result = result if isinstance(result, APIResult) else APIResult(result)

        if 'error' in result:
            return_value(result)

        result_errors = self.validate_result(result.data)
        if result_errors:
            return_value(result_errors)

        if 'error' in result:
            return_value(result)

        result_errors = self.validate_result(result.data)
        if result_errors:
            return_value(result_errors)

        return_value(result)

    def call_wrapped(self, request, claims):
        return self.wrapped(self.instance, request, claims)

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
        if isinstance(schema, (six.text_type, str)):
            schema = schema_type(schema)
        elif isinstance(schema, dict):
            schema = InlineSchema(schema)
        elif isinstance(schema, (schema_type, InlineSchema)):
            schema = schema
        elif not schema:
            schema = InlineSchema({} if default_schema == {} else default_schema or {'type': 'null'})
        else:
            raise NotImplementedError('{} of type {} is not supported'.format(schema_type.__name__, type(schema)))

        return schema


class CursorWampEndpoint(WampEndpoint):
    def __init__(self, wrapped_f, uri, input_schema, output_schema, claim_schema=None, options=None, scope=None):
        input_schema = InlineSchema({
            'oneOf': [
                {
                    'allOf': [
                        self._to_schema(input_schema, EndpointSchema),
                        self._to_schema('cursor-parameters/v1', MDStudioSchema)
                    ]
                },
                self._to_schema('cursor-request/v1', MDStudioSchema),
            ]
        })
        output_schema = InlineSchema({
            'allOf': [
                self._to_schema(output_schema, EndpointSchema),
                {
                    'properties': {
                        'results': self._to_schema('cursor-response/v1', MDStudioSchema)
                    }
                }
            ]
        })
        super(CursorWampEndpoint, self).__init__(wrapped_f, uri, input_schema, output_schema, claim_schema, options, scope)

    @chainable
    def call_wrapped(self, request, claims):

        meta = None
        id = None
        if 'next' in request:
            id = request['next']
        elif 'previous' in request:
            id = request['previous']

        if id:
            meta = json.loads(self.instance.session.cache.extract('cursor#{}'.format(id)))
            if meta.get('uuid') != id:
                return_value(APIResult(error='You tried to get a cursor that either doesn\'t exist, or is expired. Please check your code.'))
            if not meta:
                meta = None

        paging = {
            'uri': self.uri
        }
        if 'paging' in request and 'limit' in request['paging']:
            paging['limit'] = request['paging']['limit']

        result, prev, nxt = yield self.wrapped(self.instance, request, claims['claims'], **{'paging': paging, 'meta': meta})

        if prev:
            prev_uuid = uuid.uuid4()
            prev['uuid'] = prev_uuid
            paging['previous'] = prev_uuid
            self.instance.session.cache.put('cursor#{}'.format(prev_uuid), timedelta(minutes=10), json.dumps(prev))
        if next:
            next_uuid = uuid.uuid4()
            nxt['uuid'] = next_uuid
            paging['next'] = next_uuid
            self.instance.session.cache.put('cursor#{}'.format(next_uuid), timedelta(minutes=10), json.dumps(nxt))

        if not ('paging' in request or 'addPageInfo' in request['paging'] or request['paging']['addPageInfo']):
            paging = {
                'uri': paging['uri']
            }

        return_value({
            'results': result,
            'paging': paging
        })


def endpoint(uri, input_schema, output_schema=None, claim_schema=None, options=None, scope=None):
    # type: (str, SchemaType, Optional[SchemaType], Optional[SchemaType], bool, Optional[str], Optional[RegisterOptions], Optional[str]) -> Callable
    def wrap_f(f):
        return WampEndpoint(f, uri, input_schema, output_schema, claim_schema, options, scope)

    return wrap_f


def cursor_endpoint(uri, input_schema, output_schema, claim_schema=None, options=None, scope=None):
    # type: (str, SchemaType, Optional[SchemaType], Optional[SchemaType], bool, Optional[str], Optional[RegisterOptions], Optional[str]) -> Callable
    def wrap_f(f):
        return CursorWampEndpoint(f, uri, input_schema, output_schema, claim_schema, options, scope)

    return wrap_f
