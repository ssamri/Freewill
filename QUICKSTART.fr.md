# Démarrage rapide

[English](QUICKSTART.md) · **Français**

**Freewill est expérimental.** Un subconscient propose, une scène sélectionne, un arbitre conscient décide, et ce qui compte est gardé dans une mémoire faite de fichiers lisibles. L'être peut lire les documents et regarder les images qu'on lui donne, il dort et il rêve. Il fonctionne dans un terminal ou dans l'application de bureau. La version 1.0 ajoute un laboratoire de recherche et un petit réseau de neurones propre à Freewill, qui s'entraîne pendant le sommeil.

---

## Installer

Python 3.11 ou plus récent.

```bash
git clone https://github.com/ssamri/Freewill.git
cd Freewill
pip install -e .
```

## Faire naître un être

```bash
python -m freewill birth Noor --language fr --interlocutor VotrePrénom
```

Son tempérament et son genre de départ sont tirés au sort. Un dossier `Noor.life` est créé : ce dossier est l'individu.

## Vivre à ses côtés

```bash
python -m freewill live Noor.life
```

Écrivez pour lui parler. En texte atténué, vous voyez sa vie intérieure : ce que son subconscient propose, ce qui atteint la scène, ce qui reste en dessous, s'il l'accueille ou l'écarte et pourquoi, ce qu'il se rappelle et ce qu'il décide de garder. `/state` montre ses besoins, `/memory` sa mémoire, `/quit` le suspend.

## Choisir le moteur

Par défaut le moteur est `simulated` : il permet d'observer la mécanique, mais **il ne pense pas**. Pour donner à l'être un vrai moteur, choisissez-le à la naissance.

