# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/application.py
import re
from collections.abc import Callable
from typing import Optional

from dbus_fast.service import ServiceInterface
from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.aio.proxy_object import ProxyObject, ProxyInterface
from dbus_fast.signature import Variant

from bluetooth import defs
from bluetooth.advertisement import LEAdvertisement, Type
from bluetooth.characteristic import GattCharacteristic
from bluetooth.service import GattService


class GattApplication(ServiceInterface):
    def __init__(self, name: str, destination: str, bus: MessageBus):
        """
        Parameters
        ----------
        name : str
            The name of the Bluetooth Low Energy Application
        destination : str
            The destination interface to add the application to
        bus : MessageBus
            The dbus_fast connection
        """
        self.path: str = "/"
        self.app_name: str = name
        self._bus: MessageBus = bus

        # Valid path must be ASCII characters "[A-Z][a-z][0-9]_"
        # see https://dbus.freedesktop.org/doc/dbus-specification.html#message-protocol-marshaling-object-path

        self.base_path: str = "/org/bluez/" + re.sub("[^A-Za-z0-9_]", "", self.app_name)
        self.advertisements: list[LEAdvertisement] = []
        self.services: list[GattService] = []

        self.read: Optional[Callable[[GattCharacteristic], bytearray]] = None
        self.write: Optional[Callable[[GattCharacteristic, bytearray], None]] = None
        self.start_notify: Optional[Callable[[None], None]] = None
        self.stop_notify: Optional[Callable[[None], None]] = None

        self.subscribed_characteristics: list[str] = []

        super(GattApplication, self).__init__(destination)

    async def add_service(self, uuid: str) -> GattService:
        """
        Add a service to the application
        The first service to be added will be the primary service

        Parameters
        ----------
        uuid : str
            The string representation of the uuid for the service to create

        Returns
        -------
        bs.GattService
            Returns and instance of the service object
        """
        index: int = len(self.services) + 1
        primary: bool = index == 1

        service: GattService = GattService(uuid, primary, index, self.base_path, self.subscribed_characteristics, self._bus)
        self.services.append(service)
        self._bus.export(service.path, service)
        return service

    async def add_characteristic(
        self, service_uuid: str, uuid: str, value: bytearray, flags: list[defs.GattCharacteristicFlags]
    ) -> GattCharacteristic:
        """
        Add a characteristic to the service


        Parameters
        ----------
        service_uuid: str
            The string representation of the UUID for the service that this
            characteristic belongs to
        uuid : str
            The string representation of the UUID for the characteristic
        value : bytearray
            The value of the characteristic,
        flags: list[CharacteristicFlags]
            A list of flags to apply to the characteristic

        Returns
        -------
        bc.GattCharacteristic
            The characteristic object
        """
        service: GattService = next(iter([x for x in self.services if x._uuid == service_uuid]))
        characteristic: GattCharacteristic = await service.add_characteristic(uuid, flags, value)
        characteristic.read = self.read
        characteristic.write = self.write
        characteristic.start_notify = self.start_notify
        characteristic.stop_notify = self.stop_notify
        return characteristic

    async def set_name(self, adapter: ProxyObject, name: str):
        """
        Set's the alias of our bluetooth adapter to our application's name

        Parameters
        ----------
        adapter : ProxyObject
            The adapter whose alias name to set
        name : str
            The name to set the adapter alias
        """
        iface: ProxyInterface = adapter.get_interface(defs.DBUS_PROPERTIES_INTERFACE)
        await iface.call_set(defs.ADAPTER_INTERFACE, "Alias", Variant("s", name))  # type: ignore

    async def register(self, adapter: ProxyObject):
        """
        Register the application with DBus

        Parameters
        ----------
        adapter : ProxyObject
            The adapter to register the application with
        """
        iface: ProxyInterface = adapter.get_interface(defs.GATT_MANAGER_INTERFACE)
        await iface.call_register_application(self.path, {})  # type: ignore

    async def unregister(self, adapter: ProxyObject):
        """
        Unregister the application with DBus

        Parameters
        ----------
        adapter : ProxyObject
            The adapter on which the current application is registered
        """
        iface: ProxyInterface = adapter.get_interface(defs.GATT_MANAGER_INTERFACE)
        await iface.call_unregister_application(self.path)  # type: ignore

    async def start_advertising(self, adapter: ProxyObject) -> LEAdvertisement:
        """
        Start Advertising the application

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to start advertising on
        """
        await self.set_name(adapter, self.app_name)
        advertisement: LEAdvertisement = LEAdvertisement(self.app_name, Type.PERIPHERAL, len(self.advertisements) + 1, self.base_path)
        advertisement._tx_power = 20

        self.advertisements.append(advertisement)

        # Only add the first service UUID
        advertisement._service_uuids.append(self.services[0].UUID)
        self._bus.export(advertisement.path, advertisement)
        iface: ProxyInterface = adapter.get_interface(defs.LE_ADVERTISEMENT_MANAGER_INTERFACE)
        await iface.call_register_advertisement(advertisement.path, {})  # type: ignore

        return advertisement

    async def is_advertising(self, adapter: ProxyObject) -> bool:
        """
        Check if the adapter is advertising

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to check for advertising

        Returns
        -------
        bool
            Whether the adapter is advertising anything
        """
        iface: ProxyInterface = adapter.get_interface(defs.DBUS_PROPERTIES_INTERFACE)
        instances: Variant = await iface.call_get(defs.LE_ADVERTISEMENT_MANAGER_INTERFACE, "ActiveInstances")  # type: ignore
        return instances.value > 0

    async def stop_all_advertising(self, adapter: ProxyObject):
        """
        Stop Advertising

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to stop all advertising
        """

        await self.set_name(adapter, "")
        for advertisement in self.advertisements:
            iface: ProxyInterface = adapter.get_interface(defs.LE_ADVERTISEMENT_MANAGER_INTERFACE)
            await iface.call_unregister_advertisement(advertisement.path)  # type: ignore
            self._bus.unexport(advertisement.path)

    async def stop_advertising(self, adapter: ProxyObject, advertisement: LEAdvertisement):
        """
        Stop Advertising

        Parameters
        ----------
        adapter : ProxyObject
            The adapter object to stop advertising
        advertisement: LEAdvertisement
            The advertisement to stop
        """
        self.advertisements.remove(advertisement)
        iface: ProxyInterface = adapter.get_interface(defs.LE_ADVERTISEMENT_MANAGER_INTERFACE)
        await iface.call_unregister_advertisement(advertisement.path)  # type: ignore
        self._bus.unexport(advertisement.path)

    async def is_connected(self) -> bool:
        """
        Check if the application is connected
        This is not the same as if the adapter is connected to a device, but
        rather if there is a subscribed characteristic

        Returns
        -------
        bool
            Whether a central device is subscribed to one of our
            characteristics
        """
        return len(self.subscribed_characteristics) > 0

    async def get_supported_features(self, adapter: ProxyObject) -> list[str]:

        iface: ProxyInterface = adapter.get_interface(defs.LE_ADVERTISEMENT_MANAGER_INTERFACE)
        return await iface.get_supported_features()  # type: ignore
