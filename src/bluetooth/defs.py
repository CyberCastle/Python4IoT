# Mix oof code obtained from here: https://github.com/hbldh/bleak/blob/develop/bleak/backends/dbus/defs.py
# and here: https://github.com/kevincar/bless/blob/master/bless/backends/bluezdbus/dbus/characteristic.py
from enum import Enum, Flag
from typing import TypedDict

# DBus Interfaces
OBJECT_MANAGER_INTERFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROPERTIES_INTERFACE = "org.freedesktop.DBus.Properties"

#  Specific DBUS
BLUEZ_SERVICE = "org.bluez"

# General Bluez interfaces
ADAPTER_INTERFACE = "org.bluez.Adapter1"
ADVERTISEMENT_MONITOR_INTERFACE = "org.bluez.AdvertisementMonitor1"
ADVERTISEMENT_MONITOR_MANAGER_INTERFACE = "org.bluez.AdvertisementMonitorManager1"
DEVICE_INTERFACE = "org.bluez.Device1"
BATTERY_INTERFACE = "org.bluez.Battery1"
LE_ADVERTISEMENT_INTERFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISEMENT_MANAGER_INTERFACE = "org.bluez.LEAdvertisingManager1"

# GATT interfaces
GATT_MANAGER_INTERFACE = "org.bluez.GattManager1"
GATT_PROFILE_INTERFACE = "org.bluez.GattProfile1"
GATT_SERVICE_INTERFACE = "org.bluez.GattService1"
GATT_CHARACTERISTIC_INTERFACE = "org.bluez.GattCharacteristic1"
GATT_DESCRIPTOR_INTERFACE = "org.bluez.GattDescriptor1"


# D-Bus properties for interfaces
# https://github.com/bluez/bluez/blob/master/doc/org.bluez.Adapter.rst
class Adapter1(TypedDict):
    Address: str
    Name: str
    Alias: str
    Class: int
    Powered: bool
    Discoverable: bool
    Pairable: bool
    PairableTimeout: int
    DiscoverableTimeout: int
    Discovering: int
    UUIDs: list[str]
    Modalias: str
    Roles: list[str]
    ExperimentalFeatures: list[str]


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.AdvertisementMonitor.rst
class AdvertisementMonitor1(TypedDict):
    Type: str
    RSSILowThreshold: int
    RSSIHighThreshold: int
    RSSILowTimeout: int
    RSSIHighTimeout: int
    RSSISamplingPeriod: int
    Patterns: list[tuple[int, int, bytes]]


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.AdvertisementMonitorManager.rst
class AdvertisementMonitorManager1(TypedDict):
    SupportedMonitorTypes: list[str]
    SupportedFeatures: list[str]


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.Battery.rst
class Battery1(TypedDict):
    SupportedMonitorTypes: list[str]
    SupportedFeatures: list[str]


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.Device.rst
class Device1(TypedDict):
    Address: str
    AddressType: str
    Name: str
    Icon: str
    Class: int
    Appearance: int
    UUIDs: list[str]
    Paired: bool
    Bonded: bool
    Connected: bool
    Trusted: bool
    Blocked: bool
    WakeAllowed: bool
    Alias: str
    Adapter: str
    LegacyPairing: bool
    Modalias: str
    RSSI: int
    TxPower: int
    ManufacturerData: dict[int, bytes]
    ServiceData: dict[str, bytes]
    ServicesResolved: bool
    AdvertisingFlags: bytes
    AdvertisingData: dict[int, bytes]


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.GattService.rst
class GattService1(TypedDict):
    UUID: str
    Primary: bool
    Device: str
    Includes: list[str]
    Handle: int  # (Server only)


# https://github.com/bluez/bluez/blob/master/src/shared/att-types.h
class GattCharacteristicProperties(Flag):
    broadcast = 0x0001
    read = 0x0002
    write_without_response = 0x0004
    write = 0x0008
    notify = 0x0010
    indicate = 0x0020
    authenticated_signed_writes = 0x0040
    extended_properties = 0x0080
    reliable_write = 0x0100
    writable_auxiliaries = 0x0200


# https://github.com/bluez/bluez/blob/master/src/shared/att-types.h
class GattAttributePermissions(Flag):
    readable = 0x1
    writeable = 0x2
    read_encryption_required = 0x4
    write_encryption_required = 0x8


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.GattCharacteristic.rst
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


class GattCharacteristic1(TypedDict):
    UUID: str
    Service: str
    Value: bytes
    WriteAcquired: bool
    NotifyAcquired: bool
    Notifying: bool
    Flags: list[GattCharacteristicFlags]
    MTU: int
    Handle: int  # (Server only)


# https://github.com/bluez/bluez/blob/master/doc/org.bluez.GattDescriptor.rst
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


class GattDescriptor1(TypedDict):
    UUID: str
    Characteristic: str
    Value: bytes
    Flags: list[GattDescriptorFlags]
    Handle: int  # (Server only)
