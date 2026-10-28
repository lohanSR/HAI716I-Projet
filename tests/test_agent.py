import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import reconfort_io as rio
from agent import main
from simulateur import ActionIllegale, Simulateur
from decision import est_adjacent
from tests.test_navigation import CARTE_MUREE, CARTE_REPLAN, creer_agent

RACINE = Path(__file__).resolve().parent.parent

# Dictionnaire muré : (1,4), (2,5) et le bord l'entourent, P reste accessible par (3,4).
CARTE_DICO_MURE = {
    "dimensions": {"hauteur": 5, "largeur": 7},
    "grille": [
        "#######",
        "#R..#D#",
        "#A..###",
        "#....P#",
        "#######",
    ],
    "depart_robot": [1, 1],
    "armoire": {"position": [2, 1]},
    "dictionnaire": {"position": [1, 5]},
    "residents": [{"id": "R1", "nom": "Lou", "position": [3, 5]}],
}

# R1 muré (comme CARTE_MUREE), R2 accessible.
CARTE_DEUX_RESIDENTS = {
    "dimensions": {"hauteur": 5, "largeur": 8},
    "grille": [
        "########",
        "#R...#.#",
        "#AD..#P#",
        "#...P###",
        "########",
    ],
    "depart_robot": [1, 1],
    "armoire": {"position": [2, 1]},
    "dictionnaire": {"position": [2, 2]},
    "residents": [
        {"id": "R1", "nom": "Hugo", "position": [2, 6]},
        {"id": "R2", "nom": "Ines", "position": [3, 4]},
    ],
}


def charger_dictionnaire() -> dict:
    return rio.charger_dictionnaire(RACINE / "donnees" / "dictionnaire.json")


def lancer(arguments: list) -> tuple:
    """Appelle main() comme en ligne de commande ; renvoie (code, sortie d'erreur)."""
    erreurs = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(erreurs):
        code = main(["agent.py"] + arguments)
    return code, erreurs.getvalue()


def actions(trace) -> list:
    resultat = []
    for pas in trace.pas:
        resultat.append(pas["action"])
    return resultat


def avancer_avant_prendre(trace, debut, pos_armoire) -> int:
    """Nombre d'AVANCER entre l'arrivée devant l'armoire (après CONSULTER) et PRENDRE."""
    consulter = actions(trace).index("CONSULTER", debut)
    prendre = actions(trace).index("PRENDRE", debut)
    arrivee = None
    for t in range(consulter + 1, prendre + 1):
        if arrivee is None and est_adjacent(tuple(trace.pas[t]["position"]), pos_armoire):
            arrivee = t
    nombre = 0
    for t in range(arrivee, prendre):
        if trace.pas[t]["action"] == "AVANCER":
            nombre += 1
    return nombre


