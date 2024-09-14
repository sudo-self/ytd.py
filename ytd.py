# ytd.py

import sys
import os
import subprocess
import platform
import pyperclip
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel, QLineEdit
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon 

logging.basicConfig(filename='app.log', level=logging.INFO)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

class DownloadThread(QThread):
    update_signal = pyqtSignal(str, str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            process = subprocess.Popen(
                ['yt-dlp', '-S', 'res,ext:mp4:m4a', '--recode', 'mp4', self.url, '-o', f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            out, err = process.communicate()
            self.update_signal.emit(out, err)
        except Exception as e:
            self.update_signal.emit('', str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ytd.py')
        self.setWindowIcon(QIcon('ytd.icns'))
        self.setFixedSize(250, 380) 

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText('Enter URL')

        self.paste_button = QPushButton('Paste clipboard', self)
        self.paste_button.clicked.connect(self.paste_from_clipboard)
        
        self.clear_button = QPushButton('Clear input', self)
        self.clear_button.clicked.connect(self.clear_input)
        
        self.download_button = QPushButton('Download video', self)
        self.download_button.clicked.connect(self.download_video)
        
        self.open_button = QPushButton('Open folder', self)
        self.open_button.clicked.connect(self.open_directory)
        
        self.install_button = QPushButton('brew install', self)
        self.install_button.clicked.connect(self.install_yt_dlp)
        
        self.status_label = QLabel('', self)

        self.footer_label = QLabel('<a href="https://x.com/ilostmyipad" style="color: white; text-decoration: none;">@iLostmyipad</a>', self)
        self.footer_label.setOpenExternalLinks(True)
        self.footer_label.setAlignment(Qt.AlignCenter)

     
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.url_input)
        main_layout.addWidget(self.download_button)
        main_layout.addWidget(self.open_button)
        main_layout.addWidget(self.paste_button)
        main_layout.addWidget(self.clear_button)
        main_layout.addWidget(self.install_button)
        main_layout.addWidget(self.status_label)
        
        footer_layout = QVBoxLayout()
        footer_layout.addWidget(self.footer_label)
        footer_widget = QWidget()
        footer_widget.setLayout(footer_layout)

        container = QWidget()
        container.setLayout(main_layout)
        
        main_layout.addStretch(1)
        main_layout.addWidget(footer_widget)

        self.setCentralWidget(container)

       
        self.setStyleSheet("""
            QMainWindow {
                background-color: black;
            }
            QLineEdit {
                background-color: transparent;
                color: white;
                border: 1px solid #b32134;
                padding: 5px;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: 1px solid #b32134;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #b32134;
            }
            QLabel {
                color: white;
            }
            QLabel a {
                color: white;
                text-decoration: none;
            }
            QLabel a:hover {
                text-decoration: underline;
            }
        """)

       
        self.setFixedSize(250, 380)

    def download_video(self):
        url = self.url_input.text()
        if url:
            self.status_label.setText(f'Started download for: {url}')
            self.thread = DownloadThread(url)
            self.thread.update_signal.connect(self.update_status)
            self.thread.start()
        else:
            self.status_label.setText('No video URL input')

    def update_status(self, out, err):
        self.status_label.setText(out + err)
        logging.info(out + err)

    def open_directory(self):
        directory = os.path.dirname(os.path.realpath(__file__))
        if platform.system() == 'Darwin':
            subprocess.Popen(['open', directory])
        elif platform.system() == 'Linux':
            subprocess.Popen(['xdg-open', directory])
        elif platform.system() == 'Windows':
            subprocess.Popen(['explorer', directory])
        self.status_label.setText('Opened directory')

    def paste_from_clipboard(self):
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                self.url_input.setText(clipboard_text)
                self.status_label.setText('Pasted clipboard text into URL input')
            else:
                self.status_label.setText('Clipboard is empty or inaccessible')
        except Exception as e:
            self.status_label.setText(f'Error: {e}')
    
    def clear_input(self):
        self.url_input.clear()
        self.status_label.setText('Cleared input field')

    def install_yt_dlp(self):
        try:
            process = subprocess.Popen(
                ['brew', 'install', 'yt-dlp'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            out, err = process.communicate()
            if process.returncode == 0:
                self.status_label.setText('yt-dlp installed successfully')
            else:
                self.status_label.setText(f'Error installing yt-dlp: {err}')
            logging.info(out + err)
        except Exception as e:
            self.status_label.setText(f'Error: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
