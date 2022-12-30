import grpc
from os.path import isfile


def grpc_authenticate_channel_mutual(server, port, root_ca_cert="", client_key="", client_cert=""):
    if not isfile(root_ca_cert):
        raise Exception("Error: root_ca_cert file does not exist")
    if (client_key == "") or (not isfile(client_key)):
        raise Exception(
            "Error: client_key option is missing or target file does not exist")
    elif (client_cert == "") or (not isfile(client_cert)):
        raise Exception(
            "Error: client_cert option is empty or target file does not exist")

    print("Creating channel")
    creds = grpc.ssl_channel_credentials(open(root_ca_cert, 'rb').read(),
                                         open(client_key, 'rb').read(),
                                         open(client_cert, 'rb').read())
    channel = grpc.secure_channel('%s:%s' % (server, port), creds)

    return channel


def grpc_authenticate_channel_server_only(server, port, root_ca_cert=""):
    if isfile(root_ca_cert):
        print("Creating channel")
        creds = grpc.ssl_channel_credentials(open(root_ca_cert, 'rb').read(),
                                             None,
                                             None)
        channel = grpc.secure_channel('%s:%s' % (server, port), creds)
        return channel
    else:
        raise Exception("root_ca_cert file does not exist")
