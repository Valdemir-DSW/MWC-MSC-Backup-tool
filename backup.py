import shutil
import os
from datetime import datetime
from logger import log_event

def create_backup(game_path, dest_folder, prefix):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"{prefix}_{timestamp}"
    zip_path = os.path.join(dest_folder, zip_name)

    try:
        log_event("BACKUP", f"Iniciando backup: {prefix}")
        shutil.make_archive(zip_path, "zip", game_path)

        # Verifica se o arquivo .zip foi criado e renomeia para .becupe
        zip_file = zip_path + ".zip"
        if os.path.exists(zip_file):
            final_path = zip_path + ".becupe"
            # Se o arquivo .becupe já existe, deleta ele primeiro
            if os.path.exists(final_path):
                os.remove(final_path)
            os.rename(zip_file, final_path)
            log_event("BACKUP", f"Backup concluído: {final_path}")
            return final_path
        else:
            # Se não encontrou o .zip, tenta retornar o caminho direto
            log_event("ERROR", f"Arquivo ZIP não encontrado para: {prefix}")
            return zip_path
    except Exception as e:
        log_event("ERROR", f"Erro ao criar backup ({prefix}): {str(e)}")
        print(f"Erro ao criar backup: {e}")
        raise
