from __future__ import annotations


def percevoir(agent, sim) -> None:
    """Reçoit les 4 cases voisines et le casier courant, puis les inscrit dans la mémoire de l'agent."""
    agent.perception = sim.percevoir()
    agent.contenu_casier = sim.contenu_casier()
    agent.memoire.maj(agent.position, agent.perception)
