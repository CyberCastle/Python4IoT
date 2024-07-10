from typing import Any
from dbus_fast import Variant


def getattr_variant(object: dict[str, Variant], key: str, default: Any):
    if key in object:
        return object[key].value
    else:
        return default
