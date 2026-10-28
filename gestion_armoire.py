from __future__ import annotations

from logique import calculer_chemin_casier, determiner_repli, generer_casiers_candidats


class EtatArmoire:
    """
    Fouille de l'armoire, une action par tick : mémoire des casiers vus pendant la demande en cours
    Le sélecteur n'est pas stocké ici : c'est agent.casier (une seule source de vérité)
    """

    def __init__(self, emotions: list[str], intensites: list[str]):
        self.emotions = emotions
        self.intensites = intensites
        self.candidats = []
        self.indexEmotionDemandee = None
        self.indexIntensiteDemandee = None
        # casier → objet vu, ou None = vu vide ; casier absent = pas encore vu
        self.memoire = {}

    def nouvelle_fouille(self, emotionDemandee: str, intensiteDemandee: str) -> None:
        """
        Commence la fouille d'une demande : candidats triés (§6.2) et mémoire vidée
        """
        self.candidats = generer_casiers_candidats(
            emotionDemandee,
            intensiteDemandee,
            self.emotions,
            self.intensites
        )
        self.indexEmotionDemandee = self.emotions.index(emotionDemandee)
        self.indexIntensiteDemandee = self.intensites.index(intensiteDemandee)
        # §6.2 : un repli exige d'être passé devant les casiers prioritaires pendant CETTE demande
        self.memoire = {}

    def memoriser(self, casier: tuple[int, int], contenu: str | None) -> None:
        """
        Note le contenu constaté du casier sous le sélecteur
        """
        self.memoire[tuple(casier)] = contenu

    def cible(self) -> tuple[int, int] | None:
        """
        Premier candidat pas encore vu vide ; None si les 15 candidats ont été vus vides
        """
        for candidat in self.candidats:
            if candidat not in self.memoire or self.memoire[candidat] is not None:
                return candidat
        return None

    def prochaine_action(self, casier: tuple[int, int]) -> tuple[str, str]:
        """
        Action du prochain tick : ("CHERCHER", direction), ("PRENDRE", objet) ou ("ECHEC", "armoire vide")
        Le casier sous le sélecteur doit déjà être mémorisé
        """
        cible = self.cible()
        if cible is None:
            return ("ECHEC", "armoire vide")

        casier = tuple(casier)
        if cible == casier:
            return ("PRENDRE", self.memoire[cible])

        chemin = calculer_chemin_casier(casier, cible)
        return ("CHERCHER", chemin[0])

    def repli(self, casier: tuple[int, int]) -> str:
        """
        Étiquette de repli du casier choisi
        """
        ligne, colonne = casier
        return determiner_repli(
            self.indexEmotionDemandee,
            self.indexIntensiteDemandee,
            colonne,
            ligne
        )
