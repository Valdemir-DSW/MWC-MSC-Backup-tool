import os
from datetime import datetime

LOG_FILE = "logs.txt"

def log_event(event_type: str, message: str):
    """
    Registra um evento no arquivo de log
    event_type: "INFO", "ERROR", "CONFIG", "BACKUP", "RESTORE"
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{event_type}] {message}\n"
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message)
    except Exception as e:
        print(f"Erro ao escrever no log: {e}")

def read_log():
    """Lê todo o arquivo de log"""
    try:
        if not os.path.exists(LOG_FILE):
            return ""
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Erro ao ler log: {e}"

def clear_log():
    """Limpa o arquivo de log"""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        return True
    except Exception as e:
        print(f"Erro ao limpar log: {e}")
        return False
