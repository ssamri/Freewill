# Freewill 1.8B-V, le modèle propre au projet

[English](own-model.md) · **Français**

Freewill 1.8B-V est un seul modèle qui lit du texte, regarde des images et suit des vidéos. Il est assemblé à partir de deux modèles ouverts, puis entraîné et agrandi par Freewill. Le code se trouve dans [`freewill/vlm/`](../freewill/vlm/).

Rien ici n'affirme que le modèle comprend, ni qu'il est conscient. Chaque résultat donné plus bas a été calculé par le workflow de bout en bout, et ses journaux sont cités.

## 1. De quoi il est fait

```
image, ou image d'une vidéo ─▶ œil : tour de vision de SigLIP2 base (figée)    92 884 224
                            ─▶ pont : regroupement 2×2 + MLP à deux couches     10 496 000   entraîné par Freewill
                            ─▶ 49 vecteurs par image, dans l'espace du modèle de langue
texte ──────────────────────▶ modèle de langue : Qwen3 1.7B                  1 720 574 976
                              + adaptateurs de faible rang (rang 16)            17 432 576   entraînés par Freewill
                              + couches ajoutées par croissance (une par défaut) 50 336 000  ajoutées et entraînées par Freewill
```

| | Paramètres |
|---|---|
| À la naissance (œil + pont + modèle de langue) | **1 823 955 200** |
| Après une couche ajoutée et les adaptateurs | **1 891 723 776** |
| Plafond | choisi par la personne (2 milliards par défaut ; 5, 13, 50 milliards ou tout autre nombre) |

Ces nombres sont calculés à partir des tenseurs du modèle (`FreewillVLM.count()`). La part du modèle de langue correspond exactement au nombre publié pour Qwen3 1.7B.

- **Licences.** Qwen3 1.7B et SigLIP2 sont tous deux sous licence Apache-2.0. Les deux bases sont téléchargées depuis Hugging Face, et leurs fichiers ainsi que leurs empreintes SHA-256 sont consignés dans `bases.json`.
- **Vidéo.** Une vidéo est une suite d'images dans l'ordre. Chaque image est précédée de son instant (par exemple `1.5s:`), et toutes forment une seule séquence que lit le modèle de langue.
- **Croissance.** La croissance prend deux formes, et toutes deux commencent comme l'identité : le modèle prédit exactement ce qu'il prédisait avant, avec plus de paramètres pour apprendre. Les tests le vérifient.
  - **Neurones.** Des neurones ajoutés dans chaque bloc à propagation avant. Leurs poids sortants partent de zéro, et un masque de gradient garde les anciens poids exactement tels qu'ils étaient.
  - **Couches.** Des couches entières, chacune copie de sa voisine avec ses projections de sortie mises à zéro.

  `grow_to(n)` ajoute d'abord des neurones (jusqu'à quatre fois la largeur de naissance), puis des couches. La croissance est refusée au-delà du plafond choisi par la personne, et elle doit avoir lieu avant l'ajout des adaptateurs.

## 2. Jusqu'où il peut grandir : la personne décide

Il n'y a plus de plafond fixe. Dans les **Réglages**, la carte « Le modèle propre à Freewill : jusqu'où il peut grandir » permet de choisir 2, 5, 13 ou 50 milliards de paramètres, ou de saisir n'importe quelle autre taille. Le même choix existe en ligne de commande : `freewill own-model settings --max-parameters 50e9`. Un plafond inférieur à la taille actuelle du modèle est refusé.

Pour chaque taille, la carte montre ce qu'elle demande à un ordinateur, à côté de ce que possède celui-ci (cœurs du processeur, mémoire, disque libre, cartes graphiques) : le stockage, la mémoire pour le faire tourner (pleine précision, 8 bits, 4 bits), la carte graphique nécessaire pour le faire tourner, la mémoire pour entraîner ce qui grandit (base figée) ou tout le modèle, le texte nécessaire aux nouveaux paramètres, et la durée d'entraînement sur quatre types de matériel. `freewill own-model requirements --target 13e9` donne les mêmes chiffres.

Ces chiffres sont des estimations, pas des mesures. Ils viennent de formules écrites dans [`capacity.py`](../freewill/vlm/capacity.py) :

- **Mémoire.** 2 octets par paramètre en bf16, 1 en 8 bits, 0,56 en 4 bits, plus 20 % pour les activations. L'entraînement coûte 16 octets par paramètre entraîné.
- **Texte.** 20 jetons par nouveau paramètre, et un livre moyen est compté pour 120 000 jetons.
- **Vitesse.** Les vitesses effectives sont de 0,2, 25, 65 et 400 billions d'opérations par seconde, pour un processeur à 8 cœurs, une carte de 12 Go, une carte de 24 Go et un H100.
- **Durée.** La durée suppose un partage parfait entre plusieurs cartes, donc la durée réelle est plus longue.

À la naissance (1,82 milliard), voici ce que demande chaque préréglage :

| Plafond | Disque | Faire tourner (4 bits / bf16) | Entraîner ce qui grandit | Texte pour les nouveaux paramètres | Durée d'entraînement, au mieux |
|---|---|---|---|---|---|
| 2 milliards | 25,4 Go | 1,3 / 4,8 Go | 7,6 Go | 3,5 milliards (~29 341 livres) | 1 × 24 Go : 7,5 jours · 1 × H100 : 1,2 jour |
| 5 milliards | 55,4 Go | 3,4 / 12,0 Go | 62,8 Go | 63,5 milliards (~529 341 livres) | 3 × 24 Go : 113 jours · 1 × H100 : 55,1 jours |
| 13 milliards | 135 Go | 8,7 / 31,2 Go | 210 Go | 224 milliards (~1 862 675 livres) | 9 × 24 Go : 345 jours · 3 × H100 : 168 jours |
| 50 milliards | 505 Go | 33,6 / 120 Go | 891 Go | 964 milliards (~8 029 341 livres) | 38 × 24 Go : 3,7 ans · 12 × H100 : 1,9 an |

