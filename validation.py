import reconfort_io as rio

def valider_dictionnaire(dictionnaire: dict) -> None:
    """
    """
    champsObligatoires = [
        "nom",
        "emotions",
        "intensites",
        "entrees"
    ]
    for champ in champsObligatoires:
        if champ not in dictionnaire:
            raise rio.ErreurFichier(f"Dictionnaire : champ '{champ}' manquant")

    if not isinstance(dictionnaire["entrees"], list):
        raise rio.ErreurFichier("Dictionnaire : 'entrees' doit être une liste")

    if not isinstance(dictionnaire["emotions"], list):
        raise rio.ErreurFichier("Dictionnaire : 'emotions' doit être une liste")

    if not isinstance(dictionnaire["intensites"], list):
        raise rio.ErreurFichier("Dictionnaire : 'intensites' doit être une liste")

    if not isinstance(dictionnaire["nom"], str):
        raise rio.ErreurFichier("Dictionnaire : 'nom' doit être une chaîne de caractères")