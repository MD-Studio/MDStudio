# -*- coding: utf-8 -*-

"""
file: io_jsonschema_format_drafts.py

Classes representing JSON Schema draft version as specified by
http://json-schema.org.
"""

import re

from lie_graph.graph_axis.graph_axis_mixin import NodeAxisTools
from lie_graph.graph_orm import GraphORM
from lie_graph.graph_helpers import GraphValidationError
from lie_graph.graph_model_classes.model_email import Email
from lie_graph.graph_model_classes.model_datetime import DateTime, Date, Time
from lie_graph.graph_model_classes.model_networking import IP4Address, IP6Address, Hostname, URI


class JSONSchemaValidatorDraft07(NodeAxisTools):

    def schema_validate(self, value):

        enum = self.get('enum')
        if enum and value not in enum:
            raise GraphValidationError('"{0}" should be of type {1}, got {2}'.format(self.get(self.node_key_tag),
                                                                                     repr(enum), value), self)

        return value

    def set(self, key, value=None):
        """
        Set node attribute values.

        :param key:   node attribute key
        :param value: node attribute value
        """

        if key == self.node_value_tag:
            value = self.schema_validate(value)
        self.nodes[self.nid][key] = value


class StringType(JSONSchemaValidatorDraft07):

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if not isinstance(value, (str, unicode)):
                raise GraphValidationError('{0} should be of type "string" got "{1}"'.format(key, type(value)), self)

            value = self.schema_validate(value)

            # String specific validation
            length = len(value)
            if length > self.get('maxLength', length):
                raise GraphValidationError('Length of string {0} ({1}) larger then maximum {2}'.format(value, length,
                                                                                             self.get('maxLength')),
                                                                                             self)
            if length < self.get('minLength', length):
                raise GraphValidationError('Length of string {0} ({1}) smaller then minimum {2}'.format(value, length,
                                                                                             self.get('minLength')),
                                                                                             self)
            # Regular expression pattern matching
            if self.get('pattern'):
                pattern = re.compile(self.get('pattern'))
                if not pattern.match(value):
                    raise GraphValidationError('String {0} does not match regex pattern {1}'.format(value,
                                                                                             self.get('pattern')), self)

        self.nodes[self.nid][key] = value


class IntegerType(JSONSchemaValidatorDraft07):

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if not isinstance(value, int):
                raise GraphValidationError('{0} should be of type "integer" got "{1}"'.format(key, type(value)), self)

            value = self.schema_validate(value)

            # Integer specific validation
            if value > self.get('maximum', value):
                raise GraphValidationError('{0} is larger than maximum allowed {1}'.format(value,
                                                                                    self.get('maximum')), self)
            if value >= self.get('exclusiveMaximum', value+1):
                raise GraphValidationError('{0} is larger than maximum allowed {1}'.format(value,
                                                                                    self.get('exclusiveMaximum')), self)
            if value < self.get('minimum', value):
                raise GraphValidationError('{0} is smaller than minimum allowed {1}'.format(value,
                                                                                    self.get('minimum')), self)
            if value <= self.get('exclusiveMinimum', value-1):
                raise GraphValidationError('{0} is larger than minimum allowed {1}'.format(value,
                                                                                    self.get('exclusiveMinimum')), self)
            if value != 0:
                if self.get('multipleOf', value) % value != 0:
                    raise GraphValidationError('{0} is not a multiple of {1}'.format(value,
                                                                                self.get('multipleOf')), self)

        self.nodes[self.nid][key] = value


class NumberType(JSONSchemaValidatorDraft07):

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if not isinstance(value, float):
                raise GraphValidationError('{0} should be of type "float" got "{1}"'.format(key, type(value)), self)

            value = self.schema_validate(value)

            # Number specific validation
            if value > self.get('maximum', value):
                raise GraphValidationError('{0} is larger than maximum allowed {1}'.format(value,
                                                                                    self.get('maximum')), self)
            if value >= self.get('exclusiveMaximum', value+1):
                raise GraphValidationError('{0} is larger than maximum allowed {1}'.format(value,
                                                                                    self.get('exclusiveMaximum')), self)
            if value < self.get('minimum', value):
                raise GraphValidationError('{0} is smaller than minimum allowed {1}'.format(value,
                                                                                    self.get('minimum')), self)
            if value <= self.get('exclusiveMinimum', value-1):
                raise GraphValidationError('{0} is larger than minimum allowed {1}'.format(value,
                                                                                    self.get('exclusiveMinimum')), self)
            if value != 0:
                if self.get('multipleOf', value) % value != 0:
                    raise GraphValidationError('{0} is not a multiple of {1}'.format(value,
                                                                                    self.get('multipleOf')), self)

        self.nodes[self.nid][key] = value


class BooleanType(JSONSchemaValidatorDraft07):

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if value not in (True, False):
                raise GraphValidationError('{0} should be of type "boolean" got "{1}"'.format(key, type(value)), self)

            value = self.schema_validate(value)

        self.nodes[self.nid][key] = value


class ArrayType(JSONSchemaValidatorDraft07):

    def set(self, key, value=None):

        if key == self.node_value_tag:
            if not isinstance(value, list):
                raise GraphValidationError('{0} should be of type "array" got "{1}"'.format(key, type(value)), self)

            value = self.schema_validate(value)

            # Array specific validation
            length = len(value)
            if length > self.get('maxItems', length):
                raise GraphValidationError('Length of array {0} ({1}) larger then maximum {2}'.format(key, length,
                                                                                            self.get('maxItems')), self)
            if length < self.get('minItems', length):
                raise GraphValidationError('Length of array {0} ({1}) smaller then minimum {2}'.format(key, length,
                                                                                            self.get('minItems')), self)
            if self.get('uniqueItems', False):
                if len(set(value)) > 1:
                    raise GraphValidationError('Items in array {0} must be unique, got: {1}'.format(key,
                                                                                                    set(value)), self)

        self.nodes[self.nid][key] = value


JSONSchemaORMDraft07 = GraphORM()
JSONSchemaORMDraft07.map_node(StringType, type='string')
JSONSchemaORMDraft07.map_node(IntegerType, type='integer')
JSONSchemaORMDraft07.map_node(NumberType, type='number')
JSONSchemaORMDraft07.map_node(BooleanType, type='boolean')
JSONSchemaORMDraft07.map_node(ArrayType, type='array')
JSONSchemaORMDraft07.map_node(Email, type='email')
JSONSchemaORMDraft07.map_node(Email, type='idn-email')
JSONSchemaORMDraft07.map_node(DateTime, type='date-time')
JSONSchemaORMDraft07.map_node(Date, type='date')
JSONSchemaORMDraft07.map_node(Time, type='time')
JSONSchemaORMDraft07.map_node(IP4Address, type='ipv4')
JSONSchemaORMDraft07.map_node(IP6Address, type='ipv6')
JSONSchemaORMDraft07.map_node(Hostname, type='hostname')
JSONSchemaORMDraft07.map_node(Hostname, type='idn-hostname')
JSONSchemaORMDraft07.map_node(URI, type='uri')