# **********************************************************************************************************************
#   FileName:
#       frame_packager.py
#
#   Description:
#       Utilities for packing and unpacking frames
#
#   2/27/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************


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
    FRAME_LENGTH_BITS = 5
    FRAME_LENGTH_OFFSET = 3
    FRAME_LENGTH_MASK = 0x1F

    # ---------------------------------------------
    # Byte 1
    # ---------------------------------------------
    MULTICAST_LENGTH_BITS = 1
    MULTICAST_LENGTH_OFFSET = 0
    MULTICAST_LENGTH_MASK = 0x1
    REQ_ACK_LENGTH_BITS = 1
    REQ_ACK_LENGTH_OFFSET = 1
    REQ_ACK_LENGTH_MASK = 0x1
    PAD_LENGTH_BITS = 1
    PAD_LENGTH_OFFSET = 2
    PAD_LENGTH_MASK = 0x1
    DATA_LENGTH_BITS = 5
    DATA_LENGTH_OFFSET = 3
    DATA_LENGTH_MASK = 0x1F

    # ---------------------------------------------
    # Byte 2
    # ---------------------------------------------
    FRAME_NUMBER_BITS = 5
    FRAME_NUMBER_OFFSET = 0
    FRAME_NUMBER_MASK = 0x1F
    ENDPOINT_BITS = 3
    ENDPOINT_OFFSET = 5
    ENDPOINT_MASK = 0x7

    # ---------------------------------------------
    # Various properties
    # ---------------------------------------------
    MAX_FRAME_SIZE = 32  # Max number of bytes per transfer supported by the NRF24L01 radio
    CONTROL_FIELD_SIZE = 3  # Bytes

    def __init__(self):
        self.version = 0
        self.frameLength = 0
        self.multicast = False
        self.requireAck = False
        self.dataLength = 0
        self.frameNumber = 0
        self.endpoint = 0
        self.userData = bytearray(29)
        self._pad0 = 0

        # Some runtime checks to ensure sizing constraints are met
        assert(len(self.userData) + self.CONTROL_FIELD_SIZE == self.MAX_FRAME_SIZE)

    def write_data(self, data: bytearray):
        assert(len(data) <= len(self.userData))
        self.userData[:len(data)] = data
        self.dataLength = len(data)
        self.frameLength = self.dataLength + self.CONTROL_FIELD_SIZE

    def read_data(self) -> bytearray:
        assert(self.dataLength < len(self.userData))
        return self.userData[:self.dataLength]

    def pack(self) -> bytearray:
        """
        Packs the class attributes into a network transferable byte array
        """
        buffer = bytearray(self.MAX_FRAME_SIZE)
        buffer.zfill(self.MAX_FRAME_SIZE)

        # ---------------------------------------------
        # Pack the control field
        # ---------------------------------------------
        # Byte 0
        version_bytes = (self.version & self.VERSION_LENGTH_MASK) << self.VERSION_LENGTH_OFFSET
        frame_len_bytes = (self.frameLength & self.FRAME_LENGTH_MASK) << self.FRAME_LENGTH_OFFSET
        buffer[0] = version_bytes | frame_len_bytes

        # Byte 1
        multi_cast_bytes = (self.multicast & self.MULTICAST_LENGTH_MASK) << self.MULTICAST_LENGTH_OFFSET
        require_ack_bytes = (self.requireAck & self.REQ_ACK_LENGTH_MASK) << self.REQ_ACK_LENGTH_OFFSET
        data_len_bytes = (self.dataLength & self.DATA_LENGTH_MASK) << self.DATA_LENGTH_OFFSET
        buffer[1] = multi_cast_bytes | require_ack_bytes | data_len_bytes

        # Byte 2
        frame_num_bytes = (self.frameNumber & self.FRAME_NUMBER_MASK) << self.FRAME_LENGTH_OFFSET
        endpoint_bytes = (self.endpoint & self.ENDPOINT_MASK) << self.ENDPOINT_OFFSET
        buffer[2] = frame_num_bytes | endpoint_bytes

        # Pack the user data via slicing
        buffer[self.CONTROL_FIELD_SIZE:] = self.userData

        return buffer

    def unpack(self, data: bytearray) -> None:
        """
        Unpacks the data into the appropriate class attributes
        """
        assert(len(data) == self.MAX_FRAME_SIZE)

        # Unpack the user data first. That's the easiest.
        self.userData = data[self.CONTROL_FIELD_SIZE:]

        # Next unpack the control field, assuming little endian
        self.version = int((data[0] >> self.VERSION_LENGTH_OFFSET) & self.VERSION_LENGTH_MASK)
        self.frameLength = int((data[0] >> self.FRAME_LENGTH_OFFSET) & self.FRAME_LENGTH_MASK)
        self.multicast = int((data[1] >> self.MULTICAST_LENGTH_OFFSET) & self.MULTICAST_LENGTH_MASK)
        self.requireAck = int((data[1] >> self.REQ_ACK_LENGTH_OFFSET) & self.REQ_ACK_LENGTH_MASK)
        self.dataLength = int((data[1] >> self.DATA_LENGTH_OFFSET) & self.DATA_LENGTH_MASK)
        self.frameNumber = int((data[2] >> self.FRAME_NUMBER_OFFSET) & self.FRAME_NUMBER_MASK)
        self.endpoint = int((data[2] >> self.ENDPOINT_OFFSET) & self.ENDPOINT_MASK)


