from dbus_fast.service import ServiceInterface, method, dbus_property
from dbus_fast.constants import PropertyAccess
from dbus_fast.signature import Variant

from bluetooth import defs


class GattDescriptor(ServiceInterface):
    """
    org.bluez.GattDescriptor1 interface implementation
    """

    def __init__(self, uuid: str, flags: list[defs.GattDescriptorFlags], index: int, characteristic_path: str):
        """
        Create a BlueZ Gatt Descriptor

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
        return self._value

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
        self._value = value

    async def get_obj(self) -> dict:
        """
        Obtain the underlying dictionary within the BlueZ API that describes
        the descriptor

        Returns
        -------
        Dict
            The dictionary that describes the descriptor
        """
        return {"UUID": Variant("s", self._uuid)}
