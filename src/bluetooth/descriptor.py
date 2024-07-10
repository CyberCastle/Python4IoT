from enum import Enum
from typing import Callable, Optional
from dbus_fast.service import ServiceInterface, method, dbus_property
from dbus_fast.constants import PropertyAccess
from dbus_fast.signature import Variant

from bluetooth import defs
from utils.dbus_utils import getattr_variant


class DescriptorReadOptions:
    """Options supplied to descriptor read functions.
    Generally you can ignore these unless you have a long descriptor (eg > 48 bytes) or you have some specific authorization requirements.
    """

    def __init__(self, options):
        self._offset = getattr_variant(options, "offset", 0)
        self._link = getattr_variant(options, "link", None)
        self._device = getattr_variant(options, "device", None)

    @property
    def offset(self):
        """A byte offset to use when writing to this descriptor."""
        return self._offset

    @property
    def link(self):
        """The link type."""
        return self._link

    @property
    def device(self):
        """The path of the remote device on the system dbus or None."""
        return self._device


class DescriptorWriteOptions:
    """Options supplied to descriptor write functions.
    Generally you can ignore these unless you have a long descriptor (eg > 48 bytes) or you have some specific authorization requirements.
    """

    def __init__(self, options):
        self._offset = getattr_variant(options, "offset", 0)
        self._mtu = int(getattr_variant(options, "mtu", 0))
        self._device = getattr_variant(options, "device", None)
        self._link = getattr_variant(options, "link", None)
        self._prepare_authorize = getattr_variant(options, "prepare-authorize", False)

    @property
    def offset(self):
        """A byte offset to use when writing to this descriptor."""
        return self._offset

    @property
    def mtu(self):
        """The exchanged Maximum Transfer Unit of the connection with the remote device or 0."""
        return self._mtu

    @property
    def device(self):
        """The path of the remote device on the system dbus or None."""
        return self._device

    @property
    def link(self):
        """The link type."""
        return self._link

    @property
    def prepare_authorize(self):
        """True if prepare authorization request. False otherwise."""
        return self._prepare_authorize


class GattDescriptorFlags(Enum):
    READ = "read"
    WRITE = "write"
    ENCRYPT_READ = "encrypt-read"
    ENCRYPT_WRITE = "encrypt-write"
    ENCRYPT_AUTHENTICATED_READ = "encrypt-authenticated-read"
    ENCRYPT_AUTHENTICATED_WRITE = "encrypt-authenticated-write"
    SECURE_READ = "secure-read"  # (Server only)
    SECURE_WRITE = "secure-write"  # (Server only)
    AUTHORIZE = "authorize"


class GattDescriptor(ServiceInterface):
    """
    org.bluez.GattDescriptor1 interface implementation
    """

    def __init__(self, uuid: str, flags: list[GattDescriptorFlags], index: int, characteristic_path: str):
        """
        Create a GATT Descriptor

        Parameters
        ----------
        uuid : str
            The unique identifier for the descriptor
        flags : List[DescriptorFlags]
            A list of strings that represent the properties of the
            descriptor
        index : int
            The index number for this descriptor in the descriptors
        characteristic_path: str
            The Characteristic path
        """
        self.path: str = characteristic_path + "/descriptor" + f"{index:04d}"
        self._uuid: str = uuid
        self._flags: list[str] = [x.value for x in flags]
        self._characteristic_path: str = characteristic_path
        self._value: bytearray = bytearray()

        self._read: Optional[Callable[["GattDescriptor", DescriptorReadOptions], bytearray]]
        self._write: Optional[Callable[["GattDescriptor", DescriptorWriteOptions, bytearray], None]]

        super(GattDescriptor, self).__init__(defs.GATT_DESCRIPTOR_INTERFACE)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Characteristic(self) -> "o":  # type: ignore
        return self._characteristic_path

    @dbus_property()
    def Value(self) -> "ay":  # type: ignore
        return self._value

    @Value.setter
    def Value(self, value: "ay"):  # type: ignore
        self._value = value
        self.emit_properties_changed(changed_properties={"Value": self._value})

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":  # type: ignore
        return self._flags

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":  # type: ignore
        """
        Read the value of the descriptor.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : Dict
            A list of options

        Returns
        -------
        bytearray
            The bytearray that is the value of the descriptor
        """
        f = self._read
        if f is None:
            raise NotImplementedError()

        return f(self, DescriptorReadOptions(options))

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}"):  # type: ignore # noqa
        """
        Write a value to the descriptor
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytearray
            The value to set
        options : Dict
            Some options for you to select from
        """
        f = self._write
        if f is None:
            raise NotImplementedError()
        f(self, DescriptorWriteOptions(options), value)

    @property
    def read(self) -> Optional[Callable[["GattDescriptor", DescriptorReadOptions], bytearray]]:
        return self._read

    @read.setter
    def read(self, fn: Optional[Callable[["GattDescriptor", DescriptorReadOptions], bytearray]]):
        self._read = fn

    @property
    def write(self) -> Optional[Callable[["GattDescriptor", DescriptorWriteOptions, bytearray], None]]:
        return self._write

    @write.setter
    def write(self, fn: Optional[Callable[["GattDescriptor", DescriptorWriteOptions, bytearray], None]]):
        self._write = fn
