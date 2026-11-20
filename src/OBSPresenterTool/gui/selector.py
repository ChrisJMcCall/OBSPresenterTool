"""Small floating window (200x350) listing the windows OBS offers for its capture source."""
import sys

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QListWidgetItem,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from OBSPresenterTool import obs_client
from OBSPresenterTool.gui import app_icons
from OBSPresenterTool.gui.auto_switch import AutoSwitcher
from OBSPresenterTool.gui.widgets import ICON_SIZE, NoAutoSelectList, TopLeftIconDelegate
from OBSPresenterTool.windows import OWN_TITLE, is_filtered, owner, sort_key, window_title

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = obs_client.connect()
    return _client


def _drop_client() -> None:
    global _client
    _client = None


def get_open_windows(source: str) -> tuple[list[dict], object]:
    """Return (windows, current window id) for the source from OBS. Raises on failure."""
    try:
        client = _get_client()
        return (
            obs_client.list_windows(client, source),
            obs_client.get_current_window(client, source),
        )
    except Exception:
        _drop_client()
        raise


class WindowSelector(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(OWN_TITLE)
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(200, 350)
        # macOS hides Qt.Tool windows when the app is inactive; keep it visible.
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        # Qt suppresses tooltips while the app is inactive; this window usually is.
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips)

        self._settings = QSettings("OBSPresenterTool", "OBSPresenterTool")
        self.source = str(self._settings.value("source", obs_client.DEFAULT_SOURCE))
        self._sources = None  # last source names shown in the combo

        self.auto_switcher = AutoSwitcher(_get_client, self)
        self.auto_switch_box = QCheckBox("Auto scene switch")
        self.auto_switch_box.toggled.connect(self._on_auto_switch)
        self.auto_switch_box.setChecked(True)  # on by default; starts the switcher

        self.show_all = QToolButton()
        self.show_all.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.show_all.setToolTip("Show all windows (disable filter)")
        self.show_all.setFixedSize(26, 26)
        self.show_all.setCheckable(True)
        self.show_all.toggled.connect(self._on_show_all)

        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self._on_source_changed)

        self.list = NoAutoSelectList()
        self.list.setWordWrap(False)
        self.list.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        self.list.setItemDelegate(TopLeftIconDelegate(self.list))
        # Scroll by pixel (not by whole item) so the mouse wheel moves smoothly.
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.verticalScrollBar().setSingleStep(10)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setStyleSheet(
            "QListWidget::item { border-bottom: 1px solid #d9d9d9; }"
            # Keep the selected item readable whether or not the window is active.
            "QListWidget::item:selected, QListWidget::item:selected:!active "
            "{ background: palette(highlight); color: palette(highlighted-text); }"
        )
        # Act only on deliberate clicks / Enter; a selection change alone does nothing.
        self.list.itemClicked.connect(self._on_select)
        self.list.itemActivated.connect(self._on_select)
        self.list.deselected.connect(self._on_deselect)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self.combo)
        toolbar = QHBoxLayout()
        toolbar.addWidget(self.auto_switch_box)
        toolbar.addStretch(1)
        toolbar.addWidget(self.show_all)
        layout.addLayout(toolbar)
        layout.addWidget(self.list)

        self._initial_scroll_done = False
        self._shown = None  # last rendered state, to skip no-op refreshes
        self.refresh()
        timer = QTimer(self)
        timer.timeout.connect(self.refresh)
        timer.start(2000)

    def _show_hint(self, text: str) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItem(text)
        self.list.item(0).setFlags(Qt.ItemFlag.NoItemFlags)
        self.list.blockSignals(False)

    def _refresh_sources(self) -> None:
        """Keep the drop-down in sync with OBS's capture sources."""
        names = obs_client.list_sources(_get_client())
        if names == self._sources:
            return
        # Only worth showing a chooser when there is a real choice to make.
        self.combo.setVisible(len(names) > 1)
        self._sources = names
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(names)
        self.combo.setEnabled(bool(names))
        if names:
            if self.source not in names:
                self.source = names[0]
                self.auto_switcher.set_source(self.source)
            self.combo.setCurrentText(self.source)
        self.combo.blockSignals(False)
        self._shown = None  # force the window list to rebuild

    def _on_auto_switch(self, checked: bool) -> None:
        if not checked:
            self.auto_switcher.stop()
        elif not self.auto_switcher.start(self.source):
            self.auto_switch_box.blockSignals(True)
            self.auto_switch_box.setChecked(False)  # couldn't reach OBS
            self.auto_switch_box.blockSignals(False)

    def closeEvent(self, event) -> None:
        self.auto_switcher.stop()
        super().closeEvent(event)

    def _on_show_all(self, _checked: bool) -> None:
        self._shown = None
        self.refresh()

    def _on_source_changed(self, name: str) -> None:
        if not name or name == self.source:
            return
        self.source = name
        self._settings.setValue("source", name)
        self.auto_switcher.set_source(name)
        self._shown = None
        self.refresh()

    def refresh(self) -> None:
        try:
            self._refresh_sources()
            if not self._sources:
                if self._shown != "nosources":
                    self._show_hint("No capture sources in OBS")
                    self._shown = "nosources"
                return
            windows, current_id = get_open_windows(self.source)
            if not self.show_all.isChecked():
                windows = [
                    w for w in windows
                    if not is_filtered(w["title"]) or (current_id and w["id"] == current_id)
                ]
        except Exception:
            _drop_client()
            if self._shown != "error":
                self._show_hint("Can't reach OBS (is the WebSocket server on?)")
                self._shown = "error"
            return

        windows.sort(key=sort_key)
        state = [w["id"] for w in windows]
        scroll = self.list.verticalScrollBar().value()  # keep the view where the user left it
        self.list.blockSignals(True)
        if state != self._shown:
            self._shown = state
            self.list.clear()
            if not windows:
                self.list.blockSignals(False)
                self._show_hint("No windows reported by OBS")
                return
            for w in windows:
                app_name = owner(w["title"])
                icon = app_icons.icon_for_owner(app_name)
                if icon is not None:
                    item = QListWidgetItem(icon, window_title(w["title"]))
                else:  # no icon found: keep the "[Owner]" text so it stays identifiable
                    item = QListWidgetItem(f"[{app_name}] {window_title(w['title'])}")
                item.setToolTip(window_title(w["title"]))  # full title on hover
                item.setData(Qt.ItemDataRole.UserRole, w)
                self.list.addItem(item)
        # Highlight whatever OBS currently has selected (source of truth).
        for i in range(self.list.count()):
            data = self.list.item(i).data(Qt.ItemDataRole.UserRole)
            if data and current_id and data["id"] == current_id:
                self.list.setCurrentRow(i)
                break
        else:
            self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        if not self._initial_scroll_done and self.list.currentItem() is not None:
            # First time the list is populated: bring the selected item into view.
            self._initial_scroll_done = True
            QTimer.singleShot(0, self._scroll_to_selected)
            return
        # setCurrentRow()/rebuilding can scroll the list; put it back (now and after layout).
        self._restore_scroll(scroll)
        QTimer.singleShot(0, lambda: self._restore_scroll(scroll))

    def _scroll_to_selected(self) -> None:
        item = self.list.currentItem()
        if item is not None:
            self.list.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)

    def _restore_scroll(self, value: int) -> None:
        self.list.verticalScrollBar().setValue(value)

    def _on_deselect(self) -> None:
        """Clicking the selected row again clears the selection and blanks the source's window."""
        try:
            obs_client.set_window(_get_client(), self.source, 0)
            print("Cleared window (blank)")
        except Exception as e:
            _drop_client()
            print(f"Could not clear window: {e}", file=sys.stderr)

    def _on_select(self, item: QListWidgetItem | None) -> None:
        w = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not w:
            return
        try:
            client = _get_client()
            if self.auto_switch_box.isChecked():
                # Make sure a scene that uses the source is live before changing its window.
                live = obs_client.current_scene(client)
                if not obs_client.scene_uses_source(client, live, self.source):
                    target = obs_client.scene_to_enter(client, self.source, live)
                    if target:
                        obs_client.set_scene(client, target)
            obs_client.switch_window(client, self.source, w["id"])
            print(f"Switched to: {w['title']}")
        except Exception as e:
            _drop_client()
            print(f"Could not switch window: {e}", file=sys.stderr)
