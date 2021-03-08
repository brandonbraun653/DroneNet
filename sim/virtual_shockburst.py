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
from threading import Thread, RLock, Event
from multiprocessing import Queue
from ipc_utils import gen_ipc_path_for_rx_pipe, gen_ipc_path_for_tx_pipe
from frame_interface import BaseFrame, RxFifoEntry
from frame_packager import PackedFrame
from network_frames import *


class ShockBurstRadio(Thread):
    TOPIC_DATA = b'packet'
    TOPIC_SHOCKBURST = b'shockburst'

    def __init__(self):
        super().__init__()
        self.mac_address = 0

        # ---------------------------------------------------------------------
        # Create pub/sub sockets for all pipes. Only pipe 0 is used for actual
        # data transmission. Pipes 1-5 are used to mimic ShockBurst functions
        # like auto-ack or ack-payloads without getting in the way of pipe 0.
        # ---------------------------------------------------------------------
        self.context = zmq.Context()
        self.txPipe = [self.context.socket(zmq.PUSH) for x in range(self.total_pipes())]
        self.rxPipe = [self.context.socket(zmq.PULL) for x in range(self.total_pipes())]

        # ---------------------------------------------
        # Internal multi-threading utilities
        # ---------------------------------------------
        self._txQueue = Queue()
        self._txLock = RLock()
        self._rxQueue = Queue()
        self._rxLock = RLock()
        self._kill_switch = Event()

    @staticmethod
    def available_tx_pipes():
        return 1

    @staticmethod
    def available_rx_pipes():
        return 6

    @staticmethod
    def total_pipes():
        return 6

    def kill(self) -> None:
        self._kill_switch.set()

    def open_tx_pipe(self, dst_mac: int, pipe: int) -> None:
        """
        Opens a TX pipe to an RX pipe on a given MAC address. Also opens
        RX pipe 0 for receiving any ACKS or additional data.

        Args:
            dst_mac: Address to open the pipe to
            pipe: Which pipe to write to on the destination. Should be 1-5.
        """
        # ---------------------------------------------------------------------
        # Figure out the address of the RX pipe on the destination device, then
        # instruct Pipe 0 publisher to open a connection to it. If that RX pipe
        # exists, it will have attempted to connect to the publisher already.
        # ---------------------------------------------------------------------
        tx_ipc_path = gen_ipc_path_for_rx_pipe(dst_mac, pipe)
        tx_url = "ipc://" + str(tx_ipc_path)
        self.txPipe[0].connect(tx_url)
        print("TX pipe 0 bound to device {} pipe {}. IPC address: {}".format(hex(dst_mac), pipe, tx_url))

        # ---------------------------------------------------------------------
        # Set up pipe 0 RX socket to subscribe to messages from the destination
        # device's pipe <x> TX socket. This will allow us to receive ShockBurst
        # messages in reply should they be needed.
        # ---------------------------------------------------------------------
        rx_ipc_path = gen_ipc_path_for_tx_pipe(dst_mac, pipe)
        rx_url = "ipc://" + str(rx_ipc_path)
        self.rxPipe[0].bind(rx_url)
        print("RX pipe 0 listen to device {} pipe {}. IPC address: {}".format(hex(dst_mac), pipe, rx_url))

    def set_device_mac(self, mac: int) -> None:
        """
        Opens up the root RX pipe with the given mac and then opens the
        remaining pipes following the NRF24L01 addressing scheme. Assumes
        all 5 bytes are used.

        Note:
            Only pipes 1-5 are valid for receiving data. Pipe 0 is dedicated
            for communication with other nodes in conjunction with the TX pipe.

        Args:
            mac: Root MAC address
        """
        rx_ipc_paths = [gen_ipc_path_for_rx_pipe(mac, x) for x in range(self.total_pipes())]

        idx = 0
        for path in rx_ipc_paths:
            # url = "ipc://" + str(path)
            url = "tcp://127.0.0.1:1234"
            self.rxPipe[idx].connect(url)
            # self.rxPipe[idx].set(zmq.SUBSCRIBE, b'')
            #self.rxPipe[idx].set(zmq.SUBSCRIBE, self.TOPIC_DATA)
            #self.rxPipe[idx].set(zmq.SUBSCRIBE, self.TOPIC_SHOCKBURST)
            print("RX pipe {} on device {} is listening on {}".format(idx, hex(mac), url))
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
        process_period = 0.1
        print("Starting ShockBurst processing")
        time.sleep(0.5)

        while not self._kill_switch.is_set():
            # Pump messages through the "transceiver"
            time.sleep(process_period)
            self._enqueue_rx_pipes()
            self._dequeue_tx_pipes()

        print("Killing ShockBurst thread")

    def _enqueue_rx_pipes(self) -> None:
        """
        Enqueues all data that may be present in the RX pipes
        Returns:
            None
        """
        with self._rxLock:

            for pipe in range(self.available_rx_pipes()):
                # ---------------------------------------------
                # Any data available?
                # ---------------------------------------------
                try:
                    data = self.rxPipe[pipe].recv(flags=zmq.DONTWAIT)
                    if not data:
                        continue
                except zmq.Again:
                    continue

                # ---------------------------------------------
                # Enqueue the RX'd frame
                # ---------------------------------------------
                frame = PackedFrame()
                frame.unpack(data)
                self._rxQueue.put(RxFifoEntry(pipe, frame))

                # Will need to reconfigure the TX pipe for sending back to the source node

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
                        try:
                            ack = ACKFrame()
                            ack.from_bytes(self.rxPipe[0].recv(flags=zmq.DONTWAIT))

                            if ack.is_valid():
                                received = True
                                break
                        except zmq.Again:
                            continue

                    # Notify if transmit failed
                    if not received:
                        print("Failed to receive packet ACK")



