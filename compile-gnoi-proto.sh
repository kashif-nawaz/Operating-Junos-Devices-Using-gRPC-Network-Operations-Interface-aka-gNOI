#!/usr/bin/env bash

src=src/gnoi/proto
fileList="types common cert diag file os system"

echo "Updating proto file source location and import statements"
mkdir -p $src

for p in $fileList; do
    cp src/github.com/openconfig/gnoi/$p/$p.proto $src
    python3 -c "
import re
with open('$src/$p.proto', 'r') as fd:
    data = fd.read()
data1 = re.sub(r'import \"(common|types)\/((common|types).proto)\"', r'import \"\2\"', data)
with open('$src/$p.proto', 'w') as fd:
    fd.write(data1)    "
done

echo "Compiling proto files"
for p in $fileList; do
    python3 -m grpc_tools.protoc --proto_path=$src --python_out=$src --grpc_python_out=$src $p.proto
done
