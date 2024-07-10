import logging
from typing import Optional

from dbus_fast import BusType
from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.aio.proxy_object import ProxyObject, ProxyInterface
from dbus_fast.introspection import Node

from bluetooth import defs
from bluetooth.bluetooth_exception import BluetoothException

logger = logging.getLogger(name=__name__)


async def is_bluez_available() -> bool:
    """Checks if bluez is registered on the system dbus.

    Returns:
        True if bluez is found. False otherwise.
    """
    try:
        bus: MessageBus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        await bus.introspect("org.bluez", "/org/bluez")
        return True
    except Exception as e:
        logger.warning(e)
        return False


class BleDevice:
    def __init__(self, bus: MessageBus):
        self.bus: MessageBus = bus
        self.device_obj: ProxyObject
        self.device_path: str
        self.device_node: Node
        self.adapter_face: ProxyInterface

    async def list(self) -> list[str]:
        """
        Returns a list of strings that represent host-controller interfaces for
        bluetooth

        Parameters
        ----------

        Returns
        -------
        List[str]
            A list of device interfaces on the dbus
        """
        bluez_node: Node = await self.__get_bluez_dbus_node("/")
        bluez_obj: ProxyObject = self.bus.get_proxy_object(defs.BLUEZ_SERVICE, "/", bluez_node)
        interface: ProxyInterface = bluez_obj.get_interface(defs.OBJECT_MANAGER_INTERFACE)
        bt_objects: dict = await interface.call_get_managed_objects()  # type: ignore

        devices: list[str] = [objs for objs, props in bt_objects.items() if defs.GATT_MANAGER_INTERFACE in props.keys()]
        return devices

    async def find(self, device: str = "hci0") -> str:
        """
        Returns the first object within the bluez service that has a GattManager1
        interface

        Parameters
        ----------
        device : str
            The device to find. Default is 'hci0'

        Returns
        -------
        str
            The dbus path to the device
        """
        device_strs: list[str] = await self.list()
        found_device: list[str] = [a for a in device_strs if device in a]
        if len(found_device) > 0:
            return found_device[0]
        raise BluetoothException(f"No device named {device} found")

    async def select(self, device: Optional[str] = None) -> Optional[ProxyObject]:
        """
        Gets the bluetooth device specified by device or the default if device
        is None

        Parameters
        ----------
        device: Optional[str]
            A string that points to the HCI device

        Returns
        -------
        ProxyObject
            The device object
        """
        self.device_path: str = await self.find(device if device is not None else "hci0")
        self.device_node: Node = await self.__get_bluez_dbus_node(self.device_path)
        self.device_obj: ProxyObject = self.bus.get_proxy_object(defs.BLUEZ_SERVICE, self.device_path, self.device_node)

        # ProxyInterface for enable controls over Bluetooth adapter
        self.adapter_face = self.device_obj.get_interface(defs.ADAPTER_INTERFACE)

        return self.device_obj

    async def power_on(self):
        await self.adapter_face.set_powered(True)  # type: ignore
        return

    async def power_off(self):
        await self.adapter_face.set_powered(False)  # type: ignore
        return

    async def discoverable_on(self, timeout: int = 180):
        await self.adapter_face.set_discoverable_timeout(timeout)  # type: ignore
        await self.adapter_face.set_discoverable(True)  # type: ignore
        return

    async def discoverable_off(self):
        await self.adapter_face.set_discoverable(False)  # type: ignore
        return

    async def get_address(self) -> str:
        return await self.adapter_face.get_address()  # type: ignore

    async def __get_bluez_dbus_node(self, path: str) -> Node:
        return await self.bus.introspect(defs.BLUEZ_SERVICE, path)
