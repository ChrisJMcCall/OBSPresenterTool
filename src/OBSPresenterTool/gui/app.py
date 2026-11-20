"""Entry point for the OBS window selector GUI."""
import sys

from PySide6.QtWidgets import QApplication

from OBSPresenterTool.gui.selector import WindowSelector


def main() -> int:
    app = QApplication(sys.argv)
    win = WindowSelector()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
