import unittest

from logique import (
    calculer_chemin_casier,
    calculer_distance_roue,
    calculer_sens,
    determiner_repli,
    generer_casiers_candidats,
    trouver_emotion,
)
from tests.test_agent import charger_dictionnaire
from tests.test_gestion_armoire import contenus_reels
from tests.test_navigation import charger_armoire_standard

EMOTIONS = ["joie", "confiance", "peur", "surprise", "tristesse", "degout", "colere", "anticipation"]
INTENSITES = ["faible", "moyenne", "forte"]


def choisir_casier(candidats: list, contenus: dict):
    """§6.2 : le premier candidat garni, ou None (armoire vide)."""
    for casier in candidats:
        if contenus.get(casier) is not None:
            return casier
    return None


def repli_pour(emotion: str, intensite: str, casier: tuple) -> str:
    return determiner_repli(EMOTIONS.index(emotion), INTENSITES.index(intensite), casier[1], casier[0])


def appliquer_chemin(depart: tuple, mouvements: list) -> tuple:
    """Rejoue les mouvements comme le simulateur ; échoue si N en ligne 0 ou S en ligne 2."""
    ligne, colonne = depart
    for mouvement in mouvements:
        if mouvement == "N":
            if ligne == 0:
                raise AssertionError("N depuis la ligne 0")
            ligne -= 1
        elif mouvement == "S":
            if ligne == 2:
                raise AssertionError("S depuis la ligne 2")
            ligne += 1
        elif mouvement == "E":
            colonne = (colonne + 1) % 8
        else:
            colonne = (colonne - 1) % 8
    return (ligne, colonne)


class TestTrouverEmotion(unittest.TestCase):
    def setUp(self):
        self.dictionnaire = charger_dictionnaire()

    def test_un_message_par_emotion(self):
        # Majuscules, accents et ponctuation : passent par normaliser (§6.1 étape 1).
        cas = [
            ("Je suis tellement HEUREUSE aujourd'hui !", ("joie", "moyenne")),
            ("Merci, je vous fais confiance.", ("confiance", "moyenne")),
            ("J'ai l'angoisse de tomber.", ("peur", "moyenne")),
            ("Je suis sidéré, c'est fou.", ("surprise", "forte")),
            ("Un petit cafard ce matin...", ("tristesse", "faible")),
            ("Cette soupe est écoeurante, non : c'est sale.", ("degout", "moyenne")),
            ("Je suis furieux contre l'infirmier", ("colere", "forte")),
            ("Vivement demain, j'ai hâte !", ("anticipation", "moyenne")),
        ]
        for message, attendu in cas:
            with self.subTest(message=message):
                self.assertEqual(trouver_emotion(message, self.dictionnaire), attendu)

    def test_exemple_6_1_premier_mot_gagne(self):
        message = "Je suis sidéré, la télévision s'est allumée toute seule."
        self.assertEqual(trouver_emotion(message, self.dictionnaire), ("surprise", "forte"))

    def test_deux_mots_connus_ordre_du_message(self):
        # Le premier mot du message gagne, pas l'émotion la plus forte ni l'ordre du dictionnaire.
        self.assertEqual(trouver_emotion("Je suis calme mais terrifie", self.dictionnaire), ("joie", "faible"))
        self.assertEqual(trouver_emotion("Je suis terrifie mais calme", self.dictionnaire), ("peur", "forte"))

    def test_annexe_d_demande_1(self):
        message = "Je me sens tellement seule ce soir, personne n'est passé."
        self.assertEqual(trouver_emotion(message, self.dictionnaire), ("tristesse", "moyenne"))

    def test_aucun_mot_connu(self):
        self.assertIsNone(trouver_emotion("Bonjour, quelle heure est-il ?", self.dictionnaire))
        self.assertIsNone(trouver_emotion("", self.dictionnaire))
        self.assertIsNone(trouver_emotion("!!! ... ???", self.dictionnaire))

    def test_mot_entier_seulement(self):
        # "seulement" contient "seul" mais n'est pas le mot "seul".
        self.assertIsNone(trouver_emotion("Seulement une question.", self.dictionnaire))


