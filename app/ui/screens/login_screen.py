from collections.abc import Callable

from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LoginScreen(QWidget):
    def __init__(self, on_login: Callable[[str, str], None], on_go_register: Callable[[], None]) -> None:
        super().__init__()
        self._on_login = on_login

        title = QLabel("Smart Journal - Login")
        title.setObjectName("title")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Parola")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Email", self.email_input)
        form.addRow("Parola", self.password_input)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self._handle_login)

        register_button = QPushButton("Creeaza cont")
        register_button.clicked.connect(on_go_register)

        root = QVBoxLayout()
        root.addWidget(title)
        root.addLayout(form)
        root.addWidget(login_button)
        root.addWidget(register_button)
        root.addStretch()
        self.setLayout(root)

    def _handle_login(self) -> None:
        self._on_login(self.email_input.text(), self.password_input.text())
