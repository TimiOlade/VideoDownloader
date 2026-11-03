# main.py
import sys
from PyQt6 import QtWidgets
from mainwindow import MainWindow
from workerFunctions import WorkerFunctions
#---------------------------[Do all Imports Above]-------------------------

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    worker = WorkerFunctions()

    # Clean signal & slot wiring
    #window.ui.AddBtn.clicked.connect(worker.tester)
    #window.ui.DeleteBtn.clicked.connect(worker.start_loop_safely)
    worker.updateGUI.connect(window.process_GUI_Updates)
    window.sendDownloadList.connect(worker.ReceiveDownloadList)
    window.sendLinkForMetaData.connect(worker.peekMetaData)

    window.show()
    sys.exit(app.exec())