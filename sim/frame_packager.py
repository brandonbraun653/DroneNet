# **********************************************************************************************************************
#   FileName:
#       frame_packager.py
#
#   Description:
#       Utilities for packing and unpacking frames
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

from typing import Union


class PackedFrame:
    """
    Python representation of the PackedFrame structure defined in data_link_frame.hpp
    of the Ripple NRF24L01 NetIf module.
    """
    # Note that offsets here reference a SINGLE byte and masks are NOT shifted
    # ---------------------------------------------
    # Byte 0
    # ---------------------------------------------
    VERSION_LENGTH_BITS = 3
    VERSION_LENGTH_OFFSET = 0
    VERSION_LENGTH_MASK = 0x7
    DATA_LENGTH_BITS = 5
    DATA_LENGTH_OFFSET = 3
    DATA_LENGTH_MASK = 0x1F

    # ---------------------------------------------
    # Byte 1
    # ---------------------------------------------
    FRAME_NUMBER_BITS = 5
    FRAME_NUMBER_OFFSET = 0
    FRAME_NUMBER_MASK = 0x1F
    ENDPOINT_BITS = 3
    ENDPOINT_OFFSET = 5
    ENDPOINT_MASK = 0x7

    # ---------------------------------------------
    # Byte 2
    # ---------------------------------------------
    MULTICAST_LENGTH_BITS = 1
    MULTICAST_LENGTH_OFFSET = 0
    MULTICAST_LENGTH_MASK = 0x1
    REQ_ACK_LENGTH_BITS = 1
    REQ_ACK_LENGTH_OFFSET = 1
    REQ_ACK_LENGTH_MASK = 0x1
    PAD_LENGTH_BITS = 6
    PAD_LENGTH_OFFSET = 2
    PAD_LENGTH_MASK = 0x3F

    # ---------------------------------------------
    # Various properties
    # ---------------------------------------------
    MAX_FRAME_SIZE = 32  # Max number of bytes per transfer supported by the NRF24L01 radio
    CONTROL_FIELD_SIZE = 3  # Bytes

    def __init__(self):
        self.version = 0
        self.multicast = False
        self.requireAck = False
        self.dataLength = 0
        self.frameNumber = 0
        self.endpoint = 0
        self.userData = bytearray(29)
        self._pad0 = 0

        # Some runtime checks to ensure sizing constraints are met
        assert(len(self.userData) + self.CONTROL_FIELD_SIZE == self.MAX_FRAME_SIZE)

    def write_data(self, data: Union[bytearray, bytes]) -> None:
        """
        Takes byte level data and places it into the output buffer storage.
        Args:
            data: Data to be placed

        Returns:
            None
        """
        assert(len(data) <= len(self.userData))
        self.userData[:len(data)] = data
        self.dataLength = len(data)

    def read_data(self) -> bytearray:
        """
        Reads the packed user data out to the caller

        Returns:
            User data
        """
        assert(self.dataLength < len(self.userData))
        return self.userData[:self.dataLength]

    def pack(self) -> bytearray:
        """
        Packs the class attributes into a network transferable byte array

        Returns:
            bytearray of data to be transmitted
        """
        buffer = bytearray(self.MAX_FRAME_SIZE)
        buffer.zfill(self.MAX_FRAME_SIZE)

        # ---------------------------------------------
        # Pack the user data
        # ---------------------------------------------
        buffer[self.CONTROL_FIELD_SIZE:] = self.userData

        # ---------------------------------------------
        # Pack the control field
        # ---------------------------------------------
        # Byte 0
        version_bytes = (self.version & self.VERSION_LENGTH_MASK) << self.VERSION_LENGTH_OFFSET
        data_len_bytes = (self.dataLength & self.DATA_LENGTH_MASK) << self.DATA_LENGTH_OFFSET
        buffer[0] = version_bytes | data_len_bytes

        # Byte 1
        frame_num_bytes = (self.frameNumber & self.FRAME_NUMBER_MASK) << self.FRAME_NUMBER_OFFSET
        endpoint_bytes = (self.endpoint & self.ENDPOINT_MASK) << self.ENDPOINT_OFFSET
        buffer[1] = frame_num_bytes | endpoint_bytes

        # Byte 2
        multi_cast_bytes = (self.multicast & self.MULTICAST_LENGTH_MASK) << self.MULTICAST_LENGTH_OFFSET
        require_ack_bytes = (self.requireAck & self.REQ_ACK_LENGTH_MASK) << self.REQ_ACK_LENGTH_OFFSET
        buffer[2] = multi_cast_bytes | require_ack_bytes

        return buffer

    def unpack(self, data: bytearray) -> None:
        """
        Unpacks the data into the appropriate class attributes

        Returns:
            None
        """
        assert(len(data) == self.MAX_FRAME_SIZE)

        # Unpack the user data first. That's the easiest.
        self.userData = data[self.CONTROL_FIELD_SIZE:]

        # Next unpack the control field, assuming little endian
        self.version = int((data[0] >> self.VERSION_LENGTH_OFFSET) & self.VERSION_LENGTH_MASK)
        self.dataLength = int((data[0] >> self.DATA_LENGTH_OFFSET) & self.DATA_LENGTH_MASK)

        self.frameNumber = int((data[1] >> self.FRAME_NUMBER_OFFSET) & self.FRAME_NUMBER_MASK)
        self.endpoint = int((data[1] >> self.ENDPOINT_OFFSET) & self.ENDPOINT_MASK)

        self.multicast = int((data[2] >> self.MULTICAST_LENGTH_OFFSET) & self.MULTICAST_LENGTH_MASK)
        self.requireAck = int((data[2] >> self.REQ_ACK_LENGTH_OFFSET) & self.REQ_ACK_LENGTH_MASK)


