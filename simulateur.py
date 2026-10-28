from __future__ import annotations

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}

SYMBOLES = {
    "#": "mur",
    ".": "libre",
    "R": "libre",
    "A": "armoire",
    "D": "dictionnaire",
    "P": "resident",
}


class ActionIllegale(Exception):
    """Action refusée par le simulateur (§3.4) ; l'état du monde n'a pas changé."""


class Simulateur:
    """La vérité terrain : vraie grille, vrais casiers, position réelle du robot, sélecteur, objet porté."""

    def __init__(self, carte: dict, armoire: dict):
        self.grille = carte["grille"]
        self.hauteur = len(self.grille)
        self.largeur = len(self.grille[0])

        self.position = tuple(carte["depart_robot"])
        self.pos_armoire = tuple(carte["armoire"]["position"])
        self.pos_dictionnaire = tuple(carte["dictionnaire"]["position"])

        self.residents = {}
        for resident in carte["residents"]:
            self.residents[resident["id"]] = tuple(resident["position"])

        self.nb_lignes_armoire = len(armoire["intensites"])
        self.nb_colonnes_armoire = len(armoire["emotions"])

        self.objets = {}
        for casier in armoire["casiers"]:
            self.objets[(casier["ligne"], casier["colonne"])] = casier["objet"]

        self.selecteur = tuple(armoire["casier_depart"])
        self.objet_porte = None

    def type_case(self, pos: tuple[int, int]) -> str:
        """Type réel de la case ; hors grille = 'mur', départ R = 'libre'."""
        ligne, colonne = pos
        if not (0 <= ligne < self.hauteur and 0 <= colonne < self.largeur):
            return "mur"
        return SYMBOLES[self.grille[ligne][colonne]]

    def voisine(self, pos: tuple[int, int], direction: str) -> tuple[int, int]:
        """La case voisine de pos dans la direction N, S, E ou O."""
        dl, dc = DIRECTIONS[direction]
        return (pos[0] + dl, pos[1] + dc)

    def percevoir(self) -> dict[str, str]:
        """§3.2 : le type des 4 cases voisines du robot, et rien d'autre."""
        perception = {}
        for direction in DIRECTIONS:
            perception[direction] = self.type_case(self.voisine(self.position, direction))
        return perception

    def adjacent_a(self, pos_cible: tuple[int, int]) -> bool:
        """Vrai si le robot est sur une case orthogonalement voisine de pos_cible."""
        ligne, colonne = self.position
        return abs(ligne - pos_cible[0]) + abs(colonne - pos_cible[1]) == 1

    def contenu_casier(self) -> str | None:
        """§3.3 : l'objet du casier sous le sélecteur, seulement devant l'armoire ; sinon None."""
        if not self.adjacent_a(self.pos_armoire):
            return None
        return self.objets.get(self.selecteur)

    def executer(
        self, action: str, argument: str | None = None, resident: str | None = None
    ) -> None:
        """Exécute une action ; lève ActionIllegale si §3.4 l'interdit. resident = destinataire de DONNER."""
        if action == "AVANCER":
            self.avancer(argument)
        elif action == "CONSULTER":
            self.consulter()
        elif action == "CHERCHER":
            self.chercher(argument)
        elif action == "PRENDRE":
            self.prendre(argument)
        elif action == "DONNER":
            self.donner(argument, resident)
        elif action != "ATTENDRE":
            raise ActionIllegale(f"action inconnue : {action}")

    def avancer(self, direction: str | None) -> None:
        """AVANCER : seulement vers une case libre."""
        if direction not in DIRECTIONS:
            raise ActionIllegale(f"AVANCER : direction invalide {direction}")

        cible = self.voisine(self.position, direction)
        if self.type_case(cible) != "libre":
            raise ActionIllegale(f"AVANCER : la case {cible} n'est pas libre")

        self.position = cible

    def consulter(self) -> None:
        """CONSULTER : seulement à côté du dictionnaire."""
        if not self.adjacent_a(self.pos_dictionnaire):
            raise ActionIllegale("CONSULTER : le robot n'est pas à côté du dictionnaire")

    def chercher(self, direction: str | None) -> None:
        """CHERCHER : déplace le sélecteur ; les colonnes bouclent, pas les lignes."""
        if direction not in DIRECTIONS:
            raise ActionIllegale(f"CHERCHER : direction invalide {direction}")
        if not self.adjacent_a(self.pos_armoire):
            raise ActionIllegale("CHERCHER : le robot n'est pas à côté de l'armoire")

        ligne, colonne = self.selecteur
        dl, dc = DIRECTIONS[direction]
        ligne += dl
        if not 0 <= ligne < self.nb_lignes_armoire:
            raise ActionIllegale("CHERCHER : le sélecteur sortirait de l'armoire")

        self.selecteur = (ligne, (colonne + dc) % self.nb_colonnes_armoire)

    def prendre(self, objet: str | None) -> None:
        """PRENDRE : casier garni, mains vides, et objet = vrai contenu (stock infini en P1)."""
        if not self.adjacent_a(self.pos_armoire):
            raise ActionIllegale("PRENDRE : le robot n'est pas à côté de l'armoire")

        contenu = self.objets.get(self.selecteur)
        if contenu is None:
            raise ActionIllegale(f"PRENDRE : le casier {self.selecteur} est vide")
        if self.objet_porte is not None:
            raise ActionIllegale(f"PRENDRE : le robot transporte déjà {self.objet_porte}")
        if objet != contenu:
            raise ActionIllegale(f"PRENDRE : le casier contient {contenu}, pas {objet}")

        self.objet_porte = contenu

    def donner(self, objet: str | None, resident: str | None) -> None:
        """DONNER : à côté du bon résident, avec l'objet porté."""
        if resident not in self.residents:
            raise ActionIllegale(f"DONNER : résident inconnu {resident}")
        if not self.adjacent_a(self.residents[resident]):
            raise ActionIllegale(f"DONNER : le robot n'est pas à côté du résident {resident}")
        if self.objet_porte != objet or objet is None:
            raise ActionIllegale(f"DONNER : le robot ne transporte pas {objet}")

        self.objet_porte = None
