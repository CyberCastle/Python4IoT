# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/service.py
from typing import Optional
from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.service import ServiceInterface, dbus_property
from dbus_fast.constants import PropertyAccess
from dbus_fast.signature import Variant

from bluetooth import defs
from bluetooth.characteristic import GattCharacteristic, GattCharacteristicFlags


class GattService(ServiceInterface):
    """
    org.bluez.GattService1 interface implementation
    """

    def __init__(
        self,
        uuid: str,
        primary: bool,
        index: int,
        base_path: str,
        subscribed_characteristics: list[str],
        bus: MessageBus,
    ):
        """
        Initialize the DBusObject

        Parameters
        ----------
        uuid : str
            A string representation of the unique identifier
        primary : bool
            Whether the service is the primary service for the application it
            belongs to
        index : int
            The index of the service amongst the other service of the
        base_path : str
            The base path for service
        bus : MessageBus
            The dbus_fast connection
        """
        hex_index: str = hex(index)[2:].rjust(4, "0")
        self.path: str = base_path + "/service" + hex_index
        self._uuid: str = uuid
        self._primary: bool = primary
        self._bus: MessageBus = bus
        self.characteristics: list[GattCharacteristic] = []
        self.subscribed_characteristics: list[str] = subscribed_characteristics

        super(GattService, self).__init__(defs.GATT_SERVICE_INTERFACE)

    @dbus_property(access=PropertyAccess.READ)
    def UUID(self) -> "s":  # type: ignore
        return self._uuid

    @dbus_property(access=PropertyAccess.READ)
    def Primary(self) -> "b":  # type: ignore
        return self._primary

    async def add_characteristic(self, uuid: str, flags: list[GattCharacteristicFlags], value: Optional[bytearray]) -> GattCharacteristic:
        """
        Adds a bc.GattCharacteristic to the service.

        Parameters
        ----------
        uuid : str
            The string representation of the UUID for the characteristic
        flags : list[CharacteristicFlags],
            A list of flags to apply to the characteristic
        value : bytearray
            The characteristic's value
        """
        index: int = len(self.characteristics) + 1
        characteristic: GattCharacteristic = GattCharacteristic(uuid, flags, index, self.path, self.subscribed_characteristics, self._bus)
        if value != None:
            characteristic._value = value

        self.characteristics.append(characteristic)
        self._bus.export(characteristic.path, characteristic)

        return characteristic
