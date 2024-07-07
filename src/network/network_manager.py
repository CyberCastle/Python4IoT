import logging
import uuid
from typing import TypedDict

from dbus_fast import BusType, unpack_variants
from dbus_fast.aio.message_bus import MessageBus
from dbus_fast.aio.proxy_object import ProxyObject, ProxyInterface
from dbus_fast.introspection import Node
from dbus_fast.signature import Variant

from network.network_exception import NetworkException

logger = logging.getLogger(name=__name__)

NETWORKMANAGER_SERVICE_NAME = "org.freedesktop.NetworkManager"
NETWORKMANAGER_SERVICE_PATH = "/org/freedesktop/NetworkManager"
DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"
NETWORKMANAGER_SETTINGS_INTERFACE = "org.freedesktop.NetworkManager.Settings"
NETWORKMANAGER_SETTINGS_PATH = "/org/freedesktop/NetworkManager/Settings"
NETWORKMANAGER_WIRELESS_INTERFACE = "org.freedesktop.NetworkManager.Device.Wireless"
NETWORKMANAGER_DEVICE_INTERFACE = "org.freedesktop.NetworkManager.Device"
NETWORKMANAGER_CONNECTION_INTERFACE = "org.freedesktop.NetworkManager.Settings.Connection"
NETWORKMANAGER_DEVICETYPE_PROP = "DeviceType"
NETWORKMANAGER_ACCESS_POINT_INTERFACE = "org.freedesktop.NetworkManager.AccessPoint"
NETWORKMANAGER_SSID_PROP = "Ssid"

WIFI_DEVICETYPE_ID = 2


async def is_networkmanager_available() -> bool:
    """Checks if NetworkManager is registered on the system dbus.

    Returns:
        True if NetworkManager is found. False otherwise.
    """
    try:
        bus: MessageBus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        await bus.introspect(NETWORKMANAGER_SERVICE_NAME, NETWORKMANAGER_SERVICE_PATH)
        return True
    except Exception as e:
        logger.warning(e)
        return False


class SsidAccessPointPathMap(TypedDict):
    ssid: str
    ap_path: str


