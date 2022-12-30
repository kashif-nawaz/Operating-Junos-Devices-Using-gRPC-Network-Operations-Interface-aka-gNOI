"""gRPC gNOI OS Upgrade Utility."""

from __future__ import print_function
import argparse
import hashlib
import logging
from functools import partial
from getpass import getpass

import system_pb2
import system_pb2_grpc
from grpc_channel import grpc_authenticate_channel_mutual

MAX_BYTES = 65536


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

    parser.add_argument('--activate',
                        dest='activate',
                        type=int,
                        default=0,
                        help='Reboot and activate the package. Default: 0 (Do not reboot/activate). Valid value: 1 (Reboot/activate).')

    parser.add_argument('--filename',
                        dest='filename',
                        type=str,
                        default='',
                        help='Destination path and filename of the package.  Default ""')

    parser.add_argument('--source_package',
                        dest='source_package',
                        type=str,
                        default='',
                        help='Full path of the source file to send.  Default ""')

    parser.add_argument('--timeout',
                        dest='timeout',
                        type=int,
                        default=None,
                        help='Timeout in seconds.')

    parser.add_argument('--version',
                        dest='version',
                        type=str,
                        default='',
                        help='Version of the package.  Default ""')

    args = parser.parse_args()
    return args


def send_rpc(channel, metadata, args):
    stub = system_pb2_grpc.SystemStub(channel)

    print("Executing GNOI::System::SetPackage")

    # Create request
    # Add file information to request
    req = system_pb2.SetPackageRequest()
    req.package.activate = args.activate
    req.package.filename = args.filename
    it = []
    it.append(req)

    # Prepare hash generator
    gen_hash = hashlib.sha256()

    # Read source package and add to request
    with open(args.source_package, "rb") as fd:
        # Read data in 64 KB chunks and calculate checksum and data messages
        for data in iter(partial(fd.read, MAX_BYTES), b''):
            req = system_pb2.SetPackageRequest()
            req.contents = data
            it.append(req)
            gen_hash.update(data)

    # Add checksum to request
    req = system_pb2.SetPackageRequest()
    req.hash.hash = gen_hash.hexdigest().encode()
    req.hash.method = 1
    it.append(req)

    # Install the package
    try:
        logging.info('Installing package %s', args.source_package)
        print('SetPackage start.')
        response = stub.SetPackage(
            iter(it), metadata=metadata, timeout=args.timeout)
        print('SetPackage complete.')
    except Exception as e:
        logging.error('Software install error: %s', e)
        print(e)
    else:
        logging.info('SetPackage complete.')
        return response


def main():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    args = get_args(parser)

    grpc_server_password = getpass("gRPC server password for executing RPCs: ")
    metadata = [('username', args.user_id),
                ('password', grpc_server_password)]

    try:
        # Establish grpc channel to network device
        channel = grpc_authenticate_channel_mutual(
            args.server, args.port, args.root_ca_cert, args.client_key, args.client_cert)
        response = send_rpc(channel, metadata, args)
    except Exception as e:
        logging.error('Error: %s', e)
        print(e)


if __name__ == '__main__':
    logging.basicConfig(filename='gnoi-install.log',
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S')
    main()
