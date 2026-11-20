"""Auto scene switch: leave the scene when the source's window goes empty."""
import os
from collections.abc import Callable

import obsws_python as obs
from PySide6.QtCore import QObject, QTimer, Signal

from OBSPresenterTool import obs_client

COUNTDOWN_MS = 300
POLL_MS = 250  # closing a window sends no OBS event, so also poll for it


def _fmt(data) -> dict:
    """An obsws-python event dataclass as a plain dict (for debug printing)."""
    return {name: getattr(data, name) for name in data.attrs()}


class AutoSwitcher(QObject):
    # Emitted from the websocket event thread; Qt queues them onto the GUI thread.
    _source_changed = Signal()
    _scene_changed = Signal()

    def __init__(self, get_client: Callable[[], obs.ReqClient], parent=None) -> None:
        super().__init__(parent)
        self._get_client = get_client
        self._events: obs.EventClient | None = None
        self.source = ""
        self.running = False

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(COUNTDOWN_MS)
        self._timer.timeout.connect(self._on_countdown_done)
        self._poll = QTimer(self)
        self._poll.setInterval(POLL_MS)
        self._poll.timeout.connect(self._check_window)
        self._source_changed.connect(self._check_window)
        self._scene_changed.connect(self._check_scene)

    # --- lifecycle -------------------------------------------------------
    def start(self, source: str) -> bool:
        """Begin listening; returns False if OBS can't be reached."""
        self.stop()
        self.source = source
        try:
            self._events = obs.EventClient(
                host=os.environ.get("OBS_HOST", "localhost"),
                port=int(os.environ.get("OBS_PORT", "4455")),
                password=os.environ.get("OBS_PASSWORD", ""),
                timeout=5,
            )
        except Exception:
            self._events = None
            return False
        self._events.callback.register([
            self.on_input_settings_changed,
            self.on_current_program_scene_changed,
            self.on_input_active_state_changed,
            self.on_input_show_state_changed,
        ])
        self.running = True
        self._poll.start()
        self._check_window()  # handle a source that is already empty
        return True

    def stop(self) -> None:
        self.running = False
        self._poll.stop()
        self._timer.stop()
        if self._events is not None:
            try:
                self._events.disconnect()
            except Exception:
                pass
            self._events = None

    def set_source(self, source: str) -> None:
        self.source = source
        self._timer.stop()
        if self.running:
            self._check_window()

    # --- event thread callbacks (names are matched by obsws-python) -------
    def on_input_active_state_changed(self, data) -> None:
        print(f"[event] InputActiveStateChanged: {_fmt(data)}")

    def on_input_show_state_changed(self, data) -> None:
        print(f"[event] InputShowStateChanged: {_fmt(data)}")

    def on_input_settings_changed(self, data) -> None:
        print(f"[event] InputSettingsChanged: {_fmt(data)}")
        if getattr(data, "input_name", None) == self.source:
            self._source_changed.emit()

    def on_current_program_scene_changed(self, data) -> None:
        print(f"[event] CurrentProgramSceneChanged: {_fmt(data)}")
        self._scene_changed.emit()

    # --- GUI-thread logic -----------------------------------------------
    def _window_is_empty(self, client) -> bool:
        """True if no window is set, or the set window no longer exists (e.g. it was closed)."""
        window = obs_client.get_current_window(client, self.source)
        if not window:
            return True
        return window not in {w["id"] for w in obs_client.list_windows(client, self.source)}

    def _live_scene_uses_source(self, client) -> bool:
        return obs_client.scene_uses_source(client, obs_client.current_scene(client), self.source)

    def _check_window(self) -> None:
        if not self.running:
            return
        try:
            client = self._get_client()
            if self._window_is_empty(client) and self._live_scene_uses_source(client):
                if not self._timer.isActive():
                    self._timer.start()
            else:
                self._timer.stop()  # window is non-empty again: cancel the countdown
        except Exception:
            self._timer.stop()

    def _check_scene(self) -> None:
        if not self.running:
            return
        try:
            if not self._live_scene_uses_source(self._get_client()):
                self._timer.stop()
            else:
                self._check_window()
        except Exception:
            self._timer.stop()

    def _on_countdown_done(self) -> None:
        try:
            client = self._get_client()
            if not (self._window_is_empty(client) and self._live_scene_uses_source(client)):
                return
            target = obs_client.scene_to_leave_to(client, self.source)
            if target:
                obs_client.set_scene(client, target)
                print(f"Auto scene switch: -> {target}")
        except Exception as e:
            print(f"Auto scene switch failed: {e}")
