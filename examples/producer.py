import threading
import time
import uuid
import grpc
import argparse

import app.grpc_service.proto.virdi_pb2 as virdi_pb2
import app.grpc_service.proto.virdi_pb2_grpc as virdi_pb2_grpc


def get_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="gRPC Producer Client for ViRDi")
    parser.add_argument("--client-id", type=str, default=str(uuid.uuid4())[:8],
                        help="Optional client ID. Defaults to a random string.")
    parser.add_argument("--resource-id", type=str, default="iron",
                        help="Resource ID to produce.")
    return parser.parse_args()


def create_grpc_stub():
    """Creates a gRPC channel and stub."""
    channel = grpc.insecure_channel('localhost:50051')
    stub = virdi_pb2_grpc.VirdiStub(channel)
    return stub


def offer_production(stub, resource_id, metadata):
    """Offers a production request to the gRPC server."""
    production_offer = virdi_pb2.ProductionOffer(resource_id=resource_id)
    return stub.OfferProduction(production_offer, metadata=metadata)


def produce_resources(resource_id, stop_production: threading.Event):
    """Yields resource production data for streaming."""
    print("Sending ResourceProductionInitInfo")
    yield virdi_pb2.ResourceProduction(
        init_info=virdi_pb2.ResourceProductionInitInfo(resource_id=resource_id)
    )
    try:
        while not stop_production.is_set():
            print("Sending ResourceProduction")
            yield virdi_pb2.ResourceProduction(amount=10)
            time.sleep(1)
    finally:
        print("Closing ResourceProduction")


def main():
    args = get_args()
    # Setting client-id in metadata
    metadata = [("client-id", args.client_id)]
    stub = create_grpc_stub()

    print("Sending ProductionOffer")
    call = offer_production(stub, args.resource_id, metadata)

    for response in call:
        stop_production = threading.Event()
        try:
            print("Received ProductionRequest, starting production")
            stub.Produce(produce_resources(args.resource_id, stop_production), metadata=metadata)
        except grpc.RpcError as e:
            stop_production.set()
            if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
                print(f"Server stopped Production stream: '{e.details()}'")


if __name__ == "__main__":
    main()
