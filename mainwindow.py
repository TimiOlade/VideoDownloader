import sys
import os
import validators
import json
import configparser
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt6.QtCore import pyqtSignal, Qt
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
    videoData = {}
    configFile = "config.ini"
    sendDownloadList = pyqtSignal(list,str)
    sendLinkForMetaData = pyqtSignal(str)
    sendDestFolder = pyqtSignal(str)
    saveSignal = pyqtSignal(str)
    loadSignal = pyqtSignal()
    
    def __init__(self):  # init the class constructor
        super().__init__()
        # Create an instance of the UI MainForm class
        self.ui = Ui_MainWindow()
        # Setup and draw all form objects on this window reference
        self.ui.setupUi(self)
        # Lock the window to the size defined in Qt Designer (widgets use absolute positioning)
        self.setFixedSize(self.size())
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)


#================[Local Signal to Slot Connections here]====================
        
        self.ui.AddBtn.clicked.connect(self.AddLink)
        self.ui.MultiLoadBtn.clicked.connect(self.MultiAddLink)
        self.ui.DeleteBtn.clicked.connect(self.RemoveItem)
        self.ui.LinkInputBox.textChanged.connect(lambda text: self.ui.AddBtn.setEnabled(len(text) > 0))
        # Load URLs button is only enabled when the bulk URL box has text
        self.ui.MultiLoadBtn.setEnabled(False)
        self.ui.URLBox.textChanged.connect(
            lambda: self.ui.MultiLoadBtn.setEnabled(len(self.ui.URLBox.toPlainText().strip()) > 0)
        )
        self.ui.DownloadBtn.clicked.connect(self.CreateDownloadList)
        self.ui.LinkList.model().rowsInserted.connect(lambda p,f,l: self.ui.DeleteBtn.setEnabled(self.ui.LinkList.count() > 0))
        self.ui.LinkList.model().rowsRemoved.connect(lambda p,f,l: self.ui.DeleteBtn.setEnabled(self.ui.LinkList.count() > 0))
        # Download button: disabled on startup, enabled only by AddLink(), disabled when clicked
        self.ui.DownloadBtn.setEnabled(False)
        # ...and also disabled if the link list becomes empty (nothing to download)
        self.ui.LinkList.model().rowsRemoved.connect(
            lambda p,f,l: self.ui.DownloadBtn.setEnabled(False) if self.ui.LinkList.count() == 0 else None
        )
        self.ui.LinkList.itemSelectionChanged.connect(self.sendMetaData)
        self.ui.getFolderBtn.clicked.connect(self.GetFolder)
        self.ui.actionAppInfo.triggered.connect(self.displayAppData)
        self.ui.actionDonate.triggered.connect(self.displayDonateInfo)
        self.ui.actionHelp.triggered.connect(lambda: os.startfile(os.path.join(os.path.dirname(sys.argv[0]), "Help.pdf")))
        self.ui.ClearLoggerBtn.clicked.connect(self.ui.DownloadLog.clear)

