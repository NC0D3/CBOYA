import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGraphicsDropShadowEffect

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.setWindowTitle("Interfaz CBOYA")
        self.setGeometry(0, 0, 1024, 600)
        self.showFullScreen()

        # Crear layout principal
        main_layout = QVBoxLayout()

        # Sección superior
        top_section = QHBoxLayout()
        top_section.setSpacing(10)

        # Logo y texto "CBOYA"
        logo_label = QLabel(self)
        pixmap = QPixmap("path_to_logo.png")  # Sustituir con la ruta del logo
        logo_label.setPixmap(pixmap)
        top_section.addWidget(logo_label)

        # Botones
        for i in range(1, 5):
            btn = QPushButton(f"Boton{i}", self)
            btn.setStyleSheet("border-radius: 15px;")  # Bordes redondeados
            top_section.addWidget(btn)

        # Agregar sección superior al layout principal
        main_layout.addLayout(top_section)

        # Sección inferior
        bottom_section = QWidget(self)
        bottom_section.setStyleSheet("background-color: #005281;")
        main_layout.addWidget(bottom_section)

        # Asignar el layout principal
        self.setLayout(main_layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()  # Salir del modo pantalla completa
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
