from __future__ import annotations

from planification import DIRECTIONS, cases_adjacentes, plus_court_chemin


def est_adjacent(position: tuple[int, int], cible: tuple[int, int]) -> bool:
    """Vrai si position et cible sont voisines orthogonales (distance de Manhattan 1)."""
    return abs(position[0] - cible[0]) + abs(position[1] - cible[1]) == 1


def planifier(
    memoire, position: tuple[int, int], cible: tuple[int, int], pessimiste: bool = False
) -> list | None:
    """Plus court chemin sur la carte mentale vers une case adjacente à cible ; None = pas de chemin.

    Optimiste (inconnu = libre) par défaut ; pessimiste = seulement les cases déjà vues libres.
    """
    arrivees = cases_adjacentes(cible, (memoire.hauteur, memoire.largeur))
    est_traversable = memoire.est_traversable
    if pessimiste:
        est_traversable = memoire.est_connue_libre
    return plus_court_chemin(position, arrivees, est_traversable)


def premiere_direction(chemin: list) -> str:
    """Direction (N, S, E ou O) du premier pas du chemin."""
    depart = chemin[0]
    suivante = chemin[1]
    for direction in DIRECTIONS:
        dl, dc = DIRECTIONS[direction]
        if (depart[0] + dl, depart[1] + dc) == suivante:
            return direction
    raise ValueError(f"{depart} et {suivante} ne sont pas voisines")
