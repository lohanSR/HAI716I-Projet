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

def calculer_distance_roue(emotion1: str, emotion2: str, emotions: list[str]) -> int:
    """
    Calcule la distance entre deux émotions sur la roue des émotions
    """
    index1 = emotions.index(emotion1)
    index2 = emotions.index(emotion2)

    diff = abs(index1 - index2)
    return min(diff, 8 - diff)
