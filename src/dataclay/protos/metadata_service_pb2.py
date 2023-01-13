# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: protos/metadata_service.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from . import common_messages_pb2 as protos_dot_common__messages__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1dprotos/metadata_service.proto\x12\x17protos.metadata_service\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1cprotos/common_messages.proto\"7\n\x11NewAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"%\n\x11GetAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"\x14\n\x12GetAccountResponse\"M\n\x11NewSessionRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x03 \x01(\t\"!\n\x13\x43loseSessionRequest\x12\n\n\x02id\x18\x01 \x01(\t\"H\n\x11NewDatasetRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\x12\x0f\n\x07\x64\x61taset\x18\x03 \x01(\t\"-\n\x15GetAllBackendsRequest\x12\x14\n\x0c\x66rom_backend\x18\x01 \x01(\x08\"\xb2\x01\n\x16GetAllBackendsResponse\x12O\n\x08\x62\x61\x63kends\x18\x01 \x03(\x0b\x32=.protos.metadata_service.GetAllBackendsResponse.BackendsEntry\x1aG\n\rBackendsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.protos.common.Backend:\x02\x38\x01\")\n\x12GetDataclayRequest\x12\x13\n\x0b\x64\x61taclay_id\x18\x01 \x01(\t\"]\n\x15RegisterObjectRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x30\n\tobject_md\x18\x02 \x01(\x0b\x32\x1d.protos.common.ObjectMetadata\"?\n\x16GetObjectMDByIdRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x11\n\tobject_id\x18\x02 \x01(\t\"Y\n\x19GetObjectMDByAliasRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x12\n\nalias_name\x18\x02 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x03 \x01(\t\"R\n\x12\x44\x65leteAliasRequest\x12\x12\n\nsession_id\x18\x01 \x01(\t\x12\x12\n\nalias_name\x18\x02 \x01(\t\x12\x14\n\x0c\x64\x61taset_name\x18\x03 \x01(\t2\x9c\x08\n\x0fMetadataService\x12R\n\nNewAccount\x12*.protos.metadata_service.NewAccountRequest\x1a\x16.google.protobuf.Empty\"\x00\x12g\n\nGetAccount\x12*.protos.metadata_service.GetAccountRequest\x1a+.protos.metadata_service.GetAccountResponse\"\x00\x12R\n\nNewSession\x12*.protos.metadata_service.NewSessionRequest\x1a\x16.protos.common.Session\"\x00\x12V\n\x0c\x43loseSession\x12,.protos.metadata_service.CloseSessionRequest\x1a\x16.google.protobuf.Empty\"\x00\x12R\n\nNewDataset\x12*.protos.metadata_service.NewDatasetRequest\x1a\x16.google.protobuf.Empty\"\x00\x12s\n\x0eGetAllBackends\x12..protos.metadata_service.GetAllBackendsRequest\x1a/.protos.metadata_service.GetAllBackendsResponse\"\x00\x12U\n\x0bGetDataclay\x12+.protos.metadata_service.GetDataclayRequest\x1a\x17.protos.common.Dataclay\"\x00\x12Z\n\x0eRegisterObject\x12..protos.metadata_service.RegisterObjectRequest\x1a\x16.google.protobuf.Empty\"\x00\x12\x63\n\x0fGetObjectMDById\x12/.protos.metadata_service.GetObjectMDByIdRequest\x1a\x1d.protos.common.ObjectMetadata\"\x00\x12i\n\x12GetObjectMDByAlias\x12\x32.protos.metadata_service.GetObjectMDByAliasRequest\x1a\x1d.protos.common.ObjectMetadata\"\x00\x12T\n\x0b\x44\x65leteAlias\x12+.protos.metadata_service.DeleteAliasRequest\x1a\x16.google.protobuf.Empty\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'protos.metadata_service_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _GETALLBACKENDSRESPONSE_BACKENDSENTRY._options = None
  _GETALLBACKENDSRESPONSE_BACKENDSENTRY._serialized_options = b'8\001'
  _NEWACCOUNTREQUEST._serialized_start=117
  _NEWACCOUNTREQUEST._serialized_end=172
  _GETACCOUNTREQUEST._serialized_start=174
  _GETACCOUNTREQUEST._serialized_end=211
  _GETACCOUNTRESPONSE._serialized_start=213
  _GETACCOUNTRESPONSE._serialized_end=233
  _NEWSESSIONREQUEST._serialized_start=235
  _NEWSESSIONREQUEST._serialized_end=312
  _CLOSESESSIONREQUEST._serialized_start=314
  _CLOSESESSIONREQUEST._serialized_end=347
  _NEWDATASETREQUEST._serialized_start=349
  _NEWDATASETREQUEST._serialized_end=421
  _GETALLBACKENDSREQUEST._serialized_start=423
  _GETALLBACKENDSREQUEST._serialized_end=468
  _GETALLBACKENDSRESPONSE._serialized_start=471
  _GETALLBACKENDSRESPONSE._serialized_end=649
  _GETALLBACKENDSRESPONSE_BACKENDSENTRY._serialized_start=578
  _GETALLBACKENDSRESPONSE_BACKENDSENTRY._serialized_end=649
  _GETDATACLAYREQUEST._serialized_start=651
  _GETDATACLAYREQUEST._serialized_end=692
  _REGISTEROBJECTREQUEST._serialized_start=694
  _REGISTEROBJECTREQUEST._serialized_end=787
  _GETOBJECTMDBYIDREQUEST._serialized_start=789
  _GETOBJECTMDBYIDREQUEST._serialized_end=852
  _GETOBJECTMDBYALIASREQUEST._serialized_start=854
  _GETOBJECTMDBYALIASREQUEST._serialized_end=943
  _DELETEALIASREQUEST._serialized_start=945
  _DELETEALIASREQUEST._serialized_end=1027
  _METADATASERVICE._serialized_start=1030
  _METADATASERVICE._serialized_end=2082
# @@protoc_insertion_point(module_scope)
