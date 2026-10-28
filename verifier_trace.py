from __future__ import annotations

import sys

import reconfort_io as rio
from agent import charger_entrees
from logique import determiner_repli, generer_casiers_candidats, trouver_emotion
from planification import cases_adjacentes, plus_court_chemin
from simulateur import ActionIllegale, Simulateur

USAGE = "usage : python verifier_trace.py <carte> <scenario> <dossier_donnees> <trace>"
# Les 3 motifs du §5.5 + les 2 que nous avons ajoutés (PLAN §3).
MOTIFS = (
    "resident inaccessible",
    "armoire vide",
    "emotion indeterminee",
    "dictionnaire inaccessible",
    "armoire inaccessible",
)


def nouveau_bilan() -> dict:
    """Ce que le rejeu a constaté pendant une demande."""
    return {"vus": set(), "consulter": None, "prendre": None, "donner": None,
            "casier": None, "objet": None}


class Verificateur:
    """Rejoue une trace contre la réalité (grille et casiers), comme la correction (§10)."""

    def __init__(self, carte: dict, scenario: dict, dictionnaire: dict, armoire: dict, trace: dict):
        self.carte = carte
        self.scenario = scenario
        self.dictionnaire = dictionnaire
        self.armoire = armoire
        self.trace = trace
        self.sim = Simulateur(carte, armoire)
        self.depart = tuple(carte["depart_robot"])
        self.bilans = {}
        self.residents = {}
        for demande in scenario["demandes"]:
            self.bilans[demande["numero"]] = nouveau_bilan()
            self.residents[demande["numero"]] = demande["resident"]
        self.erreurs = []

    def verifier(self) -> list[str]:
        """Toutes les vérifications ; renvoie la liste des erreurs (vide = trace conforme)."""
        self.verifier_entete()
        self.rejouer()
        self.verifier_livraisons()
        self.verifier_resume()
        return self.erreurs

    def verifier_entete(self) -> None:
        if self.trace["carte"] != self.carte["nom"]:
            self.erreurs.append(f"entête : carte {self.trace['carte']}, attendu {self.carte['nom']}")
        if self.trace["scenario"] != self.scenario["nom"]:
            self.erreurs.append(f"entête : scénario {self.trace['scenario']}, attendu {self.scenario['nom']}")
        if not isinstance(self.trace["equipe"], list) or len(self.trace["equipe"]) == 0:
            self.erreurs.append("entête : equipe doit être une liste non vide")

    def rejouer(self) -> None:
        """Chaque pas sur un simulateur neuf : état AVANT l'action, puis l'action elle-même."""
        ordre = list(self.bilans)
        rang_precedent = 0
        for t in range(len(self.trace["pas"])):
            pas = self.trace["pas"][t]
            numero = pas["demande"]
            if numero not in self.bilans:
                self.erreurs.append(f"pas {t} : demande {numero} absente du scénario, rejeu arrêté")
                return
            if ordre.index(numero) < rang_precedent:
                self.erreurs.append(f"pas {t} : retour à la demande {numero} déjà terminée")
            rang_precedent = ordre.index(numero)
            self.verifier_pas(pas, t)
            self.noter_pas(self.bilans[numero], pas, t)
            try:
                self.sim.executer(pas["action"], pas["argument"], self.residents[numero])
            except ActionIllegale as erreur:
                self.erreurs.append(f"pas {t} : action illégale ({erreur}), rejeu arrêté")
                return

    def verifier_pas(self, pas: dict, t: int) -> None:
        """§5.5 : t continu, position/casier avant l'action, perception et contenu_casier réels."""
        if pas["t"] != t:
            self.erreurs.append(f"pas {t} : t vaut {pas['t']}")
        if pas["position"] != list(self.sim.position):
            self.erreurs.append(f"pas {t} : position {pas['position']}, réelle {list(self.sim.position)}")
        if pas["casier"] != list(self.sim.selecteur):
            self.erreurs.append(f"pas {t} : casier {pas['casier']}, réel {list(self.sim.selecteur)}")
        if pas["perception"] != self.sim.percevoir():
            self.erreurs.append(f"pas {t} : perception {pas['perception']}, réelle {self.sim.percevoir()}")
        if pas["contenu_casier"] != self.sim.contenu_casier():
            self.erreurs.append(
                f"pas {t} : contenu_casier {pas['contenu_casier']!r}, réel {self.sim.contenu_casier()!r}"
            )

    def noter_pas(self, bilan: dict, pas: dict, t: int) -> None:
        # §6.2 : un casier « vu » = le sélecteur y était pendant un pas devant l'armoire.
        if self.sim.adjacent_a(self.sim.pos_armoire):
            bilan["vus"].add(self.sim.selecteur)
        action = pas["action"]
        if action == "CONSULTER" and bilan["consulter"] is None:
            bilan["consulter"] = t
        elif action == "PRENDRE":
            bilan["prendre"] = t
            bilan["casier"] = self.sim.selecteur
            bilan["objet"] = pas["argument"]
        elif action == "DONNER":
            bilan["donner"] = t

    def verifier_livraisons(self) -> None:
        demandes = self.scenario["demandes"]
        livraisons = self.trace["livraisons"]
        if len(livraisons) != len(demandes):
            self.erreurs.append(f"{len(livraisons)} livraisons pour {len(demandes)} demandes")
        for i in range(min(len(livraisons), len(demandes))):
            self.verifier_livraison(livraisons[i], demandes[i])

    def verifier_livraison(self, livraison: dict, demande: dict) -> None:
        """Ce qui est annoncé = ce qui a été fait pendant la demande, et ce qu'imposent §6.1 / §6.2."""
        numero = demande["numero"]
        prefixe = f"livraison {numero}"
        bilan = self.bilans[numero]
        if livraison["demande"] != numero or livraison["resident"] != demande["resident"]:
            self.erreurs.append(f"{prefixe} : demande/résident ne suivent pas le scénario")
        if livraison["pas_utilises"] != self.compter_pas(numero):
            self.erreurs.append(f"{prefixe} : pas_utilises {livraison['pas_utilises']}, compté {self.compter_pas(numero)}")
        if livraison["objet"] != bilan["objet"]:
            self.erreurs.append(f"{prefixe} : objet {livraison['objet']!r}, pris {bilan['objet']!r}")
        casier_pris = None
        if bilan["casier"] is not None:
            casier_pris = list(bilan["casier"])
        if livraison["casier_choisi"] != casier_pris:
            self.erreurs.append(f"{prefixe} : casier_choisi {livraison['casier_choisi']}, PRENDRE en {casier_pris}")

        lu = trouver_emotion(demande["message"], self.dictionnaire)
        if livraison["emotion"] is not None:
            if bilan["consulter"] is None:
                self.erreurs.append(f"{prefixe} : émotion annoncée sans CONSULTER")
            if lu is None or (livraison["emotion"], livraison["intensite"]) != tuple(lu):
                self.erreurs.append(f"{prefixe} : émotion {livraison['emotion']}/{livraison['intensite']}, le dictionnaire donne {lu}")

        if livraison["succes"]:
            self.verifier_reussite(livraison, bilan, lu, prefixe)
        else:
            self.verifier_echec(livraison, demande, bilan, lu, prefixe)

    def compter_pas(self, numero: int) -> int:
        nombre = 0
        for pas in self.trace["pas"]:
            if pas["demande"] == numero:
                nombre += 1
        return nombre

    def verifier_reussite(self, livraison: dict, bilan: dict, lu, prefixe: str) -> None:
        if livraison["motif_echec"] is not None:
            self.erreurs.append(f"{prefixe} : réussie mais motif_echec {livraison['motif_echec']!r}")
        if bilan["consulter"] is None or bilan["prendre"] is None or bilan["donner"] is None:
            self.erreurs.append(f"{prefixe} : réussie sans CONSULTER, PRENDRE et DONNER dans la demande")
            return
        if not bilan["consulter"] < bilan["prendre"] < bilan["donner"]:
            self.erreurs.append(f"{prefixe} : CONSULTER, PRENDRE, DONNER dans le désordre")
        if lu is None:
            self.erreurs.append(f"{prefixe} : réussie alors qu'aucun mot du message n'est connu")
            return
        self.verifier_choix_casier(livraison, bilan, lu, prefixe)

    def verifier_choix_casier(self, livraison: dict, bilan: dict, lu, prefixe: str) -> None:
        """§6.2 : chaque candidat plus prioritaire est vide ET a été vu pendant cette demande."""
        candidats = generer_casiers_candidats(lu[0], lu[1], self.armoire["emotions"], self.armoire["intensites"])
        casier = bilan["casier"]
        if casier not in candidats:
            self.erreurs.append(f"{prefixe} : casier {list(casier)} hors des 15 candidats")
            return
        for candidat in candidats:
            if candidat == casier:
                break
            if self.sim.objets.get(candidat) is not None:
                self.erreurs.append(f"{prefixe} : le candidat prioritaire {list(candidat)} était garni")
            if candidat not in bilan["vus"]:
                self.erreurs.append(f"{prefixe} : repli sans être passé devant {list(candidat)}")
        repli = determiner_repli(
            self.armoire["emotions"].index(lu[0]), self.armoire["intensites"].index(lu[1]), casier[1], casier[0]
        )
        if livraison["repli"] != repli:
            self.erreurs.append(f"{prefixe} : repli {livraison['repli']!r}, attendu {repli!r}")

    def verifier_echec(self, livraison: dict, demande: dict, bilan: dict, lu, prefixe: str) -> None:
        """Le motif doit être vrai dans la réalité : on ne déclare pas un échec évitable."""
        motif = livraison["motif_echec"]
        if bilan["donner"] is not None:
            self.erreurs.append(f"{prefixe} : DONNER dans une demande en échec")
        if motif not in MOTIFS:
            self.erreurs.append(f"{prefixe} : motif_echec inconnu {motif!r}")
        elif motif == "emotion indeterminee":
            if bilan["consulter"] is None:
                self.erreurs.append(f"{prefixe} : emotion indeterminee sans CONSULTER")
            if lu is not None:
                self.erreurs.append(f"{prefixe} : emotion indeterminee alors que le dictionnaire donne {lu}")
        elif motif == "armoire vide":
            self.verifier_armoire_vide(bilan, lu, prefixe)
        elif motif == "dictionnaire inaccessible":
            self.verifier_inaccessible(self.sim.pos_dictionnaire, motif, prefixe)
        elif motif == "armoire inaccessible":
            self.verifier_inaccessible(self.sim.pos_armoire, motif, prefixe)
        else:
            self.verifier_inaccessible(self.sim.residents[demande["resident"]], motif, prefixe)

    def verifier_armoire_vide(self, bilan: dict, lu, prefixe: str) -> None:
        if lu is None:
            self.erreurs.append(f"{prefixe} : armoire vide sans émotion connue")
            return
        candidats = generer_casiers_candidats(lu[0], lu[1], self.armoire["emotions"], self.armoire["intensites"])
        for candidat in candidats:
            if self.sim.objets.get(candidat) is not None:
                self.erreurs.append(f"{prefixe} : armoire vide alors que {list(candidat)} est garni")
            if candidat not in bilan["vus"]:
                self.erreurs.append(f"{prefixe} : armoire vide sans être passé devant {list(candidat)}")

    def verifier_inaccessible(self, cible, motif: str, prefixe: str) -> None:
        # Le robot ne quitte jamais sa zone connexe : partir du départ revient à partir d'où il est.
        arrivees = cases_adjacentes(cible, (self.sim.hauteur, self.sim.largeur))
        chemin = plus_court_chemin(self.depart, arrivees, self.est_libre)
        if chemin is not None:
            self.erreurs.append(f"{prefixe} : {motif} alors qu'un chemin réel de {len(chemin) - 1} pas existe")

    def est_libre(self, pos: tuple[int, int]) -> bool:
        return self.sim.type_case(pos) == "libre"

    def verifier_resume(self) -> None:
        livraisons = self.trace["livraisons"]
        reussies = 0
        for livraison in livraisons:
            if livraison["succes"]:
                reussies += 1
        attendu = {
            "demandes": len(livraisons),
            "reussies": reussies,
            "echecs": len(livraisons) - reussies,
            "pas_total": len(self.trace["pas"]),
        }
        if self.trace["resume"] != attendu:
            self.erreurs.append(f"resume {self.trace['resume']}, attendu {attendu}")


def main(argv: list) -> int:
    """0 = trace conforme, 1 = erreurs trouvées, 2 = mauvais appel ou fichier illisible."""
    if len(argv) != 5:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        carte, scenario, dictionnaire, armoire = charger_entrees(argv[1], argv[2], argv[3])
        trace = rio._lire_json(argv[4], "robot-reconfort/trace")
    except rio.ErreurFichier as erreur:
        print(f"erreur : {erreur}", file=sys.stderr)
        return 2

    try:
        erreurs = Verificateur(carte, scenario, dictionnaire, armoire, trace).verifier()
    except (KeyError, TypeError, ValueError, IndexError) as erreur:
        print(f"erreur : trace mal formée ({erreur!r})", file=sys.stderr)
        return 2

    if len(erreurs) > 0:
        for erreur in erreurs:
            print(erreur)
        print(f"{argv[4]} : NON conforme, {len(erreurs)} erreur(s)")
        return 1
    resume = trace["resume"]
    print(f"{argv[4]} : conforme ({resume['reussies']}/{resume['demandes']} demandes réussies, {resume['pas_total']} pas)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
