"""Custom Qt widgets for the window list."""
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QIcon
from PySide6.QtWidgets import QApplication, QListWidget, QStyle, QStyledItemDelegate, QWidget

ICON_SIZE = 24
PAD = 4  # horizontal padding
PAD_Y = 10  # top/bottom padding of each item


def _elide(fm: QFontMetrics, text: str, width: int) -> str:
    """Truncate `text` with a literal "..." so it fits in `width` pixels."""
    if fm.horizontalAdvance(text) <= width:
        return text
    while text and fm.horizontalAdvance(text + "...") > width:
        text = text[:-1]
    return text.rstrip() + "..."


_NAV_KEYS = {
    Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End,
    Qt.Key.Key_PageUp, Qt.Key.Key_PageDown, Qt.Key.Key_Tab, Qt.Key.Key_Backtab,
}


class NoAutoSelectList(QListWidget):
    """QListWidget whose rows are only selected by an explicit mouse click.

    No automatic selection of the first row on focus, and no keyboard navigation changing it.
    """

    deselected = Signal()  # clicked the row that was already selected
    _swallow_release = False

    def mousePressEvent(self, event) -> None:
        item = self.itemAt(event.position().toPoint())
        if item is not None and item is self.currentItem() and item.isSelected():
            self.setCurrentRow(-1)  # unselect (Qt's toggle would leave it current)
            self.clearSelection()
            self._swallow_release = True  # the release would otherwise emit itemClicked
            self.deselected.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._swallow_release:
            self._swallow_release = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in _NAV_KEYS:
            event.ignore()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # On macOS Qt doesn't activate on Return by itself, so do it explicitly.
            if self.currentItem() is not None:
                self.itemActivated.emit(self.currentItem())
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event) -> None:
        # QAbstractItemView.focusInEvent would make row 0 current (and so trigger a window
        # switch); skip it and just do the plain widget behavior.
        QWidget.focusInEvent(self, event)
        self.viewport().update()


class TopLeftIconDelegate(QStyledItemDelegate):
    """Icon at the item's top-left; single-line title (elided with "...") centered vertically."""

    def _text_rect(self, rect: QRect, has_icon: bool) -> QRect:
        left = PAD + (ICON_SIZE + PAD if has_icon else 0)
        return rect.adjusted(left, PAD_Y, -PAD, -PAD_Y)

    def paint(self, painter, option, index) -> None:
        opt = type(option)(option)
        self.initStyleOption(opt, index)
        icon, text = QIcon(opt.icon), str(opt.text)  # copies: opt.icon is cleared below
        opt.icon = QIcon()
        opt.text = ""
        style = opt.widget.style() if opt.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        painter.save()
        if not icon.isNull():
            icon.paint(painter, QRect(opt.rect.left() + PAD, opt.rect.top() + PAD_Y, ICON_SIZE, ICON_SIZE))
        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        palette = opt.palette
        painter.setPen(palette.highlightedText().color() if selected else palette.text().color())
        painter.setFont(opt.font)
        # Text area spans the full item height (minus the 1px separator) so it centers vertically.
        area = self._text_rect(opt.rect, not icon.isNull()).adjusted(0, -PAD_Y, 0, PAD_Y - 1)
        elided = _elide(QFontMetrics(opt.font), text, area.width())
        painter.drawText(
            area, int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), elided
        )
        painter.restore()

    def sizeHint(self, option, index) -> QSize:
        opt = type(option)(option)
        self.initStyleOption(opt, index)
        has_icon = not opt.icon.isNull()
        content = max(QFontMetrics(opt.font).height(), ICON_SIZE if has_icon else 0)
        return QSize(0, content + 2 * PAD_Y + 1)  # +1 for the separator line
