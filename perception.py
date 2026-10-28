from __future__ import annotations

from decision import est_adjacent


def percevoir(agent, sim) -> None:
    """Reçoit les 4 cases voisines et le casier courant, puis les inscrit dans la mémoire de l'agent (carte + armoire)."""
    agent.perception = sim.percevoir()
    agent.contenu_casier = sim.contenu_casier()
    agent.memoire.maj(agent.position, agent.perception)
    if est_adjacent(agent.position, agent.pos_armoire):
        agent.etat_armoire.memoriser(agent.casier, agent.contenu_casier)
