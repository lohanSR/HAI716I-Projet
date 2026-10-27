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

    EMOTIONS = ["joie", "confiance", "peur", "surprise", "tristesse", "degout", "colere", "anticipation"]
    INTENSITES = ["faible", "moyenne", "forte"]

    if dictionnaire["emotions"] != EMOTIONS:
        raise rio.ErreurFichier(f"Dictionnaire : 'emotions' doit être {EMOTIONS}")

    if dictionnaire["intensites"] != INTENSITES:
        raise rio.ErreurFichier(f"Dictionnaire : 'intensites' doit être {INTENSITES}")

    for entree in dictionnaire["entrees"]:
        if not isinstance(entree, dict):
            raise rio.ErreurFichier("Dictionnaire : chaque entrée doit être un dictionnaire")

        champsEntreeObligatoires = [
            "formes",
            "emotion",
            "intensite"
        ]

        for champ in champsEntreeObligatoires:
            if champ not in entree:
                raise rio.ErreurFichier(f"Dictionnaire : champ '{champ}' manquant dans une entrée")

        if not isinstance(entree["formes"], list):
            raise rio.ErreurFichier("Dictionnaire : 'formes' doit être une liste dans chaque entrée")

        if not isinstance(entree["emotion"], str):
            raise rio.ErreurFichier("Dictionnaire : 'emotion' doit être une chaîne de caractères dans chaque entrée")

        if not isinstance(entree["intensite"], str):
            raise rio.ErreurFichier("Dictionnaire : 'intensite' doit être une chaîne de caractères dans chaque entrée")

        for forme in entree["formes"]:
            if not isinstance(forme, str):
                raise rio.ErreurFichier("Dictionnaire : chaque forme doit être une chaîne de caractères dans chaque entrée")

            if forme.strip() == "":
                raise rio.ErreurFichier("Dictionnaire : chaque forme ne doit pas être vide dans chaque entrée")

            if not forme.islower():
                raise rio.ErreurFichier("Dictionnaire : chaque forme doit être en minuscules dans chaque entrée")

            if not forme.isalpha():
                raise rio.ErreurFichier("Dictionnaire : chaque forme doit être composée d'un seul mot dans chaque entrée")

            if not forme.isascii():
                raise rio.ErreurFichier("Dictionnaire : chaque forme doit être sans accents dans chaque entrée")

        if entree["emotion"] not in EMOTIONS:
            raise rio.ErreurFichier(f"Dictionnaire : 'emotion' doit être l'une des émotions {EMOTIONS} dans chaque entrée")

        if entree["intensite"] not in INTENSITES:
            raise rio.ErreurFichier(f"Dictionnaire : 'intensite' doit être l'une des intensités {INTENSITES} dans chaque entrée")

        # Mots en double
        formes_vues = set()
        for forme in entree["formes"]:
            if forme in formes_vues:
                raise rio.ErreurFichier(f"Dictionnaire : forme '{forme}' en double dans une entrée")
            formes_vues.add(forme)
