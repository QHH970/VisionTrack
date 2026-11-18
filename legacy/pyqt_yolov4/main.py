import os
import sys
import warnings
from DetectionTracking import Ui_MainWindow
from PySide6 import QtCore, QtGui, QtWidgets

if __name__ == '__main__':
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    warnings.filterwarnings(action='ignore')

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())