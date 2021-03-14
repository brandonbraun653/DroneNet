#!/bin/bash
# Note: This file expects environment variables to be set in order to get the correct
#       paths for .proto resources. When written, this was accomplished by a bootstrap
#       file in the project root.
#
# NanoPB Git: https://github.com/nanopb/nanopb
# NANOPB_PROTO_DIR: Absolute path to "nanopb/generator/proto"

THIS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
protoc --proto_path=$NANOPB_PROTO_DIR --proto_path=$THIS_DIR --python_out=$THIS_DIR "$THIS_DIR/shockburst.proto"