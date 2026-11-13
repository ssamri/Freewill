# Vitesse des moteurs locaux

[English](speed.md) · **Français**

À quelle vitesse les moteurs locaux de Freewill pensent sur un processeur, ce qui a été essayé pour les accélérer, et ce qui a été gardé. Tous les chiffres ci-dessous viennent du workflow `speed of the local engines` (`.github/workflows/speed-bench.yml`, `tools/speed_bench.py`), exécution 43287951339 du 12 novembre 2026, sauf mention d'une autre exécution. Rien ici n'est une estimation.

## D'où viennent les idées

De la lecture de [colibri](https://github.com/JustVugg/colibri) (Apache 2.0, de Vincenzo Fornaro). Son idée principale est de faire tourner de très grands modèles à « mélange d'experts » (des centaines de milliards de paramètres) sur un ordinateur ordinaire : la partie que chaque mot utilise reste en mémoire, et les experts sont lus sur le disque quand le modèle les demande. **Cette idée ne s'applique pas aux modèles de Freewill** : Qwen3 1.7B, SmolVLM2 2.2B et Freewill 1.8B-V sont petits, denses (chaque paramètre sert à chaque mot) et tiennent déjà en mémoire. Trois idées plus modestes pouvaient s'appliquer, et ont été mesurées :

1. garder en mémoire ce que chaque pensée relit (les instructions de l'être) ;
2. calculer avec un fil par cœur physique ;
3. le brouillon par recherche en arrière (« prompt lookup », brouillons n-grammes), vérifié en un seul passage du modèle.

Aucun code n'a été pris à colibri. llama.cpp, que Freewill fournit déjà, implémente 2 et 3 ; 1 est écrit pour Freewill 1.8B-V dans `freewill/vlm/model.py`.

## Comment c'est mesuré

Un être naît, on lui parle en anglais et en français par la vraie boucle de vie, puis on le laisse penser un moment. Les 14 requêtes qu'il a faites (ses instructions, environ 3 400 caractères, et chaque situation) sont enregistrées, puis rejouées à l'identique dans chaque configuration, en mode glouton (température 0), pour pouvoir comparer les réponses mot à mot. Machines : exécuteurs GitHub à 4 cœurs logiques et 2 cœurs physiques (AMD EPYC), 16 Go de mémoire, sans carte graphique, Linux et Windows Server 2025.

## Freewill 1.8B-V (PyTorch)

Les 6 premières requêtes, 96 mots-jetons par réponse, Linux. Secondes par réponse, médiane des 6.

| Configuration | Par réponse | Premier mot (lecture) | Mêmes réponses qu'« avant » |
|---|---|---|---|
| bfloat16, instructions relues à chaque fois (**avant**) | 89,3 s | 60,3 s | référence |
| bfloat16, instructions lues une fois et gardées | 52,6 s | 29,4 s | **1 sur 6** |
| float32, instructions relues à chaque fois | 39,1 s | 13,4 s | référence |
| float32, instructions lues une fois et gardées (**maintenant**) | 31,3 s | 7,0 s | **6 sur 6** |

De l'ancien réglage par défaut au nouveau, une réponse passe de 89,3 s à 31,3 s (2,9 fois plus rapide), et l'attente avant le premier mot de 60,3 s à 7,0 s. Une exécution précédente sur un autre exécuteur du même type (43245499469) donne le même ordre : lecture 6 à 7 fois plus longue en bfloat16 qu'en float32, réponse 3,5 fois plus longue.

Ce qui est gardé :

- **float32 par défaut** quand le processeur n'a pas de bfloat16 natif (la plupart des PC : sans AVX512-BF16 ni AMX, PyTorch convertit chaque poids bfloat16 à la volée) et que la mémoire suffit (12 Go ou plus ; le float32 prend environ 8 Go, le bfloat16 environ 4 Go). Sinon bfloat16. `FREEWILL_OWN_DTYPE` permet de forcer.
- **Instructions lues une fois et gardées**, en float32 : réponses identiques 6 fois sur 6. En bfloat16, les réponses différaient 5 fois sur 6 (l'arrondi change quand le texte est lu en deux morceaux), donc c'est éteint dans ce cas sauf `FREEWILL_OWN_REUSE=1`. La mémoire des instructions est effacée dès que les poids peuvent changer (une nuit d'entraînement).

## Qwen3 1.7B par llama.cpp (b12306)

Les 14 requêtes, deux tours, secondes pour les 14 ensemble.

| Configuration | Linux, tour 1 / 2 | Windows, tour 1 / 2 | Mêmes réponses |
|---|---|---|---|
| tous les cœurs logiques sauf un (3 fils, **avant et maintenant**) | 257,8 / 250,1 | 458,0 / 455,3 | référence |
| cœurs physiques (2 fils) | 240,3 / 239,3 | 474,7 / 473,9 | 14 sur 14 |
| cœurs physiques, brouillons ngram-simple | 248,9 / 240,9 | 502,7 / 526,8 | 14 sur 14 |
| cœurs physiques, brouillons ngram-mod | 248,7 / 244,2 | 486,4 / 487,1 | **2 sur 14** |

- **Fils de calcul.** Sous Linux, les cœurs physiques ont été environ 5 % plus rapides (lecture du texte plus rapide : 94 à 96 jetons par seconde contre 75 à 78). Sous Windows, cible principale de Freewill, ils ont été environ 4 % plus lents (l'écriture est passée de 12,2–12,5 à 10,8 jetons par seconde). **Le réglage par défaut ne change pas.** `FREEWILL_THREADS=physical` demande les cœurs physiques.
- **Brouillons.** ngram-simple garde les réponses mais ne fait gagner aucun temps : 111 jetons acceptés sur 608 proposés sous Linux, 64 sur 768 sous Windows. ngram-mod a changé 12 réponses sur 14, même en mode glouton. **Les deux restent éteints.** `FREEWILL_DRAFT=ngram` allume le premier, pour essayer.
- **Cache du texte.** llama-server réutilise déjà ce que deux requêtes ont en commun : 11 338 des 18 840 jetons de texte sont venus de son cache dans chaque configuration. Rien à ajouter.

## Pour de plus grands modèles : colibri comme moteur externe

colibri sert ses modèles à une adresse compatible OpenAI (`http://127.0.0.1:8000/v1`), que Freewill sait déjà utiliser comme moteur de type `compatible`. C'est ainsi qu'un ordinateur de 16 à 32 Go pourrait penser avec un modèle à mélange d'experts bien plus grand que Qwen3 1.7B. Cela n'a pas été mesuré avec Freewill. Une vie qui pense avec un moteur externe ne l'entraîne pas la nuit : seuls le moteur embarqué et Freewill 1.8B-V apprennent.

## Limites

Deux exécuteurs, une seule famille de processeurs, sans carte graphique, sans macOS ; une exécution de chaque configuration de Freewill 1.8B-V, deux de chaque configuration llama.cpp. Le pont de Freewill 1.8B-V n'était pas entraîné (texte seul), ce qui ne change rien à la vitesse. Dans l'application, les réponses à une personne sont tirées au sort, pas gloutonnes : le temps est le même, les mots n'y sont pas comparés.
