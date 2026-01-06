import os

def get_amistech_path():
    return os.path.join(
        os.environ["USERPROFILE"],
        "AppData", "LocalLow", "Amistech"
    )

def get_game_paths():
    base = get_amistech_path()
    return {
        "MSC": os.path.join(base, "My Summer Car"),
        "MWC": os.path.join(base, "My Winter Car")
    }
