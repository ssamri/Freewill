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

**Avant toute croissance, une garde.** Le plafond est un choix ; la garde vérifie ce que cet ordinateur peut contenir maintenant. Avant d'ajouter des paramètres, elle lit la mémoire disponible à cet instant (pas la mémoire installée), le disque libre là où vit le modèle, et la mémoire libre de chaque carte graphique. Elle estime ce que la croissance demande : les nouveaux poids, les activations, le gradient et l'état de l'optimiseur pour les entraîner, et deux points de reprise sur le disque, avec une marge de 15 %. Si cela ne tient pas, la croissance est refusée avant que rien ne change. Le refus dit ce qu'il fallait, ce qui était libre, le plus grand pas qui tiendrait, et les solutions de rechange : un pas plus petit, des adaptateurs au lieu de la croissance, la quantification pour le faire tourner, ou attendre une machine plus grande. Pendant l'entraînement, une croissance refusée est inscrite au registre, et l'exécution continue à la taille que le modèle a déjà.

**Configuré, disponible, prouvé.** La carte des réglages sépare trois choses, chacune lue à sa propre source :

- **Configuré** : ce qui est écrit dans les réglages, un choix et non une capacité.
- **Disponible sur cet ordinateur** : si PyTorch, Transformers et les deux bases sont installés, et si grandir jusqu'au plafond passerait la garde en ce moment.
- **Prouvé** : pour lire, voir et regarder, si un entraînement a gardé l'étape sur la validation, et si le test scellé la confirme. Confirmer veut dire : mieux qu'à la naissance, mieux que chaque contrôle, et moins d'une chance sur 100 d'y arriver par hasard. Apprendre pendant les nuits d'une vie est présenté à part, et reste « pas encore démontré » tant qu'une exécution de bout en bout ne l'a pas montré.

**Ce que cela veut dire.** On peut faire grandir le modèle autant que la personne le veut : la croissance est mécanique et vérifiée. Mais les nouveaux paramètres ne valent quelque chose qu'une fois entraînés sur assez de texte. Au-delà d'environ 2 milliards, les livres seuls sont loin de suffire (le Projet Gutenberg en compte environ 75 000), et il faudrait d'autres corpus ouverts. Élargir les blocs à propagation avant et ajouter de la profondeur, alors que la largeur propre du modèle (2 048) reste fixe, est aussi moins efficace qu'un modèle conçu d'emblée à cette taille.

## 3. Comment il est entraîné

L'entraînement compte trois étapes. Chacune est une décision distincte, inscrite dans un registre où l'on ne fait qu'ajouter (`ledger.jsonl`), avec ce qui a été mesuré avant et après.

