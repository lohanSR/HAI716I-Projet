import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import reconfort_io as rio
from agent import main
from tests.test_navigation import CARTE_MUREE, creer_agent

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

        # 1re demande : le plan optimiste passe, il prend l'objet puis découvre le mur et le garde.
        agent.traiter_demande({"numero": 1, "resident": "R1", "message": message}, dictionnaire)
        premiere = trace.livraisons[0]
        self.assertEqual(premiere["motif_echec"], "resident inaccessible")
        self.assertEqual(premiere["objet"], "couverture")
        self.assertEqual(agent.objet_porte, "couverture")

        # 2e demande : la preuve est déjà en mémoire, il ne reprend rien.
        agent.traiter_demande({"numero": 2, "resident": "R1", "message": message}, dictionnaire)
        seconde = trace.livraisons[1]
        self.assertEqual(seconde["motif_echec"], "resident inaccessible")
        self.assertIsNone(seconde["objet"])
        self.assertEqual(actions(trace).count("PRENDRE"), 1)
        self.assertNotIn("DONNER", actions(trace))

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
