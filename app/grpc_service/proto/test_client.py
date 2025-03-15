import grpc

import virdi_pb2
import virdi_pb2_grpc

# open a gRPC channel
channel = grpc.insecure_channel('localhost:50051')

# create a stub (client)
stub = virdi_pb2_grpc.VirdiStub(channel)
metadata = [("client-id", "12345")]

production_offer = virdi_pb2.ProductionOffer(
    resource_id="iron"
)

# make the call
response = stub.OfferProduction(production_offer, metadata=metadata)


# time.sleep(5)

def produce_resources():
    yield virdi_pb2.ResourceProduction(
        init_info=virdi_pb2.ResourceProductionInitInfo(
            resource_id="iron"
        )
    )
    for amount in [10, 20, 30, 40, 50]:  # Example amounts
        yield virdi_pb2.ResourceProduction(
            amount=amount
        )


try:
    for r in response:
        print("Production request", r)
        response = stub.Produce(produce_resources(), metadata=metadata)
except KeyboardInterrupt:
    pass

response.cancel()
