import threading
import time
import uuid
import grpc
import argparse

import app.grpc_service.proto.virdi_pb2 as virdi_pb2
import app.grpc_service.proto.virdi_pb2_grpc as virdi_pb2_grpc


def get_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="gRPC Consumer Client for ViRDi")
    parser.add_argument("--client-id", type=str, default=str(uuid.uuid4())[:8],
                        help="Optional client ID. Defaults to a random string.")
    parser.add_argument("--consumer-id", type=str, default=str(uuid.uuid4())[:8],
                        help="Optional consumer ID. Defaults to a random string.")
    parser.add_argument("--resource-id", type=str, default="iron",
                        help="Resource ID to consume.")
    parser.add_argument("--max-rate", type=int, default=60,
                        help="Max rate to consume the resource in (1/min).")
    return parser.parse_args()


def create_grpc_stub():
    """Creates a gRPC channel and stub."""
    channel = grpc.insecure_channel('localhost:50051')
    stub = virdi_pb2_grpc.VirdiStub(channel)
    return stub


def request_consumption(stub, consumer_id, resource_id, max_rate, metadata):
    print(f"{consumer_id=}, {resource_id=}, {max_rate=}")
    """Offers a production request to the gRPC server."""
    production_offer = virdi_pb2.ConsumptionRequest(
        consumer_id=consumer_id,
        resource_id=resource_id,
        max_rate=max_rate
    )
    return stub.Consume(production_offer, metadata=metadata)


def main():
    args = get_args()
    # Setting client-id in metadata
    metadata = [("client-id", args.client_id)]
    stub = create_grpc_stub()

    print("Sending ProductionOffer")
    call = request_consumption(stub, args.consumer_id, args.resource_id, args.max_rate, metadata)

    amount = 0

    for response in call:
        amount += response.amount
        print(amount)


if __name__ == "__main__":
    main()
