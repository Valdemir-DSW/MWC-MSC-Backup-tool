import os
import webbrowser

LINKS_FILE = "links.txt"

def load_links():
    """Carrega os links do arquivo links.txt"""
    try:
        if not os.path.exists(LINKS_FILE):
            return {"hub": "", "discord": ""}
        
        links = {}
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    links[key.strip()] = value.strip()
        return links
    except Exception as e:
        print(f"Erro ao carregar links: {e}")
        return {"hub": "", "discord": ""}

def open_link(link_type):
    """Abre um link no navegador"""
    try:
        from logger import log_event
        links = load_links()
        url = links.get(link_type, "")
        
        if url:
            log_event("INFO", f"Abrindo link: {link_type} - {url}")
            webbrowser.open(url)
        else:
            log_event("ERROR", f"Link {link_type} não encontrado")
            print(f"Link {link_type} não encontrado")
    except Exception as e:
        print(f"Erro ao abrir link: {e}")
