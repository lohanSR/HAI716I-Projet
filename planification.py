from __future__ import annotations

from collections import deque

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}


def voisines(pos: tuple[int, int]) -> list[tuple[int, int]]:
    """Les 4 cases orthogonales de pos, dans l'ordre N, S, E, O (sans vérifier les bords)."""
    resultat = []
    for direction in DIRECTIONS:
        dl, dc = DIRECTIONS[direction]
        resultat.append((pos[0] + dl, pos[1] + dc))
    return resultat


def cases_adjacentes(
    cible: tuple[int, int], dimensions: tuple[int, int]
) -> list[tuple[int, int]]:
    """Les voisines de cible qui sont dans la grille (hauteur, largeur)."""
    hauteur, largeur = dimensions
    resultat = []
    for ligne, colonne in voisines(cible):
        if 0 <= ligne < hauteur and 0 <= colonne < largeur:
            resultat.append((ligne, colonne))
    return resultat


def plus_court_chemin(
    depart, arrivees, est_traversable
) -> list[tuple[int, int]] | None:
    """BFS (annexe B.4) : chemin [depart, ..., arrivée] vers la plus proche des arrivées, ou None."""
    if depart in arrivees:
        return [depart]

    predecesseur = {depart: None}
    file = deque([depart])

    while len(file) > 0:
        courant = file.popleft()
        for voisin in voisines(courant):
            if voisin in predecesseur:
                continue
            if not est_traversable(voisin):
                continue
            predecesseur[voisin] = courant
            if voisin in arrivees:
                return reconstruire(predecesseur, voisin)
            file.append(voisin)

    return None


def reconstruire(predecesseur: dict, case: tuple[int, int]) -> list[tuple[int, int]]:
    """Remonte les prédécesseurs depuis case jusqu'au départ, puis inverse."""
    chemin = [case]
    while predecesseur[chemin[-1]] is not None:
        chemin.append(predecesseur[chemin[-1]])
    chemin.reverse()
    return chemin
