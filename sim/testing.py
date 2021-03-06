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


def main() -> None:
    radio = ShockBurstRadio()
    radio.start()

    dst_mac = 0xB4B5B6B7B5
    src_mac = 0xA4A5A6A7A0

    radio.set_device_mac(src_mac)
    radio.open_tx_pipe(dst_mac, 1)

    while True:
        time.sleep(0.1)

    radio.kill()
    radio.join()


if __name__ == "__main__":
    main()