import sys

from PyQt6.QtWidgets import QApplication

from app.db.init_db import init_db
from app.ui.app_window import AppWindow


def main() -> None:
	init_db()
	app = QApplication(sys.argv)
	window = AppWindow()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()