| Étape | Ce qui est entraîné | Décidée sur le jeu de validation (jamais vu à l'entraînement) | Gardée seulement si |
|---|---|---|---|
| **lire** | adaptateurs + couches ajoutées | 24 passages des blocs de validation des livres | les passages de validation sont mieux prédits, d'au moins 0,01 nat par jeton |
| **voir** | le pont | 50 images dessinées : couleur (6 choix) et forme (4) | la justesse monte d'au moins 5 points **et** dépasse d'au moins 5 points les mêmes questions posées sur l'image d'un autre exemple |
| **regarder** | pont + adaptateurs | 30 vidéos dessinées : sens du mouvement (4 choix) | la justesse monte d'au moins 5 points **et** dépasse le contrôle aux images inversées comme le contrôle à une seule image ; la vue perd au plus 5 points ; la lecture se dégrade d'au plus 0,05 nat par jeton |

Quand une étape est refusée, les poids d'avant l'étape sont restaurés.

**Trois jeux séparés.** Les données sont partagées en trois, et ce partage est fait par construction, pas par tirage au moment de l'exécution :

- **Entraînement** : ce dont le modèle apprend.
- **Validation** : ce que lit chaque règle ci-dessus pour garder ou refuser une étape.
- **Test scellé** : mesuré une fois à la naissance et une fois à la fin, inscrit dans le résumé et le registre, et lu par aucune règle. C'est lui que rapportent les résultats.

Les images et vidéos dessinées de chaque jeu viennent de leur propre espace de graines (`image-train-N`, `image-validation-N`, `image-test-N`) : un exemple ne peut jamais appartenir à deux jeux. Les livres sont découpés en blocs de 20 passages consécutifs, et chaque bloc est attribué par l'empreinte du livre et du numéro de bloc : 1 sur 10 au test, 1 sur 10 à la validation, le reste à l'entraînement. Les passages voisins, qui partagent des noms et des phrases, restent ensemble. À la première exécution, le jeu de test est fixé par une empreinte SHA-256 dans `sealed_test.json` ; une exécution ultérieure dont le jeu de test diffère est refusée, pour que le test ne puisse pas être changé après avoir vu des résultats. Pour chaque résultat à choix multiples du test scellé, le résumé donne la probabilité de l'atteindre par le seul hasard.

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
- **Les nuits d'une vie.** Quand un être pense avec ce modèle et que la personne active l'apprentissage du moteur pour cette vie (son nom vaut accord), chaque nuit entraîne les adaptateurs du modèle sur ce que l'être a entendu et répondu ([`nights.py`](../freewill/vlm/nights.py)). Elle reprend le corpus et les règles des nuits du modèle local ([engine-learning.fr.md](engine-learning.fr.md)) : un élément sur quatre est mis de côté pour toujours, d'anciens éléments et des passages ordinaires sont rejoués, et la nuit n'est gardée que si les éléments mis de côté de cette vie sont mieux prédits d'au moins 0,01 nat par jeton, tandis que les textes de référence et les nuits précédentes se dégradent d'au plus 0,05. Une nuit gardée est enregistrée dans le dossier de la vie (`engine/own/checkpoints/`), et le moteur de cette vie la charge la fois suivante. L'être attend entre deux moments pendant que la nuit s'entraîne. `python -m freewill own-model night --life <dossier>` lance une nuit à la main.
- **Ce qu'il n'affirme pas encore.** Le moteur indique toujours `can_learn = False` : l'interface ne le présente donc pas comme un modèle qui apprend. Elle ne le fera qu'une fois qu'une exécution de bout en bout avec les vraies bases aura gardé une nuit (dernière étape du workflow). llama.cpp ne le fait pas tourner, il n'a donc pas de fichier GGUF.

## 5. L'entraîner de zéro : ce qu'il faudrait

La même architecture peut être construite avec des poids aléatoires (`build(init="random")`). Voici un ordre de grandeur. C'est un calcul, pas une mesure.

- **Données.** Environ 20 jetons par paramètre, soit près de 36 milliards de jetons. Tout le Projet Gutenberg en contient quelques milliards : les livres seuls ne suffisent pas.
- **Calcul.** Environ 6 × 1,8·10⁹ × 3,6·10¹⁰ ≈ 4·10²⁰ opérations. Cela représente à peu près 300 heures sur un GPU H100 avec un rendement réaliste, donc plusieurs centaines d'euros de location, sans compter l'œil.
- **Sur un ordinateur personnel.** Des mois de calcul sur une carte graphique haut de gamme, et l'état de l'optimiseur pour 1,8 milliard de paramètres ne tient pas dans 24 Go sans techniques particulières.

C'est pourquoi la voie choisie part de bases ouvertes déjà pré-entraînées.

## 6. Résultats

**Premier essai réel, 12 novembre 2026** ([exécution 43204057091](https://github.com/ssamri/Freewill/actions/runs/43204057091), commit 85f5624, machine GitHub à 4 cœurs sans carte graphique, float32). Chaque nombre ci-dessous est recopié de son journal.

Cet essai est antérieur au test scellé. Ses chiffres sont des **chiffres de validation** : ils ont été mesurés sur les exemples mêmes qui ont décidé de garder chaque étape, ils sont donc optimistes. Les résultats sur lesquels s'appuyer viendront d'un essai avec le test scellé.

| | Avant | Après | Décision |
|---|---|---|---|
| Taille | 1 823 955 200 à la naissance | 1 874 291 200 après une couche ajoutée (en position 15) | |
| **lire** : nats par jeton sur 1 passage sur 10 des livres (40 pas, 521 s) | 3,5000 | 2,9074 | gardée |
| **voir** : justesse sur 120 images dessinées (300 pas, 3 804 s) | 15,8 % | 100 % (couleur 100 %, forme 100 %) | gardée |
| contrôle : les mêmes questions sur l'image d'un autre exemple | 15,8 % | 23,3 % | |
| **regarder** : justesse sur 40 vidéos dessinées (200 pas, 3 420 s) | 27,5 % | 15,0 % | refusée, poids restaurés |
| contrôles : images inversées / une seule image | 25 % / 30 % | 15 % / 15 % | |

**Ce que cela montre.** Dans ce protocole, sur les exemples de validation, le pont transmet la couleur et la forme de l'œil au modèle de langue. Les réponses dépendent de l'image montrée : sur l'image d'un autre exemple, la justesse reste près du hasard (20,8 %). Les livres sont mieux prédits après la lecture. Le mouvement n'a pas été appris : l'étape regarder a fait moins bien que le hasard et aussi mal que ses contrôles, et elle a été refusée. Pendant cette étape, la lecture s'était dégradée à 3,1889 nats par jeton avant que les poids soient restaurés.

**Ce que cela ne montre pas.** Rien n'a été mesuré sur un test scellé. Les images dessinées sont simples et produites par le même code : les réussir n'est pas comprendre le monde.

**Où il s'est arrêté.** L'essai a été arrêté pendant la reconstruction du modèle depuis son point de reprise (code de sortie 143, signal d'arrêt de la machine). La cause la plus probable est la mémoire : un second modèle à taille réelle en float32 se chargeait à côté du premier, sur une machine de 16 Go. C'est une déduction tirée du moment de l'arrêt, le journal ne le dit pas. Le script de bout en bout libère désormais le premier modèle avant de charger le second. Les réponses aux questions libres ont été calculées mais jamais affichées, parce que l'étape des résultats n'a pas tourné.
