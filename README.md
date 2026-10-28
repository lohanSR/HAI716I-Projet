# Robot de réconfort — MAHDI Raouf & SERRE Lohan

Projet de semestre, master informatique. Un robot à perception locale
consulte un dictionnaire, fouille une armoire et rapporte un objet à un
résident.

Langage : Python — Version : 3.13.0

## Lancer

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json
```

Dépendances : *aucune*, ou la liste et comment les installer.

## Tester

```
<votre commande de test>
```

*Une phrase sur ce que couvrent les tests.*

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent.py` | point d'entrée, boucle de décision |
| `logique.py` | Reconnaissance des émotions dans les messages, classe les casiers par priorité et calcule les chemins du sélecteur |
| `gestion_armoire.py` | Gère les déplacements du sélecteur, mémorise les casiers observés et recherche un objet en respectant l'ordre de priorité |
| `validation.py` | Vérifie les champs, les types et la cohérence des fichiers JSON (dictionnaire, armoire, carte et scénario) |

## État

**Ce qui marche.** *À compléter.*

**Ce qui ne marche pas.** *À compléter — soyez honnêtes, c'est noté en
votre faveur.*

## Vidéo

`demo.mp4` (ou le lien), également déclarée dans `rendu.json`.