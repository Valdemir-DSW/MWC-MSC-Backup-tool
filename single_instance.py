"""
Módulo para prevenir múltiplas instâncias da aplicação rodando simultaneamente.
Usa lock file com arquivo mantido aberto para garantir apenas uma instância por vez.
"""
import os
import sys
import tempfile
from app_paths import get_lock_file

class SingleInstanceLock:
    """
    Gerencia lock de instância única.
    Mantém um arquivo aberto exclusivamente para garantir apenas uma instância.
    """
    
    def __init__(self):
        self.lock_file = get_lock_file()
        self.lock_acquired = False
        self.lock_handle = None
    
    def acquire(self):
        """
        Tenta adquirir o lock mantendo o arquivo aberto.
        Se conseguir, retorna True.
        Se não conseguir (outra instância está rodando), retorna False.
        """
        try:
            # Primeiro, remove lock file antigo se existir (de processo morto)
            if os.path.exists(self.lock_file):
                try:
                    # Tenta remover - se conseguir, era de um processo morto
                    os.remove(self.lock_file)
                except:
                    # Se não conseguir remover, significa que está em uso por outro processo
                    return False
            
            # Tenta abrir o arquivo em modo exclusivo e manter aberto
            # No Windows, quando um arquivo está aberto, outros processos não conseguem deletar
            try:
                self.lock_handle = open(self.lock_file, 'w')
                self.lock_handle.write(str(os.getpid()))
                self.lock_handle.flush()
                self.lock_acquired = True
                return True
            except IOError:
                return False
            
        except Exception as e:
            print(f"Erro ao adquirir lock: {e}")
            return False
    
    def release(self):
        """Libera o lock fechando e removendo o arquivo"""
        try:
            if self.lock_handle:
                self.lock_handle.close()
                self.lock_handle = None
            
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
            
            self.lock_acquired = False
        except Exception as e:
            print(f"Erro ao liberar lock: {e}")
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Outra instância da aplicação já está rodando!")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Outra instância da aplicação já está rodando!")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