class TestMain(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.sortie = Path(self.dossier.name) / "trace.json"

    def tearDown(self):
        self.dossier.cleanup()

    def test_appartement_01_bout_en_bout(self):
        code, erreurs = lancer([
            str(RACINE / "cartes" / "appartement_01.json"),
            str(RACINE / "cartes" / "scenario_01.json"),
            str(RACINE / "donnees"),
            str(self.sortie),
        ])
        self.assertEqual(code, 0)
        self.assertEqual(erreurs, "")
        trace = json.loads(self.sortie.read_text(encoding="utf-8"))
        self.assertEqual(trace["resume"]["reussies"], 4)
        self.assertEqual(trace["resume"]["pas_total"], len(trace["pas"]))
        rendu = json.loads((RACINE / "rendu.json").read_text(encoding="utf-8"))
        self.assertEqual(trace["equipe"], rendu["equipe"])

        # Annexe D, demande 1 : seule → tristesse/moyenne → couverture en [1, 4].
        premiere = trace["livraisons"][0]
        self.assertEqual(premiere["emotion"], "tristesse")
        self.assertEqual(premiere["casier_choisi"], [1, 4])
        self.assertEqual(premiere["objet"], "couverture")

        for t in range(len(trace["pas"])):
            self.assertEqual(trace["pas"][t]["t"], t)
        self.assertEqual(trace["pas"][-1]["action"], "DONNER")

    def test_annexe_c5_sur_appartement_03(self):
        code, erreurs = lancer([
            str(RACINE / "cartes" / "appartement_03.json"),
            str(RACINE / "cartes" / "scenario_03.json"),
            str(RACINE / "donnees"),
            str(self.sortie),
        ])
        self.assertEqual(code, 0)
        trace = json.loads(self.sortie.read_text(encoding="utf-8"))
        premiere = trace["livraisons"][0]
        self.assertEqual((premiere["emotion"], premiere["intensite"]), ("surprise", "forte"))
        self.assertEqual(premiere["casier_choisi"], [2, 4])
        self.assertEqual(premiere["repli"], "voisine_1")
        self.assertEqual(premiere["objet"], "telephone")
        chercher = 0
        for pas in trace["pas"]:
            if pas["demande"] == 1 and pas["action"] == "CHERCHER":
                chercher += 1
        self.assertEqual(chercher, 9)

    def test_mauvais_nombre_arguments(self):
        code, erreurs = lancer(["a", "b", "c"])
        self.assertNotEqual(code, 0)
        self.assertIn("usage", erreurs)

    def test_fichier_absent_pas_de_trace(self):
        code, erreurs = lancer([
            str(RACINE / "cartes" / "absente.json"),
            str(RACINE / "cartes" / "scenario_01.json"),
            str(RACINE / "donnees"),
            str(self.sortie),
        ])
        self.assertEqual(code, 1)
        self.assertIn("introuvable", erreurs)
        self.assertFalse(self.sortie.exists())

    def test_scenario_autre_carte_pas_de_trace(self):
        code, erreurs = lancer([
            str(RACINE / "cartes" / "appartement_01.json"),
            str(RACINE / "cartes" / "scenario_02.json"),
            str(RACINE / "donnees"),
            str(self.sortie),
        ])
        self.assertEqual(code, 1)
        self.assertIn("Scénario", erreurs)
        self.assertFalse(self.sortie.exists())

    def test_action_illegale_pas_de_trace(self):
        # Le simulateur refuse le premier PRENDRE, après de vrais pas déjà journalisés.
        refus = ActionIllegale("PRENDRE refusé (test)")
        with patch.object(Simulateur, "prendre", side_effect=refus):
            code, erreurs = lancer([
                str(RACINE / "cartes" / "appartement_01.json"),
                str(RACINE / "cartes" / "scenario_01.json"),
                str(RACINE / "donnees"),
                str(self.sortie),
            ])
        self.assertEqual(code, 3)
        self.assertIn("action illégale", erreurs)
        self.assertFalse(self.sortie.exists())


class TestDemande(unittest.TestCase):
    def test_emotion_indeterminee(self):
        agent, sim, trace = creer_agent(CARTE_MUREE)
        demande = {"numero": 1, "resident": "R1", "message": "Bonjour, quelle heure est-il ?"}
        agent.traiter_demande(demande, charger_dictionnaire())

        livraison = trace.livraisons[0]
        self.assertFalse(livraison["succes"])
        self.assertEqual(livraison["motif_echec"], "emotion indeterminee")
        self.assertIsNone(livraison["emotion"])
        self.assertEqual(actions(trace)[-1], "CONSULTER")
        self.assertEqual(livraison["pas_utilises"], len(trace.pas))

    def test_resident_mure(self):
        agent, sim, trace = creer_agent(CARTE_MUREE)
        dictionnaire = charger_dictionnaire()
        message = "Je me sens seule."

        # 1re demande : résident incertain → exploration d'abord, preuve du mur, rien n'est pris.
        agent.traiter_demande({"numero": 1, "resident": "R1", "message": message}, dictionnaire)
        premiere = trace.livraisons[0]
        self.assertEqual(premiere["motif_echec"], "resident inaccessible")
        self.assertIsNone(premiere["objet"])
        self.assertIsNone(agent.objet_porte)

        # 2e demande : la preuve est déjà en mémoire, aucun pas vers le résident.
        nb_pas = len(trace.pas)
        agent.traiter_demande({"numero": 2, "resident": "R1", "message": message}, dictionnaire)
        seconde = trace.livraisons[1]
        self.assertEqual(seconde["motif_echec"], "resident inaccessible")
        self.assertLess(seconde["pas_utilises"], nb_pas)
        self.assertNotIn("PRENDRE", actions(trace))
        self.assertNotIn("CHERCHER", actions(trace))

    def test_resident_mure_puis_demande_suivante(self):
        agent, sim, trace = creer_agent(CARTE_DEUX_RESIDENTS)
        dictionnaire = charger_dictionnaire()
        agent.traiter_demande({"numero": 1, "resident": "R1", "message": "Je me sens seule."}, dictionnaire)
        agent.traiter_demande({"numero": 2, "resident": "R2", "message": "Je me sens seule."}, dictionnaire)

        premiere, seconde = trace.livraisons
        self.assertEqual(premiere["motif_echec"], "resident inaccessible")
        self.assertIsNone(premiere["objet"])
        self.assertTrue(seconde["succes"])
        self.assertEqual(seconde["objet"], "couverture")
        self.assertEqual(actions(trace).count("PRENDRE"), 1)
        self.assertEqual(actions(trace)[-1], "DONNER")

    def test_resident_incertain_explore_avant_prendre(self):
        agent, sim, trace = creer_agent(CARTE_REPLAN)
        dictionnaire = charger_dictionnaire()
        agent.traiter_demande({"numero": 1, "resident": "R1", "message": "Je me sens seule."}, dictionnaire)

        self.assertTrue(trace.livraisons[0]["succes"])
        # Aller-retour armoire → R1 → armoire avant de prendre (au moins 2 × 7 pas).
        self.assertGreaterEqual(avancer_avant_prendre(trace, 0, (3, 1)), 14)

        # 2e demande : le chemin est connu (cases vues libres), il prend l'objet sans explorer.
        debut = len(trace.pas)
        agent.traiter_demande({"numero": 2, "resident": "R1", "message": "Je me sens seule."}, dictionnaire)
        self.assertTrue(trace.livraisons[1]["succes"])
        self.assertEqual(avancer_avant_prendre(trace, debut, (3, 1)), 0)

    def test_dictionnaire_inaccessible(self):
        agent, sim, trace = creer_agent(CARTE_DICO_MURE)
        demande = {"numero": 1, "resident": "R1", "message": "Je me sens seule."}
        agent.traiter_demande(demande, charger_dictionnaire())

        livraison = trace.livraisons[0]
        self.assertEqual(livraison["motif_echec"], "dictionnaire inaccessible")
        self.assertIsNone(livraison["emotion"])
        self.assertNotIn("CONSULTER", actions(trace))
        self.assertEqual(agent.position, sim.position)


if __name__ == "__main__":
    unittest.main()
