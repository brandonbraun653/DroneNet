# **********************************************************************************************************************
#   FileName:
#       testing.py
#
#   Description:
#
#
#   3/4/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

import time
from virtual_shockburst import ShockBurstRadio

PIPE_TX = 0
PIPE_DEVICE_ROOT = 1
PIPE_NET_SERVICES = 2
PIPE_DATA_FWD = 3
PIPE_APP_DATA_0 = 4
PIPE_APP_DATA_1 = 5


def main() -> None:
    radio = ShockBurstRadio()
    radio.start()

    dst_mac = 0xB4B5B6B7B5
    src_mac = 0xA4A5A6A7A0

    radio.set_device_mac(src_mac)
    # radio.open_tx_pipe(dst_mac, PIPE_APP_DATA_0)

    while True:
        time.sleep(0.1)

    radio.kill()
    radio.join()


if __name__ == "__main__":
    main()
