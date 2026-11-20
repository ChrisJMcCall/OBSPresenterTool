"""Look up macOS application icons by app (window owner) name."""
import time

from AppKit import NSWorkspace
from PySide6.QtGui import QIcon, QPixmap

_cache: dict[str, QIcon | None] = {}
_misses: dict[str, float] = {}  # owner -> time of last failed lookup
_RETRY_SECONDS = 30


def _make_icon(ns_image) -> QIcon | None:
    data = ns_image.TIFFRepresentation()
    if data is None:
        return None
    pixmap = QPixmap()
    if not pixmap.loadFromData(bytes(data)):
        return None
    return QIcon(pixmap)


def icon_for_owner(owner: str) -> QIcon | None:
    """Icon of the running app whose name matches `owner`, or None if not found."""
    if owner in _cache:
        return _cache[owner]
    if time.monotonic() - _misses.get(owner, -_RETRY_SECONDS) < _RETRY_SECONDS:
        return None  # recently failed; don't rescan on every refresh
    for app in NSWorkspace.sharedWorkspace().runningApplications():
        if app.localizedName() == owner and app.icon() is not None:
            icon = _make_icon(app.icon())
            if icon is not None:
                _cache[owner] = icon
                return icon
    _misses[owner] = time.monotonic()
    return None
