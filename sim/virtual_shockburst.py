# **********************************************************************************************************************
#   FileName:
#       virtual_shockburst.py
#
#   Description:
#       Creates a virtual PHY layer that mimics the behavior of the NRF24 ShockBurst protocol
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

import time
import zmq
from threading import Thread, Rlock
from multiprocessing import Queue
from ipc_utils import gen_ipc_path_for_rx_pipe, gen_ipc_path_for_tx_pipe
from frame_interface import BaseFrame, RxFifoEntry
from frame_packager import PackedFrame
from network_frames import *


class ShockBurstRadio(Thread):

    def __init__(self):
        super().__init__()
        self.mac_address = 0

        self.context = zmq.Context()
        self.txPipe = self.context.socket(zmq.PUSH)
        self.rxPipe = [self.context.socket(zmq.PULL) for x in range(self.available_rx_pipes())]

        self._txQueue = Queue()
        self._txLock = Rlock()
        self._rxQueue = Queue()
        self._rxLock = Rlock()

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
        # ---------------------------------------------
        # Connect this TX pipe to destination RX pipe
        # ---------------------------------------------
        rx_ipc_path = gen_ipc_path_for_rx_pipe(mac, 0)
        mbed_rx_url = "ipc://" + str(rx_ipc_path)
        self.txPipe.connect(mbed_rx_url)
        print("TX pipe connected to {}".format(mbed_rx_url))

        # ---------------------------------------------
        # Open this RX pipe to listen for TX responses
        # ---------------------------------------------
        rx_ipc_path = gen_ipc_path_for_rx_pipe(mac, 0)

        mbed_rx_url = "ipc://" + str(rx_ipc_path)
        self.rxPipe[0].connect(mbed_rx_url)
        print("TX pipe connected to {}".format(mbed_rx_url))

    def open_rx_pipe(self, mac: int) -> None:
        """
        Opens up the root RX pipe with the given mac and then opens the
        remaining pipes following the NRF24L01 addressing scheme. Assumes
        all 5 bytes are used.

        Args:
            mac: Root MAC address
        """
        # ---------------------------------------------
        # Generate the MAC addresses for all RX pipes
        # ---------------------------------------------
        rx_ipc_paths = [gen_ipc_path_for_rx_pipe(mac, x+1) for x in range(5)]

        idx = 1
        for path in rx_ipc_paths:
            url = "ipc://" + str(path)
            self.rxPipe[idx].bind(url)
            print("RX pipe {} connected to {}".format(idx, url))
            idx += 1

    def transmit(self, data: bytearray) -> None:
        with self._txLock:
            self._txQueue.put(data)

    def receive(self, block, timeout) -> RxFifoEntry:
        with self._rxLock:
            return self._rxQueue.get(block=block, timeout=timeout)

    def run(self) -> None:
        """
        Main message pump that acts as the hardware transceiver in the NRF24L01
        """
        last_processed = time.time()
        process_period = 0.025

        while True:
            # Calculate time remaining until next processing period
            sleep_time = (last_processed + process_period) - time.time()
            if sleep_time < 0.0:
                print("ShockBurst processing overrun!")
                sleep_time = process_period

            # Perform the periodic sleep
            time.sleep(sleep_time)

            # Pump messages through the "transceiver"
            self._enqueue_rx_pipes()
            self._dequeue_tx_pipes()

    def _enqueue_rx_pipes(self) -> None:
        """
        Enqueues all data that may be present in the RX pipes
        Returns:
            None
        """
        with self._rxLock():
            for pipe in range(1, 6):
                # ---------------------------------------------
                # Any data available?
                # ---------------------------------------------
                data = self.rxPipe[pipe].recv(flags=zmq.DONTWAIT)
                if not data:
                    continue

                # ---------------------------------------------
                # Enqueue the RX'd frame
                # ---------------------------------------------
                frame = PackedFrame()
                frame.unpack(data)
                self._rxQueue.put(RxFifoEntry(pipe, frame))

                # ---------------------------------------------
                # If required, transmit an ACK
                # ---------------------------------------------
                if frame.requireAck:
                    self.txPipe.send(ACKFrame().to_bytes())

    def _dequeue_tx_pipes(self) -> None:
        """
        Transmits all data available in the TX queue
        Returns:
            None
        """
        ack_timeout = 5

        with self._txLock:
            while not self._txQueue.empty():
                # ---------------------------------------------
                # Transmit the raw data
                # ---------------------------------------------
                next_frame = PackedFrame()
                next_frame.unpack(self._txQueue.get())

                self.txPipe.send(next_frame.pack())

                # ---------------------------------------------
                # Wait for the ACK if needed
                # ---------------------------------------------
                if next_frame.requireAck:
                    start_time = time.time()
                    received = False

                    while (time.time() - start_time) < ack_timeout:
                        time.sleep(0.01)

                        ack = ACKFrame()
                        ack.from_bytes(self.rxPipe[0].recv(flags=zmq.DONTWAIT))

                        if ack.is_valid():
                            received = True
                            break

                    # Notify if transmit failed
                    if not received:
                        print("Failed to receive packet ACK")



