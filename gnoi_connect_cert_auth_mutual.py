"""gRPC gNOI Time request utility."""

from __future__ import print_function
import argparse
import logging
from getpass import getpass

import system_pb2
import system_pb2_grpc

from grpc_channel import grpc_authenticate_channel_mutual


def get_args(parser):
    parser.add_argument('--server',
                        dest='server',
                        type=str,
                        default='localhost',
                        help='Server IP or name.  Default is localhost')

    parser.add_argument('--port',
                        dest='port',
                        nargs='?',
                        type=int,
                        default=50051,
                        help='The server port. Default is 50051')

    parser.add_argument('--client_key',
                        dest='client_key',
                        type=str,
                        default='',
                        help='Full path of the client private key.  Default ""')

    parser.add_argument('--client_cert',
                        dest='client_cert',
                        type=str,
                        default='',
                        help='Full path of the client certificate.  Default ""')

    parser.add_argument('--root_ca_cert',
                        dest='root_ca_cert',
                        required=True,
                        type=str,
                        help='Full path of the Root CA certificate.')

    parser.add_argument('--user_id',
                        dest='user_id',
                        required=True,
                        type=str,
                        help='User ID for RPC call credentials.')

    args = parser.parse_args()
    return args


def send_rpc(channel, metadata):
    stub = system_pb2_grpc.SystemStub(channel)
    print("Executing GNOI::System::Time RPC")
    req = system_pb2.TimeRequest()
    try:
        response = stub.Time(request=req, metadata=metadata, timeout=60)
    except Exception as e:
        logging.error('Error executing RPC: %s', e)
        print(e)
    else:
        logging.info('Received message: %s', response)
        return response


def main():
    parser = argparse.ArgumentParser()
    args = get_args(parser)

    grpc_server_password = getpass("gRPC server password for executing RPCs: ")
    metadata = [('username', args.user_id),
                ('password', grpc_server_password)]

    try:
        # Establish grpc channel to network device
        channel = grpc_authenticate_channel_mutual(
            args.server, args.port, args.root_ca_cert, args.client_key, args.client_cert)
        response = send_rpc(channel, metadata)
        print("Response received: time since last epoch in nanoseconds is ", str(response))
    except Exception as e:
        logging.error('Received error: %s', e)
        print(e)


if __name__ == '__main__':
    logging.basicConfig(filename='gnoi-testing.log',
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    main()
