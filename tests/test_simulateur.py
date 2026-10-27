import unittest
from pathlib import Path

import reconfort_io as rio
from simulateur import ActionIllegale, Simulateur

RACINE = Path(__file__).resolve().parent.parent

# Petite carte faite à la main :
#   (1,2) adjacent à l'armoire, (2,2) adjacent au dictionnaire,
#   (1,4) adjacent à l'armoire et au résident R1.
CARTE_MINI = {
    "grille": [
        "#######",
        "#R.A.P#",
        "#..D..#",
        "#######",
    ],
    "depart_robot": [1, 1],
    "armoire": {"position": [1, 3]},
    "dictionnaire": {"position": [2, 3]},
    "residents": [{"id": "R1", "nom": "Camille", "position": [1, 5]}],
}


def charger_armoire_standard() -> dict:
    return rio.charger_armoire(RACINE / "donnees" / "armoire_standard.json")


class TestPerception(unittest.TestCase):
    def setUp(self):
        self.sim = Simulateur(CARTE_MINI, charger_armoire_standard())

    def test_type_case(self):
        self.assertEqual(self.sim.type_case((0, 0)), "mur")
        self.assertEqual(self.sim.type_case((1, 1)), "libre")
        self.assertEqual(self.sim.type_case((1, 2)), "libre")
        self.assertEqual(self.sim.type_case((1, 3)), "armoire")
        self.assertEqual(self.sim.type_case((2, 3)), "dictionnaire")
        self.assertEqual(self.sim.type_case((1, 5)), "resident")
        self.assertEqual(self.sim.type_case((-1, 2)), "mur")
        self.assertEqual(self.sim.type_case((1, 99)), "mur")

    def test_percevoir_depart(self):
        self.assertEqual(self.sim.percevoir(), {"N": "mur", "S": "libre", "E": "libre", "O": "mur"})

    def test_percevoir_devant_armoire_et_resident(self):
        self.sim.position = (1, 4)
        self.assertEqual(self.sim.percevoir(), {"N": "mur", "S": "libre", "E": "resident", "O": "armoire"})

    def test_percevoir_appartement_01(self):
      
        carte = rio.charger_carte(RACINE / "cartes" / "appartement_01.json")
        sim = Simulateur(carte, charger_armoire_standard())
        self.assertEqual(sim.position, (6, 1))
        self.assertEqual(sim.selecteur, (1, 0))
        self.assertEqual(sim.percevoir(), {"N": "libre", "S": "libre", "E": "libre", "O": "mur"})

    def test_adjacent_a(self):
        self.sim.position = (1, 2)
        self.assertTrue(self.sim.adjacent_a((1, 3)))
        self.assertFalse(self.sim.adjacent_a((2, 3)))
        self.assertFalse(self.sim.adjacent_a((1, 2)))

    def test_contenu_casier_seulement_devant_armoire(self):
        self.assertIsNone(self.sim.contenu_casier())
        self.sim.position = (1, 2)
        self.assertEqual(self.sim.contenu_casier(), "photo de famille")
        self.sim.selecteur = (1, 3)
        self.assertIsNone(self.sim.contenu_casier())


class TestAvancer(unittest.TestCase):
    def setUp(self):
        self.sim = Simulateur(CARTE_MINI, charger_armoire_standard())

    def test_avancer_case_libre(self):
        self.sim.executer("AVANCER", "E")
        self.assertEqual(self.sim.position, (1, 2))
        self.sim.executer("AVANCER", "S")
        self.assertEqual(self.sim.position, (2, 2))

    def test_avancer_cases_non_traversables(self):
        cas = [
            ((1, 1), "N"),
            ((1, 2), "E"),
            ((2, 2), "E"),
            ((1, 4), "E"),
        ]
        for position, direction in cas:
            with self.subTest(position=position, direction=direction):
                self.sim.position = position
                with self.assertRaises(ActionIllegale):
                    self.sim.executer("AVANCER", direction)
                self.assertEqual(self.sim.position, position)

    def test_direction_invalide(self):
        for argument in (None, "X", "n"):
            with self.subTest(argument=argument), self.assertRaises(ActionIllegale):
                self.sim.executer("AVANCER", argument)

    def test_action_inconnue_et_attendre(self):
        with self.assertRaises(ActionIllegale):
            self.sim.executer("VOLER", "N")
        self.sim.executer("ATTENDRE")
        self.assertEqual(self.sim.position, (1, 1))


