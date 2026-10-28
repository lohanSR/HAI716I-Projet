import copy
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import reconfort_io as rio
import validation

RACINE = Path(__file__).resolve().parent.parent
CASSES = RACINE / "tests" / "fichiers_casses"
CARTE = RACINE / "cartes" / "appartement_01.json"
SCENARIO = RACINE / "cartes" / "scenario_01.json"
DICTIONNAIRE = RACINE / "donnees" / "dictionnaire.json"
ARMOIRE = RACINE / "donnees" / "armoire_standard.json"

# (fichier cassé, morceau attendu dans le message d'erreur) : une altération par fichier, catégories du §5.6
CARTES_CASSEES = [
    ("carte_non_utf8.json", "UTF-8"),
    ("carte_json_invalide.json", "pas un JSON valide"),
    ("carte_format.json", "format attendu"),
    ("carte_version.json", "version 1 attendue"),
    ("carte_version_booleen.json", "version 1 attendue, trouve True"),
    ("carte_champ_absent.json", "champ 'residents' manquant"),
    ("carte_mauvais_type.json", "doivent être des entiers"),
    ("carte_non_rectangulaire.json", "pas rectangulaire"),
    ("carte_dimensions.json", "ne correspond pas à 'hauteur'"),
    ("carte_hors_grille.json", "hors limites"),
    ("carte_resident_sur_mur.json", "resident R2 : position ne correspond pas"),
    ("carte_depart_faux.json", "Robot : position ne correspond pas"),
    ("carte_armoire_faux.json", "Armoire : position ne correspond pas"),
    ("carte_dictionnaire_faux.json", "Dictionnaire : position ne correspond pas"),
    ("carte_id_double.json", "'R1' présent plusieurs fois"),
]
SCENARIOS_CASSES = [
    ("scenario_autre_carte.json", "'carte' doit correspondre"),
    ("scenario_resident_absent.json", "'R9' n'existe pas"),
    ("scenario_champ_absent.json", "champ 'message' manquant"),
    ("scenario_armoire_absente.json", "armoire_inexistante.json"),
]
DICTIONNAIRES_CASSES = [
    ("dictionnaire_emotion_inconnue.json", "'emotion' doit être l'une"),
    ("dictionnaire_intensite_inconnue.json", "'intensite' doit être l'une"),
    ("dictionnaire_mot_double.json", "'apaise' présente dans deux entrées"),
    ("dictionnaire_emotions_liste.json", "'emotions' doit être"),
]
ARMOIRES_CASSEES = [
    ("armoire_casier_hors.json", "'ligne' doit être compris entre 0 et 2"),
    ("armoire_casier_double.json", "casier en double"),
    ("armoire_etiquette.json", "émotion incohérente"),
    ("armoire_depart_hors.json", "'casier_depart[1]'"),
    ("armoire_mauvais_type.json", "'objet' doit être"),
]


