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

def calculer_distance_roue(index1: int, index2: int) -> int:
    """
    Calcule la distance entre deux émotions sur la roue des émotions
    """
    diff = abs(index1 - index2)
    return min(diff, 8 - diff)

def calculer_sens(index1: int, index2: int) -> int:
    """
    Calcule le sens de rotation entre deux émotions sur la roue des émotions
    """
    if index1 == index2:
        return 0

    distance_horaire = (index2 - index1) % 8 
    distance_antihoraire = (index1 - index2) % 8

    if distance_horaire < distance_antihoraire:
        return 0 # sens horaire
    else:
        return 1 # sens antihoraire

def generer_casiers_candidats(emotionDemandee: str, intensiteDemandee: str, emotions: list[str], intensites: list[str]) -> list[tuple[int, int]]:
    """
    Génère les casiers candidats pour une émotion et une intensité données
    Triés dans cet ordre : distance émotion, distance intensité, intensité, sens
    """
    indexEmotion = emotions.index(emotionDemandee)
    indexIntensite = intensites.index(intensiteDemandee)

    candidats = []

    for indexEmotionCandidate, _ in enumerate(emotions):
        distanceEmotion = calculer_distance_roue(indexEmotion, indexEmotionCandidate)

        if distanceEmotion > 2:
            continue

        sens = calculer_sens(indexEmotion, indexEmotionCandidate)

        for indexIntensiteCandidate, _ in enumerate(intensites):
            distanceIntensite = abs(indexIntensiteCandidate - indexIntensite)

            cle = (distanceEmotion, distanceIntensite, indexIntensiteCandidate, sens)
            candidats.append((cle, (indexIntensiteCandidate, indexEmotionCandidate)))

    candidats.sort()
    return [candidat[1] for candidat in candidats] # Retourne les positions des casiers

def determiner_repli(indexEmotionDemandee: int, indexIntensiteDemandee: int, indexEmotionTrouvee: int, indexIntensiteTrouvee: int) -> str:
    """
    Détermine le type de repli entre deux émotions
    """
    distanceEmotion = calculer_distance_roue(indexEmotionDemandee, indexEmotionTrouvee)

    if distanceEmotion == 0:
        if indexIntensiteDemandee == indexIntensiteTrouvee:
            return "aucun"
        else:
            return "intensite"

    if distanceEmotion == 1:
        return "voisine_1"

    if distanceEmotion == 2:
        return "voisine_2"

    raise ValueError("Emotion trouvée trop éloignée pour être un repli valide")

def calculer_chemin_casier(depart: tuple[int, int], arrivee: tuple[int, int]) -> list[str]:
    """
    Calcule le chemin pour aller d'un casier à un autre
    """
    ligneDepart, colonneDepart = depart
    ligneArrivee, colonneArrivee = arrivee

    mouvements = []

    while ligneDepart < ligneArrivee:
        mouvements.append("S")
        ligneDepart += 1

    while ligneDepart > ligneArrivee:
        mouvements.append("N")
        ligneDepart -= 1

    distanceEst = (colonneArrivee - colonneDepart) % 8
    distanceOuest = (colonneDepart - colonneArrivee) % 8

    if distanceEst <= distanceOuest:
        for _ in range(distanceEst):
            mouvements.append("E")
    else:
        for _ in range(distanceOuest):
            mouvements.append("O")

    return mouvements