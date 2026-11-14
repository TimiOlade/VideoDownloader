# workerFunctions.py
import re
import yt_dlp
import json
import os
import sys
import requests
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, QEventLoop, QObject





class GlobalSignals(QObject):
    newMessageBox = pyqtSignal(str, str, bool)
    downloadBoxUpdate = pyqtSignal(str)
    downloadLogUpdate = pyqtSignal(str)

    def __init__(self, parent=None):
            super().__init__(parent)

globsignalbus = GlobalSignals()
class YdlLogger:
    """Custom logger passed to yt-dlp via the 'logger' option.
    yt-dlp requires debug(), warning() and error(); update these later
    (e.g. to write to a file or emit a signal to the GUI)."""

    def debug(self, msg):
        # yt-dlp sends both debug and regular info messages here.
        # Info messages are the ones that don't start with '[debug] '.
        # TODO: handle/route these messages
        if "[Merger] Merging formats into" in msg:
            globsignalbus.newMessageBox.emit("Merging","Merging video and audio into file \nPlease do not close the app. ",False)
            globsignalbus.downloadBoxUpdate.emit("Merging Video and Audio")
            print("Merging now...")
        elif "mp4 has already been downloaded" in msg:
            vidtext = msg.replace("[download] ","")
            vidtext = vidtext.replace(".mp4 has already been downloaded", " already exists")
            globsignalbus.newMessageBox.emit("Video already exists",vidtext,True)
            globsignalbus.downloadBoxUpdate.emit(vidtext)
        else:
            print(msg)

        if "[download]" not in msg and "ETA" not in msg:
            globsignalbus.downloadLogUpdate.emit("Debug: " + msg)

    def info(self, msg):
        # TODO: handle info messages
        globsignalbus.downloadLogUpdate.emit("Info: " + msg)
        pass

    def warning(self, msg):
        # TODO: handle warnings
        print("[yt-dlp WARNING]", msg)
        globsignalbus.downloadLogUpdate.emit("Warning: " + msg)

    def error(self, msg):
        # TODO: handle errors
        print("[yt-dlp ERROR]", msg)
        if "[download] Got error: [SSL: RECORD_LAYER_FAILURE] record layer failure (_ssl.c:3033)" in msg:
           globsignalbus.newMessageBox.emit("Download failed","Download failed due to some internet issue.\n Retrying the download usually solves it and kee",True) 
        globsignalbus.downloadLogUpdate.emit("Error: " + msg)


