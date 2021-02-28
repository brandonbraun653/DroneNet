# **********************************************************************************************************************
#   FileName:
#       frame_interface.py
#
#   Description:
#       Interface classes to define common functionality with framing
#
#   2/28/21 | Brandon Braun | brandonbraun653@gmail.com
# **********************************************************************************************************************

from abc import ABCMeta, abstractmethod
from frame_packager import PackedFrame


class BaseFrame(metaclass=ABCMeta):

    @abstractmethod
    def from_bytes(self, data: bytearray) -> None:
        """
        Converts a set of bytes into the inherited frame type
        Args:
            data: Byte data that represents the frame

        Returns:
            None
        """
        raise NotImplementedError

    @abstractmethod
    def to_bytes(self) -> bytearray:
        """
        Gets the frame as transmittable network bytes
        Returns:
            The frame as a byte array
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """
        Clears the frame to default values
        Returns:
            None
        """
        raise NotImplementedError

    @abstractmethod
    def is_valid(self) -> bool:
        """
        Checks if the frame is valid for the inherited type
        Returns:
            bool
        """
        raise NotImplementedError


class RxFifoEntry(metaclass=ABCMeta):

    def __init__(self, pipe: int, frame: PackedFrame):
        self.pipe = pipe
        self.payload = frame
