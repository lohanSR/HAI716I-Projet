import json
import tempfile
import unittest
from pathlib import Path

from agent import charger_entrees
from tests.test_agent import lancer
from verifier_trace import Verificateur

RACINE = Path(__file__).resolve().parent.parent
CARTES = RACINE / "tests" / "cartes"
DONNEES = str(RACINE / "donnees")
DONNEES_TEST = str(RACINE / "tests" / "donnees_test")

# Carte → (dossier de données, motif attendu pour chaque demande, None = réussie).
CAS = {
    "grande_plate": (DONNEES, [None, None, None, None, None, None]),
    "impasses": (DONNEES, [None, None, None]),
    "acces_difficile": (DONNEES, [None, None, None]),
    "resident_mure": (DONNEES, [None, "resident inaccessible", None, "resident inaccessible"]),
    "dictionnaire_inaccessible": (DONNEES, ["dictionnaire inaccessible", "dictionnaire inaccessible"]),
    "armoire_inaccessible": (DONNEES, ["armoire inaccessible", "emotion indeterminee", "armoire inaccessible"]),
    "salle_trouee": (DONNEES_TEST, [
        None, None, None, None, "armoire vide", "emotion indeterminee", None, "armoire vide",
    ]),
}


def pas_de_la_demande(trace: dict, numero: int) -> list:
    resultat = []
    for pas in trace["pas"]:
        if pas["demande"] == numero:
            resultat.append(pas)
    return resultat


class TestCartesPerso(unittest.TestCase):
    """Chaque carte de tests/cartes/ jouée par agent.py puis rejouée par le vérificateur."""

    @classmethod
    def setUpClass(cls):
        cls.dossier = tempfile.TemporaryDirectory()
        cls.traces = {}
        cls.codes = {}
        for nom in CAS:
            donnees = CAS[nom][0]
            sortie = Path(cls.dossier.name) / f"trace_{nom}.json"
            code, erreurs = lancer([
                str(CARTES / f"{nom}.json"), str(CARTES / f"scenario_{nom}.json"), donnees, str(sortie),
            ])
            cls.codes[nom] = (code, erreurs)
            if sortie.exists():
                cls.traces[nom] = json.loads(sortie.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.dossier.cleanup()

    def test_toutes_les_cartes_sont_testees(self):
        noms = set()
        for chemin in CARTES.glob("*.json"):
            if not chemin.name.startswith("scenario_"):
                noms.add(chemin.stem)
        self.assertEqual(noms, set(CAS))

    def test_traces_conformes(self):
        for nom in CAS:
            with self.subTest(carte=nom):
                self.assertEqual(self.codes[nom], (0, ""))
                carte, scenario, dictionnaire, armoire = charger_entrees(
                    str(CARTES / f"{nom}.json"), str(CARTES / f"scenario_{nom}.json"), CAS[nom][0]
                )
                erreurs = Verificateur(carte, scenario, dictionnaire, armoire, self.traces[nom]).verifier()
                self.assertEqual(erreurs, [])

    def test_motifs_attendus(self):
        for nom in CAS:
            with self.subTest(carte=nom):
                motifs = []
                for livraison in self.traces[nom]["livraisons"]:
                    motifs.append(livraison["motif_echec"])
                self.assertEqual(motifs, CAS[nom][1])

    def test_replis_armoire_trouee(self):
        # Seules les colonnes tristesse et degout sont garnies, et [1,5] est vide.
        attendu = [
            ([1, 4], "aucun"), ([0, 5], "intensite"), ([2, 4], "voisine_1"), ([0, 4], "voisine_2"),
            (None, "aucun"), (None, "aucun"), ([2, 5], "voisine_1"), (None, "aucun"),
        ]
        obtenu = []
        for livraison in self.traces["salle_trouee"]["livraisons"]:
            obtenu.append((livraison["casier_choisi"], livraison["repli"]))
        self.assertEqual(obtenu, attendu)

    def test_armoire_vide_journalise_le_dernier_casier(self):
        # Le 15e casier n'est vu qu'après le dernier CHERCHER : un pas de plus le met dans la trace.
        trace = self.traces["salle_trouee"]
        for numero in (5, 8):
            dernier = pas_de_la_demande(trace, numero)[-1]
            self.assertEqual(dernier["action"], "ATTENDRE")
            self.assertIsNone(dernier["contenu_casier"])
        self.assertEqual(trace["pas"][-1]["demande"], 8)

    def test_preuves_gardees_en_memoire(self):
        # Une fois l'inaccessibilité prouvée, la même demande ne coûte plus de pas pour rien.
        livraisons = self.traces["dictionnaire_inaccessible"]["livraisons"]
        self.assertEqual(livraisons[1]["pas_utilises"], 0)
        livraisons = self.traces["armoire_inaccessible"]["livraisons"]
        self.assertEqual(livraisons[2]["pas_utilises"], 1)

    def test_resident_mure_rien_pris(self):
        trace = self.traces["resident_mure"]
        for numero in (2, 4):
            for pas in pas_de_la_demande(trace, numero):
                self.assertNotIn(pas["action"], ("CHERCHER", "PRENDRE", "DONNER"))


if __name__ == "__main__":
    unittest.main()
