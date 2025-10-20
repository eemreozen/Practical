import sys
from PyQt5.QtWidgets import QApplication
from main_app import YouTubeConverter

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = YouTubeConverter()
    window.show()
    sys.exit(app.exec_())