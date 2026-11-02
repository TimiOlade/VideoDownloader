# workerFunctions.py
import time
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QThread, pyqtSignal

class WorkerFunctions(QThread):
    # Custom signal that emits a status dict to the GUI thread
    updateGUI = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        """Standard QThread entry point."""
        self.dodownload()

    def dodownload(self):
        """Simulates a download loop updating every 2 seconds."""
        for step in range(1, 22):
            message = f"Downloading item {step} of 10..."
            # Emit the signal to update the main thread/GUI safely
            data_packet = {"Edit_LinkDetail": message}
            self.updateGUI.emit(data_packet)
            print(message)
            time.sleep(2)
            
        self.updateGUI.emit({"textEdit":"Download Complete!"})

    def ReceiveDownloadList(self, URLList):
        if not isinstance(URLList, list) or not URLList:
            print("[-] Error: process_GUI_Updates expected a non-empty dictionary.")
            return 

        for link in URLList:
            print(link)
            self.updateGUI.emit({"statusBar": link}) 
            for pb in range(100):
                data_packet = {"progressBar": pb}
                self.updateGUI.emit(data_packet) 
                time.sleep(0.1)

    def tester(self):
        print("Button Pressed ")
        data_packet = {"textEdit": "Button Pressed"}
        self.updateGUI.emit(data_packet)

    def DoGUI_to_Worker_Link(self, main_window):

        #A gui btn calls a function in the worker class
        main_window.ui.myBtn.clicked.connect(self.tester)
        #calls a method in GUI
        self.updateGUI.connect(main_window.process_GUI_Updates)
        #This calls the thread to start the loop
        main_window.ui.btnStartLoop.clicked.connect(self.start)

    def start_loop_safely(self):
            """Prevents starting a new thread if one is already running."""
            if not self.isRunning():
                self.start()
                print("[*] Worker thread started.")
            else:
                print("[!] Worker thread is already running.")