"""
Módulo para gerenciar todos os paths da aplicação de forma absoluta.
Isso garante que funcione corretamente mesmo quando iniciado do Windows.
"""
import os
import sys

# Diretório onde a aplicação está instalada
if getattr(sys, 'frozen', False):
    # Se foi congelada com cx_Freeze
    APP_DIR = os.path.dirname(sys.executable)
else:
    # Se é desenvolvimento
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Arquivos de configuração e logs no mesmo diretório da aplicação
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
LOG_FILE = os.path.join(APP_DIR, "logs.txt")
LINKS_FILE = os.path.join(APP_DIR, "links.txt")

# Arquivo de lock para evitar múltiplas instâncias
LOCK_FILE = os.path.join(APP_DIR, ".becupe_lock")

def ensure_app_dir_exists():
    """Garante que o diretório da aplicação existe"""
    os.makedirs(APP_DIR, exist_ok=True)

def get_app_dir():
    """Retorna o diretório da aplicação"""
    return APP_DIR

def get_config_file():
    """Retorna o caminho absoluto do arquivo de config"""
    return CONFIG_FILE

def get_log_file():
    """Retorna o caminho absoluto do arquivo de log"""
    return LOG_FILE

def get_links_file():
    """Retorna o caminho absoluto do arquivo de links"""
    return LINKS_FILE

def get_lock_file():
    """Retorna o caminho absoluto do arquivo de lock para instância única"""
    return LOCK_FILE
