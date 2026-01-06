import shutil
import os
import zipfile
from logger import log_event

def restore_backup(becupe_file, target_path):
    """
    Restaura um backup .becupe para a pasta do jogo.
    
    Args:
        becupe_file: Caminho do arquivo .becupe (zip)
        target_path: Caminho da pasta do jogo onde extrair
    """
    try:
        log_event("RESTORE", f"Iniciando restauração de: {becupe_file}")
        
        # Remove a pasta existente se houver
        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        # Cria a pasta do jogo
        os.makedirs(target_path, exist_ok=True)

        # Extrai o arquivo zip diretamente na pasta do jogo
        with zipfile.ZipFile(becupe_file, 'r') as zip_ref:
            zip_ref.extractall(target_path)
        
        log_event("RESTORE", f"Restauração concluída: {target_path}")
    except Exception as e:
        log_event("ERROR", f"Erro ao restaurar backup: {str(e)}")
        raise
