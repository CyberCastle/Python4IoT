# Based in this code: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/advertisement.py
from enum import Enum
import logging

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
        advertising_type: Type,
        index: int,
        base_path: str,
    ):
        """
        New Low Energy Advertisement

        Parameters
        ----------
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
        self._solicit_uuids: list[str] = [""]
        self._service_data: dict = {}

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

        self._local_name = ""

        self.data = None
        super(LEAdvertisement, self).__init__(defs.LE_ADVERTISEMENT_INTERFACE)

    @method()
    def Release(self):
        logger.info("%s: Released!" % self.path)

    @dbus_property()
    def Type(self) -> "s":  # type: ignore
        return self._type

    @Type.setter
    def Type(self, type: "s"):  # type: ignore
        self._type = type

    @dbus_property()
    def ServiceUUIDs(self) -> "as":  # type: ignore
        return self._service_uuids

    @ServiceUUIDs.setter
    def ServiceUUIDs(self, service_uuids: "as"):  # type: ignore
        self._service_uuids = service_uuids

    @dbus_property()
    def ManufacturerData(self) -> "a{qv}":  # type: ignore
        return self._manufacturer_data

    @ManufacturerData.setter
    def ManufacturerData(self, data: "a{qv}"):  # type: ignore
        self._manufacturer_data = data

    @dbus_property()
    def SolicitUUIDs(self) -> "as":  # type: ignore
        return self._solicit_uuids

    @SolicitUUIDs.setter  # type: ignore
    def SolicitUUIDs(self, uuids: "as"):  # type: ignore
        self._solicit_uuids = uuids

    @dbus_property()
    def ServiceData(self) -> "a{sv}":  # type: ignore
        return self._service_data

    @ServiceData.setter
    def ServiceData(self, data: "a{sv}"):  # type: ignore
        self._service_data = data

    @dbus_property()
    def Includes(self) -> "as":  # type: ignore
        return ["tx-power", "local-name"]

    @Includes.setter
    def Includes(self, include):  # type: ignore
        pass

    @dbus_property()
    def TxPower(self) -> "n":  # type: ignore
        return self._tx_power

    @TxPower.setter
    def TxPower(self, dbm: "n"):  # type: ignore
        self._tx_power = dbm

    @dbus_property()
    def MaxInterval(self) -> "u":  # type: ignore
        return self._max_interval

    @MaxInterval.setter
    def MaxInterval(self, interval: "u"):  # type: ignore
        self._max_interval = interval

    @dbus_property()
    def MinInterval(self) -> "u":  # type: ignore
        return self._min_interval

    @MinInterval.setter
    def MinInterval(self, interval: "u"):  # type: ignore
        self._min_interval = interval

    @dbus_property()
    def LocalName(self) -> "s":  # type: ignore
        return self._local_name

    @LocalName.setter
    def LocalName(self, name: str):
        self._local_name = name
