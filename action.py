from __future__ import annotations

from planification import DIRECTIONS


def executer_action(agent, sim, trace, demande, action: str, argument: str | None = None) -> None:
    """Journalise le pas (état AVANT l'action) puis exécute l'action dans le simulateur."""
    numero = None
    resident = None
    if demande is not None:
        numero = demande["numero"]
        resident = demande["resident"]

    trace.ajouter_pas(
        demande=numero,
        position=agent.position,
        casier=agent.casier,
        action=action,
        argument=argument,
        perception=agent.perception,
        contenu_casier=agent.contenu_casier,
    )
    sim.executer(action, argument, resident)
    mettre_a_jour_etat(agent, action, argument)


def mettre_a_jour_etat(agent, action: str, argument: str | None) -> None:
    """Après une action acceptée par le simulateur, l'agent met à jour sa propre position, son sélecteur, son objet."""
    if action == "AVANCER":
        dl, dc = DIRECTIONS[argument]
        agent.position = (agent.position[0] + dl, agent.position[1] + dc)
    elif action == "CHERCHER":
        dl, dc = DIRECTIONS[argument]
        colonne = (agent.casier[1] + dc) % agent.nb_colonnes_armoire
        agent.casier = (agent.casier[0] + dl, colonne)
    elif action == "PRENDRE":
        agent.objet_porte = argument
    elif action == "DONNER":
        agent.objet_porte = None
