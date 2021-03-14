include("${COMMON_TOOL_ROOT}/cmake/utility/embedded.cmake")

project(NanoPB_Netif_NRF24 C)

# Generates the shockburst.pb.c/h files
nanopb_generate_cpp(PROTO_SRCS PROTO_HDRS shockburst.proto)
set_source_files_properties(${PROTO_SRCS} ${PROTO_HDRS} PROPERTIES GENERATED TRUE)

# Library target that builds the generated sources
gen_static_lib_variants(
  TARGET
    ripple_netif_nrf24_protobuf
  SOURCES
    ${PROTO_SRCS}
  PRV_INCLUDES
    .
    ${NANOPB_INCLUDE_DIRS}
  EXPORT_DIR
    "${PROJECT_BINARY_DIR}/Ripple/netif/protobuf"
)

# Target for getting the location of the generated headers
gen_intf_lib(
  TARGET
    ripple_netif_nrf24_protobuf_intf
  INTF_INCLUDES
    ${CMAKE_CURRENT_BINARY_DIR}
  EXPORT_DIR
    "${PROJECT_BINARY_DIR}/Ripple/netif/protobuf"
)

add_custom_command(OUTPUT shockburst_pb2.py
  COMMAND
  DEPENDS shockburst_pb2.py
)