class TestRoue(unittest.TestCase):
    def test_distance_roue(self):
        self.assertEqual(calculer_distance_roue(3, 3), 0)
        self.assertEqual(calculer_distance_roue(3, 4), 1)
        self.assertEqual(calculer_distance_roue(0, 7), 1)
        self.assertEqual(calculer_distance_roue(7, 1), 2)
        self.assertEqual(calculer_distance_roue(1, 6), 3)
        # Les 4 paires opposées de §6.2.
        self.assertEqual(calculer_distance_roue(0, 4), 4)
        self.assertEqual(calculer_distance_roue(1, 5), 4)
        self.assertEqual(calculer_distance_roue(2, 6), 4)
        self.assertEqual(calculer_distance_roue(3, 7), 4)

    def test_sens_horaire_avec_bouclage(self):
        # 0 = horaire (indices croissants modulo 8), 1 = antihoraire.
        self.assertEqual(calculer_sens(3, 4), 0)
        self.assertEqual(calculer_sens(3, 2), 1)
        self.assertEqual(calculer_sens(7, 0), 0)
        self.assertEqual(calculer_sens(0, 7), 1)
        self.assertEqual(calculer_sens(6, 0), 0)


class TestCandidats(unittest.TestCase):
    def test_annexe_c5_surprise_forte(self):
        attendu = [
            (2, 3), (1, 3), (0, 3),
            (2, 4), (2, 2), (1, 4), (1, 2), (0, 4), (0, 2),
            (2, 5), (2, 1), (1, 5), (1, 1), (0, 5), (0, 1),
        ]
        self.assertEqual(generer_casiers_candidats("surprise", "forte", EMOTIONS, INTENSITES), attendu)

    def test_intensite_la_plus_faible_d_abord(self):
        # Demande moyenne : faible et forte sont à écart 1, faible passe avant (critère 3).
        attendu = [
            (1, 4), (0, 4), (2, 4),
            (1, 5), (1, 3), (0, 5), (0, 3), (2, 5), (2, 3),
            (1, 6), (1, 2), (0, 6), (0, 2), (2, 6), (2, 2),
        ]
        self.assertEqual(generer_casiers_candidats("tristesse", "moyenne", EMOTIONS, INTENSITES), attendu)

    def test_sens_horaire_a_travers_le_bouclage(self):
        # Joie (colonne 0) : la voisine horaire est confiance (1), l'antihoraire anticipation (7).
        attendu = [
            (0, 0), (1, 0), (2, 0),
            (0, 1), (0, 7), (1, 1), (1, 7), (2, 1), (2, 7),
            (0, 2), (0, 6), (1, 2), (1, 6), (2, 2), (2, 6),
        ]
        self.assertEqual(generer_casiers_candidats("joie", "faible", EMOTIONS, INTENSITES), attendu)

    def test_quinze_candidats_distincts_a_distance_2_au_plus(self):
        for emotion in EMOTIONS:
            for intensite in INTENSITES:
                with self.subTest(emotion=emotion, intensite=intensite):
                    candidats = generer_casiers_candidats(emotion, intensite, EMOTIONS, INTENSITES)
                    self.assertEqual(len(candidats), 15)
                    self.assertEqual(len(set(candidats)), 15)
                    self.assertEqual(candidats[0], (INTENSITES.index(intensite), EMOTIONS.index(emotion)))
                    for ligne, colonne in candidats:
                        self.assertLessEqual(calculer_distance_roue(EMOTIONS.index(emotion), colonne), 2)


