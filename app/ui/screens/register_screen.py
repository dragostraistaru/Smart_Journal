from collections.abc import Callable

from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class RegisterScreen(QWidget):
    def __init__(
        self,
        on_register: Callable[[str, str, str], None],
        on_go_login: Callable[[], None],
    ) -> None:
        super().__init__()
        self._on_register = on_register

        title = QLabel("Smart Journal - Register")
        title.setObjectName("title")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Parola")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirma parola")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Email", self.email_input)
        form.addRow("Parola", self.password_input)
        form.addRow("Confirmare", self.confirm_input)

        register_button = QPushButton("Inregistreaza")
        register_button.clicked.connect(self._handle_register)

        back_button = QPushButton("Inapoi la login")
        back_button.clicked.connect(on_go_login)

        root = QVBoxLayout()
        root.addWidget(title)
        root.addLayout(form)
        root.addWidget(register_button)
        root.addWidget(back_button)
        root.addStretch()
        self.setLayout(root)

    def _handle_register(self) -> None:
        self._on_register(
            self.email_input.text(),
            self.password_input.text(),
            self.confirm_input.text(),
        )
