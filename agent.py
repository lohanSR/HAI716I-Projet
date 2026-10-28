from __future__ import annotations

import sys
from pathlib import Path

import affichage
import reconfort_io as rio
import validation
from action import executer_action
from decision import est_adjacent, planifier, premiere_direction
from gestion_armoire import EtatArmoire
from logique import trouver_emotion
from memoire import CarteMentale
from perception import percevoir
from simulateur import ActionIllegale, Simulateur

EQUIPE = ["MAHDI Raouf", "SERR Lohan"]
USAGE = (
    "usage : python agent.py <carte> <scenario> <dossier_donnees> <trace> [--afficher]"
)


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
        self.emotions = armoire["emotions"]
        self.intensites = armoire["intensites"]
        self.nb_colonnes_armoire = len(armoire["emotions"])
        self.etat_armoire = EtatArmoire(self.emotions, self.intensites)
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

    def traiter_demande(self, demande: dict, dictionnaire: dict) -> None:
        """Traite une demande du scénario puis ajoute sa livraison (réussie ou non) à la trace."""
        self.demande = demande
        livraison = {
            "emotion": None,
            "intensite": None,
            "casier_choisi": None,
            "repli": "aucun",
            "objet": None,
        }
        motif = self.servir(demande, dictionnaire, livraison)
        self.trace.ajouter_livraison(
            demande=demande["numero"],
            resident=demande["resident"],
            emotion=livraison["emotion"],
            intensite=livraison["intensite"],
            casier_choisi=livraison["casier_choisi"],
            repli=livraison["repli"],
            objet=livraison["objet"],
            succes=motif is None,
            motif_echec=motif,
        )

    def servir(self, demande: dict, dictionnaire: dict, livraison: dict) -> str | None:
        """§4 : dictionnaire → CONSULTER → armoire → PRENDRE → résident → DONNER. Renvoie le motif d'échec, ou None."""
        if not self.aller_vers(self.pos_dictionnaire):
            return "dictionnaire inaccessible"
        self.agir("CONSULTER")
        resultat = trouver_emotion(demande["message"], dictionnaire)
        if resultat is None:
            return "emotion indeterminee"
        livraison["emotion"] = resultat[0]
        livraison["intensite"] = resultat[1]

        if not self.aller_vers(self.pos_armoire):
            return "armoire inaccessible"
        pos_resident = self.residents[demande["resident"]]
        motif = self.verifier_resident(pos_resident)
        if motif is not None:
            return motif
        motif = self.prendre_objet(livraison)
        if motif is not None:
            return motif

        if not self.aller_vers(pos_resident):
            return "resident inaccessible"
        self.agir("DONNER", self.objet_porte)
        return None

    def verifier_resident(self, pos_resident) -> str | None:
        """Avant PRENDRE (aucune action ne permet de poser un objet) : n'avancer que si le résident est atteignable à coup sûr."""
        if planifier(self.memoire, self.position, pos_resident) is None:
            return "resident inaccessible"
        if planifier(self.memoire, self.position, pos_resident, True) is not None:
            return None
        # Incertain : on explore jusqu'au résident (ou jusqu'à la preuve qu'il est muré), puis on revient.
        if not self.aller_vers(pos_resident):
            return "resident inaccessible"
        if not self.aller_vers(self.pos_armoire):
            return "armoire inaccessible"
        return None

    def prendre_objet(self, livraison: dict) -> str | None:
        """§6.2, une action par tick : candidats dans l'ordre de priorité, PRENDRE dans le premier trouvé garni."""
        self.etat_armoire.nouvelle_fouille(livraison["emotion"], livraison["intensite"])
        # Le robot est devant l'armoire : le casier sous le sélecteur est déjà visible.
        self.etat_armoire.memoriser(self.casier, self.contenu_casier)
        while True:
            action, argument = self.etat_armoire.prochaine_action(self.casier)
            if action == "ECHEC":
                # §6.2 : le dernier casier n'est vu qu'après le dernier CHERCHER ; ce pas le journalise dans la demande.
                self.agir("ATTENDRE")
                return argument
            if self.afficher:
                self.dessiner(None, f"armoire : casier {list(self.casier)} → {action} {argument}")
            if action == "PRENDRE":
                livraison["casier_choisi"] = self.casier
                livraison["objet"] = argument
                livraison["repli"] = self.etat_armoire.repli(self.casier)
                self.agir("PRENDRE", argument)
                return None
            self.agir("CHERCHER", argument)


def charger_entrees(
    chemin_carte: str, chemin_scenario: str, dossier_donnees: str
) -> tuple:
    """Charge puis valide les 4 fichiers (§5.6) ; lève rio.ErreurFichier au premier problème."""
    carte = rio.charger_carte(chemin_carte)
    validation.valider_carte(carte)
    scenario = rio.charger_scenario(chemin_scenario)
    validation.valider_scenario(scenario, carte)
    dossier = Path(dossier_donnees)
    dictionnaire = rio.charger_dictionnaire(dossier / "dictionnaire.json")
    validation.valider_dictionnaire(dictionnaire)
    armoire = rio.charger_armoire(dossier / (scenario["armoire"] + ".json"))
    validation.valider_armoire(armoire)
    return carte, scenario, dictionnaire, armoire


def main(argv: list) -> int:
    """Contrat d'appel : 4 arguments (+ --afficher en option). Renvoie le code de retour."""
    afficher = False
    if len(argv) == 6 and argv[5] == "--afficher":
        afficher = True
    elif len(argv) != 5:
        print(USAGE, file=sys.stderr)
        return 2

    try:
        carte, scenario, dictionnaire, armoire = charger_entrees(
            argv[1], argv[2], argv[3]
        )
    except rio.ErreurFichier as erreur:
        print(f"erreur : {erreur}", file=sys.stderr)
        return 1

    trace = rio.Trace(carte["nom"], scenario["nom"], EQUIPE)
    sim = Simulateur(carte, armoire)
    agent = Agent(
        vue_publique_carte(carte), vue_publique_armoire(armoire), sim, trace, afficher
    )
    try:
        for demande in scenario["demandes"]:
            agent.traiter_demande(demande, dictionnaire)
    except ActionIllegale as erreur:
        # Bug de l'agent : mieux vaut aucune trace qu'une trace contenant un pas illégal.
        print(f"erreur : action illégale de l'agent ({erreur})", file=sys.stderr)
        return 3

    try:
        trace.ecrire(argv[4])
    except OSError as erreur:
        print(f"erreur : impossible d'écrire la trace ({erreur})", file=sys.stderr)
        return 1
    resume = trace.en_dictionnaire()["resume"]
    print(
        f"{resume['reussies']}/{resume['demandes']} demandes réussies, {resume['pas_total']} pas → {argv[4]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
