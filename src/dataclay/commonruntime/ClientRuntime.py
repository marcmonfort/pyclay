"""Initialization and finalization of dataClay client API.

The `init` and `finish` functions are availble through the
dataclay.api package.
"""

import logging
import traceback

from dataclay.commonruntime.DataClayRuntime import DataClayRuntime
from dataclay.commonruntime.Settings import settings
from dataclay.communication.grpc.clients.ExecutionEnvGrpcClient import EEClient
from dataclay.heap.ClientHeapManager import ClientHeapManager
from dataclay.loader.ClientObjectLoader import ClientObjectLoader
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo
from dataclay_common.clients.metadata_service_client import MDSClient
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON

UNDEFINED_LOCAL = object()

logger = logging.getLogger(__name__)


class ClientRuntime(DataClayRuntime):

    metadata_service = None
    dataclay_heap_manager = None
    dataclay_object_loader = None
    session = None

    def __init__(self, metadata_service_host, metadata_service_port):
        DataClayRuntime.__init__(self)
        self.metadata_service = MDSClient(metadata_service_host, metadata_service_port)
        self.dataclay_heap_manager = ClientHeapManager(self)
        self.dataclay_object_loader = ClientObjectLoader(self)
        self.dataclay_heap_manager.start()

    def is_client(self):
        return True

    def make_persistent(self, instance, alias, backend_id, recursive):
        """This method creates a new Persistent Object using the provided stub
        instance and, if indicated, all its associated objects also Logic module API used for communication
        This function is called from a stub/execution class

        Args:
            instance: Instance to make persistent
            backend_id: Indicates which is the destination backend
            recursive: Indicates if make persistent is recursive
            alias: Alias for the object

        Returns:
            ID of the backend in which te object was persisted.
        """

        if instance.is_persistent():
            raise RuntimeError("Instance is already persistent")
        else:
            logger.debug(f"Starting make persistent for object {instance.get_object_id()}")

            location = instance.get_hint() or backend_id or self.choose_location(instance)
            instance.set_hint(location)

            logger.debug(f"Sending object {instance.get_object_id()} to EE")

            # sets the default master location
            instance.set_master_location(location)
            instance.set_alias(alias)

            # serializes objects like volatile parameters
            serialized_objs = SerializationLibUtilsSingleton.serialize_params_or_return(
                params=[instance],
                iface_bitmaps=None,
                params_spec={"object": "DataClayObject"},
                params_order=["object"],
                hint_volatiles=instance.get_hint(),
                runtime=self,
                recursive=recursive,
            )

            # Avoid some race-conditions in communication (make persistent + execute where execute arrives before).
            # TODO: fix volatiles under deserialization support for __setstate__ and __getstate__
            self.add_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            # Gets EE Client
            try:
                execution_client = self.ready_clients[instance.get_hint()]
            except KeyError:
                exec_env = self.get_execution_environment_info(instance.get_hint())
                logger.debug(
                    f"ExecutionEnvironment {location} not found in cache! Starting it at {exec_env.hostname}:{exec_env.port}",
                )
                execution_client = EEClient(exec_env.hostname, exec_env.port)
                self.ready_clients[location] = execution_client

            logger.verbose(f"Calling make persistent to EE {location}")
            execution_client.make_persistent(self.session.id, serialized_objs.vol_objs.values())

            # removes volatiles under deserialization
            self.remove_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            # TODO: Use ObjectMD instead ?
            metadata_info = MetaDataInfo(
                instance.get_object_id(),
                False,
                instance.get_dataset_name(),
                instance.get_class_extradata().class_id,
                {location},
                alias,
                None,
            )

            self.metadata_cache[instance.get_object_id()] = metadata_info
            return location

    def execute_implementation_aux(self, operation_name, instance, parameters, exec_env_id=None):
        object_id = instance.get_object_id()

        logger.debug(
            f"Calling operation {operation_name} in object {object_id} with parameters {parameters}"
        )

        using_hint = True
        exec_env_id = instance.get_hint()
        if exec_env_id is None:
            exec_env_id = next(iter(self.get_metadata(object_id).locations))
            using_hint = False

        return self.call_execute_to_ds(
            instance, parameters, operation_name, exec_env_id, using_hint
        )

    def get_operation_info(self, object_id, operation_name):
        dcc_extradata = self.get_object_by_id(object_id).get_class_extradata()
        stub_info = dcc_extradata.stub_info
        implementation_stub_infos = stub_info.implementations
        operation = implementation_stub_infos[operation_name]
        return operation

    def get_implementation_id(self, object_id, operation_name, implementation_idx=0):
        operation = self.get_operation_info(object_id, operation_name)
        return operation.remoteImplID

    def delete_alias(self, dc_obj):
        session_id = self.session.id
        hint = dc_obj.get_hint()
        object_id = dc_obj.get_object_id()
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            backend_to_call = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
            self.ready_clients[exec_location_id] = execution_client
        execution_client.delete_alias(session_id, object_id)
        dc_obj.set_alias(None)

    def close_session(self):
        self.metadata_service.close_session(self.session.id)

    def get_hint(self):
        return None

    def synchronize(self, instance, operation_name, params):
        session_id = self.session.id
        object_id = instance.get_object_id()
        dest_backend_id = self.get_location(instance.get_object_id())
        operation = self.get_operation_info(instance.get_object_id(), operation_name)
        implementation_id = self.get_implementation_id(instance.get_object_id(), operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance.get_hint(),
            runtime=self,
        )
        try:
            execution_client = self.ready_clients[dest_backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(dest_backend_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[dest_backend_id] = execution_client
        execution_client.synchronize(session_id, object_id, implementation_id, serialized_params)

    def detach_object_from_session(self, object_id, hint):
        try:
            cur_session = self.session.id
            exec_location_id = hint
            if exec_location_id is None:
                exec_location_id = self.get_location(object_id)
            try:
                execution_client = self.ready_clients[exec_location_id]
            except KeyError:
                backend_to_call = self.get_execution_environment_info(exec_location_id)
                execution_client = EEClient(backend_to_call.hostname, backend_to_call.port)
                self.ready_clients[exec_location_id] = execution_client
            execution_client.detach_object_from_session(object_id, cur_session)
        except:
            traceback.print_exc()

    def federate_to_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj.get_object_id()
        hint = dc_obj.get_hint()
        session_id = self.session.id
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[exec_location_id] = execution_client

        logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            object_id,
            exec_location_id,
            external_execution_environment_id,
            session_id,
        )
        execution_client.federate(
            session_id, object_id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, dc_obj, external_execution_environment_id, recursive):
        object_id = dc_obj.get_object_id()
        hint = dc_obj.get_hint()
        session_id = self.session.id
        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            object_id,
            external_execution_environment_id,
            session_id,
        )
        exec_location_id = hint
        if exec_location_id is None:
            exec_location_id = self.get_location(object_id)
        try:
            execution_client = self.ready_clients[exec_location_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(exec_location_id)
            execution_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[exec_location_id] = execution_client

        execution_client.unfederate(
            session_id, object_id, external_execution_environment_id, recursive
        )
