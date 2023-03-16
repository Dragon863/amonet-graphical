from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QPlainTextEdit,
                                QVBoxLayout, QWidget, QProgressBar, QDialog, QDialogButtonBox, QLabel)
from PySide6.QtCore import QProcess
from PySide6.QtGui import QIcon, QScreen
import sys
import re
from qt_material import apply_stylesheet

progress_re = re.compile("(\d+.\d+)")

def simple_percent_parser(output):
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return float(pc_complete)

class WelcomeWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Welcome!")
        QBtn = QDialogButtonBox.Ok

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel("Welcome to AlexaPwn! Please check the <a href='https://dragon863.github.io/blog/alexa.html'>article</a> for documentation")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        dlg = WelcomeWindow(self)
        dlg.exec()

        self.p = None

        self.setWindowTitle('AlexaPwn')
        app_icon = QIcon()
        app_icon.addFile('app_icon.png')

        self.setWindowIcon(app_icon)

        self.btn = QPushButton("Start")
        self.btn2 = QPushButton("OK")
        self.btnOne = QPushButton("1")
        self.btnTwo = QPushButton("2")
        self.btnThree = QPushButton("3")
        self.btn.pressed.connect(self.start_process)
        self.btn2.pressed.connect(self.okay)
        self.btnOne.pressed.connect(self.one)
        self.btnTwo.pressed.connect(self.two)
        self.btnThree.pressed.connect(self.three)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        l = QVBoxLayout()
        l.addWidget(self.btn)
        l.addWidget(self.btn2)
        l.addWidget(self.btnOne)
        l.addWidget(self.btnTwo)
        l.addWidget(self.btnThree)
        l.addWidget(self.text)
        l.addWidget(self.progress)

        w = QWidget()
        w.setLayout(l)

        self.setCentralWidget(w)
        self.message("To begin, click start.")

    def message(self, s):
        self.text.appendPlainText(s)

    def okay(self):
        self.p.write("\n".encode())
    
    def one(self):
        self.p.write("1\n".encode())

    def two(self):
        self.p.write("2\n".encode())

    def three(self):
        self.p.write("3\n".encode())

    def start_process(self):
        if self.p is None:  # No process running.
            self.message("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            self.p.start("python3", ["-m", "amonet"])

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        # Extract progress if it is in the data.
        progress = simple_percent_parser(stderr)
        if progress:
            self.progress.setValue(progress)
        else:
            self.message(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.message(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.message(f"State changed: {state_name}")

    def process_finished(self):
        self.message("Process finished.")
        self.p = None

    def closeEvent(self,event):
        self.p.kill()


app = QApplication(sys.argv)
apply_stylesheet(app, theme='dark_red.xml')

w = MainWindow()

SrcSize = QScreen.availableGeometry(QApplication.primaryScreen())

frmX=SrcSize.width()
frmY=SrcSize.height()

w.setGeometry(0, 0, frmX, frmY)
w.show()

app.exec()