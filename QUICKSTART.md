# Quickstart · Démarrage rapide

**English** below · **Français** plus bas

This is phase 1 of the roadmap: the minimal loop. A subconscious proposes, a stage selects, a conscious arbiter decides, and what matters is kept in a memory made of readable files. It runs in a terminal. Sleep, dreams, the project's own model and the graphical application come later.

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

### Tests

```bash
pip install -e ".[dev]"
pytest
```
