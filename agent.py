import affichage
from action import executer_action
from decision import est_adjacent, planifier, premiere_direction
from memoire import CarteMentale
from perception import percevoir


def vue_publique_carte(carte: dict) -> dict:
    """Copie de la carte sans la grille : les murs sont inconnus du robot."""
    vue = {}
    for cle in carte:
        if cle != "grille":
            vue[cle] = carte[cle]
    return vue


def vue_publique_armoire(armoire: dict) -> dict:
    """Copie de l'armoire sans les casiers : leur contenu est inconnu du robot."""
    vue = {}
    for cle in armoire:
        if cle != "casiers":
            vue[cle] = armoire[cle]
    return vue


class Agent:
    """Le robot : construit uniquement à partir des vues publiques, il agit sur le monde via le simulateur."""

    def __init__(self, carte: dict, armoire: dict, sim, trace, afficher: bool = False):
        if "grille" in carte:
            raise ValueError(
                "l'agent doit recevoir la vue publique de la carte (sans grille)"
            )

        dimensions = (carte["dimensions"]["hauteur"], carte["dimensions"]["largeur"])
        residents = {}
        for resident in carte["residents"]:
            residents[resident["id"]] = tuple(resident["position"])

        self.residents = residents
        self.pos_armoire = tuple(carte["armoire"]["position"])
        self.pos_dictionnaire = tuple(carte["dictionnaire"]["position"])
        self.memoire = CarteMentale(
            dimensions, self.pos_armoire, self.pos_dictionnaire, residents
        )

        self.position = tuple(carte["depart_robot"])
        self.casier = tuple(armoire["casier_depart"])
        self.nb_colonnes_armoire = len(armoire["emotions"])
        self.objet_porte = None

        self.sim = sim
        self.trace = trace
        self.afficher = afficher
        self.demande = None
        self.perception = None
        self.contenu_casier = None
        percevoir(self, sim)

    def agir(self, action: str, argument: str | None = None) -> None:
        """Un tick : journaliser + exécuter l'action, puis percevoir depuis le nouvel état."""
        executer_action(self, self.sim, self.trace, self.demande, action, argument)
        percevoir(self, self.sim)

    def aller_vers(self, cible) -> bool:
        """Boucle B.5 jusqu'à une case adjacente à cible ; False si la carte mentale prouve qu'il n'y a pas de chemin."""
        cible = tuple(cible)
        while not est_adjacent(self.position, cible):
            chemin = planifier(self.memoire, self.position, cible)
            if chemin is None:
                return False
            if self.afficher:
                self.dessiner(chemin, f"vers {list(cible)}")
            self.agir("AVANCER", premiere_direction(chemin))
        if self.afficher:
            self.dessiner(None, f"arrivé près de {list(cible)}")
        return True

    def dessiner(self, chemin, message: str) -> None:
        numero = None
        if self.demande is not None:
            numero = self.demande["numero"]
        entete = f"t={len(self.trace.pas)}  demande={numero}  {message}"
        affichage.afficher(self.memoire, self.position, chemin, entete)
