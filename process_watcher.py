import psutil
from PyQt5.QtCore import QTimer


class GameProcessWatcher:
    def __init__(self, on_open, on_close):
        self.on_open = on_open
        self.on_close = on_close

        self.states = {
            "MSC": False,
            "MWC": False
        }

        self.process_names = {
            "MSC": "mysummercar.exe",
            "MWC": "mywintercar.exe"
        }

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_processes)

    def start(self):
        self.timer.start(2000)

    def check_processes(self):
        running = set()
        for proc in psutil.process_iter(attrs=["name"]):
            try:
                running.add(proc.info["name"].lower())
            except Exception:
                pass

        for game, exe in self.process_names.items():
            is_running = exe in running

            if is_running and not self.states[game]:
                self.states[game] = True
                self.on_open(game)

            elif not is_running and self.states[game]:
                self.states[game] = False
                self.on_close(game)
