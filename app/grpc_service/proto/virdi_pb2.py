# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: virdi.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'virdi.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0bvirdi.proto\"&\n\x0fProductionOffer\x12\x13\n\x0bresource_id\x18\x01 \x01(\t\"\x13\n\x11ProductionRequest\"c\n\x12ResourceProduction\x12\x30\n\tinit_info\x18\x01 \x01(\x0b\x32\x1b.ResourceProductionInitInfoH\x00\x12\x10\n\x06\x61mount\x18\x02 \x01(\rH\x00\x42\t\n\x07payload\"1\n\x1aResourceProductionInitInfo\x12\x13\n\x0bresource_id\x18\x01 \x01(\t\"\x14\n\x12ProductionResponse\"\x85\x01\n\x12\x43onsumptionRequest\x12\x13\n\x0b\x63onsumer_id\x18\x01 \x01(\t\x12\x13\n\x0bresource_id\x18\x02 \x01(\t\x12\x10\n\x08max_rate\x18\x03 \x01(\r\x12\x1d\n\x15\x63urrent_buffer_amount\x18\x05 \x01(\r\x12\x14\n\x0c\x62uffer_limit\x18\x04 \x01(\r\"%\n\x13ResourceConsumption\x12\x0e\n\x06\x61mount\x18\x02 \x01(\r2\xb1\x01\n\x05Virdi\x12\x39\n\x0fOfferProduction\x12\x10.ProductionOffer\x1a\x12.ProductionRequest0\x01\x12\x35\n\x07Produce\x12\x13.ResourceProduction\x1a\x13.ProductionResponse(\x01\x12\x36\n\x07\x43onsume\x12\x13.ConsumptionRequest\x1a\x14.ResourceConsumption0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'virdi_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_PRODUCTIONOFFER']._serialized_start=15
  _globals['_PRODUCTIONOFFER']._serialized_end=53
  _globals['_PRODUCTIONREQUEST']._serialized_start=55
  _globals['_PRODUCTIONREQUEST']._serialized_end=74
  _globals['_RESOURCEPRODUCTION']._serialized_start=76
  _globals['_RESOURCEPRODUCTION']._serialized_end=175
  _globals['_RESOURCEPRODUCTIONINITINFO']._serialized_start=177
  _globals['_RESOURCEPRODUCTIONINITINFO']._serialized_end=226
  _globals['_PRODUCTIONRESPONSE']._serialized_start=228
  _globals['_PRODUCTIONRESPONSE']._serialized_end=248
  _globals['_CONSUMPTIONREQUEST']._serialized_start=251
  _globals['_CONSUMPTIONREQUEST']._serialized_end=384
  _globals['_RESOURCECONSUMPTION']._serialized_start=386
  _globals['_RESOURCECONSUMPTION']._serialized_end=423
  _globals['_VIRDI']._serialized_start=426
  _globals['_VIRDI']._serialized_end=603
# @@protoc_insertion_point(module_scope)
