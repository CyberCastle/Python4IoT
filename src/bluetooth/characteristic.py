# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/characteristic.py
from collections.abc import Callable
from typing import Optional

import logging

from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.service import ServiceInterface, method, dbus_property
from dbus_fast.constants import PropertyAccess
from dbus_fast.signature import Variant

from bluetooth import defs
from bluetooth.descriptor import GattDescriptor

logger = logging.getLogger(name=__name__)


class GattCharacteristic(ServiceInterface):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """

    def __init__(
        self,
        uuid: str,
        flags: list[defs.GattCharacteristicFlags],
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

        self._read: Optional[Callable[[GattCharacteristic], bytearray]] = None
        self._write: Optional[Callable[[GattCharacteristic, bytearray], None]] = None

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

        return f(self)

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
        f(self, value)

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

    async def add_descriptor(self, uuid: str, flags: list[defs.GattDescriptorFlags], value: bytearray) -> GattDescriptor:
        """
        Adds a BlueZGattDescriptor to the characteristic.

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
    def read(self) -> Optional[Callable[["GattCharacteristic"], bytearray]]:
        return self._read

    @read.setter
    def read(self, fn: Optional[Callable[["GattCharacteristic"], bytearray]]):
        self._read = fn

    @property
    def write(self) -> Optional[Callable[["GattCharacteristic", bytearray], None]]:
        return self._write

    @write.setter
    def write(self, fn: Optional[Callable[["GattCharacteristic", bytearray], None]]):
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

    async def get_obj(self) -> dict:
        """
        Obtain the underlying dictionary within the  API that describes
        the characteristic

        Returns
        -------
        dict
            The dictionary that describes the characteristic
        """
        return {"UUID": Variant("s", self._uuid)}
