from __future__ import annotations

from planification import DIRECTIONS

TRAVERSABLES = ("libre", "inconnu")


class CarteMentale:
    """Ce que le robot sait de l'appartement : 'inconnu' partout au départ, sauf A, D et P."""

    def __init__(
        self, dimensions: tuple[int, int], armoire_pos, dico_pos, residents: dict
    ):
        self.hauteur, self.largeur = dimensions
        self.cases = []
        for _ in range(self.hauteur):
            self.cases.append(["inconnu"] * self.largeur)

        for colonne in range(self.largeur):
            self.marquer((0, colonne), "mur")
            self.marquer((self.hauteur - 1, colonne), "mur")
        for ligne in range(self.hauteur):
            self.marquer((ligne, 0), "mur")
            self.marquer((ligne, self.largeur - 1), "mur")

        self.marquer(tuple(armoire_pos), "armoire")
        self.marquer(tuple(dico_pos), "dictionnaire")
        for identifiant in residents:
            self.marquer(tuple(residents[identifiant]), "resident")

    def dans_grille(self, pos: tuple[int, int]) -> bool:
        return 0 <= pos[0] < self.hauteur and 0 <= pos[1] < self.largeur

    def type_case(self, pos: tuple[int, int]) -> str:
        """Type mémorisé de pos ; hors grille = 'mur'."""
        if not self.dans_grille(pos):
            return "mur"
        return self.cases[pos[0]][pos[1]]

    def marquer(self, pos: tuple[int, int], type_case: str) -> None:
        if self.dans_grille(pos):
            self.cases[pos[0]][pos[1]] = type_case

    def maj(self, position: tuple[int, int], perception: dict[str, str]) -> None:
        """Inscrit la case du robot (libre) et ses 4 voisines perçues."""
        self.marquer(position, "libre")
        for direction in perception:
            dl, dc = DIRECTIONS[direction]
            self.marquer((position[0] + dl, position[1] + dc), perception[direction])

    def est_traversable(self, pos: tuple[int, int]) -> bool:
        """Hypothèse optimiste (annexe B.5) : une case inconnue est supposée libre."""
        return self.type_case(pos) in TRAVERSABLES