class TestCheminCasier(unittest.TestCase):
    def test_exemples_c3(self):
        self.assertEqual(calculer_chemin_casier((1, 0), (1, 4)), ["E", "E", "E", "E"])
        self.assertEqual(calculer_chemin_casier((2, 7), (0, 1)), ["N", "N", "E", "E"])
        self.assertEqual(calculer_chemin_casier((1, 0), (2, 6)), ["S", "O", "O"])

    def test_meme_casier(self):
        self.assertEqual(calculer_chemin_casier((2, 5), (2, 5)), [])

    def test_etapes_de_la_fouille_c5(self):
        mouvements = []
        etapes = [(1, 0), (2, 3), (1, 3), (0, 3), (2, 4)]
        for i in range(len(etapes) - 1):
            mouvements = mouvements + calculer_chemin_casier(etapes[i], etapes[i + 1])
        self.assertEqual(mouvements, ["S", "E", "E", "E", "N", "N", "S", "S", "E"])

    def test_tous_les_couples(self):
        # Formule C.3 : |l' - l| + min(a, 8 - a), et le chemin arrive bien sans mouvement illégal.
        casiers = []
        for ligne in range(3):
            for colonne in range(8):
                casiers.append((ligne, colonne))
        for depart in casiers:
            for arrivee in casiers:
                with self.subTest(depart=depart, arrivee=arrivee):
                    chemin = calculer_chemin_casier(depart, arrivee)
                    a = (arrivee[1] - depart[1]) % 8
                    self.assertEqual(len(chemin), abs(arrivee[0] - depart[0]) + min(a, 8 - a))
                    self.assertEqual(appliquer_chemin(depart, chemin), arrivee)


class TestRepli(unittest.TestCase):
    def setUp(self):
        self.contenus = contenus_reels(charger_armoire_standard())

    def choisir(self, emotion: str, intensite: str):
        candidats = generer_casiers_candidats(emotion, intensite, EMOTIONS, INTENSITES)
        return choisir_casier(candidats, self.contenus)

    def test_casier_exact_garni(self):
        casier = self.choisir("tristesse", "moyenne")
        self.assertEqual(casier, (1, 4))
        self.assertEqual(self.contenus[casier], "couverture")
        self.assertEqual(repli_pour("tristesse", "moyenne", casier), "aucun")

    def test_repli_intensite(self):
        # Armoire standard : anticipation/forte [2,7] est vide.
        casier = self.choisir("anticipation", "forte")
        self.assertEqual(casier, (1, 7))
        self.assertEqual(repli_pour("anticipation", "forte", casier), "intensite")

    def test_colonne_vide_voisine_1(self):
        casier = self.choisir("surprise", "forte")
        self.assertEqual(casier, (2, 4))
        self.assertEqual(self.contenus[casier], "telephone")
        self.assertEqual(repli_pour("surprise", "forte", casier), "voisine_1")

    def test_voisine_2(self):
        for casier in generer_casiers_candidats("surprise", "faible", EMOTIONS, INTENSITES)[:9]:
            self.contenus[casier] = None
        casier = self.choisir("surprise", "faible")
        self.assertEqual(casier, (0, 5))
        self.assertEqual(repli_pour("surprise", "faible", casier), "voisine_2")

    def test_rien_a_distance_2_armoire_vide(self):
        for casier in generer_casiers_candidats("joie", "moyenne", EMOTIONS, INTENSITES):
            self.contenus[casier] = None
        # Les colonnes à distance 3 et 4 restent garnies mais ne comptent jamais (§6.2).
        self.assertEqual(self.contenus[(1, 4)], "couverture")
        self.assertIsNone(self.choisir("joie", "moyenne"))

    def test_determiner_repli_bouclage_et_distance_3(self):
        self.assertEqual(determiner_repli(0, 1, 7, 1), "voisine_1")
        self.assertEqual(determiner_repli(0, 1, 6, 0), "voisine_2")
        self.assertEqual(determiner_repli(3, 2, 3, 0), "intensite")
        with self.assertRaises(ValueError):
            determiner_repli(0, 1, 3, 1)


if __name__ == "__main__":
    unittest.main()
