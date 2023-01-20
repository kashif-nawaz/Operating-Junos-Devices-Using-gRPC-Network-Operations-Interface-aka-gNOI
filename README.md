# Operating-Junos-Devices-Using-gRPC-Network-Operations-Interface-gNOI
* In this wiki I will explain how to operate Junos devices with gRPC Network Operations Interface (gNOI).
## References
* Junos support gRPC working groups (gNOI, gNMI specifications) [Reference](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/concept/grpc-services-overview.html#:~:text=Whereas%20gNMI%20handles%20state%20management,common%20operations%20on%20network%20devices.)
* To get more information about gRPC Network Operations Interface (gNOI), please explore the [document](https://grpc.io/).
## Execution
* TLS based mutual authentication  is required between gRPC Server (Junos Device) and client (Ubuntu 20.04 in my case).
* gRPC server (Junos Device) needs to have its  own certificate and private key along with CA certificate.
* gRPC Client needs to have its own certificate and private key along with CA certificate.
* To meet above requirments, I will use self-signed certificates.
### Prepare  Self-Signed Certificates
* CA Cert
```
mkdir ~/PKI
cd ~/PKI
openssl genrsa -out ca.key 4096
openssl req -new -sha256 -key ca.key -subj "/CN=DEMO-LAB" -out ca.csr
openssl req -in ca.csr -noout ca.csr
openssl req -in ca.csr -noout -text
openssl req -x509 -sha256 -days 365 -key ca.key -in ca.csr -out ca.pem
```
* gRPC client Cert
```
openssl genrsa -out mgmt-client.key 4096
openssl req -new -sha256 -key mgmt-client.key -subj "/CN=mgmt-client" -out mgmt-client.csr
openssl req -in mgmt-client.csr --noout text
openssl x509 -req -in mgmt-client.csr -CAcreateserial -CAserial ca.seq -sha256 -days 365 -CA ca.pem -CAkey ca.key -out mgmt-client.crt
```
* gRPC Server Cert
* Hence gRPC client will connect with the gRPC server (Junos Device) using IP-Address so certificate needs to be signed using Subject-Alternate-Name (SAN) as Common Name (CN) can't have IP-Address entry. 
```
openssl genrsa -out A1-R2.key 4096 
openssl req -new -sha256 \
    -key A1-R2.key \
    -subj "/C=US/ST=CA/O=DEMO-LAB, Inc./CN=A1-R2" \
    -reqexts SAN \
    -config <(cat /etc/ssl/openssl.cnf \
        <(printf "\n[SAN]\nsubjectAltName=IP:192.168.10.10")) \
    -out A1-R2.csr

openssl x509 -req -extfile <(printf "subjectAltName=IP:192.168.10.10") -days 365 -in  A1-R2.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out  A1-R2.crt 
```
## Prepare gRPC Server (Junos Device) for gRPC Connections
* Copy gRPC Server Cert, Key and CA Cert into Junos Device.
```
scp A1-R2.crt user@192.168.10.10:/var/tmp
scp A1-R2.key user@192.168.10.10:/var/tmp
scp ca.pem user@192.168.10.10:/var/tmp
```
* Load the Certificate into Junos Device 
```
request security pki local-certificate load certificate-id gnoi-server filename /var/tmp/A1-R2.crt key /var/tmp/A1-R2.key
show security pki local-certificate certificate-id gnoi-server
```
* Configure Junos Device for gRPC Sessions
```
edit
set system services extension-service request-response grpc ssl port 50051
set system services extension-service request-response grpc ssl local-certificate gnoi-server
set system services extension-service request-response grpc ssl mutual-authentication certificate-authority gRPC
set system services extension-service request-response grpc ssl mutual-authentication client-certificate-request require-certificate-and-verify
set system services extension-service request-response grpc ssl hot-reloading
set system services extension-service request-response grpc ssl use-pki
set system services extension-service traceoptions file jsd
set system services extension-service traceoptions flag all
set security pki ca-profile gRPC ca-identity gRPC
commit and quit
request security pki ca-certificate load ca-profile gRPC filename /var/tmp/ca.pem 
```
## Prepare gRPC Client 
 
* [Reference](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/topic-map/gnoi-services-configuring.html).
* Installation of required packages.
```
sudo apt install python3-pip
mkdir -p src/github.com/openconfig/gnoi
git clone https://github.com/openconfig/gnoi.git src/github.com/openconfig/gnoi
sudo pip3 install grpcio
sudo pip3 install grpcio-tools
```
* Compile proto files by executing the script [compile-gnoi-proto.sh](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/topic-map/gnoi-services-configuring.html).
* Above named script is also uploaded with this wiki.
* Execute the script from parent directory of src directory created in above step.
```
cd ~/
sh compile-gnoi-proto.sh
Updating proto file source location and import statements
Compiling proto files
```
* Verify if proto files are compiled
```
ls ~/src/gnoi/proto
cert_pb2_grpc.py    common.proto      file_pb2.py     system_pb2_grpc.py  types.proto
cert_pb2.py         diag_pb2_grpc.py  file.proto      system_pb2.py
cert.proto          diag_pb2.py       os_pb2_grpc.py  system.proto
common_pb2_grpc.py  diag.proto        os_pb2.py       types_pb2_grpc.py
common_pb2.py       file_pb2_grpc.py  os.proto        types_pb2.py
```

### Test Connectivity between gRPC client and Server 
* For this step we need two python scripts [grpc_channel.py and gnoi_connect_cert_auth_mutual.py](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/topic-map/gnoi-services-configuring.html)
* Above named scripts are also uploaded with this wiki.
```
user@mgmt-client:~/src/gnoi/proto$ python3 gnoi_connect_cert_auth_mutual.py --server 192.168.10.10 --port 50051 --root_ca_cert PKI/ca.pem --client_key PKI/mgmt-client.key --client_cert  PKI/mgmt-client.crt --user_id user
gRPC server password for executing RPCs:
Creating channel
Executing GNOI::System::Time RPC
Response received: time since last epoch in nanoseconds is  time: 167242598263437500
```
### gNOI Supported Services in Junos
* [Reference](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/topic-map/gnoi-services-overview.html)
* I have used System Service [Software Upgrade](https://www.juniper.net/documentation/us/en/software/junos/grpc-network-services/topics/topic-map/gnoi-system-service.html#id-upgrade-software) for testing. 
* Prepare args_system_set_package.txt
```
cd ~/src/gnoi/proto
cat > args_system_set_package.txt << EOF

--root_ca_cert=~/PKI/ca.pem
--client_key=~/PKI/mgmt-client.key
--client_cert=~/PKI/mgmt-client.crt
--server=192.168.10.10
--port=50051
--user_id=user
--activate=0
--filename=/var/tmp/junos-evo-install-ptx-fixed-x86-64-22.3R1-S1.4-EVO.iso
--source_package=junos-evo-install-ptx-fixed-x86-64-22.3R1-S1.4-EVO.iso
--timeout=1800
EOF
```
* Junos  Upgrade via gNOI System Service Upgrade Software
```
user@mgmt-client:~/src/gnoi/proto$ python3 gnoi_system_set_package.py @args_system_set_package.txt 
gRPC server password for executing RPCs: 
Creating channel
Executing GNOI::System::SetPackage
SetPackage start.
SetPackage complete.
```
* Login to Junos EVO and check if new OS pakcage is installed

```
 show system software list
-------------------------------
node: re0
-------------------------------
Active boot device is primary: /dev/sda
List of installed version(s) :

    '-' running version
    '>' next boot version after upgrade/downgrade
    '<' rollback boot version
    '*' deleted JSU version

 >   junos-evo-install-ptx-fixed-x86-64-22.3R1-S1.4-EVO - [2023-01-18 14:15:56]
 -   junos-evo-install-ptx-fixed-x86-64-22.3R1.9-EVO - [2022-12-27 00:35:10]
     junos-evo-install-ptx-fixed-x86-64-22.4R1.11-EVO - [2022-12-30 18:20:40]
``` 
* Reboot the Junos EVO Box to activate new OS

```
cd ~/src/gnoi/proto$
cat > reboot_status_request_args.txt << EOF

--root_ca_cert=~/PKI/ca.pem
--client_key=~/PKI/mgmt-client.key
--client_cert=~/PKI/mgmt-client.crt
--server=192.168.10.10
--user_id=user
--message="Testing gNOI reboot"
--delay=60
EOF

user@mgmt-client:~/src/gnoi/proto$ python3 gnoi_reboot_status_request.py @reboot_status_request_args.txt
gRPC server password for executing RPCs:
Creating channel
Executing GNOI::System::Reboot RPC
Executing GNOI::System::Reboot Status RPC
Reboot status response received. active: true
wait: 59596694300
when: 1674080351000000000
reason: "\"Testing gNOI reboot\
```
* Junos EVO Box should show following message

```
System going down IMMEDIATELY

"Testing gNOI reboot"
```
* After reboot verify running OS in Junos EVO Box

```
show system software list
-------------------------------
node: re0
-------------------------------
Active boot device is primary: /dev/sda
List of installed version(s) :

    '-' running version
    '>' next boot version after upgrade/downgrade
    '<' rollback boot version
    '*' deleted JSU version

 -   junos-evo-install-ptx-fixed-x86-64-22.3R1-S1.4-EVO - [2023-01-18 14:15:56]
 <   junos-evo-install-ptx-fixed-x86-64-22.3R1.9-EVO - [2022-12-27 00:35:10]
     junos-evo-install-ptx-fixed-x86-64-22.4R1.11-EVO - [2022-12-30 18:20:40]

```
