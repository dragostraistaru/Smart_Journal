from PyQt6.QtWidgets import QListWidget


class AttachmentPreview(QListWidget):
    def set_paths(self, paths: list[str]) -> None:
        self.clear()
        self.addItems(paths)
