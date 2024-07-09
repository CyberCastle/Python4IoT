# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/advertisement.py
from enum import Enum
import logging

from dbus_fast import PropertyAccess
from dbus_fast.service import ServiceInterface, method, dbus_property

from bluetooth import defs

logger = logging.getLogger(name=__name__)


class Type(Enum):
    BROADCAST = "broadcast"
    PERIPHERAL = "peripheral"


class LEAdvertisement(ServiceInterface):
    """
    org.bluez.LEAdvertisement1 interface implementation

    https://github.com/bluez/bluez/blob/master/doc/org.bluez.LEAdvertisement.rst
    https://python-dbus-next.readthedocs.io/en/latest/type-system/index.html
    https://elixir.bootlin.com/linux/v5.11/source/include/net/bluetooth/mgmt.h#L794
    https://github.com/bluez/bluez/issues/527
    https://patches.linaro.org/project/linux-bluetooth/list/?series=31700
    """

    def __init__(
        self,
        local_name: str,
        advertising_type: Type,
        index: int,
        base_path: str,
    ):
        """
        New Low Energy Advertisement

        Parameters
        ----------
        local_name: str
            Local name for advertisement
        advertising_type : Type
            The type of advertisement
        index : int,
            The index of the advertisement
        app : GattApplication
            The Application that is responsible for this advertisement
        """
        self.path = base_path + "/advertisement" + str(index)

        self._type: str = advertising_type.value
        self._service_uuids: list[str] = []
        self._manufacturer_data: dict = {}
        self._solicit_uuids: list[str] = []
        self._service_data: dict = {}

        # Default, Remote Control (https://github.com/boskokg/flutter_blue_plus/files/10681601/Appearance.Values.pdf)
        self._appearance: int = 0x0180

        # 3 options below are classified as Experimental in  and really
        # work only: - when  is compiled with such option (usually it is)
        # - and when "bluetoothd" daemon is started with -E, --experimental
        # option (usually it's not) They are taken into account only with
        # Kernel v5.11+ and  v5.65+. It's a known fact that  verions
        # 5.63-5.64 have broken Dbus part for LEAdvertisingManager and do not
        # work properly when the Experimental mode is enabled.
        self._min_interval: int = 100  # in ms, range [20ms, 10,485s]
        self._max_interval: int = 100  # in ms, range [20ms, 10,485s]
        self._tx_power: int = 20  # range [-127 to +20]

        self._local_name = local_name
        self._timeout = 3600
        self._discoverable = True

        super(LEAdvertisement, self).__init__(defs.LE_ADVERTISEMENT_INTERFACE)

    @method()
    def Release(self):
        logger.info("%s: Released!" % self.path)

    @dbus_property(PropertyAccess.READ)
    def Type(self) -> "s":  # type: ignore
        return self._type

    @dbus_property()
    def ServiceUUIDs(self) -> "as":  # type: ignore
        return self._service_uuids

    @ServiceUUIDs.setter
    def ServiceUUIDs(self, service_uuids: "as"):  # type: ignore
        self._service_uuids = service_uuids

    @dbus_property(PropertyAccess.READ)
    def ManufacturerData(self) -> "a{qv}":  # type: ignore
        return self._manufacturer_data

    @dbus_property(PropertyAccess.READ)
    def SolicitUUIDs(self) -> "as":  # type: ignore # noqa: F821 F722
        return self._solicit_uuids

    @dbus_property()
    def ServiceData(self) -> "a{sv}":  # type: ignore
        return self._service_data

    @ServiceData.setter
    def ServiceData(self, data: "a{sv}"):  # type: ignore
        self._service_data = data

    @dbus_property(PropertyAccess.READ)
    def Includes(self) -> "as":  # type: ignore
        return ["0"]

    @dbus_property(PropertyAccess.READ)
    def TxPower(self) -> "n":  # type: ignore
        return self._tx_power

    @dbus_property(PropertyAccess.READ)
    def MaxInterval(self) -> "u":  # type: ignore
        return self._max_interval

    @dbus_property(PropertyAccess.READ)
    def MinInterval(self) -> "u":  # type: ignore
        return self._min_interval

    @dbus_property(PropertyAccess.READ)
    def LocalName(self) -> "s":  # type: ignore
        return self._local_name

    @dbus_property(PropertyAccess.READ)
    def Appearance(self) -> "q":  # type: ignore
        return self._appearance

    @dbus_property(PropertyAccess.READ)
    def Timeout(self) -> "q":  # type: ignore
        return self._timeout

    @dbus_property(PropertyAccess.READ)
    def Discoverable(self) -> "b":  # type: ignore
        return self._discoverable
