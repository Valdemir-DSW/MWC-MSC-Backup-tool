import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from app_paths import ensure_app_dir_exists
from single_instance import SingleInstanceLock
from ui_main import MainWindow

# Garante que o diretório da aplicação existe
ensure_app_dir_exists()

# Tenta adquirir lock de instância única (mantém em escopo global)
lock = None
try:
    lock = SingleInstanceLock()
    if not lock.acquire():
        # Se não conseguir, mostra mensagem e fecha
        app = QApplication(sys.argv)
        QMessageBox.warning(None, "PERKELE", "A aplicação já está sendo executada!\n\nFeche a instância atual antes de iniciar novamente.")
        sys.exit(1)
except Exception as e:
    print(f"Erro ao verificar instância única: {e}")
    sys.exit(1)

# Se foi iniciado via startup do Windows, define uma variável de ambiente
if len(sys.argv) > 1 and 'startup' in sys.argv[1].lower():
    os.environ['BECUPE_STARTUP'] = '1'

app = QApplication(sys.argv)
window = MainWindow()
# A função check_startup_and_minimize() será chamada automaticamente
sys.exit(app.exec_())

