# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/characteristic.py
from collections.abc import Callable
from enum import Enum
from typing import Optional

import logging

from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property
from dbus_fast.constants import PropertyAccess

from bluetooth import defs
from bluetooth.descriptor import GattDescriptor, GattDescriptorFlags
from utils.dbus_utils import getattr_variant

logger = logging.getLogger(name=__name__)


class CharacteristicReadOptions:
    """Options supplied to characteristic read functions.
    Generally you can ignore these unless you have a long characteristic (eg > 48 bytes) or you have some specific authorization requirements.
    """

    def __init__(self, options):
        self._offset = int(getattr_variant(options, "offset", 0))
        self._mtu = int(getattr_variant(options, "mtu", 0))
        self._device = getattr_variant(options, "device", None)

    @property
    def offset(self) -> int:
        """A byte offset to read the characteristic from until the end."""
        return self._offset

    @property
    def mtu(self) -> Optional[int]:
        """The exchanged Maximum Transfer Unit of the connection with the remote device or 0."""
        return self._mtu

    @property
    def device(self):
        """The path of the remote device on the system dbus or None."""
        return self._device


class CharacteristicWriteType(Enum):
    """Possible value of the :class:`CharacteristicWriteOptions`.type field"""

    COMMAND = 0
    """Write without response
    """
    REQUEST = 1
    """Write with response
    """
    RELIABLE = 2
    """Reliable Write
    """


class CharacteristicWriteOptions:
    """Options supplied to characteristic write functions.
    Generally you can ignore these unless you have a long characteristic (eg > 48 bytes) or you have some specific authorization requirements.
    """

    def __init__(self, options):
        self._offset = int(getattr_variant(options, "offset", 0))
        type = getattr_variant(options, "type", None)
        if not type is None:
            type = CharacteristicWriteType[type.upper()]
        self._type = type
        self._mtu = int(getattr_variant(options, "mtu", 0))
        self._device = getattr_variant(options, "device", None)
        self._link = getattr_variant(options, "link", None)
        self._prepare_authorize = getattr_variant(options, "prepare-authorize", False)

    @property
    def offset(self):
        """A byte offset to use when writing to this characteristic."""
        return self._offset

    @property
    def type(self):
        """The type of write operation requested or None."""
        return self._type

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


class GattCharacteristicFlags(Enum):
    BROADCAST = "broadcast"
    READ = "read"
    WRITE_WITHOUT_RESPONSE = "write-without-response"
    WRITE = "write"
    NOTIFY = "notify"
    INDICATE = "indicate"
    AUTHENTICATED_SIGNED_WRITES = "authenticated-signed-writes"
    EXTENDED_PROPERTIES = "extended-properties"
    RELIABLE_WRITE = "reliable-write"
    WRITABLE_AUXILIARIES = "writable-auxiliaries"
    ENCRYPT_READ = "encrypt-read"
    ENCRYPT_WRITE = "encrypt-write"
    ENCRYPT_NOTIFY = "encrypt-notify"  # (Server only)
    ENCRYPT_INDICATE = "encrypt-indicate"  # (Server only)
    ENCRYPT_AUTHENTICATED_READ = "encrypt-authenticated-read"
    ENCRYPT_AUTHENTICATED_WRITE = "encrypt-authenticated-write"
    ENCRYPT_AUTHENTICATED_NOTIFY = "encrypt-authenticated-notify"  # (Server on
    ENCRYPT_AUTHENTICATED_INDICATE = "encrypt-authenticated-indicate"  # (Server
    SECURE_READ = "secure-read"  # (Server only)
    SECURE_WRITE = "secure-write"  # (Server only)
    SECURE_NOTIFY = "secure-notify"  # (Server only)
    SECURE_INDICATE = "secure-indicate"  # (Server only)
    AUTHORIZE = "authorize"


