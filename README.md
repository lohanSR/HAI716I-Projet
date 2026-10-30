# Robot de réconfort — MAHDI Abderaouf & SERRE Lohan

Projet de semestre, master informatique (HAI716I). Un robot à perception locale
consulte un dictionnaire, fouille une armoire et rapporte un objet à un
résident.

Langage : Python — Version : **3.8 ou plus** (développé et testé sous 3.12)

## Lancer

```
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

Exemple :

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json
```

Dépendances : *aucune*. Le projet utilise uniquement la bibliothèque standard de Python.

Il est possible d'ajouter --afficher à la fin de la commande pour suivre les déplacements du robot dans le terminal.

## Tester

```
python -m unittest discover -s tests -v
```

Nous avons réalisé des tests automatisés. Ils vérifient notamment la navigation, la découverte des obstacles, la reconnaissance des émotions, la recherche dans l'armoire et la validation des fichiers JSON. Certains tests vérifient aussi le déroulement complet d'une demande.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent.py` | Programme principal qui organise les demandes du robot |
| `perception.py` | Récupère les informations visibles autour du robot |
| `memoire.py` | Conserve les informations découvertes sur l'appartement |
| `planification.py` | Calcule les chemins avec l'algorithme BFS |
| `decision.py` | Choisit la prochaine direction du robot |
| `action.py` | Exécute les actions et les ajoute à la trace |
| `logique.py` | Reconnaît les émotions et définit l'ordre de recherche des casiers |
| `gestion_armoire.py` | Gère les mouvements du sélecteur et la mémoire des casiers |
| `validation.py` | Vérifie les fichiers JSON avant le lancement |
| `simulateur.py` | Gère l'environnement et vérifie les actions du robot |
| `affichage.py` | Affiche la carte mentale dans le terminal |
| `reconfort_io.py` | Contient les fonctions de lecture et d'écriture des fichiers |
| `tests/` | Contient les tests et les scénarios supplémentaires |

## État

**Ce qui marche.**

- Les 29 demandes des cinq scénarios fournis ont été réalisées avec succès.
- Le robot découvre progressivement les murs et recalcule son chemin lorsqu'il obtient de nouvelles informations.
- Il reconnaît les émotions et recherche les objets en respectant l'ordre de priorité des casiers.
- Il effectue une seule action par tour et enregistre ses actions dans une trace.
- Il vérifie que le résident est accessible avant de prendre un objet.
- Il gère les situations où aucune émotion n'est reconnue, où l'armoire est vide ou lorsque le résident est inaccessible.
- Les fichiers JSON invalides sont détectés avant le lancement.

**Ce qui ne marche pas / limites.**

- **Navigation :** le robot peut explorer des impasses avant de découvrir qu'elles sont bloquées. Cela entraîne des déplacements supplémentaires.
- **Recherche dans l'armoire :** il peut repasser devant des casiers déjà observés vides. La recherche prend alors plus de temps.
- **Reconnaissance des émotions :** certains mots contenant `œ`, comme « écœuré », ne sont pas correctement reconnus.
- **Choix des objets :** la règle de repli peut conduire à choisir un objet peu adapté à l'émotion du résident.
- **Exploration :** vérifier qu'un résident est accessible peut nécessiter un aller-retour supplémentaire.

## Vidéo

`demo.mp4`, également déclarée dans `rendu.json`.

La vidéo présente une exécution du robot avec l'affichage de sa carte mentale. Elle montre notamment comment il adapte son chemin lorsqu'il découvre un mur.