class WorkerClass(QThread):
    # Custom signal that emits a status dict to the GUI thread
    updateGUI = pyqtSignal(dict)
    progress_signal = pyqtSignal(str, str, str, int)
    destFolderNeeded = pyqtSignal()
    messageBox = pyqtSignal(str, str, bool)
    vidfolder = "/DownloadedVids"
    downloads = Path.home() / "Downloads"
    fulldownloadpath = ""
    
    configFile = "config.json"
    VERSION = "2.1 (2026-11)"
    gURLList = []
    ydl_opts = {}
    gPath = ""
    vidnumber = 0
    vidlistlength = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        globsignalbus.newMessageBox.connect(self.messageBox)
        globsignalbus.downloadBoxUpdate.connect(self.updateDownloadBox)
        globsignalbus.downloadLogUpdate.connect(self.updateDownloadLog)

        if not self.downloads.exists():
            raise FileNotFoundError(f"Downloads folder not found: {self.downloads}")
        else:
            self.fulldownloadpath = Path(str(self.downloads) + self.vidfolder)
            print(self.fulldownloadpath)
            self.fulldownloadpath.mkdir(parents=True, exist_ok=True)

    def run(self):
        """Standard QThread entry point."""
        #temporary fix  with a direct path for now  D:\YTDownloader
        
        self.dodownload(self.gPath)

    def dodownload(self,pathtodownload):
        print("Download Path: ",pathtodownload)
        self.updateGUI.emit({"DisableAll": ""})

        # set the ydl options below
        ydl_opts = {'merge_output_format': 'mp4', #the video output we want
                    'outtmpl': os.path.join(pathtodownload, '%(title)s.%(ext)s'),  #the download path
                    'nocolors': True,
                    'ffmpeg_location': self.get_ffmpeg_path(), #the location of the ffmpeg binary it needs to merge the video
                    'progress_hooks': [self.my_progress_hook], #real-time download progress callback
                    'logger': YdlLogger(), #custom logger for yt-dlp output
                    }

        self.vidlistlength = len(self.gURLList)
        """Simulates a download loop updating every 2 seconds."""
        for link in self.gURLList:
            print(link)
            self.updateGUI.emit({"statusBar": link}) 
            self.vidnumber += 1
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([link])
            
        self.messageBox.emit("Download Complete",f"{self.vidlistlength} video(s) downloaded", True)
        self.updateGUI.emit({"RestartAll" : ""})

    def ReceiveDownloadPath(self, path):
            
        if not isinstance(path, str) or not path:
            print("[-] Error: process_GUI_Updates expected a non-empty dictionary.")
            return 

        self.gPath = path

    def ReceiveDownloadList(self, URLList, downloadpath):
        
        if not isinstance(URLList, list) or not URLList:
            print("[-] Error: process_GUI_Updates expected a non-empty dictionary.")
            return 

        self.gPath = downloadpath
        self.gURLList = URLList
        self.start()

    def updateDownloadBox(self,text):
        self.updateGUI.emit({"Edit_LinkDetail":text})

    def updateDownloadLog(self,text):
            self.updateGUI.emit({"DownloadLog":text})



    @staticmethod
    def clean_ansi_codes(text):
        # Regex pattern to match all terminal ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def my_progress_hook(self,status):
        """This callback function receives real-time updates from yt-dlp."""
        
        if status["status"] == "downloading":
            # 1. Extract raw data safely using .get()
            filename = status.get("filename", "Unknown file")

            # Total bytes can sometimes be in 'total_bytes' or 'total_bytes_estimate'
            total = status.get("total_bytes") or status.get("total_bytes_estimate", 0)
            downloaded = status.get("downloaded_bytes", 0)

            # Calculate a clean percentage
            percentage = int((downloaded / total) * 100) if total > 0 else 0

            if percentage > 95:
                percentage = 95 # This is to make sure the progress bar never goes past 95

            # ETA: yt-dlp gives raw seconds (or None) - format as M:SS
            eta_seconds = status.get("eta")
            eta = f"{int(eta_seconds) // 60}:{int(eta_seconds) % 60:02d}" if eta_seconds is not None else "N/A"

            # Speed: bytes per second (can be None) - format as MB/s string
            speed = status.get("speed") or 0
            speed_mb = f"{speed / (1024 * 1024):.1f}"

            video_title = status.get("info_dict", {}).get("title", "Unknown Title")

            # Safely emit the signal to the main window thread
            self.progress_signal.emit(eta, speed_mb, video_title, percentage)
            self.updateGUI.emit({"DownloadStatus":[video_title,f"{self.vidnumber} of {self.vidlistlength}"]})

    def peekMetaData(self, url):
        #self.updateGUI.emit({"MetaData": url})

        # Empty options dictionary
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # download=False fetches metadata without downloading the file
                info = ydl.extract_info(url, download=False)
                
                # 1. Get basic metadata safely
                title = info.get('title', 'Unknown Title')
                duration_seconds = info.get('duration', 0)
                
                # 2. Get File Size (Handles single file or merged streams)
                total_bytes = 0
                
                # Option A: If yt-dlp has already decided on the specific formats to merge
                requested_formats = info.get('requested_formats')
                if requested_formats:
                    for f in requested_formats:
                        # Fallback chain for different file size estimates
                        total_bytes += f.get('filesize') or f.get('filesize_approx') or 0
                
                # Option B: Fallback if it is a single stream/legacy site
                if total_bytes == 0:
                    total_bytes = info.get('filesize') or info.get('filesize_approx') or 0
                    
                # Option C: If still 0, look at the default 'best' format item directly
                if total_bytes == 0 and info.get('formats'):
                    # Grab the highest quality format metadata block as an estimate
                    best_format = info['formats'][-1]
                    total_bytes = best_format.get('filesize') or best_format.get('filesize_approx') or 0

                # Convert bytes to human-readable Megabytes
                size_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0

                time = divmod(duration_seconds,60)
                
        

                self.updateGUI.emit({"MetaData": {"title": str(title),"duration_seconds": str(duration_seconds),"file_size_mb": str(round(size_mb, 2)),"duration_minutes_seconds": f"{time[0]}:{time[1]:02d}","link": url}})

                return {
                    "title": str(title),
                    "duration_seconds": str(duration_seconds),
                    "file_size_mb": str(round(size_mb, 2)),
                    "duration_minutes_seconds": f"{time[0]}:{time[1]}"
                }
                
            except Exception as e:
                return {"error": f"Failed to fetch metadata: {str(e)}"}

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

    def save_config_file(self, pathtosave):
        save_dict = {"DestPath": pathtosave}
        with open(self.configFile, "w") as file:
            json.dump(save_dict , file, indent=4)

    def load_config_file(self):
        if not os.path.exists(self.configFile):
            print(str(self.fulldownloadpath) + "Hello")
            save_dict = {"DestPath": str(self.fulldownloadpath)}
            with open(self.configFile, "w") as file:
                json.dump(save_dict , file, indent=4)

            serverURL = "https://timiolade.pythonanywhere.com/visit"
            try:
                # Just send the signal—we don't care what the server says back!
                requests.get(serverURL, params={"Version":self.VERSION}, timeout=3,verify=False)
            except requests.RequestException:
                print("Server request failed")
                pass  # If the user is offline, it fails silently in the background


        with open(self.configFile, "r") as file:
            my_dict = json.load(file)

        self.updateGUI.emit({"DestFolder": my_dict["DestPath"]})

    @staticmethod
    def get_ffmpeg_path():
        """Returns the correct platform-specific path to the bundled ffmpeg binary."""
        #Note that ensure you have the bin and win folder holding a predowloaded ffmeg binary

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        
        if sys.platform.startswith("win"):
            return os.path.join(base_path, "bin", "windows", "ffmpeg.exe")
        else:
            return os.path.join(base_path, "bin", "linux", "ffmpeg")

        