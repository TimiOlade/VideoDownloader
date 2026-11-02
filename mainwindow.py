import sys
import validators
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import pyqtSignal
from ui_compiler import ensure_ui_compiled

#--------------[ All imports above this line ]-----------------
#--------------[ Do not touch the XML QT designer Complier logic below] ---------
# 1. Trigger the external compiler check first
ensure_ui_compiled()

# 2. Import the generated module
#from Ui_MainForm import Ui_MainWindow
from DownloaderForm import Ui_MainWindow
#-------------------------------------------------------------------

#--------------[ Declare you Global Variables here ]-----------------


class MainWindow(QMainWindow):
    sendDownloadList = pyqtSignal(list)
    def __init__(self):  # init the class constructor
        super().__init__()
        # Create an instance of the UI MainForm class
        self.ui = Ui_MainWindow()
        # Setup and draw all form objects on this window reference
        self.ui.setupUi(self)

#================[Local Signal to Slot Connections here]====================
        
        self.ui.AddBtn.clicked.connect(self.AddLink)
        self.ui.LinkInputBox.textChanged.connect(lambda text: self.ui.AddBtn.setEnabled(len(text) > 0))
        self.ui.DownloadBtn.clicked.connect(self.CreateDownloadList)
        self.ui.LinkList.model().rowsInserted.connect(lambda p,f,l: self.ui.DeleteBtn.setEnabled(self.ui.LinkList.count() > 0))
        self.ui.LinkList.model().rowsRemoved.connect(lambda p,f,l: self.ui.DeleteBtn.setEnabled(self.ui.LinkList.count() > 0))
        self.ui.LinkList.model().rowsInserted.connect(lambda p,f,l: self.ui.DownloadBtn.setEnabled(self.ui.LinkList.count() > 0))
        self.ui.LinkList.model().rowsRemoved.connect(lambda p,f,l: self.ui.DownloadBtn.setEnabled(self.ui.LinkList.count() > 0))

#=====================================================================================        
        self.ConfigureStatusBar()

    def AddLink(self):
        if len(self.ui.LinkInputBox.text()) == 0:
            QMessageBox.information(
                        self, 
                        "No", 
                        "There's nothing in there!"
                    )
        if bool(validators.url(self.ui.LinkInputBox.text())) == True:
            if len(self.ui.LinkInputBox.text()) > 0:
                self.ui.LinkList.addItem(self.ui.LinkInputBox.text())
                self.ui.LinkInputBox.setText("")
        else:
            QMessageBox.information(
            self, 
            "Invalid Link", 
            "This doesn't look like an URL!"
        )  

    def CreateDownloadList(self):
        DownloadList = []
        for f in range(self.ui.LinkList.count()):
            DownloadList.append(self.ui.LinkList.item(f).text())
            #print(self.ui.LinkList.item(f).text())

        if len(DownloadList) > 0:
            self.sendDownloadList.emit(DownloadList)

    def ConfigureStatusBar(self):
        self.statusBar().addWidget(self.ui.statusETA)
        self.statusBar().addWidget(self.ui.statusDownloadSpeed)
        self.statusBar().addWidget(self.ui.statusCurrentVideo)

    def process_GUI_Updates(self, data_dict: dict):
        """Processes incoming dictionary data safely."""
        # Safeguard: ensure we have a valid, non-empty dictionary
        if not isinstance(data_dict, dict) or not data_dict:
            print("[-] Error: process_GUI_Updates expected a non-empty dictionary.")
            return        

        (action_type, message), = data_dict.items()
        
        match action_type:
            case "textEdit":
                self.ui.textEdit.append(message)
            case "progressBar":
                self.ui.progressBar.setValue(message)
            case "statusBar":
                #self.ui.progressBar.setValue(message)
                self.ui.statusCurrentVideo.setText("Video: " + message)
            case "Edit_LinkDetail":
                self.ui.Edit_LinkDetail.append(message)
            case _:
                print(f"[-] Warning: Unknown action key received -> '{action_type}'")

        
    
    