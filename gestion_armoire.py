from logique import calculer_chemin_casier

class EtatArmoire:
    """
    Représente l'état de l'armoire
    """
    
    def __init__(self, casierDepart: tuple[int, int]):
        self.positionSelecteur = casierDepart
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

        return (ligne, colonne)

    def deplacer_selecteur(self, cible: tuple[int, int], observer_casier) -> list[str]:
        """
        Déplace le sélecteur jusqu'au casier cible et mémorise le contenu des nouveaux casiers rencontrés
        Retourne la liste des directions effectuées
        """
        if self.positionSelecteur not in self.memoire:
            contenu = observer_casier(self.positionSelecteur)
            self.memoire[self.positionSelecteur] = contenu

        chemin = calculer_chemin_casier(self.positionSelecteur, cible)

        for direction in chemin:
            self.positionSelecteur = self.appliquer_mouvement_casier(direction)

            if self.positionSelecteur not in self.memoire:
                contenu = observer_casier(self.positionSelecteur)
                self.memoire[self.positionSelecteur] = contenu

        return chemin
        

etatArmoire = EtatArmoire((0, 0))  # Initialisation de l'état de l'armoire avec le casier de départ (0, 0)
assert etatArmoire.appliquer_mouvement_casier("S") == (1, 0)