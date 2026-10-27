from __future__ import annotations

import reconfort_io as rio

def valider_dictionnaire(dictionnaire: dict) -> None:
    """
    Valide le dictionnaire de mots et d'émotions
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

    if not dictionnaire["nom"].strip():
        raise rio.ErreurFichier("Dictionnaire : 'nom' ne doit pas être vide")

    formes_vues = set()
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

        if not entree["formes"]:
            raise rio.ErreurFichier("Dictionnaire : 'formes' ne doit pas être vide")

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
        for forme in entree["formes"]:
            if forme in formes_vues:
                raise rio.ErreurFichier(f"Dictionnaire : forme '{forme}' présente plusieurs fois")
            formes_vues.add(forme)

def valider_armoire(armoire: dict) -> None:
    """
    Valide le dictionnaire de l'armoire
    """
    champsObligatoires = [
        "nom",
        "emotions",
        "intensites",
        "casier_depart",
        "casiers"
    ]
    for champ in champsObligatoires:
        if champ not in armoire:
            raise rio.ErreurFichier(f"Armoire : champ '{champ}' manquant")

    if not isinstance(armoire["nom"], str):
        raise rio.ErreurFichier("Armoire : 'nom' doit être une chaîne de caractères")

    if not armoire["nom"].strip():
        raise rio.ErreurFichier("Armoire : 'nom' ne doit pas être vide")

    if not isinstance(armoire["emotions"], list):
        raise rio.ErreurFichier("Armoire : 'emotions' doit être une liste")

    if not isinstance(armoire["intensites"], list):
        raise rio.ErreurFichier("Armoire : 'intensites' doit être une liste")

    if not isinstance(armoire["casier_depart"], list):
        raise rio.ErreurFichier("Armoire : 'casier_depart' doit être une liste")

    if not isinstance(armoire["casiers"], list):
        raise rio.ErreurFichier("Armoire : 'casiers' doit être une liste")

    EMOTIONS = ["joie", "confiance", "peur", "surprise", "tristesse", "degout", "colere", "anticipation"]
    INTENSITES = ["faible", "moyenne", "forte"]

    if armoire["emotions"] != EMOTIONS:
        raise rio.ErreurFichier(f"Armoire : 'emotions' doit être {EMOTIONS}")

    if armoire["intensites"] != INTENSITES:
        raise rio.ErreurFichier(f"Armoire : 'intensites' doit être {INTENSITES}")

    if len(armoire["casier_depart"]) != 2:
        raise rio.ErreurFichier("Armoire : 'casier_depart' doit contenir exactement deux éléments")

    if not all(type(coord) is int for coord in armoire["casier_depart"]):
        raise rio.ErreurFichier("Armoire : 'casier_depart' doit contenir uniquement des entiers")

    if armoire["casier_depart"][0] > 2 or armoire["casier_depart"][0] < 0:
        raise rio.ErreurFichier("Armoire : 'casier_depart[0]' doit être compris entre 0 et 2")

    if armoire["casier_depart"][1] > 7 or armoire["casier_depart"][1] < 0:
        raise rio.ErreurFichier("Armoire : 'casier_depart[1]' doit être compris entre 0 et 7")

    casiers_vus = set()
    for casier in armoire["casiers"]:
        if not isinstance(casier, dict):
            raise rio.ErreurFichier("Armoire : chaque casier doit être un dictionnaire")

        champsCasierObligatoires = [
            "ligne",
            "colonne",
            "emotion",
            "intensite",
            "objet"
        ]

        for champ in champsCasierObligatoires:
            if champ not in casier:
                raise rio.ErreurFichier(f"Armoire : champ '{champ}' manquant dans un casier")

        if type(casier["ligne"]) is not int:
            raise rio.ErreurFichier("Armoire : 'ligne' doit être un entier dans chaque casier")

        if type(casier["colonne"]) is not int:
            raise rio.ErreurFichier("Armoire : 'colonne' doit être un entier dans chaque casier")

        if not isinstance(casier["emotion"], str):
                    raise rio.ErreurFichier("Armoire : 'emotion' doit être une chaîne de caractères dans chaque casier")
                
        if not isinstance(casier["intensite"], str):
            raise rio.ErreurFichier("Armoire : 'intensite' doit être une chaîne de caractères dans chaque casier")

        if casier["objet"] is not None and not isinstance(casier["objet"], str):
            raise rio.ErreurFichier("Armoire : 'objet' doit être une chaîne de caractères ou null")

        if casier["ligne"] > 2 or casier["ligne"] < 0:
            raise rio.ErreurFichier("Armoire : 'ligne' doit être compris entre 0 et 2 dans chaque casier")

        if casier["colonne"] > 7 or casier["colonne"] < 0:
            raise rio.ErreurFichier("Armoire : 'colonne' doit être compris entre 0 et 7 dans chaque casier")

        # emotion et intensité cohérentes avec la position du casier
        if casier["emotion"] != EMOTIONS[casier["colonne"]]:
            raise rio.ErreurFichier("Armoire : émotion incohérente avec la colonne")

        if casier["intensite"] != INTENSITES[casier["ligne"]]:
            raise rio.ErreurFichier("Armoire : intensité incohérente avec la ligne")

        # casiers en double
        position = (casier["ligne"], casier["colonne"])
        if position in casiers_vus:
            raise rio.ErreurFichier(f"Armoire : casier en double à la position {position}")
        casiers_vus.add(position)

def valider_carte(carte: dict) -> None:
    if not isinstance(carte, dict):
        raise rio.ErreurFichier("Carte : doit être un dictionnaire")

    champsObligatoires = [
        "nom",
        "dimensions",
        "legende",
        "grille",
        "depart_robot",
        "armoire",
        "dictionnaire",
        "residents"
    ]

    for champ in champsObligatoires:
        if champ not in carte:
            raise rio.ErreurFichier(f"Carte : champ '{champ}' manquant")

    if not isinstance(carte["nom"], str):
        raise rio.ErreurFichier("Carte : 'nom' doit être une chaîne de caractères")

    if not isinstance(carte["dimensions"], dict):
        raise rio.ErreurFichier("Carte : 'dimensions' doit être un dictionnaire")

    if not isinstance(carte["legende"], dict):
        raise rio.ErreurFichier("Carte : 'legende' doit être un dictionnaire")

    if not isinstance(carte["grille"], list):
        raise rio.ErreurFichier("Carte : 'grille' doit être une liste")

    if not isinstance(carte["residents"], list):
        raise rio.ErreurFichier("Carte : 'residents' doit être une liste")

    if "hauteur" not in carte["dimensions"] or "largeur" not in carte["dimensions"]:
        raise rio.ErreurFichier("Carte : 'dimensions' doit contenir 'hauteur' et 'largeur'")

    if type(carte["dimensions"]["hauteur"]) is not int or type(carte["dimensions"]["largeur"]) is not int:
        raise rio.ErreurFichier("Carte : 'hauteur' et 'largeur' doivent être des entiers")

    if carte["dimensions"]["hauteur"] <= 0 or carte["dimensions"]["largeur"] <= 0:
        raise rio.ErreurFichier("Carte : 'hauteur' et 'largeur' doivent être des entiers positifs")

    hauteur = carte["dimensions"]["hauteur"]
    largeur = carte["dimensions"]["largeur"]
    grille = carte["grille"]

    if len(grille) != hauteur:
        raise rio.ErreurFichier("Carte : le nombre de lignes dans 'grille' ne correspond pas à 'hauteur'")

    for ligne in grille:
        if not isinstance(ligne, str):
            raise rio.ErreurFichier("Carte : chaque ligne de 'grille' doit être une chaîne de caractères")

        if len(ligne) != largeur:
            raise rio.ErreurFichier("Carte : La grille n'est pas rectangulaire")

    symbolesAutorises = {"#", ".", "R", "A", "D", "P"}
    for ligne in grille:
        for symbole in ligne:
            if symbole not in symbolesAutorises:
                raise rio.ErreurFichier(f"Carte : symbole '{symbole}' non autorisé dans la grille")

    # les bordures de la grille doivent être des murs
    for i in range(hauteur):
        if grille[i][0] != "#" or grille[i][largeur - 1] != "#": # bords gauche et droit
            raise rio.ErreurFichier("Carte : les bordures de la grille doivent être des murs")

    for j in range(largeur):
        if grille[0][j] != "#" or grille[hauteur - 1][j] != "#": # bords haut et bas
            raise rio.ErreurFichier("Carte : les bordures de la grille doivent être des murs")

    def verifier_position(position: tuple[int, int], symboleAttendu: str, nom: str) -> None:
        if not isinstance(position, (list, tuple)) or len(position) != 2:
            raise rio.ErreurFichier(f"{nom} : position doit être un tuple ou une liste de deux entiers")

        if not all(type(coord) is int for coord in position):
            raise rio.ErreurFichier(f"{nom} : position doit contenir uniquement des entiers")

        ligne, colonne = position

        if ligne < 0 or ligne >= hauteur or colonne < 0 or colonne >= largeur:
            raise rio.ErreurFichier(f"{nom} : position hors limites de la grille")

        if grille[ligne][colonne] != symboleAttendu:
            raise rio.ErreurFichier(f"{nom} : position ne correspond pas au symbole attendu '{symboleAttendu}' dans la grille")

    verifier_position(carte["depart_robot"], "R", "Robot")

    if not isinstance(carte["armoire"], dict):
        raise rio.ErreurFichier("Carte : 'armoire' doit être un dictionnaire")

    if "position" not in carte["armoire"]:
        raise rio.ErreurFichier("Carte : 'armoire' doit contenir 'position'")

    verifier_position(carte["armoire"]["position"], "A", "Armoire")

    if not isinstance(carte["dictionnaire"], dict):
        raise rio.ErreurFichier("Carte : 'dictionnaire' doit être un dictionnaire")

    if "position" not in carte["dictionnaire"]:
        raise rio.ErreurFichier("Carte : 'dictionnaire' doit contenir 'position'")

    verifier_position(carte["dictionnaire"]["position"], "D", "Dictionnaire")

    ids_residents = set()
    for resident in carte["residents"]:
        if not isinstance(resident, dict):
            raise rio.ErreurFichier("Carte : chaque résident doit être un dictionnaire")

        champsResidentObligatoires = ["id", "nom", "position"]

        for champ in champsResidentObligatoires:
            if champ not in resident:
                raise rio.ErreurFichier(f"Carte : champ '{champ}' manquant dans un résident")

        if not isinstance(resident["id"], str):
            raise rio.ErreurFichier("Carte : 'id' doit être une chaîne de caractères dans chaque résident")

        if not isinstance(resident["nom"], str):
            raise rio.ErreurFichier("Carte : 'nom' doit être une chaîne de caractères dans chaque résident")

        verifier_position(resident["position"], "P", f"resident {resident['id']}")

        if resident["id"] in ids_residents:
            raise rio.ErreurFichier(f"Carte : id '{resident['id']}' présent plusieurs fois dans les résidents")
        ids_residents.add(resident["id"])    

def valider_scenario(scenario: dict, carte: dict) -> None:
    if not isinstance(scenario, dict):
        raise rio.ErreurFichier("Scénario : doit être un dictionnaire")

    champsObligatoires = [
        "nom",
        "carte",
        "armoire",
        "demandes"
    ]

    for champ in champsObligatoires:
        if champ not in scenario:
            raise rio.ErreurFichier(f"Scénario : champ '{champ}' manquant")

    if not isinstance(scenario["nom"], str):
        raise rio.ErreurFichier("Scénario : 'nom' doit être une chaîne de caractères")

    if not isinstance(scenario["carte"], str):
        raise rio.ErreurFichier("Scénario : 'carte' doit être une chaîne de caractères")

    if not isinstance(scenario["armoire"], str):
        raise rio.ErreurFichier("Scénario : 'armoire' doit être une chaîne de caractères")

    if not isinstance(scenario["demandes"], list):
        raise rio.ErreurFichier("Scénario : 'demandes' doit être une liste")

    if scenario["carte"] != carte["nom"]:
        raise rio.ErreurFichier(f"Scénario : 'carte' doit correspondre au nom de la carte '{carte['nom']}'")

    ids_residents = set(resident["id"] for resident in carte["residents"]) 
    for demande in scenario["demandes"]:
        if not isinstance(demande, dict):
            raise rio.ErreurFichier("Scénario : chaque demande doit être un dictionnaire")

        champsDemandeObligatoires = [
            "numero",
            "resident",
            "message"
        ]

        for champ in champsDemandeObligatoires:
            if champ not in demande:
                raise rio.ErreurFichier(f"Scénario : champ '{champ}' manquant dans une demande")

        if type(demande["numero"]) is not int:
            raise rio.ErreurFichier("Scénario : 'numero' doit être un entier dans chaque demande")

        if not isinstance(demande["resident"], str):
            raise rio.ErreurFichier("Scénario : 'resident' doit être une chaîne de caractères dans chaque demande")

        if not isinstance(demande["message"], str):
            raise rio.ErreurFichier("Scénario : 'message' doit être une chaîne de caractères dans chaque demande")

        if demande["resident"] not in ids_residents:
            raise rio.ErreurFichier(f"Scénario : 'resident' '{demande['resident']}' n'existe pas dans la carte")