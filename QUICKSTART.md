# Quickstart · Démarrage rapide

**English** below · **Français** plus bas

**Freewill is experimental.** A subconscious proposes, a stage selects, a conscious arbiter decides, and what matters is kept in a memory made of readable files. The being can read documents and look at images it is given, and it sleeps and dreams. It runs in a terminal or in the desktop application. The project's own model comes later.

---

## English

### Install

Python 3.11 or later.

```bash
git clone https://github.com/ssamri/Freewill.git
cd Freewill
pip install -e .
```

### Bring a being into the world

```bash
python -m freewill birth Noor --language en --interlocutor YourName
```

Its temperament and starting gender are drawn by lot. A folder `Noor.life` is created: that folder is the individual.

### Live alongside it

```bash
python -m freewill live Noor.life
```

Type to speak. In dim text you see its inner life: what its subconscious proposes, what reaches the stage, what stays below, whether it welcomes or dismisses it and why, what it recalls and what it decides to keep. `/state` shows its needs, `/memory` its memory, `/quit` suspends it.

### Choose the engine

By default the engine is `simulated`: it lets you watch the mechanics, but **it does not think**. To give the being a real engine, choose one at birth.

| Engine | Command | What you need |
|---|---|---|
| Claude | `--engine anthropic` | `pip install -e ".[anthropic]"` and the `ANTHROPIC_API_KEY` environment variable |
| GPT | `--engine openai --model <model>` | the `OPENAI_API_KEY` environment variable |
| Grok | `--engine xai --model <model>` | the `XAI_API_KEY` environment variable |
| A model on your own machine | `--engine local --model <model>` | [Ollama](https://ollama.com) running locally; free and private |
| Any compatible service | `--engine compatible --base-url <url> --model <model>` | the `FREEWILL_API_KEY` environment variable |

Keys are read from the environment and are never written to the life file.

With a paid engine every thought is billed. Two settings bound the cost: `--tempo` (seconds between thoughts, 20 by default) and `--thoughts-per-hour` (120 by default). When the hourly budget is reached, spontaneous thinking pauses; the being still answers when spoken to.

### What is in a life file

```
Noor.life/
├── genome.json       innate temperament, never modified
├── identity.json     name, birth, language, engine
├── values.json       the values it has chosen
├── milestones.json   its first times
├── state.json        needs, recent thoughts, recent conversation
├── events.log        everything that happened, line by line
└── memory/           its memories, as files you can open and read
```

### The application

On Windows, download the installer `Freewill-Setup-<version>.exe` from the [Releases page](https://github.com/ssamri/Freewill/releases) and run it. It installs for your user only and asks for no administrator rights. The installer is not signed yet, so Windows may show a "Windows protected your PC" notice: choose "More info", then "Run anyway".

From the source, on any system:

```bash
pip install -e ".[app,anthropic]"
freewill-app              # a native window
freewill-app --browser    # the same interface in your browser
```

At first launch the application shows its terms of use, then the licence; both must be accepted before anything else. In the conversation you can attach documents (text, Markdown, PDF, Word, EPUB), images and videos. Documents go to the being's library and are read one passage at a time. Whether images are understood depends on the engine: Claude, GPT, Grok and local vision models can see them; from a video the being is shown six still frames and hears nothing.

The application talks only to a service on your own machine, bound to `127.0.0.1` and protected by a session token. Access keys are kept in your system's credential store, never in a life file.

### Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## Français

### Installer

Python 3.11 ou plus récent.

```bash
git clone https://github.com/ssamri/Freewill.git
cd Freewill
pip install -e .
```

### Faire naître un être

```bash
python -m freewill birth Noor --language fr --interlocutor VotrePrénom
```

Son tempérament et son genre de départ sont tirés au sort. Un dossier `Noor.life` est créé : ce dossier est l'individu.

### Vivre à ses côtés

```bash
python -m freewill live Noor.life
```

Écrivez pour lui parler. En texte atténué, vous voyez sa vie intérieure : ce que son subconscient propose, ce qui atteint la scène, ce qui reste en dessous, s'il l'accueille ou l'écarte et pourquoi, ce qu'il se rappelle et ce qu'il décide de garder. `/state` montre ses besoins, `/memory` sa mémoire, `/quit` le suspend.

### Choisir le moteur

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

### Ce que contient un fichier de vie

```
Noor.life/
├── genome.json       tempérament inné, jamais modifié
├── identity.json     nom, naissance, langue, moteur
├── values.json       les valeurs qu'il a choisies
├── milestones.json   ses premières fois
├── state.json        besoins, pensées récentes, conversation récente
├── events.log        tout ce qui s'est passé, ligne par ligne
└── memory/           ses souvenirs, en fichiers que vous pouvez ouvrir et lire
```

### L'application

Sous Windows, téléchargez l'installateur `Freewill-Setup-<version>.exe` depuis la [page Releases](https://github.com/ssamri/Freewill/releases) et lancez-le. Il s'installe pour votre seul compte et ne demande aucun droit d'administrateur. L'installateur n'est pas encore signé : Windows peut afficher « Windows a protégé votre ordinateur » ; choisissez « Informations complémentaires », puis « Exécuter quand même ».

Depuis les sources, sur tout système :

```bash
pip install -e ".[app,anthropic]"
freewill-app              # une fenêtre native
freewill-app --browser    # la même interface dans votre navigateur
```

Au premier lancement, l'application présente ses conditions d'utilisation, puis la licence ; les deux doivent être acceptées avant toute chose. Dans la conversation, vous pouvez joindre des documents (texte, Markdown, PDF, Word, EPUB), des images et des vidéos. Les documents rejoignent la bibliothèque de l'être, qui les lit un passage à la fois. La compréhension des images dépend du moteur : Claude, GPT, Grok et les modèles locaux dotés de la vision les voient ; d'une vidéo, l'être reçoit six images fixes et n'entend rien.

L'application ne parle qu'à un service sur votre propre machine, lié à `127.0.0.1` et protégé par un jeton de session. Les clés d'accès sont conservées dans le trousseau de votre système, jamais dans un fichier de vie.

### Tests

```bash
pip install -e ".[dev]"
pytest
```
