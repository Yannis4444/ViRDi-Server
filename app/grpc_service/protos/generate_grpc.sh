cd ..
python -m grpc_tools.protoc -Igrpc_service/protos --python_out=grpc_service/proto --grpc_python_out=grpc_service/proto grpc_service/protos/virdi.proto
# import in virdi_pb2_grpc.py needs to be fixed afterwards