class GattCharacteristic(ServiceInterface):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    def __init__(
        self,
        uuid: str,
        flags: list[GattCharacteristicFlags],
        index: int,
        service_path: str,
        subscribed_characteristics: list[str],
        bus: MessageBus,
    ):
        """
        Create a  Gatt Characteristic

        Parameters
        ----------
        uuid : str
            The unique identifier for the characteristic
        flags : list[CharacteristicFlags]
            A list of strings that represent the properties of the
            characteristic
        index : int
            The index number for this characteristic in the service
        service_path : str
            The path of service
        subscribed_characteristics : list[str]
            List of subscribed characteristics
        bus : MessageBus
            The dbus_fast connection
        """
        self.path: str = service_path + "/characteristic" + f"{index:04d}"
        self._service_path: str = service_path
        self._uuid: str = uuid
        self._flags: list[str] = [x.value for x in flags]
        self.subscribed_characteristics: list[str] = subscribed_characteristics
        self._bus: MessageBus = bus
        self._value: bytearray = bytearray()
        self._notifying: bool = "notify" in self._flags or "indicate" in self._flags

        self.descriptors: list[GattDescriptor] = []

        self._read: Optional[Callable[[GattCharacteristic, CharacteristicReadOptions], bytearray]] = None
        self._write: Optional[Callable[[GattCharacteristic, CharacteristicWriteOptions, bytearray], None]] = None

        self._start_notify: Optional[Callable[[None], None]] = None
        self._stop_notify: Optional[Callable[[None], None]] = None

        super(GattCharacteristic, self).__init__(defs.GATT_CHARACTERISTIC_INTERFACE)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Service(self) -> "o":  # type: ignore
        return self._service_path

    @dbus_property()
    def Value(self) -> "ay":  # type: ignore
        return self._value

    @Value.setter
    def Value(self, value: "ay"):  # type: ignore
        self._value = value
        self.emit_properties_changed(changed_properties={"Value": self._value})

    @dbus_property(access=PropertyAccess.READ)
    def Notifying(self) -> "b":  # type: ignore
        return self._notifying

    @dbus_property(access=PropertyAccess.READ)
    def Flags(self) -> "as":  # type: ignore
        return self._flags

    @method()
    def ReadValue(self, options: "a{sv}") -> "ay":  # type: ignore
        """
        Read the value of the characteristic.
        This is to be fully implemented at the application level

        Parameters
        ----------
        options : dict
            A list of options

        Returns
        -------
        bytearray
            The bytearray that is the value of the characteristic
        """
        f = self._read
        if f is None:
            raise NotImplementedError()

        return f(self, CharacteristicReadOptions(options))

    @method()
    def WriteValue(self, value: "ay", options: "a{sv}"):  # type: ignore
        """
        Write a value to the characteristic
        This is to be fully implemented at the application level

        Parameters
        ----------
        value : bytearray
            The value to set
        options : dict
            Some options for you to select from
        """
        f = self._write
        if f is None:
            raise NotImplementedError()
        f(self, CharacteristicWriteOptions(options), value)

    @method()
    def StartNotify(self):
        """
        Begin a subscription to the characteristic
        """
        f = self._start_notify
        if f is None:
            raise NotImplementedError()
        f(None)
        self.subscribed_characteristics.append(self._uuid)

    @method()
    def StopNotify(self):
        """
        Stop a subscription to the characteristic
        """
        f = self._stop_notify
        if f is None:
            raise NotImplementedError()
        f(None)
        self.subscribed_characteristics.remove(self._uuid)

    @method()
    def Confirm(self):
        logger.info("Value was received!")

    async def add_descriptor(self, uuid: str, flags: list[GattDescriptorFlags], value: bytearray) -> GattDescriptor:
        """
        Adds a GattDescriptor to the characteristic.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the descriptor
        flags : List[DescriptorFlags],
            A list of flags to apply to the descriptor
        value : bytearray
            The descriptor's value
        """
        index: int = len(self.descriptors) + 1
        descriptor: GattDescriptor = GattDescriptor(uuid, flags, index, self.path)
        descriptor._value = value
        self.descriptors.append(descriptor)
        self._bus.export(descriptor.path, descriptor)
        return descriptor

    @property
    def read(self) -> Optional[Callable[["GattCharacteristic", CharacteristicReadOptions], bytearray]]:
        return self._read

    @read.setter
    def read(self, fn: Optional[Callable[["GattCharacteristic", CharacteristicReadOptions], bytearray]]):
        self._read = fn

    @property
    def write(self) -> Optional[Callable[["GattCharacteristic", CharacteristicWriteOptions, bytearray], None]]:
        return self._write

    @write.setter
    def write(self, fn: Optional[Callable[["GattCharacteristic", CharacteristicWriteOptions, bytearray], None]]):
        self._write = fn

    @property
    def start_notify(self) -> Optional[Callable[[None], None]]:
        return self._start_notify

    @start_notify.setter
    def start_notify(self, fn: Optional[Callable[[None], None]]):
        self._start_notify = fn

    @property
    def stop_notify(self) -> Optional[Callable[[None], None]]:
        return self._stop_notify

    @stop_notify.setter
    def stop_notify(self, fn: Optional[Callable[[None], None]]):
        self._stop_notify = fn
