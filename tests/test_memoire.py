import unittest
from pathlib import Path

import reconfort_io as rio
from memoire import CarteMentale
from planification import cases_adjacentes, plus_court_chemin
from simulateur import Simulateur

RACINE = Path(__file__).resolve().parent.parent


def nouvelle_carte() -> CarteMentale:
    return CarteMentale((4, 7), (1, 3), (2, 3), {"R1": (1, 5)})


class TestCarteMentale(unittest.TestCase):
    def test_etat_initial(self):
        memoire = nouvelle_carte()
        self.assertEqual(memoire.type_case((1, 1)), "inconnu")
        self.assertEqual(memoire.type_case((1, 3)), "armoire")
        self.assertEqual(memoire.type_case((2, 3)), "dictionnaire")
        self.assertEqual(memoire.type_case((1, 5)), "resident")
        self.assertEqual(memoire.type_case((-1, 0)), "mur")
        self.assertEqual(memoire.type_case((4, 0)), "mur")

    def test_bord_connu_comme_mur(self):
        memoire = nouvelle_carte()
        self.assertEqual(memoire.type_case((0, 0)), "mur")
        self.assertEqual(memoire.type_case((0, 4)), "mur")
        self.assertEqual(memoire.type_case((3, 2)), "mur")
        self.assertEqual(memoire.type_case((2, 6)), "mur")
        self.assertEqual(memoire.type_case((2, 5)), "inconnu")

    def test_maj(self):
        memoire = nouvelle_carte()
        memoire.maj((1, 1), {"N": "mur", "S": "libre", "E": "libre", "O": "mur"})
        self.assertEqual(memoire.type_case((1, 1)), "libre")
        self.assertEqual(memoire.type_case((0, 1)), "mur")
        self.assertEqual(memoire.type_case((2, 1)), "libre")
        self.assertEqual(memoire.type_case((1, 2)), "libre")
        self.assertEqual(memoire.type_case((1, 0)), "mur")
        self.assertEqual(memoire.type_case((2, 2)), "inconnu")

    def test_est_traversable_optimiste(self):
        memoire = nouvelle_carte()
        memoire.maj((1, 1), {"N": "mur", "S": "libre", "E": "libre", "O": "mur"})
        self.assertTrue(memoire.est_traversable((2, 1)))
        self.assertTrue(memoire.est_traversable((2, 5)))
        self.assertFalse(memoire.est_traversable((3, 6)))
        self.assertFalse(memoire.est_traversable((0, 1)))
        self.assertFalse(memoire.est_traversable((1, 3)))
        self.assertFalse(memoire.est_traversable((2, 3)))
        self.assertFalse(memoire.est_traversable((1, 5)))
        self.assertFalse(memoire.est_traversable((-1, 1)))
        self.assertFalse(memoire.est_traversable((1, 7)))


class TestBfsSurCarteMentale(unittest.TestCase):
    def test_chemin_vers_le_dictionnaire_appartement_01(self):
        carte = rio.charger_carte(RACINE / "cartes" / "appartement_01.json")
        armoire = rio.charger_armoire(RACINE / "donnees" / "armoire_standard.json")
        sim = Simulateur(carte, armoire)
        dimensions = (carte["dimensions"]["hauteur"], carte["dimensions"]["largeur"])
        memoire = CarteMentale(
            dimensions, sim.pos_armoire, sim.pos_dictionnaire, sim.residents
        )
        memoire.maj(sim.position, sim.percevoir())

        arrivees = cases_adjacentes(sim.pos_dictionnaire, dimensions)
        chemin = plus_court_chemin(sim.position, arrivees, memoire.est_traversable)
        self.assertEqual(chemin[0], sim.position)
        self.assertIn(chemin[-1], arrivees)
        self.assertEqual(len(chemin) - 1, 5)
        self.assertNotIn(sim.pos_armoire, chemin)


if __name__ == "__main__":
    unittest.main()
