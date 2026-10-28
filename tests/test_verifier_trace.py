import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import agent
import reconfort_io as rio
import verifier_trace
from agent import Agent, vue_publique_armoire, vue_publique_carte
from simulateur import Simulateur
from tests.test_agent import CARTE_DICO_MURE, CARTE_DEUX_RESIDENTS, charger_dictionnaire
from tests.test_navigation import CARTE_MUREE, CARTE_REPLAN, charger_armoire_standard
from verifier_trace import Verificateur

RACINE = Path(__file__).resolve().parent.parent

# Depuis (1,2), le robot touche D (O), P (E) et A (S) : aucune case à parcourir, seule l'armoire compte.
CARTE_MINI = {
    "nom": "mini",
    "dimensions": {"hauteur": 4, "largeur": 6},
    "grille": [
        "######",
        "#DRP.#",
        "##A..#",
        "######",
    ],
    "depart_robot": [1, 2],
    "armoire": {"position": [2, 2]},
    "dictionnaire": {"position": [1, 1]},
    "residents": [{"id": "R1", "nom": "Lou", "position": [1, 3]}],
}

# Annexe C.5 : surprise/forte, colonne surprise vide → [2,4] telephone, voisine_1.
FOUILLE_C5 = ["S", "E", "E", "E", "N", "N", "S", "S", "E"]


def scenario_mini(message: str) -> dict:
    return {
        "nom": "scenario_mini",
        "carte": "mini",
        "armoire": "armoire_standard",
        "demandes": [{"numero": 1, "resident": "R1", "message": message}],
    }


def jouer(chercher: list, objet: str) -> rio.Trace:
    """Trace d'une demande sur CARTE_MINI, journalisée avec l'état réel (perceptions toujours justes)."""
    sim = Simulateur(CARTE_MINI, charger_armoire_standard())
    trace = rio.Trace("mini", "scenario_mini", ["test"])
    actions = [("CONSULTER", None)]
    for direction in chercher:
        actions.append(("CHERCHER", direction))
    actions.append(("PRENDRE", objet))
    actions.append(("DONNER", objet))
    for action, argument in actions:
        trace.ajouter_pas(
            demande=1, position=sim.position, casier=sim.selecteur, action=action,
            argument=argument, perception=sim.percevoir(), contenu_casier=sim.contenu_casier(),
        )
        sim.executer(action, argument, "R1")
    return trace


def trace_c5() -> dict:
    trace = jouer(FOUILLE_C5, "telephone")
    trace.ajouter_livraison(1, "R1", "surprise", "forte", (2, 4), "voisine_1", "telephone", True)
    return trace.en_dictionnaire()


def verifier(trace: dict, message: str = "Je suis sidéré !") -> list:
    return Verificateur(
        CARTE_MINI, scenario_mini(message), charger_dictionnaire(), charger_armoire_standard(), trace
    ).verifier()


def contient(erreurs: list, morceau: str) -> bool:
    for erreur in erreurs:
        if morceau in erreur:
            return True
    return False


class TestTraceFalsifiee(unittest.TestCase):
    def test_fouille_c5_conforme(self):
        self.assertEqual(verifier(trace_c5()), [])

    def test_repli_sans_fouille(self):
        # Tout droit vers [2,4] : [1,3] et [0,3] ne sont jamais passés sous le sélecteur.
        trace = jouer(["S", "E", "E", "E", "E"], "telephone")
        trace.ajouter_livraison(1, "R1", "surprise", "forte", (2, 4), "voisine_1", "telephone", True)
        erreurs = verifier(trace.en_dictionnaire())
        self.assertTrue(contient(erreurs, "passé devant [1, 3]"))
        self.assertTrue(contient(erreurs, "passé devant [0, 3]"))
        self.assertFalse(contient(erreurs, "garni"))

    def test_candidat_prioritaire_garni_ignore(self):
        # tristesse/moyenne : [1,4] (couverture) est vu garni, puis le robot prend [2,4].
        trace = jouer(["E", "E", "E", "E", "S"], "telephone")
        trace.ajouter_livraison(1, "R1", "tristesse", "moyenne", (2, 4), "intensite", "telephone", True)
        erreurs = verifier(trace.en_dictionnaire(), "Je suis triste.")
        self.assertTrue(contient(erreurs, "prioritaire [1, 4] était garni"))

    def test_perception_falsifiee(self):
        trace = trace_c5()
        trace["pas"][1]["perception"]["N"] = "libre"
        self.assertTrue(contient(verifier(trace), "pas 1 : perception"))

    def test_contenu_casier_falsifie(self):
        trace = trace_c5()
        trace["pas"][2]["contenu_casier"] = "doudou"
        self.assertTrue(contient(verifier(trace), "pas 2 : contenu_casier"))

    def test_t_position_casier_faux(self):
        trace = trace_c5()
        trace["pas"][3]["t"] = 99
        trace["pas"][4]["position"] = [1, 4]
        trace["pas"][5]["casier"] = [0, 0]
        erreurs = verifier(trace)
        self.assertTrue(contient(erreurs, "pas 3 : t vaut 99"))
        self.assertTrue(contient(erreurs, "pas 4 : position"))
        self.assertTrue(contient(erreurs, "pas 5 : casier"))

    def test_action_illegale_arrete_le_rejeu(self):
        trace = trace_c5()
        trace["pas"][0]["action"] = "AVANCER"
        trace["pas"][0]["argument"] = "N"
        erreurs = verifier(trace)
        self.assertTrue(contient(erreurs, "pas 0 : action illégale"))
        self.assertTrue(contient(erreurs, "rejeu arrêté"))

    def test_livraison_et_resume_faux(self):
        trace = trace_c5()
        trace["livraisons"][0]["repli"] = "aucun"
        trace["livraisons"][0]["objet"] = "couverture"
        trace["livraisons"][0]["pas_utilises"] = 3
        trace["resume"]["pas_total"] = 3
        erreurs = verifier(trace)
        self.assertTrue(contient(erreurs, "repli 'aucun'"))
        self.assertTrue(contient(erreurs, "objet 'couverture'"))
        self.assertTrue(contient(erreurs, "pas_utilises 3"))
        self.assertTrue(contient(erreurs, "resume"))

    def test_echec_evitable(self):
        # Le résident est juste à côté : « resident inaccessible » est faux.
        trace = rio.Trace("mini", "scenario_mini", ["test"])
        trace.ajouter_livraison(1, "R1", None, None, None, "aucun", None, False, "resident inaccessible")
        erreurs = verifier(trace.en_dictionnaire())
        self.assertTrue(contient(erreurs, "chemin réel de 0 pas"))