**Ce que cela veut dire.** On peut faire grandir le modèle autant que la personne le veut : la croissance est mécanique et vérifiée. Mais les nouveaux paramètres ne valent quelque chose qu'une fois entraînés sur assez de texte. Au-delà d'environ 2 milliards, les livres seuls sont loin de suffire (le Projet Gutenberg en compte environ 75 000), et il faudrait d'autres corpus ouverts. Élargir les blocs à propagation avant et ajouter de la profondeur, alors que la largeur propre du modèle (2 048) reste fixe, est aussi moins efficace qu'un modèle conçu d'emblée à cette taille.

## 3. Comment il est entraîné

L'entraînement compte trois étapes. Chacune est une décision distincte, inscrite dans un registre où l'on ne fait qu'ajouter (`ledger.jsonl`), avec ce qui a été mesuré avant et après.

| Étape | Ce qui est entraîné | Mesuré sur (jamais vu à l'entraînement) | Gardée seulement si |
|---|---|---|---|
| **lire** | adaptateurs + couches ajoutées | 1 passage sur 10 des livres, choisi par empreinte | les passages mis de côté sont mieux prédits, d'au moins 0,01 nat par jeton |
| **voir** | le pont | 1 image dessinée sur 4 : couleur (6 choix) et forme (4) | la justesse monte d'au moins 5 points **et** dépasse d'au moins 5 points les mêmes questions posées sur l'image d'un autre exemple |
| **regarder** | pont + adaptateurs | 1 vidéo dessinée sur 4 : sens du mouvement (4 choix) | la justesse monte d'au moins 5 points **et** dépasse le contrôle aux images inversées comme le contrôle à une seule image ; la vue perd au plus 5 points ; la lecture se dégrade d'au plus 0,05 nat par jeton |

Quand une étape est refusée, les poids d'avant l'étape sont restaurés.

- **Livres.** Ce sont des œuvres du domaine public issues du Projet Gutenberg, en anglais et en français (voir la liste dans [`books.py`](../freewill/vlm/books.py)). La mention de licence est retirée, et la langue inscrite dans l'en-tête de chaque livre est vérifiée : un livre qui ne correspond pas est écarté, et l'exécution le signale. La personne peut aussi donner ses propres fichiers texte, PDF, EPUB ou DOCX.
- **Images et vidéos dessinées.** Elles servent parce que leurs réponses sont connues exactement et que chaque exemple se reproduit à partir de sa graine. Réussir ces tests montre que la couleur, la forme et le mouvement parviennent au modèle de langue par l'œil et le pont. Cela ne montre pas que le modèle comprend le monde.
- **Point de reprise.** Un point de reprise ne contient que ce que Freewill a entraîné ou ajouté. Le modèle est reconstruit à partir des bases et du point de reprise, et l'exécution de bout en bout vérifie que le modèle reconstruit donne les mêmes scores.

## 4. L'utiliser

```
pip install "freewill[own-model]"
python -m freewill own-model fetch                    # environ 4,5 Go, une seule fois
python -m freewill own-model count
python -m freewill own-model settings --max-parameters 5e9      # le plafond, à votre choix
python -m freewill own-model requirements --target 5e9          # ce que cette taille demande
python -m freewill own-model train --gutenberg --books mon-livre.pdf
```

- **Moteur.** Comme moteur de pensée d'un être, choisissez le type `own` (`freewill/engines/own_model.py`). Il tourne dans le processus avec PyTorch, demande environ 8 Go de mémoire en float32 (4 Go en bfloat16) et peut recevoir des images.
- **Vitesse.** Sur processeur seul, un pas d'entraînement sur quatre images prend environ 10 secondes. Ce chiffre a été mesuré ici sur 4 cœurs, avec l'architecture à taille réelle et des poids aléatoires. Une carte graphique accélère beaucoup.
- **Ce qu'il ne fait pas encore.** Il n'est pas encore entraîné par les nuits d'une vie (`can_learn = False`), et llama.cpp ne le fait pas tourner, il n'a donc pas de fichier GGUF.

## 5. L'entraîner de zéro : ce qu'il faudrait

La même architecture peut être construite avec des poids aléatoires (`build(init="random")`). Voici un ordre de grandeur. C'est un calcul, pas une mesure.

- **Données.** Environ 20 jetons par paramètre, soit près de 36 milliards de jetons. Tout le Projet Gutenberg en contient quelques milliards : les livres seuls ne suffisent pas.
- **Calcul.** Environ 6 × 1,8·10⁹ × 3,6·10¹⁰ ≈ 4·10²⁰ opérations. Cela représente à peu près 300 heures sur un GPU H100 avec un rendement réaliste, donc plusieurs centaines d'euros de location, sans compter l'œil.
- **Sur un ordinateur personnel.** Des mois de calcul sur une carte graphique haut de gamme, et l'état de l'optimiseur pour 1,8 milliard de paramètres ne tient pas dans 24 Go sans techniques particulières.

C'est pourquoi la voie choisie part de bases ouvertes déjà pré-entraînées.

## 6. Résultats

En attente : le workflow `own model end to end` de la pull request 13 est en cours. Seuls les chiffres de ses journaux seront inscrits ici.
