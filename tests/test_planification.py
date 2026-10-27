import unittest

from planification import cases_adjacentes, plus_court_chemin, voisines

GRILLE_B3 = [
    "######",
    "#R.#.#",
    "#.#..#",
    "#...##",
    "######",
]


class GrilleConnue:
    """Grille entièrement connue, pour tester le BFS sans carte mentale."""

    def __init__(self, lignes: list[str]):
        self.lignes = lignes

    def est_traversable(self, pos: tuple[int, int]) -> bool:
        ligne, colonne = pos
        if not (0 <= ligne < len(self.lignes) and 0 <= colonne < len(self.lignes[0])):
            return False
        return self.lignes[ligne][colonne] in ".R"


class TestPlusCourtChemin(unittest.TestCase):
    def setUp(self):
        self.grille = GrilleConnue(GRILLE_B3)

    def test_exemple_b3_sept_pas(self):
        chemin = plus_court_chemin((1, 1), [(1, 4)], self.grille.est_traversable)
        attendu = [(1, 1), (2, 1), (3, 1), (3, 2), (3, 3), (2, 3), (2, 4), (1, 4)]
        self.assertEqual(chemin, attendu)
        self.assertEqual(len(chemin) - 1, 7)

    def test_depart_deja_arrivee(self):
        chemin = plus_court_chemin(
            (1, 1), [(3, 3), (1, 1)], self.grille.est_traversable
        )
        self.assertEqual(chemin, [(1, 1)])

    def test_aucun_chemin(self):
        grille = GrilleConnue(
            [
                "#####",
                "#R#.#",
                "#####",
            ]
        )
        self.assertIsNone(plus_court_chemin((1, 1), [(1, 3)], grille.est_traversable))

    def test_arrivee_non_traversable(self):
        self.assertIsNone(
            plus_court_chemin((1, 1), [(1, 3)], self.grille.est_traversable)
        )

    def test_plusieurs_arrivees_prend_la_plus_proche(self):
        chemin = plus_court_chemin(
            (1, 1), [(1, 4), (3, 2)], self.grille.est_traversable
        )
        self.assertEqual(chemin, [(1, 1), (2, 1), (3, 1), (3, 2)])

    def test_ordre_n_s_e_o_departage_les_egalites(self):
        grille = GrilleConnue(
            [
                "#####",
                "#...#",
                "#.R.#",
                "#...#",
                "#####",
            ]
        )
        chemin = plus_court_chemin((2, 2), [(3, 3), (1, 1)], grille.est_traversable)
        self.assertEqual(chemin, [(2, 2), (1, 2), (1, 1)])


class TestCasesAdjacentes(unittest.TestCase):
    def test_voisines_ordre(self):
        self.assertEqual(voisines((2, 3)), [(1, 3), (3, 3), (2, 4), (2, 2)])

    def test_cases_adjacentes_milieu(self):
        self.assertEqual(
            cases_adjacentes((2, 3), (5, 6)), [(1, 3), (3, 3), (2, 4), (2, 2)]
        )

    def test_cases_adjacentes_coin(self):
        self.assertEqual(cases_adjacentes((0, 0), (5, 6)), [(1, 0), (0, 1)])


if __name__ == "__main__":
    unittest.main()
