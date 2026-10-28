from __future__ import annotations

import time

SYMBOLES = {
    "inconnu": "?",
    "mur": "#",
    "libre": ".",
    "armoire": "A",
    "dictionnaire": "D",
    "resident": "P",
}

EFFACER_ECRAN = "\033[H\033[J"


def dessiner(memoire, position: tuple[int, int], chemin: list | None = None) -> str:
    """La carte mentale en texte : robot '@', chemin prévu '*', case inconnue '?'."""
    cases_chemin = []
    if chemin is not None:
        cases_chemin = chemin[1:]

    lignes = []
    for ligne in range(memoire.hauteur):
        texte = ""
        for colonne in range(memoire.largeur):
            case = (ligne, colonne)
            if case == position:
                texte += "@"
            elif case in cases_chemin:
                texte += "*"
            else:
                texte += SYMBOLES[memoire.type_case(case)]
        lignes.append(texte)
    return "\n".join(lignes)


def afficher(memoire, position, chemin=None, entete: str = "", delai: float = 0.3) -> None:
    """Efface le terminal, redessine la carte mentale puis attend delai secondes."""
    print(EFFACER_ECRAN + entete)
    print(dessiner(memoire, position, chemin))
    time.sleep(delai)
