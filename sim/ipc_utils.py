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
EndpointAddressModifiers = (
    0x00,   # Place holder to align pipe indices
    0xCA,   # DEVICE CONTROL
    0xC5,   # NETWORK_SERVICES
    0x54,   # DATA FORWARDING
    0xB3,   # APPLICATION DATA 0
    0xD3    # APPLICATION DATA 1
)


def _gen_ipc_path(path, base_mac, pipe) -> Path:
    if pipe == 0:
        ipc_path = Path(path, str(int(base_mac)) + ".ipc")
    else:
        masked_mac = (base_mac & ~0xFF) | EndpointAddressModifiers[pipe]
        ipc_path = Path(path, str(int(masked_mac)) + ".ipc")

    return ipc_path


def gen_ipc_path_for_rx_pipe(base_mac, pipe) -> Path:
    """
    Builds a path that should represent some RX pipe
    """
    base_path = Path("/tmp/ripple_ipc/rx")
    base_path.mkdir(exist_ok=True)
    return _gen_ipc_path(base_path, base_mac, pipe)


def gen_ipc_path_for_tx_pipe(base_mac, pipe) -> Path:
    """
    Builds a path that should represent some TX pipe
    """
    base_path = Path("/tmp/ripple_ipc/tx")
    base_path.mkdir(exist_ok=True)
    return _gen_ipc_path(base_path, base_mac, pipe)
