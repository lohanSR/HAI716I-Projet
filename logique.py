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

def calculer_sens(emotion1: str, emotion2: str, emotions: list[str]) -> int:
    """
    Calcule le sens de rotation entre deux émotions sur la roue des émotions
    """
    index1 = emotions.index(emotion1)
    index2 = emotions.index(emotion2)

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

    for emotionCandidate in emotions:
        indexEmotionCandidate = emotions.index(emotionCandidate)
        distanceEmotion = calculer_distance_roue(emotions[indexEmotion], emotionCandidate, emotions)

        if distanceEmotion > 2:
            continue

        sens = calculer_sens(emotions[indexEmotion], emotionCandidate, emotions)

        for intensiteCandidate in intensites:
            indexIntensiteCandidate = intensites.index(intensiteCandidate)
            distanceIntensite = abs(indexIntensiteCandidate - indexIntensite)

            cle = (distanceEmotion, distanceIntensite, indexIntensiteCandidate, sens)
            candidats.append((cle, (indexIntensiteCandidate, indexEmotionCandidate)))

    candidats.sort()
    return [candidat[1] for candidat in candidats] # Retourne les positions des casiers