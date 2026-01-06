import sys
import os
from PyQt5.QtWidgets import QApplication
from ui_main import MainWindow

# Se foi iniciado via startup do Windows, define uma variável de ambiente
if len(sys.argv) > 1 and 'startup' in sys.argv[1].lower():
    os.environ['BECUPE_STARTUP'] = '1'

app = QApplication(sys.argv)
window = MainWindow()
# A função check_startup_and_minimize() será chamada automaticamente
sys.exit(app.exec_())
