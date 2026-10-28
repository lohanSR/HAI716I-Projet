# Robot de réconfort — MAHDI Abderaouf & SERRE Lohan

Projet de semestre, master informatique (HAI716I). Un robot à perception locale
consulte un dictionnaire, fouille une armoire et rapporte un objet à un
résident.

Langage : Python — Version : **3.8 ou plus** (développé et testé sous 3.12 ;
chaque module commence par `from __future__ import annotations` pour rester
compatible 3.8).

## Lancer

```
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

Exemple :

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json
```

Dépendances : *aucune* (bibliothèque standard uniquement).

- L'armoire lue est `<dossier_donnees>/<scenario["armoire"]>.json`, le
  dictionnaire `<dossier_donnees>/dictionnaire.json`.
- Option (5e argument) : `--afficher` redessine la carte mentale du robot dans
  le terminal à chaque pas (`@` robot, `*` chemin prévu, `?` case inconnue,
  `#` mur, `A` armoire, `D` dictionnaire, `P` résident). Sans cette option,
  rien ne s'affiche à part une ligne de bilan.
- Codes de retour : `0` scénario joué (même si des demandes échouent),
  `1` fichier d'entrée invalide (message sur stderr, **aucune trace écrite**),
  `2` mauvaise ligne de commande, `3` action illégale de l'agent (bug, aucune
  trace écrite).

Vérifier une trace (rejoue chaque pas contre la vraie carte, comme la
correction) :

```
python verifier_trace.py <carte.json> <scenario.json> <dossier_donnees> <trace.json>
```

## Tester

```
python -m unittest discover -s tests -v
```

115 tests (`unittest`, aucune dépendance), qui couvrent les familles du §8 :

- **planification** : BFS de l'annexe B.3 (exactement 7 pas), plusieurs
  arrivées, départ déjà arrivé, aucun chemin ;
- **replanification** : mur découvert en route qui change le chemin, carte
  mentale (inconnu, bords, perceptions) ;
- **dictionnaire** : un message par émotion, premier mot reconnu, aucun mot
  connu, accents/majuscules/ponctuation ;
- **sélecteur** : les exemples C.3, bouclage des colonnes, N/S interdits aux
  bords, les 576 couples de casiers, la fouille C.5 (9 mouvements) ;
- **repli** : casier exact, `intensite`, `voisine_1`, `voisine_2`,
  `armoire vide`, et l'ordre des 15 candidats écrit à la main ;
- **validation** : 28 fichiers cassés (`tests/fichiers_casses/`), passés à
  `agent.py` dans un sous-processus : code ≠ 0, message clair, pas de
  traceback, pas de trace ; et des fichiers valides inhabituels acceptés ;
- **inaccessible** : résident muré (rien n'est pris, la demande suivante
  réussit), dictionnaire et armoire murés ;
- **bout en bout** : `appartement_01` (annexe D), 7 cartes à nous
  (`tests/cartes/`) jouées puis vérifiées par `verifier_trace.py`, et des
  traces falsifiées que le vérificateur doit refuser.

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent.py` | point d'entrée (`main`), classe `Agent` : boucle d'une demande (dictionnaire → armoire → résident) |
| `perception.py` | perception du simulateur → mémoire de l'agent (carte mentale + casiers vus) |
| `memoire.py` | `CarteMentale` : ce que le robot sait (inconnu au départ, sauf bords, A, D, P) |
| `planification.py` | BFS écrit à la main (`deque`, ordre N, S, E, O, plusieurs arrivées) |
| `decision.py` | plus court chemin sur la carte mentale (optimiste ou pessimiste) → prochaine direction |
| `action.py` | journalise le pas (état avant l'action) puis l'exécute |
| `gestion_armoire.py` | fouille de l'armoire une action par tick, mémoire des casiers vus dans la demande |
| `logique.py` | règles du §6 : émotion du message, 15 casiers candidats, chemin du sélecteur, repli |
| `validation.py` | vérifications du §5.6 sur les 4 fichiers d'entrée |
| `simulateur.py` | la vérité terrain (vraie grille, vrais casiers) ; refuse toute action illégale |
| `affichage.py` | dessin texte de la carte mentale (`--afficher`) |
| `verifier_trace.py` | rejoue une trace contre la réalité et vérifie les livraisons |
| `reconfort_io.py` | lecture des fichiers et écriture de la trace (fourni) |
| `tests/` | tests `unittest`, cartes de test, fichiers cassés |

L'agent ne lit jamais `grille` ni l'`objet` des casiers : il est construit à
partir d'une vue publique de la carte et de l'armoire, et ne parle au
simulateur que par `percevoir()`, `contenu_casier()` et `executer()`.

## État

**Ce qui marche.**

- Les 5 cartes fournies : **29/29 demandes réussies** (4/4 en 198 pas, 5/5 en
  257, 6/6 en 313, 6/6 en 282, 8/8 en 324). Annexe C.5 et annexe D reproduites.
- Perception locale, carte mentale, BFS recalculé à chaque pas (hypothèse
  optimiste : une case inconnue est supposée libre) ; un mur découvert change
  le chemin au pas suivant.
- Fouille de l'armoire une action par tick, candidats dans l'ordre de
  priorité, repli avec la bonne étiquette.
- Échecs propres (§6.3), la demande suivante continue : `emotion indeterminee`,
  `armoire vide`, `resident inaccessible`. Le robot ne prend jamais un objet
  qu'il ne pourrait pas livrer : avant `PRENDRE`, il vérifie que le résident est
  atteignable à coup sûr, sinon il va d'abord explorer vers lui.
- Fichiers invalides : message sur stderr, code 1, aucune trace.
- `verifier_trace.py` : les 12 traces (5 cartes fournies + 7 à nous) sont
  conformes.

**Ce qui ne marche pas / limites.**

- Deux motifs d'échec ajoutés, hors des trois du §5.5 :
  `dictionnaire inaccessible` et `armoire inaccessible`. Sur une livraison en
  échec, `repli` vaut `"aucun"`.
- Les trajets ne sont pas optimaux : avec l'hypothèse optimiste, le robot
  entre dans des culs-de-sac avant de les découvrir (ex. 60 pas au lieu de 40
  sur notre carte `impasses`).
- La vérification « résident atteignable à coup sûr » coûte un aller-retour
  d'exploration la première fois (32 à 68 pas par carte fournie).
- La fouille est refaite à chaque demande : le robot repasse devant les
  casiers prioritaires déjà vus vides (règle « effectivement passé devant »
  du §6.2), ce qui coûte des pas.
- Après un `armoire vide`, un `ATTENDRE` en plus pour que la trace journalise
  le dernier casier vu.
- Stock infini : `PRENDRE` ne vide pas le casier.
- Limites de `reconfort_io.normaliser` (fourni, non modifié) : `œ` n'est pas
  décomposé, donc « écœuré » ne correspond pas à la forme `ecoeure`. Un
  fichier UTF-8 avec BOM est refusé.
- Deux demandes avec le même `numero` ne sont pas refusées (hors §5.6).
- `validation.py` : quatre fonctions longues (une par type de fichier), pas
  encore découpées.

## Vidéo

`demo.mp4`, déclarée dans `rendu.json` : `appartement_01` avec `--afficher`.
Au pas t=8, le robot se cogne au mur `[6, 7]` et son chemin prévu (`*`)
remonte par la ligne 3.
