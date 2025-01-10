import sys
from PyQt5.QtWidgets import QApplication
from views.main_window import MainWindow

def load_styles(app):
    # Load your QSS files and apply them
    with open("styles/main_window.qss", "r") as f:
        main_style = f.read()
    with open("styles/buttons.qss", "r") as f:
        button_style = f.read()
    app.setStyleSheet(main_style + button_style)

def main():
    app = QApplication(sys.argv)
    load_styles(app)  # Load the QSS files

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
