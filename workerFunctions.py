# workerFunctions.py
import time
import yt_dlp
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
                print("Yeah again")
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
        #self.mainWindow = main_window

    def start_loop_safely(self):
            """Prevents starting a new thread if one is already running."""
            if not self.isRunning():
                self.start()
                print("[*] Worker thread started.")
            else:
                print("[!] Worker thread is already running.")