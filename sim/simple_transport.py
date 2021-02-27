# **********************************************************************************************************************
#   FileName:
#       simple_transport.py
#
#   Description:
#       Tests a very simple communication to the virtual device driver on the embedded code
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

import zmq
from pathlib import Path

from binascii import hexlify
from frame_packager import PackedFrame

# ---------------------------------------------
# NRF24 radio hardware addresses. Ordering is
# swapped from the embedded code.
# ---------------------------------------------
srcMAC = 0xA4A5A6A7A0
dstMAC = 0xB4B5B6B7B5

# ---------------------------------------------
# Address modifiers for pipes. Must match code.
# ---------------------------------------------
EndpointAddressModifiers = {
    0xCA,   # DEVICE CONTROL
    0xC5,   # NETWORK_SERVICES
    0x54,   # DATA FORWARDING
    0xB3,   # APPLICATION DATA 0
    0xD3    # APPLICATION DATA 1
  }


def gen_ipc_path_for_rx_pipe(base_mac, pipe) -> Path:
    """
    Builds a path that should represent some RX pipe
    """
    base_path = Path("/tmp/ripple_ipc/rx_endpoint")
    if pipe == 0:
        ipc_path = Path(base_path, str(int(base_mac)) + ".ipc")
    else:
        masked_mac = (base_mac & ~0xFF) | EndpointAddressModifiers[pipe]
        ipc_path = Path(base_path, str(int(masked_mac)) + ".ipc")

    return ipc_path


def gen_ipc_path_for_tx_pipe(mac) -> Path:
    """
    Builds a path that should represent some TX pipe
    """
    ipc_path = Path("/tmp/ripple_ipc/tx_endpoint", str(int(mac)) + ".ipc")
    return ipc_path


if __name__ == "__main__":
    context = zmq.Context()
    rxPipe = context.socket(zmq.PULL)
    txPipe = context.socket(zmq.PUSH)

    # ---------------------------------------------
    # Connect RX pipe to the embedded TX pipe
    # ---------------------------------------------
    mbed_tx_ipc_path = gen_ipc_path_for_tx_pipe(srcMAC)
    assert(mbed_tx_ipc_path.exists())
    mbed_tx_url = "ipc://" + str(mbed_tx_ipc_path)
    rxPipe.bind(mbed_tx_url)
    print("RX pipe connected to {}".format(mbed_tx_url))

    # ---------------------------------------------
    # Connect TX pipe to the embedded RX pipe
    # ---------------------------------------------
    mbed_rx_ipc_path = gen_ipc_path_for_rx_pipe(srcMAC, 0)
    assert(mbed_rx_ipc_path.exists())
    mbed_rx_url = "ipc://" + str(mbed_rx_ipc_path)
    txPipe.connect(mbed_rx_url)
    print("TX pipe connected to {}".format(mbed_rx_url))

    tmp_data = int(0xAABBCCDD).to_bytes(4, 'little')

    ack_frame = PackedFrame()
    ack_frame.write_data(tmp_data)

    while True:
        data = rxPipe.recv()
        frame = PackedFrame()
        frame.unpack(data)

        if data:
            print("Version: {}".format(frame.version))
            print("Data: {}".format(frame.read_data()))
            print("Sending ACK")
            txPipe.send(ack_frame.pack())