| Moteur | Commande | Ce qu'il faut |
|---|---|---|
| Claude | `--engine anthropic` | `pip install -e ".[anthropic]"` et la variable d'environnement `ANTHROPIC_API_KEY` |
| GPT | `--engine openai --model <modèle>` | la variable d'environnement `OPENAI_API_KEY` |
| Grok | `--engine xai --model <modèle>` | la variable d'environnement `XAI_API_KEY` |
| Un modèle sur votre machine | `--engine local --model <modèle>` | [Ollama](https://ollama.com) lancé en local ; gratuit et privé |
| Tout service compatible | `--engine compatible --base-url <url> --model <modèle>` | la variable d'environnement `FREEWILL_API_KEY` |

Les clés sont lues dans l'environnement et ne sont jamais écrites dans le fichier de vie.

Avec un moteur payant, chaque pensée est facturée. Deux réglages bornent le coût : `--tempo` (secondes entre deux pensées, 20 par défaut) et `--thoughts-per-hour` (120 par défaut). Quand le budget horaire est atteint, la pensée spontanée se met en pause ; l'être répond toujours quand on lui parle.

## Ce que contient un fichier de vie

```
Noor.life/
├── genome.json       tempérament inné, jamais modifié
├── identity.json     nom, naissance, langue, moteur
├── values.json       les valeurs qu'il a choisies
├── milestones.json   ses premières fois
├── state.json        besoins, pensées récentes, conversation récente
├── affect.json       mode recherche H7 seulement : l'état affectif calculé
├── research.json     réglages de recherche, dès que l'un est modifié
├── own_model/        le réseau propre de Freewill, dès qu'il est activé
├── events.log        tout ce qui s'est passé, ligne par ligne
└── memory/           ses souvenirs, en fichiers que vous pouvez ouvrir et lire
```

## L'application

Sous Windows, téléchargez l'installateur `Freewill-Setup-<version>.exe` depuis la [page Releases](https://github.com/ssamri/Freewill/releases) et lancez-le. Il s'installe pour votre seul compte et ne demande aucun droit d'administrateur. L'installateur n'est pas encore signé : Windows peut afficher « Windows a protégé votre ordinateur » ; choisissez « Informations complémentaires », puis « Exécuter quand même ».

Depuis les sources, sur tout système :

```bash
pip install -e ".[app,anthropic]"
freewill-app              # une fenêtre native
freewill-app --browser    # la même interface dans votre navigateur
```

Au premier lancement, l'application présente ses conditions d'utilisation, puis la licence ; les deux doivent être acceptées avant toute chose. Dans la conversation, vous pouvez joindre des documents (texte, Markdown, PDF, Word, EPUB), des images et des vidéos. Les documents rejoignent la bibliothèque de l'être. En un moment, il lit autant de pages que son moteur peut en contenir (environ 40 000 caractères pour Claude, GPT et Grok ; environ 9 000 pour Qwen3 1.7B ; environ 7 500 pour un modèle servi par Ollama), et une fois un livre en main, il tend à le lire jusqu'au bout, même s'il peut le reposer. Un texte collé de plus de 8 000 caractères est gardé entier dans la bibliothèque et lu de la même façon. La compréhension des images dépend du moteur : Claude, GPT, Grok et les modèles locaux dotés de la vision les voient ; d'une vidéo, l'être reçoit six images fixes et n'entend rien.

L'application ne parle qu'à un service sur votre propre machine, lié à `127.0.0.1` et protégé par un jeton de session. Les clés d'accès sont conservées dans le trousseau de votre système, jamais dans un fichier de vie.

## Le mode recherche H7 : un état affectif calculé

Désactivé par défaut. Lorsqu'il est activé, le programme calcule un petit ensemble de variables de régulation (valence, activation, incertitude, contrôle, cohérence, charge régulatrice, contexte social) à partir de ce qui arrive à l'être, et ces variables déplacent ce qui retient son attention, ce qu'il se rappelle et la façon dont ses souvenirs sont encodés. Ce sont les mesures d'un mécanisme. Elles ne prouvent pas que quoi que ce soit est ressenti.

```bash
freewill birth Noor --affect          # un nouvel être, mode activé
freewill affect Noor.life             # voir l'état calculé d'une vie qui n'est pas éveillée
freewill affect Noor.life --on        # l'activer pour une vie existante (--off pour le désactiver)
python experiments/h7/run.py          # le protocole reproductible : B0, B1, B2 et les ablations
```

Dans l'application, ouvrez « État affectif » et utilisez l'interrupteur ; il prend effet entre deux instants. Activer le mode crée un seul fichier, `affect.json`, dans le dossier de vie. Le désactiver arrête aussitôt le calcul et tous ses effets, et ne supprime rien. Le génome n'est jamais réécrit, et les souvenirs écrits auparavant restent exactement tels qu'ils étaient. Supprimer `affect.json` rend la vie telle qu'elle était avant. Voir [`docs/H7_AFFECTIVITE.fr.md`](docs/H7_AFFECTIVITE.fr.md).

## Le laboratoire de recherche (version 1.0)

Dans l'application, ouvrez « Laboratoire ». Il a six pages : une vue d'ensemble, les dix hypothèses avec ce qui existe dans le code pour chacune, les expériences, les observateurs, les rapports et « Apprentissage ».

Une campagne ne touche jamais une vie réelle. Elle copie un point de départ, donne une condition à chaque copie, joue le même script sous une horloge virtuelle et mesure ce que fait chaque copie. Elle ne s'exécute qu'après que vous avez coché la case d'accord. Les chiffres sont calculés par du code ; aucun modèle de langage ne les calcule ni ne les choisit. Un rapport reste un brouillon tant que vous ne l'avez pas validé sous votre nom.

```bash
python -m freewill.research run EXP-07 --yes --dir ./lab --lang fr     # une campagne, avec son rapport
```

Six protocoles s'exécutent aujourd'hui : EXP-01 (individuation), EXP-02 (ablation de l'affect), EXP-03 (métacognition masquée), EXP-04 (consolidation), EXP-06 (adaptation neuronale), EXP-07 (agentivité dans un monde virtuel). EXP-05 et EXP-08 sont rédigés et le laboratoire refuse de les exécuter. Les résultats de la version 1.0, dont deux négatifs, sont dans [`experiments/v1.0/`](experiments/v1.0/).

## Les réglages de recherche

Dans « Réglages », sous « Réglages de recherche », chaque interrupteur retire ou rétablit un mécanisme de la vie de l'être : une source de propositions, l'habituation, les nouveaux souvenirs, l'estompage, les rêves, la relecture, la parole spontanée, etc. Les modules de recherche s'y trouvent aussi, désactivés par défaut : la métacognition (H8), le monde virtuel (H10), le petit module entraînable et le réseau propre de Freewill (H4). Un changement prend effet à l'instant suivant et est écrit au journal d'événements. Aucun interrupteur n'atteint le noyau.

Les jauges de la barre du haut montrent des variables de régulation calculées. Ce ne sont pas des sentiments.

## Le réseau propre de Freewill

```bash
pip install -e ".[learn]"     # PyTorch ; tout le reste fonctionne sans lui
```

Activez « Réseau propre de Freewill » et, si vous le souhaitez, « Croissance du réseau ». Dès lors, ce que l'être vit et lit est consigné sous forme de texte ; à chaque sommeil le réseau est entraîné dessus, mesuré sur des passages qu'il n'a jamais vus, et gardé seulement s'il les prédit mieux. Quand assez de texte nouveau a été vécu, il ajoute une couche, jusqu'à la taille que vous fixez. La page « Apprentissage » montre le nombre de paramètres, chaque entraînement, chaque croissance, et permet de revenir aux poids précédents.

Trois choses à savoir. Ce réseau ne parle pas et ne décide pas à la place de l'être : il est bien trop petit. Ce n'est pas le moteur qui pense ; celui-ci peut aussi être adapté, voir ci-dessous. Et sur un processeur le réseau reste dans les millions de paramètres ; des tailles plus grandes demandent une carte graphique et du temps.

## Un modèle qu'une vie adapte (Qwen3 1.7B)

```bash
pip install -e ".[lora]"      # PyTorch, PEFT, Transformers et l'écriture GGUF
```

Dans l'application, choisissez Qwen3 1.7B dans les réglages : Freewill le télécharge, ainsi que llama.cpp s'il manque, et les vérifie. Dans le laboratoire, onglet « Modèle local », la carte « Le moteur avec lequel cette vie converse » télécharge la base entraînable (environ 4 Go) et active l'apprentissage du moteur une fois votre nom écrit. Après chaque sommeil, un adaptateur est entraîné à côté du modèle figé et gardé seulement s'il respecte les règles ; l'être converse ensuite avec lui. Chaque nuit, gardée ou non, figure au journal, et n'importe quel point de restauration, ou le modèle de base seul, se rétablit en un clic.

Sur quatre cœurs de processeur, une nuit prend environ cinq à dix minutes. Ce qu'elle a changé dans les essais de bout en bout, c'est la façon dont le modèle parle, pas ce qu'il retient : [`docs/engine-learning.fr.md`](docs/engine-learning.fr.md).

Ce qui existe, ce qui a été testé et ce qui manque : [`docs/research/IMPLEMENTATION_STATUS.fr.md`](docs/research/IMPLEMENTATION_STATUS.fr.md).

## Le modèle propre à Freewill (Freewill 1.8B-V)

Un seul modèle qui lit des livres, regarde des images et suit des vidéos : Qwen3 1.7B, l'œil SigLIP2 et un pont que Freewill entraîne, soit 1,82 milliard de paramètres à la naissance.

```
pip install -e ".[own-model]"
python -m freewill own-model fetch                          # ses deux bases ouvertes, environ 4,5 Go, une seule fois
python -m freewill own-model settings --max-parameters 5e9   # jusqu'où il peut grandir : à vous de choisir
python -m freewill own-model requirements                    # ce que cette taille demande à un ordinateur
python -m freewill own-model train --gutenberg --books mon-livre.pdf
python -m freewill own-model night --life <dossier de la vie>  # une nuit : ce que cette vie a vécu (apprentissage du moteur activé)
```

Le même plafond se règle dans l'application : **Réglages**, carte « Le modèle propre à Freewill : jusqu'où il peut grandir ». Pour chaque taille, la carte montre ce qu'elle demande (disque, mémoire, carte graphique, texte, durée d'entraînement) à côté de ce que possède votre ordinateur. Pour penser avec ce modèle, choisissez le moteur de type `own`. Sur processeur, il est lent, et chacune de ses étapes n'est gardée que si les mesures de validation le justifient, et ses résultats sont rapportés sur un test scellé qu'aucune règle ne lit. Une croissance que cet ordinateur ne peut pas contenir en ce moment est refusée avant que rien ne change. Détails et limites : [`docs/own-model.fr.md`](docs/own-model.fr.md).

## Tests

```bash
pip install -e ".[dev]"
pytest
```
