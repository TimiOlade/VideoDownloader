# main.py
import sys
from PyQt6 import QtWidgets
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import QTimer
from mainwindow import MainWindow, SplashScreen
from workerClass import WorkerClass

#-------------------------[ Use this commands to compile a standalone ]------------
# For Windows
#  py -3.15 -m PyInstaller --onefile --windowed --clean --name "WebVidDownloader" --add-data "bin/windows;bin/windows" --add-data "Help.pdf;." main.py

#---------------------------[Do all Imports Above]-------------------------
APPNAME = "Video Downloader v" 


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    worker = WorkerClass()
    #Initialize the splash screen
    splashScreen = SplashScreen(window)
    QTimer.singleShot(10000,splashScreen.mousePressEvent)

    # Clean signal & slot wiring
    #window.ui.AddBtn.clicked.connect(worker.tester)
    #window.ui.DeleteBtn.clicked.connect(worker.start_loop_safely)
    worker.updateGUI.connect(window.process_GUI_Updates)
    worker.progress_signal.connect(window.update_progress)
    window.sendDownloadList.connect(worker.ReceiveDownloadList)
    worker.messageBox.connect(window.newmessageBox)
    window.saveSignal.connect(worker.save_config_file)
    window.loadSignal.connect(worker.load_config_file)
    window.sendLinkForMetaData.connect(worker.peekMetaData)
    window.setWindowTitle(APPNAME + worker.VERSION)
    worker.load_config_file()

    window.show()
    sys.exit(app.exec())