class NetworkManager:
    def __init__(self, bus: MessageBus) -> None:
        self.bus: MessageBus = bus
        self.nm_node: Node
        self.nm_obj: ProxyObject
        self.nm_iface: ProxyInterface
        self.access_points: list[SsidAccessPointPathMap] = []

    async def init(self) -> "NetworkManager":
        self.nm_node: Node = await self.bus.introspect(NETWORKMANAGER_SERVICE_NAME, NETWORKMANAGER_SERVICE_PATH)
        self.nm_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, NETWORKMANAGER_SERVICE_PATH, self.nm_node)
        self.nm_iface: ProxyInterface = self.nm_obj.get_interface(NETWORKMANAGER_SERVICE_NAME)

        return self

    async def get_devices(self) -> list[str]:
        logger.debug("Getting devices network list.")

        return await self.nm_iface.call_get_devices()  # type: ignore

    async def get_device_type(self, device_path: str) -> int:
        logger.debug("Getting device type for %s", device_path)
        dev_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, device_path, self.nm_node)
        dev_iface: ProxyInterface = dev_obj.get_interface(DBUS_PROPERTIES_INTERFACE)
        device_type: Variant = await dev_iface.call_get(NETWORKMANAGER_DEVICE_INTERFACE, NETWORKMANAGER_DEVICETYPE_PROP)  # type: ignore

        return device_type.value

    async def get_connections(self) -> list[str]:
        logger.debug("Getting connections list.")
        settings_node: Node = await self.bus.introspect(NETWORKMANAGER_SERVICE_NAME, NETWORKMANAGER_SETTINGS_PATH)
        settings_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, NETWORKMANAGER_SETTINGS_PATH, settings_node)
        settings_iface: ProxyInterface = settings_obj.get_interface(NETWORKMANAGER_SETTINGS_INTERFACE)

        return await settings_iface.call_list_connections()  # type: ignore

    async def get_connection_info(self, connection_path: str) -> dict:
        conn_node: Node = await self.bus.introspect(NETWORKMANAGER_SERVICE_NAME, connection_path)
        conn_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, connection_path, conn_node)
        conn_iface: ProxyInterface = conn_obj.get_interface(NETWORKMANAGER_CONNECTION_INTERFACE)
        conn_info = await conn_iface.call_get_settings()  # type: ignore

        return unpack_variants(conn_info)

    async def get_first_wif_device(self) -> str:
        devices = await self.get_devices()

        for device in devices:
            device_type = await self.get_device_type(device)
            if device_type == WIFI_DEVICETYPE_ID:
                return device

        return ""

    async def get_access_point_ssid(self, access_point_path: str) -> str:
        logger.debug("Getting SSID for %s", access_point_path)
        ap_node: Node = await self.bus.introspect(NETWORKMANAGER_SERVICE_NAME, access_point_path)
        ap_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, access_point_path, ap_node)
        ap_iface: ProxyInterface = ap_obj.get_interface(DBUS_PROPERTIES_INTERFACE)

        ssid_v: Variant = await ap_iface.call_get(NETWORKMANAGER_ACCESS_POINT_INTERFACE, NETWORKMANAGER_SSID_PROP)  # type: ignore
        ssid_b: bytearray = ssid_v.value
        return ssid_b.decode("utf-8")

    async def scan_access_points(self, device_path: str) -> list[str]:
        logger.debug("Scanning access points through %s", device_path)
        device_type = await self.get_device_type(device_path)
        if device_type != WIFI_DEVICETYPE_ID:
            raise NetworkException("Device selected {} is not a WIFI".format(device_path))

        wifi_node: Node = await self.bus.introspect(NETWORKMANAGER_SERVICE_NAME, device_path)
        wifi_obj: ProxyObject = self.bus.get_proxy_object(NETWORKMANAGER_SERVICE_NAME, device_path, wifi_node)
        wifi_iface: ProxyInterface = wifi_obj.get_interface(NETWORKMANAGER_WIRELESS_INTERFACE)

        access_points: list[str] = await wifi_iface.get_access_points()  # type: ignore
        for access_point in access_points:
            ssid: str = await self.get_access_point_ssid(access_point)
            self.access_points.append({"ssid": ssid, "ap_path": access_point})

        return access_points

    async def add_wifi_connection(self, device_path: str, ssid: str, passkey: str) -> None:
        logger.debug("Adding wifi connection with SSID %s", ssid)
        device_type = await self.get_device_type(device_path)
        if device_type != WIFI_DEVICETYPE_ID:
            raise NetworkException("Device selected {} is not a WIFI".format(device_path))

        if len(self.access_points) == 0:
            await self.scan_access_points(device_path)

        access_point_path: str = self.__get_access_point_path(self.access_points, ssid)
        conn_info = self.__prepare_conn_info(ssid, passkey)

        try:
            await self.nm_iface.call_add_and_activate_connection(conn_info, device_path, access_point_path)  # type: ignore
        except Exception as e:
            logger.error(e)
            raise NetworkException("Error registering WIFI")

    def __get_access_point_path(self, access_points: list[SsidAccessPointPathMap], ssid: str) -> str:
        filtered_list = filter(lambda ap: ssid == ap["ssid"], access_points)
        result = [ap["ap_path"] for ap in filtered_list]
        return result[0]

    def __prepare_conn_info(self, ssid: str, passkey: str) -> dict:
        return {
            "connection": {"type": Variant("s", "802-11-wireless"), "uuid": Variant("s", str(uuid.uuid4())), "id": Variant("s", ssid)},
            "802-11-wireless": {"ssid": Variant("ay", bytearray(ssid, "utf-8")), "mode": Variant("s", "infrastructure")},
            "802-11-wireless-security": {
                "key-mgmt": Variant("s", "wpa-psk"),
                "auth-alg": Variant("s", "open"),
                "psk": Variant("s", passkey),
            },
            "ipv4": {"method": Variant("s", "auto")},
            "ipv6": {"method": Variant("s", "ignore")},
        }
