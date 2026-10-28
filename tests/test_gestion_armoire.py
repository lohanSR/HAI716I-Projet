import unittest

from gestion_armoire import EtatArmoire
from planification import DIRECTIONS
from tests.test_navigation import charger_armoire_standard


def contenus_reels(armoire: dict) -> dict:
    """Vérité terrain (côté test uniquement) : casier → objet ou None."""
    contenus = {}
    for casier in armoire["casiers"]:
        contenus[(casier["ligne"], casier["colonne"])] = casier["objet"]
    return contenus


def fouiller(etat, casier, contenus, emotion, intensite) -> list:
    """Joue la fouille tick par tick comme l'agent : mémoriser le casier visible, puis une action."""
    etat.nouvelle_fouille(emotion, intensite)
    actions = []
    while True:
        etat.memoriser(casier, contenus.get(casier))
        action, argument = etat.prochaine_action(casier)
        actions.append((casier, action, argument))
        if action != "CHERCHER":
            return actions
        dl, dc = DIRECTIONS[argument]
        casier = (casier[0] + dl, (casier[1] + dc) % 8)


class TestEtatArmoire(unittest.TestCase):
    def setUp(self):
        armoire = charger_armoire_standard()
        self.contenus = contenus_reels(armoire)
        self.etat = EtatArmoire(armoire["emotions"], armoire["intensites"])

    def test_annexe_c5_colonne_surprise_vide(self):
        actions = fouiller(self.etat, (1, 0), self.contenus, "surprise", "forte")
        directions = []
        for casier, action, argument in actions[:-1]:
            directions.append(argument)
        self.assertEqual(directions, ["S", "E", "E", "E", "N", "N", "S", "S", "E"])
        # [2,2] peur/forte est garni et traversé au 4e mouvement, mais tristesse/forte est prioritaire.
        self.assertEqual(actions[-1], ((2, 4), "PRENDRE", "telephone"))
        self.assertEqual(self.etat.repli((2, 4)), "voisine_1")

    def test_annexe_d_casier_exact(self):
        actions = fouiller(self.etat, (1, 0), self.contenus, "tristesse", "moyenne")
        self.assertEqual(len(actions), 5)
        self.assertEqual(actions[-1], ((1, 4), "PRENDRE", "couverture"))
        self.assertEqual(self.etat.repli((1, 4)), "aucun")

    def test_repli_intensite(self):
        self.contenus[(2, 7)] = None
        actions = fouiller(self.etat, (1, 7), self.contenus, "anticipation", "forte")
        self.assertEqual(actions[0], ((1, 7), "CHERCHER", "S"))
        self.assertEqual(actions[-1], ((1, 7), "PRENDRE", "calendrier"))
        self.assertEqual(self.etat.repli((1, 7)), "intensite")

    def test_memoire_videe_a_chaque_demande(self):
        fouiller(self.etat, (1, 0), self.contenus, "surprise", "forte")
        # Nouvelle demande : [2,3] a été vu vide avant, mais il faut repasser devant (§6.2).
        actions = fouiller(self.etat, (2, 4), self.contenus, "surprise", "forte")
        self.assertEqual(actions[0], ((2, 4), "CHERCHER", "O"))
        self.assertEqual(actions[-1], ((2, 4), "PRENDRE", "telephone"))

    def test_armoire_vide(self):
        vide = {}
        actions = fouiller(self.etat, (1, 0), vide, "joie", "faible")
        self.assertEqual(actions[-1][1:], ("ECHEC", "armoire vide"))
        vus = set()
        for casier, action, argument in actions:
            vus.add(casier)
        for candidat in self.etat.candidats:
            self.assertIn(candidat, vus)


if __name__ == "__main__":
    unittest.main()
