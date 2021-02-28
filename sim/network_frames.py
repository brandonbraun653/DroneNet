# **********************************************************************************************************************
#   FileName:
#       network_frames.py
#
#   Description:
#       Frame type definitions for use with NRF24 only network communication
#
#   2/28/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

from frame_packager import PackedFrame
from frame_interface import BaseFrame


class ACKFrame(BaseFrame):
    """ A ShockBurst ACK frame """
    _ENDIAN = 'little'
    _DATA_SIZE = 4
    _DATA_VALUE = 0xAABBCCDD
    _DATA_BYTES = _DATA_VALUE.to_bytes(_DATA_SIZE, _ENDIAN)

    def __init__(self):
        self._frame = PackedFrame()
        self._frame.write_data(self._DATA_BYTES)

    def from_bytes(self, data: bytearray) -> None:
        self._frame.unpack(data)

    def to_bytes(self) -> bytearray:
        return self._frame.pack()

    def reset(self) -> None:
        self.__init__()

    def is_valid(self) -> bool:
        data_bytes = self._frame.userData[:self._DATA_SIZE]
        stored_value = int.from_bytes(data_bytes, self._ENDIAN)
        return stored_value == self._DATA_VALUE