class TestConsulter(unittest.TestCase):
    def test_consulter(self):
        sim = Simulateur(CARTE_MINI, charger_armoire_standard())
        with self.assertRaises(ActionIllegale):
            sim.executer("CONSULTER")
        sim.position = (2, 2)
        sim.executer("CONSULTER")


class TestChercher(unittest.TestCase):
    def setUp(self):
        self.sim = Simulateur(CARTE_MINI, charger_armoire_standard())
        self.sim.position = (1, 2)

    def test_chercher_loin_de_armoire(self):
        self.sim.position = (2, 2)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("CHERCHER", "E")
        self.assertEqual(self.sim.selecteur, (1, 0))

    def test_chercher_deplace_selecteur(self):
        self.sim.executer("CHERCHER", "E")
        self.assertEqual(self.sim.selecteur, (1, 1))
        self.sim.executer("CHERCHER", "S")
        self.assertEqual(self.sim.selecteur, (2, 1))
        self.assertEqual(self.sim.contenu_casier(), "album souvenir")

    def test_colonnes_bouclent(self):
        self.sim.executer("CHERCHER", "O")
        self.assertEqual(self.sim.selecteur, (1, 7))
        self.assertEqual(self.sim.contenu_casier(), "calendrier")
        self.sim.executer("CHERCHER", "E")
        self.assertEqual(self.sim.selecteur, (1, 0))

    def test_lignes_ne_bouclent_pas(self):
        self.sim.selecteur = (0, 4)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("CHERCHER", "N")
        self.assertEqual(self.sim.selecteur, (0, 4))
        self.sim.selecteur = (2, 4)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("CHERCHER", "S")
        self.assertEqual(self.sim.selecteur, (2, 4))


class TestPrendreDonner(unittest.TestCase):
    def setUp(self):
        self.sim = Simulateur(CARTE_MINI, charger_armoire_standard())
        self.sim.position = (1, 4)

    def test_prendre_puis_donner(self):
        self.sim.executer("PRENDRE", "photo de famille")
        self.assertEqual(self.sim.objet_porte, "photo de famille")
        self.assertEqual(self.sim.contenu_casier(), "photo de famille")
        self.sim.executer("DONNER", "photo de famille", resident="R1")
        self.assertIsNone(self.sim.objet_porte)

    def test_prendre_illegal(self):
        self.sim.selecteur = (1, 3)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("PRENDRE", None)
        self.sim.selecteur = (1, 0)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("PRENDRE", "plaid")
        self.sim.position = (2, 4)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("PRENDRE", "photo de famille")
        self.assertIsNone(self.sim.objet_porte)

    def test_prendre_mains_pleines(self):
        self.sim.executer("PRENDRE", "photo de famille")
        self.sim.executer("CHERCHER", "E")
        with self.assertRaises(ActionIllegale):
            self.sim.executer("PRENDRE", "plaid")
        self.assertEqual(self.sim.objet_porte, "photo de famille")

    def test_donner_illegal(self):
        with self.assertRaises(ActionIllegale):
            self.sim.executer("DONNER", "plaid", resident="R1")
        self.sim.executer("PRENDRE", "photo de famille")
        with self.assertRaises(ActionIllegale):
            self.sim.executer("DONNER", "plaid", resident="R1")
        with self.assertRaises(ActionIllegale):
            self.sim.executer("DONNER", "photo de famille", resident="R2")
        with self.assertRaises(ActionIllegale):
            self.sim.executer("DONNER", "photo de famille")
        self.sim.position = (1, 2)
        with self.assertRaises(ActionIllegale):
            self.sim.executer("DONNER", "photo de famille", resident="R1")
        self.assertEqual(self.sim.objet_porte, "photo de famille")


if __name__ == "__main__":
    unittest.main()
