"""Initialization and finalization of dataClay client API.

The `init` and `finish` functions are availble through the
dataclay.api package.
"""

import logging
import pickle
import traceback

from dataclay.commonruntime.DataClayRuntime import DataClayRuntime
from dataclay.commonruntime.Settings import settings
from dataclay.heap.ClientHeapManager import ClientHeapManager
from dataclay.loader.ClientObjectLoader import ClientObjectLoader
from dataclay.serialization.lib.SerializationLibUtils import SerializationLibUtilsSingleton
from dataclay.util.management.metadataservice.MetaDataInfo import MetaDataInfo
from dataclay.util.management.metadataservice.RegistrationInfo import RegistrationInfo
from dataclay_common.clients.execution_environment_client import EEClient
from dataclay_common.clients.metadata_service_client import MDSClient
from dataclay_common.protos.common_messages_pb2 import LANG_PYTHON
from opentelemetry import trace

UNDEFINED_LOCAL = object()

tracer = trace.get_tracer(__name__)
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

        if instance._is_persistent:
            raise RuntimeError("Instance is already persistent")
        else:
            logger.debug(f"Starting make persistent for object {instance._object_id}")

            instance._master_ee_id = backend_id or self.get_backend_by_object_id(
                instance._object_id
            )

            logger.debug(f"Sending object {instance._object_id} to EE")

            instance._alias = alias

            # Gets Execution Environment client
            try:
                ee_client = self.ready_clients[instance._master_ee_id]
            except KeyError:
                exec_env = self.get_execution_environment_info(instance._master_ee_id)
                logger.debug(
                    f"ExecutionEnvironment {instance._master_ee_id} not found in cache! Starting it at {exec_env.hostname}:{exec_env.port}",
                )
                ee_client = EEClient(exec_env.hostname, exec_env.port)
                self.ready_clients[instance._master_ee_id] = ee_client

            ######################################
            # TODO: Serialize instance with Pickle
            ######################################

            instance._is_persistent = True

            serialized_dict = pickle.dumps(instance.__dict__)
            print("**instance_id:", instance._object_id)
            print("**instance dict:", instance.__dict__)
            ee_client.new_make_persistent(self.session.id, serialized_dict)

            ###
            # NOTE: Previous make persistent (without Pickle)
            ###

            # # serializes objects like volatile parameters
            # serialized_objs = SerializationLibUtilsSingleton.serialize_params_or_return(
            #     params=[instance],
            #     iface_bitmaps=None,
            #     params_spec={"object": "DataClayObject"},
            #     params_order=["object"],
            #     hint_volatiles=instance._master_ee_id,
            #     runtime=self,
            #     recursive=recursive,
            # )
            # # Avoid some race-conditions in communication (make persistent + execute where execute arrives before).
            # # TODO: fix volatiles under deserialization support for __setstate__ and __getstate__
            # self.add_volatiles_under_deserialization(serialized_objs.vol_objs.values())
            # ee_client.make_persistent(self.session.id, serialized_objs.vol_objs.values())

            # # removes volatiles under deserialization
            # self.remove_volatiles_under_deserialization(serialized_objs.vol_objs.values())

            #####
            # END Previous implementation
            #####

            return instance._master_ee_id

    def execute_implementation_aux(self, operation_name, instance, parameters, exec_env_id=None):
        with tracer.start_as_current_span(
            "execute_implementation",
            attributes={"operation_name": operation_name, "parameters": parameters},
        ) as span:
            logger.debug(
                f"Calling operation {operation_name} in object {instance._object_id} with parameters {parameters}"
            )

            using_hint = True
            hint = instance._master_ee_id
            if hint is None:
                self.update_object_metadata(instance)
                hint = instance._master_ee_id
                using_hint = False

            return self.call_execute_to_ds(instance, parameters, operation_name, hint, using_hint)

    def get_operation_info(self, object_id, operation_name):
        dcc_extradata = self.get_object_by_id(object_id).get_class_extradata()
        stub_info = dcc_extradata.stub_info
        implementation_stub_infos = stub_info.implementations
        operation = implementation_stub_infos[operation_name]
        return operation

    def get_implementation_id(self, object_id, operation_name, implementation_idx=0):
        operation = self.get_operation_info(object_id, operation_name)
        return operation.remoteImplID

    # NOTE: This function may be removed.
    # When an alias is removed without having the instance, the persistent object
    # has to know it if we consult its alias, therefore, in all cases, the alias
    # will have to be updated from the single source of truth i.e. the etcd metadata
    def delete_alias(self, instance):
        ee_id = instance._master_ee_id
        if not ee_id:
            self.update_object_metadata(instance)
            ee_id = self.get_hint()
        try:
            ee_client = self.ready_clients[ee_id]
        except KeyError:
            ee_info = self.get_execution_environment_info(ee_id)
            ee_client = EEClient(ee_info.hostname, ee_info.port)
            self.ready_clients[ee_id] = ee_client
        ee_client.delete_alias(self.session.id, instance._object_id)
        instance._alias = None

    def close_session(self):
        self.metadata_service.close_session(self.session.id)

    def get_hint(self):
        return None

    def synchronize(self, instance, operation_name, params):
        dest_backend_id = self.get_hint()
        operation = self.get_operation_info(instance._object_id, operation_name)
        implementation_id = self.get_implementation_id(instance._object_id, operation_name)
        # === SERIALIZE PARAMETER ===
        serialized_params = SerializationLibUtilsSingleton.serialize_params_or_return(
            params=[params],
            iface_bitmaps=None,
            params_spec=operation.params,
            params_order=operation.paramsOrder,
            hint_volatiles=instance._master_ee_id,
            runtime=self,
        )
        try:
            ee_client = self.ready_clients[dest_backend_id]
        except KeyError:
            exec_env = self.get_execution_environment_info(dest_backend_id)
            ee_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[dest_backend_id] = ee_client
        ee_client.synchronize(
            self.session.id, instance._object_id, implementation_id, serialized_params
        )

    def detach_object_from_session(self, object_id, hint):
        try:
            if hint is None:
                instance = self.get_from_heap(object_id)
                self.update_object_metadata(instance)
                hint = instance._master_ee_id
            try:
                ee_client = self.ready_clients[hint]
            except KeyError:
                ee_info = self.get_execution_environment_info(hint)
                ee_client = EEClient(ee_info.hostname, ee_info.port)
                self.ready_clients[hint] = ee_client
            ee_client.detach_object_from_session(object_id, self.session.id)
        except:
            traceback.print_exc()

    def federate_to_backend(self, instance, external_execution_environment_id, recursive):
        hint = instance._master_ee_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            ee_client = self.ready_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            ee_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[hint] = ee_client

        logger.debug(
            "[==FederateObject==] Starting federation of object by %s calling EE %s with dest dataClay %s, and session %s",
            instance._object_id,
            hint,
            external_execution_environment_id,
            self.session.id,
        )
        ee_client.federate(
            self.session.id, instance._object_id, external_execution_environment_id, recursive
        )

    def unfederate_from_backend(self, instance, external_execution_environment_id, recursive):
        logger.debug(
            "[==UnfederateObject==] Starting unfederation of object %s with ext backend %s, and session %s",
            instance._object_id,
            external_execution_environment_id,
            self.session.id,
        )
        hint = instance._master_ee_id
        if hint is None:
            self.update_object_metadata(instance)
            hint = self.get_hint()
        try:
            ee_client = self.ready_clients[hint]
        except KeyError:
            exec_env = self.get_execution_environment_info(hint)
            ee_client = EEClient(exec_env.hostname, exec_env.port)
            self.ready_clients[hint] = ee_client

        ee_client.unfederate(
            self.session.id, instance._object_id, external_execution_environment_id, recursive
        )
