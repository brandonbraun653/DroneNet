# **********************************************************************************************************************
#   FileName:
#       virtual_shockburst.py
#
#   Description:
#       Creates a virtual PHY layer that mimics the behavior of the NRF24 ShockBurst protocol
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

import zmq
import threading


create an ack frame class 

class ShockBurstRadio(threading.Thread):

    def __init__(self, mac):
        super().__init__()
        self.mac_address = mac

        self.context = zmq.Context()
        self.txPipe = self.context.socket(zmq.PUSH)
        self.rxPipe = [self.context.socket(zmq.PULL) for x in range(self.available_rx_pipes())]

    @staticmethod
    def available_tx_pipes():
        return 1

    @staticmethod
    def available_rx_pipes():
        return 5

    def open_tx_pipe(self, mac) -> None:
        """
        Opens a transmit pipe to the given MAC address. Also opens RX pipe 0 for
        receiving any ACKS or additional data.

        Args:
            mac: Address to open the pipe to
        """
        pass

    def open_rx_pipe(self, mac: int) -> None:
        """
        Opens up the root RX pipe with the given mac and then opens the
        remaining pipes following the NRF24L01 addressing scheme. Assumes
        all 5 bytes are used.

        Args:
            mac: Root MAC address
        """
        pass

    def run(self) -> None:
        """
        Main message pump that acts as the hardware transceiver in the NRF24L01
        """


