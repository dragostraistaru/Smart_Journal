from PyQt6.QtWidgets import QMessageBox, QWidget


class ConfirmDialog:
    @staticmethod
    def ask(parent: QWidget, title: str, message: str) -> bool:
        result = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes
