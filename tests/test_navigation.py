import unittest
from pathlib import Path

import reconfort_io as rio
from affichage import dessiner
from agent import Agent, vue_publique_armoire, vue_publique_carte
from decision import est_adjacent, planifier, premiere_direction
from memoire import CarteMentale
from simulateur import Simulateur

RACINE = Path(__file__).resolve().parent.parent

# Le chemin optimiste vers P passe par (1,4) : le mur n'est découvert qu'en (1,3).
CARTE_REPLAN = {
    "dimensions": {"hauteur": 5, "largeur": 9},
    "grille": [
        "#########",
        "#R..#..P#",
        "#.......#",
        "#A.....D#",
        "#########",
    ],
    "depart_robot": [1, 1],
    "armoire": {"position": [3, 1]},
    "dictionnaire": {"position": [3, 7]},
    "residents": [{"id": "R1", "nom": "Camille", "position": [1, 7]}],
}

# Résident muré : sa seule case voisine libre (1,6) est enfermée.
CARTE_MUREE = {
    "dimensions": {"hauteur": 4, "largeur": 8},
    "grille": [
        "########",
        "#R...#.#",
        "#AD..#P#",
        "########",
    ],
    "depart_robot": [1, 1],
    "armoire": {"position": [2, 1]},
    "dictionnaire": {"position": [2, 2]},
    "residents": [{"id": "R1", "nom": "Hugo", "position": [2, 6]}],
}


def charger_armoire_standard() -> dict:
    return rio.charger_armoire(RACINE / "donnees" / "armoire_standard.json")


def creer_agent(carte: dict):
    armoire = charger_armoire_standard()
    sim = Simulateur(carte, armoire)
    trace = rio.Trace("test", "test")
    agent = Agent(vue_publique_carte(carte), vue_publique_armoire(armoire), sim, trace)
    return agent, sim, trace


def positions_visitees(trace) -> list:
    resultat = []
    for pas in trace.pas:
        resultat.append(tuple(pas["position"]))
    return resultat


class TestDecision(unittest.TestCase):
    def test_est_adjacent(self):
        self.assertTrue(est_adjacent((1, 1), (1, 2)))
        self.assertTrue(est_adjacent((2, 2), (1, 2)))
        self.assertFalse(est_adjacent((1, 1), (2, 2)))
        self.assertFalse(est_adjacent((1, 1), (1, 1)))

    def test_premiere_direction(self):
        self.assertEqual(premiere_direction([(1, 1), (1, 2), (1, 3)]), "E")
        self.assertEqual(premiere_direction([(2, 2), (1, 2)]), "N")
        self.assertEqual(premiere_direction([(2, 2), (3, 2)]), "S")
        self.assertEqual(premiere_direction([(2, 2), (2, 1)]), "O")
        with self.assertRaises(ValueError):
            premiere_direction([(1, 1), (2, 2)])

    def test_mur_decouvert_change_le_plan(self):
        sim = Simulateur(CARTE_REPLAN, charger_armoire_standard())
        memoire = CarteMentale((5, 9), (3, 1), (3, 7), {"R1": (1, 7)})

        avant = planifier(memoire, (1, 1), (1, 7))
        self.assertIn((1, 4), avant)
        self.assertEqual(len(avant) - 1, 5)

        sim.position = (1, 3)
        memoire.maj((1, 3), sim.percevoir())
        apres = planifier(memoire, (1, 3), (1, 7))
        self.assertNotIn((1, 4), apres)
        self.assertEqual(apres[1], (2, 3))
        self.assertEqual(len(apres) - 1, 5)


class TestAllerVers(unittest.TestCase):
    def test_replanification_en_route(self):
        agent, sim, trace = creer_agent(CARTE_REPLAN)
        self.assertTrue(agent.aller_vers((1, 7)))

        arguments = []
        for pas in trace.pas:
            arguments.append(pas["argument"])
        self.assertEqual(arguments[:3], ["E", "E", "S"])
        self.assertEqual(len(trace.pas), 7)
        self.assertEqual(trace.pas[2]["perception"]["E"], "mur")
        self.assertNotIn((1, 4), positions_visitees(trace))
        self.assertTrue(est_adjacent(agent.position, (1, 7)))
        self.assertEqual(agent.position, sim.position)

    def test_deja_adjacent_aucun_pas(self):
        agent, sim, trace = creer_agent(CARTE_REPLAN)
        self.assertTrue(agent.aller_vers((1, 2)))
        self.assertEqual(len(trace.pas), 0)

    def test_resident_mure(self):
        agent, sim, trace = creer_agent(CARTE_MUREE)
        self.assertFalse(agent.aller_vers((2, 6)))
        self.assertLessEqual(len(trace.pas), 10)
        self.assertEqual(agent.position, sim.position)
        self.assertEqual(agent.memoire.type_case((1, 5)), "mur")
        self.assertEqual(agent.memoire.type_case((2, 5)), "mur")
        self.assertEqual(agent.memoire.type_case((1, 6)), "inconnu")

        nb_pas = len(trace.pas)
        self.assertFalse(agent.aller_vers((2, 6)))
        self.assertEqual(len(trace.pas), nb_pas)

    def test_appartement_01_contourne_le_mur(self):
        carte = rio.charger_carte(RACINE / "cartes" / "appartement_01.json")
        agent, sim, trace = creer_agent(carte)
        self.assertTrue(agent.aller_vers((7, 6)))
        self.assertTrue(agent.aller_vers((6, 11)))
        self.assertEqual(agent.memoire.type_case((6, 7)), "mur")
        self.assertIn((4, 11), positions_visitees(trace))


class TestAction(unittest.TestCase):
    def test_pas_journalise_etat_avant_action(self):
        agent, sim, trace = creer_agent(CARTE_REPLAN)
        agent.demande = {"numero": 3, "resident": "R1"}
        agent.agir("AVANCER", "E")

        pas = trace.pas[0]
        self.assertEqual(pas["t"], 0)
        self.assertEqual(pas["demande"], 3)
        self.assertEqual(pas["position"], [1, 1])
        self.assertEqual(pas["casier"], [1, 0])
        self.assertEqual(pas["perception"], {"N": "mur", "S": "libre", "E": "libre", "O": "mur"})
        self.assertIsNone(pas["contenu_casier"])
        self.assertEqual(agent.position, (1, 2))

    def test_armoire_puis_livraison(self):
        agent, sim, trace = creer_agent(CARTE_REPLAN)
        agent.demande = {"numero": 1, "resident": "R1"}
        self.assertTrue(agent.aller_vers((3, 1)))
        self.assertEqual(agent.contenu_casier, "photo de famille")

        agent.agir("CHERCHER", "O")
        self.assertEqual(trace.pas[-1]["casier"], [1, 0])
        self.assertEqual(trace.pas[-1]["contenu_casier"], "photo de famille")
        self.assertEqual(agent.casier, (1, 7))
        self.assertEqual(agent.contenu_casier, "calendrier")

        agent.agir("PRENDRE", "calendrier")
        self.assertEqual(agent.objet_porte, "calendrier")
        self.assertTrue(agent.aller_vers((1, 7)))
        self.assertIsNone(agent.contenu_casier)
        agent.agir("DONNER", "calendrier")
        self.assertIsNone(agent.objet_porte)
        self.assertIsNone(sim.objet_porte)
        self.assertEqual(trace.pas[-1]["action"], "DONNER")


class TestVuePublique(unittest.TestCase):
    def test_vues_sans_grille_ni_objets(self):
        armoire = charger_armoire_standard()
        vue_carte = vue_publique_carte(CARTE_REPLAN)
        vue_armoire = vue_publique_armoire(armoire)
        self.assertNotIn("grille", vue_carte)
        self.assertIn("grille", CARTE_REPLAN)
        self.assertNotIn("casiers", vue_armoire)
        self.assertEqual(vue_armoire["casier_depart"], armoire["casier_depart"])
        self.assertIn("casiers", armoire)

    def test_agent_refuse_la_vraie_carte(self):
        armoire = charger_armoire_standard()
        sim = Simulateur(CARTE_REPLAN, armoire)
        with self.assertRaises(ValueError):
            Agent(CARTE_REPLAN, vue_publique_armoire(armoire), sim, rio.Trace("t", "t"))


class TestAffichage(unittest.TestCase):
    def test_dessiner(self):
        memoire = CarteMentale((4, 7), (1, 3), (2, 3), {"R1": (1, 5)})
        memoire.maj((1, 1), {"N": "mur", "S": "libre", "E": "libre", "O": "mur"})
        attendu = "\n".join(["#######", "#@*A?P#", "#.*D??#", "#######"])
        self.assertEqual(dessiner(memoire, (1, 1), [(1, 1), (1, 2), (2, 2)]), attendu)


if __name__ == "__main__":
    unittest.main()
