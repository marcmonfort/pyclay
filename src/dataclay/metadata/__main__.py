import logging
import signal
import threading
import uuid
from concurrent import futures

import grpc
from dataclay_common.protos import metadata_service_pb2_grpc

from dataclay.conf import settings
from dataclay.metadata.api import MetadataAPI
from dataclay.metadata.servicer import MetadataServicer

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def serve():

    stop_event = threading.Event()

    metadata_service = MetadataAPI(settings.ETCD_HOST, settings.ETCD_PORT)
    if not metadata_service.is_ready(timeout=10):
        logger.error("Etcd is not ready. Aborting!")
        raise

    dataclay_id = metadata_service.get_dataclay_id()

    metadata_service.autoregister_mds(
        dataclay_id,
        settings.METADATA_SERVICE_HOST,
        settings.METADATA_SERVICE_PORT,
        is_this=True,
    )

    logger.info("Metadata service has been registered")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=settings.THREAD_POOL_WORKERS))
    metadata_service_pb2_grpc.add_MetadataServiceServicer_to_server(
        MetadataServicer(metadata_service), server
    )

    address = f"{settings.SERVER_LISTEN_ADDR}:{settings.SERVER_LISTEN_PORT}"
    server.add_insecure_port(address)
    server.start()

    # Set signal hook for SIGINT and SIGTERM
    signal.signal(signal.SIGINT, lambda sig, frame: stop_event.set())
    signal.signal(signal.SIGTERM, lambda sig, frame: stop_event.set())

    # Wait until stop_event is set. Then, gracefully stop dataclay backend.
    stop_event.wait()

    server.stop(5)


settings.load_metadata_properties()
serve()