class TestFichiersCasses(unittest.TestCase):
    """Chaque fichier cassé : code ≠ 0, message clair sur stderr, pas de traceback, aucune trace écrite."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.dossier = Path(dossier.name)
        self.trace = self.dossier / "trace.json"

    def lancer(self, carte, scenario, dictionnaire=DICTIONNAIRE, armoire=ARMOIRE, donnees=None):
        """Lance agent.py dans un sous-processus ; dossier de données recopié avec les fichiers choisis."""
        if donnees is None:
            donnees = self.dossier / "donnees"
            shutil.rmtree(donnees, ignore_errors=True)
            donnees.mkdir()
            shutil.copy(dictionnaire, donnees / "dictionnaire.json")
            shutil.copy(armoire, donnees / "armoire_standard.json")
        # sinon la trace d'un fichier accepté à tort ferait échouer tous les sous-tests suivants
        if self.trace.exists():
            self.trace.unlink()
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        commande = [sys.executable, "agent.py", str(carte), str(scenario), str(donnees), str(self.trace)]
        return subprocess.run(
            commande, cwd=RACINE, env=env, capture_output=True, text=True, encoding="utf-8"
        )

    def verifier_rejet(self, resultat, morceau):
        self.assertNotEqual(resultat.returncode, 0)
        self.assertIn(morceau, resultat.stderr)
        self.assertNotIn("Traceback", resultat.stderr)
        self.assertFalse(self.trace.exists())

    def test_fichiers_valides_trace_ecrite(self):
        # témoin : sans ce test, un lancer() cassé ferait passer tous les autres
        resultat = self.lancer(CARTE, SCENARIO)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        self.assertTrue(self.trace.exists())

    def test_cartes_cassees(self):
        for nom, morceau in CARTES_CASSEES:
            with self.subTest(fichier=nom):
                self.verifier_rejet(self.lancer(CASSES / nom, SCENARIO), morceau)

    def test_scenarios_casses(self):
        for nom, morceau in SCENARIOS_CASSES:
            with self.subTest(fichier=nom):
                self.verifier_rejet(self.lancer(CARTE, CASSES / nom), morceau)

    def test_dictionnaires_casses(self):
        for nom, morceau in DICTIONNAIRES_CASSES:
            with self.subTest(fichier=nom):
                resultat = self.lancer(CARTE, SCENARIO, dictionnaire=CASSES / nom)
                self.verifier_rejet(resultat, morceau)

    def test_armoires_cassees(self):
        for nom, morceau in ARMOIRES_CASSEES:
            with self.subTest(fichier=nom):
                resultat = self.lancer(CARTE, SCENARIO, armoire=CASSES / nom)
                self.verifier_rejet(resultat, morceau)

    def test_fichier_absent(self):
        self.verifier_rejet(self.lancer(CASSES / "absent.json", SCENARIO), "introuvable")

    def test_dossier_donnees_absent(self):
        resultat = self.lancer(CARTE, SCENARIO, donnees=self.dossier / "absent")
        self.verifier_rejet(resultat, "introuvable")

    def test_fichier_illisible(self):
        # un dossier à la place du fichier : lecture impossible (OSError)
        self.verifier_rejet(self.lancer(CASSES, SCENARIO), "illisible")

    def test_tous_les_fichiers_casses_sont_testes(self):
        listes = CARTES_CASSEES + SCENARIOS_CASSES + DICTIONNAIRES_CASSES + ARMOIRES_CASSEES
        testes = set()
        for nom, morceau in listes:
            testes.add(nom)
        presents = set()
        for chemin in CASSES.iterdir():
            presents.add(chemin.name)
        self.assertEqual(testes, presents)


class TestPasDeRejetEnTrop(unittest.TestCase):
    """Un fichier valide ne doit pas être refusé pour une règle absente du §5.6."""

    def setUp(self):
        self.dictionnaire = rio.charger_dictionnaire(DICTIONNAIRE)

    def test_formes_non_alphabetiques_acceptees(self):
        dico = copy.deepcopy(self.dictionnaire)
        dico["entrees"].append(
            {"formes": ["aujourd'hui", "Café", "k2"], "emotion": "joie", "intensite": "forte"}
        )
        validation.valider_dictionnaire(dico)

    def test_forme_repetee_dans_une_seule_entree_acceptee(self):
        dico = copy.deepcopy(self.dictionnaire)
        dico["entrees"][0]["formes"].append(dico["entrees"][0]["formes"][0])
        validation.valider_dictionnaire(dico)

    def test_forme_dans_deux_entrees_refusee(self):
        dico = copy.deepcopy(self.dictionnaire)
        dico["entrees"][1]["formes"].append(dico["entrees"][0]["formes"][0])
        with self.assertRaises(rio.ErreurFichier):
            validation.valider_dictionnaire(dico)


if __name__ == "__main__":
    unittest.main()
