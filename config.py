import json
import os
import winreg
from logger import log_event
from app_paths import get_config_file

CONFIG_FILE = get_config_file()

def load_config():
    try:
        if not os.path.exists(CONFIG_FILE):
            log_event("CONFIG", "Config não encontrado, usando padrão")
            return {}
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            log_event("CONFIG", f"Configurações carregadas: pasta={cfg.get('folder', 'N/A')}, paused={cfg.get('paused', True)}")
            return cfg
    except Exception as e:
        log_event("ERROR", f"Erro ao carregar config: {str(e)}")
        return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        log_event("CONFIG", f"Configurações salvas: backup_msc_open={data.get('msc_open')}, backup_mwc_open={data.get('mwc_open')}, paused={data.get('paused')}")
    except Exception as e:
        log_event("ERROR", f"Erro ao salvar config: {str(e)}")
        raise

def has_shown_disclaimer():
    """Verifica se os termos foram lidos e aceitos"""
    try:
        cfg = load_config()
        result = cfg.get("termos_lidos_e_aceitos", False)
        return result
    except:
        return False

def mark_disclaimer_shown():
    """Marca os termos como lidos e aceitos - SALVA IMEDIATAMENTE"""
    try:
        cfg = load_config()
        cfg["termos_lidos_e_aceitos"] = True
        save_config(cfg)
        return True
    except Exception as e:
        print(f"Erro ao marcar termos como aceitos: {e}")
        return False

def is_startup_enabled():
    """Verifica se a app está registrada para iniciar com Windows"""
    cfg = load_config()
    return cfg.get("startup_enabled", False)

def enable_startup():
    """Registra a app para iniciar com Windows"""
    try:
        from app_paths import get_app_dir
        app_dir = get_app_dir()
        app_path = os.path.join(app_dir, "main.py")
        python_exe = os.sys.executable
        startup_cmd = f'"{python_exe}" "{app_path}"'
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "BECUPE", 0, winreg.REG_SZ, startup_cmd)
        winreg.CloseKey(key)
        
        cfg = load_config()
        cfg["startup_enabled"] = True
        save_config(cfg)
        return True
    except:
        return False

def disable_startup():
    """Remove a app do startup do Windows"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "BECUPE")
        winreg.CloseKey(key)
        
        cfg = load_config()
        cfg["startup_enabled"] = False
        save_config(cfg)
        return True
    except:
        return False