class TestTracesDeLAgent(unittest.TestCase):
    def verifier_agent(self, carte: dict, demandes: list) -> list:
        """Joue l'agent puis vérifie sa trace après un aller-retour JSON (comme un vrai fichier)."""
        carte = dict(carte)
        carte["nom"] = "test"
        armoire = charger_armoire_standard()
        dictionnaire = charger_dictionnaire()
        trace = rio.Trace("test", "test", ["test"])
        robot = Agent(vue_publique_carte(carte), vue_publique_armoire(armoire), Simulateur(carte, armoire), trace)
        for demande in demandes:
            robot.traiter_demande(demande, dictionnaire)
        lue = json.loads(json.dumps(trace.en_dictionnaire()))
        scenario = {"nom": "test", "demandes": demandes}
        return Verificateur(carte, scenario, dictionnaire, armoire, lue).verifier()

    def test_echecs_de_l_agent_conformes(self):
        seule = "Je me sens seule."
        self.assertEqual(self.verifier_agent(CARTE_MUREE, [
            {"numero": 1, "resident": "R1", "message": seule},
            {"numero": 2, "resident": "R1", "message": "Bonjour, quelle heure est-il ?"},
        ]), [])
        self.assertEqual(self.verifier_agent(CARTE_DICO_MURE, [
            {"numero": 1, "resident": "R1", "message": seule},
        ]), [])
        self.assertEqual(self.verifier_agent(CARTE_DEUX_RESIDENTS, [
            {"numero": 1, "resident": "R1", "message": seule},
            {"numero": 2, "resident": "R2", "message": seule},
        ]), [])
        self.assertEqual(self.verifier_agent(CARTE_REPLAN, [
            {"numero": 1, "resident": "R1", "message": seule},
        ]), [])


class TestMainVerificateur(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.sortie = Path(self.dossier.name) / "trace.json"

    def tearDown(self):
        self.dossier.cleanup()

    def lancer(self, module, numero: str) -> int:
        arguments = [
            "prog",
            str(RACINE / "cartes" / f"appartement_{numero}.json"),
            str(RACINE / "cartes" / f"scenario_{numero}.json"),
            str(RACINE / "donnees"),
            str(self.sortie),
        ]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return module.main(arguments)

    def test_cinq_cartes_conformes(self):
        for numero in ["01", "02", "03", "04", "05"]:
            self.assertEqual(self.lancer(agent, numero), 0)
            self.assertEqual(self.lancer(verifier_trace, numero), 0, f"carte {numero}")

    def test_trace_falsifiee_code_1(self):
        self.assertEqual(self.lancer(agent, "01"), 0)
        trace = json.loads(self.sortie.read_text(encoding="utf-8"))
        falsifiee = copy.deepcopy(trace)
        falsifiee["pas"][0]["perception"]["O"] = "libre"
        self.sortie.write_text(json.dumps(falsifiee), encoding="utf-8")
        self.assertEqual(self.lancer(verifier_trace, "01"), 1)

    def test_mauvais_appel_code_2(self):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(verifier_trace.main(["prog", "a"]), 2)
        # Trace absente : erreur de fichier, pas de traceback.
        self.assertEqual(self.lancer(verifier_trace, "01"), 2)


if __name__ == "__main__":
    unittest.main()
