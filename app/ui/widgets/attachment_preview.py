from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt6.QtWidgets import QListWidget, QListWidgetItem


class AttachmentPreview(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setIconSize(QSize(120, 120))
        self.setGridSize(QSize(150, 160))
        self.setWordWrap(True)
        self.setSpacing(8)
        self.itemDoubleClicked.connect(self._open_item)

    def set_paths(self, paths: list[str]) -> None:
        self.clear()
        for raw_path in paths:
            path = Path(raw_path)
            item = QListWidgetItem(path.name or str(path))
            item.setToolTip(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))

            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                item.setIcon(QIcon(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))

            self.addItem(item)

    def _open_item(self, item: QListWidgetItem) -> None:
        raw_path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(raw_path, str) and raw_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(raw_path))
