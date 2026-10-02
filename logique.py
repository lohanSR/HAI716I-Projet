import reconfort_io as rio

def trouver_emotion(message: str, dictionnaire: dict) -> tuple[str, str] | None:
    """
    Permet de trouver la première émotion correspondante pour un message
    """
    mots = rio.normaliser(message)

    for mot in mots:
        for entree in dictionnaire["entrees"]:
            if mot in entree["formes"]:
                return entree["emotion"], entree["intensite"]

    return None