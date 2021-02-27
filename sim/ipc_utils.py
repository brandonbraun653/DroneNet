# **********************************************************************************************************************
#   FileName:
#       ipc_utils.py
#
#   Description:
#       Utilities for IPC with ZMQ
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

from pathlib import Path

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
