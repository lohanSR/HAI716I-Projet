from logique import calculer_chemin_casier

class EtatArmoire:
    """
    Représente l'état de l'armoire
    """
    
    def __init__(self, casierDepart):
        self.positionSelecteur = tuple(casierDepart)
        self.memoire = {}

    def appliquer_mouvement_casier(self, direction: str) -> tuple[int, int]:
        """
        Applique un mouvement à une position de casier
        """
        ligne, colonne = self.positionSelecteur

        if direction == "N":
            ligne -= 1
        elif direction == "S":
            ligne += 1
        elif direction == "E":
            colonne = (colonne + 1) % 8
        elif direction == "O":
            colonne = (colonne - 1) % 8
        else:
            raise ValueError(f"Direction inconnue : {direction}")

        if ligne < 0 or ligne > 2:
            raise ValueError("Déplacement vertical hors de l'armoire")

        return (ligne, colonne)

    def deplacer_selecteur(self, cible: tuple[int, int], observer_casier) -> list[dict]:
        """
        Déplace le sélecteur jusqu'au casier cible et mémorise le contenu des nouveaux casiers rencontrés
        Retourne les étapes du déplacement avec la direction, le casier courant et son contenu avant chaque action.
        """
        chemin = calculer_chemin_casier(self.positionSelecteur, cible)
        etapes = []

        for direction in chemin:
            casierAvant = self.positionSelecteur

            if casierAvant not in self.memoire:
                self.memoire[casierAvant] = observer_casier(casierAvant)

            contenuAvant = self.memoire[casierAvant]

            etapes.append({
                "direction": direction,
                "casier": casierAvant,
                "contenu": contenuAvant
            })

            self.positionSelecteur = self.appliquer_mouvement_casier(direction)

        if self.positionSelecteur not in self.memoire:
            contenu = observer_casier(self.positionSelecteur)
            self.memoire[self.positionSelecteur] = contenu

        return etapes