#=====================================================================================        
        self.ConfigureStatusBar()
        

    def AddLink(self):
        linkToAdd = self.ui.LinkInputBox.text().strip()
        if len(linkToAdd) == 0:
            QMessageBox.information(
                        self, 
                        "No", 
                        "There's nothing in there!"
                    )
            return
        if bool(validators.url(linkToAdd)) == True:
            self.ui.LinkList.addItem(linkToAdd)
            self.ui.LinkInputBox.setText("")
            self.ui.DownloadBtn.setEnabled(True)
        else:
            QMessageBox.information(
            self, 
            "Invalid Link", 
            "This doesn't look like an URL!"
        ) 

    def MultiAddLink(self):
        doc = self.ui.URLBox.document()
        invalidURLs = []
        addedCount = 0
        for i in range(doc.blockCount()):
            linkline = doc.findBlockByNumber(i)

            link = linkline.text().strip()

            if len(link) == 0:
                continue  # skip blank lines

            if bool(validators.url(link)) == True:
                self.ui.LinkList.addItem(link)
                addedCount += 1
            else:
                invalidURLs.append(link)

        self.ui.URLBox.clear()

        # Any valid link added means there is something to download
        if addedCount > 0:
            self.ui.DownloadBtn.setEnabled(True)

        if invalidURLs:
            QMessageBox.information(
                self,
                "Invalid Links",
                f"There were {len(invalidURLs)} invalid link(s) in your text:\n\n"
                + "\n".join(invalidURLs)
            )
        elif addedCount > 0:
            # All links were valid - switch back to the "Main" tab
            self.ui.tabWidget.setCurrentWidget(self.ui.tab)
        
                    


    def RemoveItem(self):
        if self.ui.LinkList.currentRow() != -1:
            self.ui.LinkList.takeItem(self.ui.LinkList.currentRow()).text()

    def CreateDownloadList(self):
        # Disable until AddLink() adds another valid link
        self.ui.DownloadBtn.setEnabled(False)
        DownloadList = []
        for f in range(self.ui.LinkList.count()):
            DownloadList.append(self.ui.LinkList.item(f).text())
            #print(self.ui.LinkList.item(f).text())

        if len(DownloadList) > 0:
            self.sendDownloadList.emit(DownloadList, self.ui.DestFolder.text())

    def ConfigureStatusBar(self):
        self.statusBar().addWidget(self.ui.statusETA)
        self.statusBar().addWidget(self.ui.statusDownloadSpeed)
        self.statusBar().addWidget(self.ui.statusCurrentVideo)

    def update_progress(self, eta, speed_mb, title, percentage):
        """Slot for WorkerClass.progress_signal - shows download %, ETA, speed and title."""
        self.ui.progressBar.setValue(percentage)
        self.ui.statusETA.setText(f"ETA: {eta}")
        self.ui.statusDownloadSpeed.setText(f"Speed: {speed_mb} MB/s")
        self.ui.statusCurrentVideo.setText(f"Video: {title}")

    def sendMetaData(self):
        if self.ui.LinkList.currentRow() == -1:
            return
        if self.ui.LinkList.item(self.ui.LinkList.currentRow()).text() in self.videoData:
            print("Already Exists")
            self.OutputMetaData(self.videoData[self.ui.LinkList.item(self.ui.LinkList.currentRow()).text()])
        else:
            self.sendLinkForMetaData.emit(self.ui.LinkList.item(self.ui.LinkList.currentRow()).text())

    def OutputMetaData(self,data):
        self.ui.Edit_LinkDetail.clear()
        self.ui.Edit_LinkDetail.append(f"Title:{data['title']}")
        self.ui.Edit_LinkDetail.append(f"Duration:{data['duration_minutes_seconds']}")
        self.ui.Edit_LinkDetail.append(f"Size:{data['file_size_mb']} MB")

    def GetFolder(self):
        old_path = self.ui.DestFolder.text()
        folder_path = QFileDialog.getExistingDirectory(self,"Select Folder","",QFileDialog.Option.ShowDirsOnly)
        if folder_path == None or len(folder_path) == 0:
            self.ui.DestFolder.setText(old_path)
        else:
            self.ui.DestFolder.setText(folder_path)
            self.saveSignal.emit(folder_path)



    
        
    def process_GUI_Updates(self, data_dict: dict):
        """Processes incoming dictionary data safely."""
        # Safeguard: ensure we have a valid, non-empty dictionary
        if not isinstance(data_dict, dict) or not data_dict:
            print("[-] Error: process_GUI_Updates expected a non-empty dictionary.")
            return        

        (action_type, message), = data_dict.items()
        
        match action_type:
            case "textEdit":
                #self.ui.textEdit.append(message)
                pass
            case "Download Finished":
                QMessageBox.information(self,"Download Complete", message)
            case "progressBar":
                self.ui.progressBar.setValue(message)
            case "statusBar":
                #self.ui.progressBar.setValue(message)
                self.ui.statusCurrentVideo.setText("Video: " + message)
            case "Edit_LinkDetail":
                self.ui.Edit_LinkDetail.append(message)
            case "MetaData":
                self.OutputMetaData(message)
                self.videoData[message["link"]] = message
            case "DestFolder":
                self.ui.DestFolder.setText(message)
            case "DisableAll":
                self.disableAll()
            case "RestartAll":
                self.restartAll()
            case "DownloadStatus":
                self.ui.Edit_LinkDetail.clear()
                self.ui.Edit_LinkDetail.append(f"Video File: {message[0]}\n\nDownloading video {message[1]}")
            case "DownloadLog":
                self.ui.DownloadLog.appendPlainText(message)
            case _:
                print(f"[-] Warning: Unknown action key received -> '{action_type}'")
    
    def displayAppData(self):
        QMessageBox.information(self, "App Info", "YT Downloader v 1.6")

    def displayDonateInfo(self):
        QMessageBox.information(
            self,
            "Donate",
            "Enjoying the App?\n\n"
            "Please encourage more Apps by donating below.\n\n"
            "Name : Oluwatimileyin Olade\n"
            "Sort Code : 07-12-26\n"
            "Acct # :01710508\n"
            "Bank Name : Nationwide Bank\n\n"
            "No amount is too small. Thank you"
        )

    def save_config_file(self):
        config = configparser.ConfigParser()
        
        # Define sections and key-value pairs
        config['Settings'] = {"DestPath": self.ui.DestFolder.text()}
        
        # Write the configuration to a file named 'config.ini'
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("config.ini created successfully!")

    def load_config_file(self):
        config = configparser.ConfigParser()

        if not os.path.exists(self.configFile):
            self.save_config_file()
            return

        config.read(self.configFile)
        self.ui.DestFolder.setText(config.get('Settings',"DestPath"))

    def newmessageBox(self,title,text, ismodal):
        if ismodal:
            QMessageBox.information(self,title,text)
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(text)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.show()
            

    def disableAll(self):
        self.ui.LinkInputBox.setDisabled(True)
        self.ui.LinkList.setDisabled(True)
        self.ui.getFolderBtn.setDisabled(True)
        self.ui.DestFolder.setDisabled(True)
        self.ui.AddBtn.setDisabled(True)
        self.ui.DeleteBtn.setDisabled(True)
        self.ui.DownloadBtn.setDisabled(True)
        self.ui.MultiLoadBtn.setDisabled(True)

    def restartAll(self):
        self.ui.LinkInputBox.setEnabled(True)
        self.ui.LinkList.setEnabled(True)
        self.ui.getFolderBtn.setEnabled(True)
        self.ui.DestFolder.setEnabled(True)
        self.ui.AddBtn.setEnabled(len(self.ui.LinkInputBox.text()) > 0)
        self.ui.MultiLoadBtn.setEnabled(len(self.ui.URLBox.toPlainText().strip()) > 0)
        
    
    