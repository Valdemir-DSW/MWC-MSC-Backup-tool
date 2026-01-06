from PyQt5.QtCore import QTimer, QTime

class AutoBackupScheduler:
    def __init__(self, callback):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_time)
        self.callback = callback
        self.target_time = None

    def set_time(self, qtime: QTime):
        self.target_time = qtime

    def start(self):
        self.timer.start(60000)

    def check_time(self):
        if self.target_time and QTime.currentTime().hour() == self.target_time.hour() \
           and QTime.currentTime().minute() == self.target_time.minute():
            self.callback()
