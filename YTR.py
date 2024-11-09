import sys
import os
import subprocess
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QLineEdit, QTextEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
import pyperclip

logging.basicConfig(level=logging.INFO)


DOWNLOAD_FOLDER = os.path.expanduser("./Downloads")

def create_readme():
    """Creates a readme.txt file with the specified text"""
    readme_path = os.path.join(DOWNLOAD_FOLDER, 'readme.txt')
    
    try:
        with open(readme_path, 'w') as readme_file:
            readme_file.write("Android copy the .mp3 to the ringtones folder and reboot device. iPhone drag and drop the .m4r file in iTunes and sync device.")
        print(f"readme.txt created at: {readme_path}")
    except Exception as e:
        print(f"Failed to create readme.txt: {str(e)}")

# DownloadThread handles video downloading and ringtone creation in separate threads
class DownloadThread(QThread):
    update_signal = pyqtSignal(str)
    download_complete_signal = pyqtSignal()

    def __init__(self, url, file_type):
        super().__init__()
        self.url = url
        self.file_type = file_type

    def run(self):
        try:
            if self.file_type == 'mp4':
                output_path = os.path.join(DOWNLOAD_FOLDER, '%(title)s.mp4')
                command = ['yt-dlp', '-f', 'mp4', '-o', output_path, self.url]
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    video_filename = self.get_video_filename(output_path)
                    if video_filename:
                        self.update_signal.emit(f"Video downloaded: {video_filename}")
                        create_readme()  # Create the readme.txt after successful download
                    else:
                        self.update_signal.emit("Error: Video file not found.")
                else:
                    self.update_signal.emit(f"Error downloading video: {stderr.decode()}")
                    return

            elif self.file_type == 'android':
                video_filename = self.get_video_filename(f'{DOWNLOAD_FOLDER}/%(title)s.mp4')
                if video_filename:
                    command = ['ffmpeg', '-i', video_filename, '-t', '20', '-q:a', '0', '-map', 'a', f'{DOWNLOAD_FOLDER}/AndroidRingtone.mp3']
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = process.communicate()

                    if process.returncode == 0:
                        self.update_signal.emit("Android ringtone created successfully")
                    else:
                        self.update_signal.emit(f"Error creating Android ringtone: {stderr.decode()}")
                        return
                else:
                    self.update_signal.emit("Error: Video file not found for Android ringtone.")

            elif self.file_type == 'iphone':
                command = ['ffmpeg', '-i', f'{DOWNLOAD_FOLDER}/AndroidRingtone.mp3', '-t', '20', '-acodec', 'aac', '-b:a', '128k', '-f', 'mp4', f'{DOWNLOAD_FOLDER}/iPhoneRingtone.m4r']
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    self.update_signal.emit("iPhone ringtone created successfully")
                else:
                    self.update_signal.emit(f"Error creating iPhone ringtone: {stderr.decode()}")
                    return

        except Exception as e:
            self.update_signal.emit(f"Failed to process: {str(e)}")
        finally:
            self.download_complete_signal.emit()

    def get_video_filename(self, output_path):
        """Finds and returns the actual downloaded filename"""
        title = os.path.basename(output_path).replace('%(title)s', '').strip()
        video_filename = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp4")

        if os.path.exists(video_filename):
            return video_filename
        else:
            for file in os.listdir(DOWNLOAD_FOLDER):
                if file.endswith(".mp4"):
                    return os.path.join(DOWNLOAD_FOLDER, file)

        return None

# MainWindow handles the UI and connects user actions to the appropriate functions
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('YT Ringtones')
        self.setWindowIcon(QIcon('ytd.icns'))  # You can replace this with your own icon
        self.setFixedSize(380, 500)

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText('Enter A YouTube URL')

        self.download_button = QPushButton('Download Video', self)
        self.download_button.setStyleSheet("color: yellow;")
        self.download_button.clicked.connect(self.download_video)

        self.android_button = QPushButton('Android Ringtone', self)
        self.android_button.clicked.connect(self.android_download)
        self.android_button.setEnabled(False)

        self.iphone_button = QPushButton('iPhone Ringtone', self)
        self.iphone_button.clicked.connect(self.iphone_download)
        self.iphone_button.setEnabled(False)

        self.open_folder_button = QPushButton('Open Downloads Folder', self)
        self.open_folder_button.clicked.connect(self.open_folder)

        self.paste_button = QPushButton('Paste URL from Clipboard', self)
        self.paste_button.clicked.connect(self.paste_from_clipboard)

        self.clear_button = QPushButton('Reset', self)
        self.clear_button.clicked.connect(self.clear_input)

        self.status_text = QTextEdit(self)
        self.status_text.setReadOnly(True)

        self.footer_label = QLabel('<a href="https://cash.app/$iLostmyipod" style="color:white">it works!</a>', self)
        self.footer_label.setOpenExternalLinks(True)
        self.footer_label.setAlignment(Qt.AlignCenter)

        self.btc_label = QLabel('<span style="color:yellow; font-size:10px;">BTC: 32WfTVZTzoJXSTdgfLer1Ad3SMVvjokkbX</span>', self)
        self.btc_label.setAlignment(Qt.AlignCenter)

        self.eth_label = QLabel('<span style="color:lightgreen; font-size:10px;">ETH: 0x47aCF0718770f3E1a57e4cCEA7609aEd95E220b5</span>', self)
        self.eth_label.setAlignment(Qt.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.url_input)
        main_layout.addWidget(self.download_button)
        main_layout.addWidget(self.android_button)
        main_layout.addWidget(self.iphone_button)
        main_layout.addWidget(self.open_folder_button)
        main_layout.addWidget(self.paste_button)
        main_layout.addWidget(self.clear_button)
        main_layout.addWidget(self.status_text)

        footer_layout = QVBoxLayout()
        footer_layout.addWidget(self.footer_label)
        footer_layout.addWidget(self.btc_label)
        footer_layout.addWidget(self.eth_label)

        footer_widget = QWidget()
        footer_widget.setLayout(footer_layout)

        container = QWidget()
        container.setLayout(main_layout)

        main_layout.addStretch(1)
        main_layout.addWidget(footer_widget)

        self.setCentralWidget(container)

    def download_video(self):
        url = self.url_input.text()
        if url:
            self.status_text.append(f"Started downloading video for: {url}")
            self.thread = DownloadThread(url, 'mp4')
            self.thread.update_signal.connect(self.update_status)
            self.thread.download_complete_signal.connect(self.enable_buttons)
            self.thread.start()
        else:
            self.status_text.append('No video URL input')

    def android_download(self):
        self.start_conversion('android', "Creating Android Ringtone")

    def iphone_download(self):
        self.start_conversion('iphone', "Creating iPhone ringtone")

    def start_conversion(self, file_type, message):
        url = self.url_input.text()
        if url:
            self.status_text.append(message)
            self.thread = DownloadThread(url, file_type)
            self.thread.update_signal.connect(self.update_status)
            self.thread.download_complete_signal.connect(self.enable_buttons)
            self.thread.start()
        else:
            self.status_text.append('No video URL input')

    def update_status(self, message):
        self.status_text.append(message)
        logging.info(message)

    def enable_buttons(self):
        self.android_button.setEnabled(True)
        self.iphone_button.setEnabled(True)

    def open_folder(self):
        try:
            if sys.platform == 'win32':
                os.startfile(DOWNLOAD_FOLDER)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', DOWNLOAD_FOLDER])
            else:
                subprocess.Popen(['xdg-open', DOWNLOAD_FOLDER])
        except Exception as e:
            self.status_text.append(f"Failed to open folder: {str(e)}")

    def paste_from_clipboard(self):
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                self.url_input.setText(clipboard_text)
                self.status_text.append('Added URL from clipboard')
            else:
                self.status_text.append('Clipboard is empty or inaccessible')
        except Exception as e:
            self.status_text.append(f'Error: {e}')
    
    def clear_input(self):
        self.url_input.clear()
        self.status_text.append('Cleared input field')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())





