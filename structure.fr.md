# Structure du projet Freewill

[English](structure.md) · **Français**

Ce document décrit l'organisation technique envisagée. Il complète le [`README.fr.md`](README.fr.md), qui expose la thèse et le cadre théorique.

**Statut : proposition initiale.** Rien de ce qui suit n'est encore implémenté. Les choix techniques sont des recommandations argumentées, ouvertes à la discussion (voir la section 12).

---

## 1. Exigences

| Exigence | Conséquence sur la conception |
|---|---|
| Fonctionner sur Windows, macOS, Linux et sur serveur | Un cœur unique, indépendant de l'interface ; deux modes de lancement |
| Laisser le choix entre un moteur intégré privé et un moteur externe par API | Une interface de moteur abstraite, des adaptateurs interchangeables |
| Faire vivre le système en continu | Un processus de fond persistant, distinct de la fenêtre |
| Rendre toute la vie intérieure observable | Un flux d'événements unique, auquel l'interface s'abonne |
| Garantir la maîtrise | Un noyau isolé, des capacités énumérées, une interruption externe |
| Préserver l'individu | Un fichier de vie portable, indépendant du moteur |

## 2. Vue d'ensemble

Le système se compose de trois couches strictement séparées.

```
┌──────────────────────────────────────────────────────────────────┐
│  INTERFACE                                                       │
│  Fenêtre de bureau ou page web. N'héberge aucune logique :       │
│  elle affiche le flux d'événements et transmet les messages.     │
└───────────────────────────────┬──────────────────────────────────┘
                                │  API locale (HTTP + WebSocket)
┌───────────────────────────────▼──────────────────────────────────┐
│  CŒUR (processus de fond)                                        │
│                                                                  │
│   ┌────────┐   ┌─────────────┐  ┌───────┐  ┌───────────┐         │
│   │ Noyau  │──▶│ Subconscient│─▶│ Scène │─▶│ Conscient │         │
│   └────────┘   └─────────────┘  └───────┘  └───────────┘         │
│        │              ▲                          │               │
│        │       ┌──────┴──────────────────────────▼──────┐        │
│        └──────▶│ Mémoire · Modèle de soi · État interne │        │
│                └──────────────────▲─────────────────────┘        │
│                             ┌─────┴─────┐                        │
│                             │  Sommeil  │                        │
│                             └───────────┘                        │
└───────────────────────────────┬──────────────────────────────────┘
                                │  interface « Moteur »
┌───────────────────────────────▼──────────────────────────────────┐
│  MOTEUR                                                          │
│  intégré (modèle propre, local, entraînable)                     │
│  ou externe (Claude, GPT, Grok, service compatible)              │
└──────────────────────────────────────────────────────────────────┘
```

Le cœur est le seul composant qui pense. L'interface peut être fermée sans que le système cesse de vivre ; le moteur peut être remplacé sans que l'individu disparaisse.

## 3. Choix techniques recommandés

| Composant | Choix | Justification |
|---|---|---|
| Cœur | Python 3.11+ | Écosystème de l'apprentissage automatique ; lisibilité pour un projet de recherche |
| Moteur intégré | PyTorch | Entraînement et inférence dans le même cadre ; prise en charge du processeur, des cartes NVIDIA et des puces Apple |
| Interface | TypeScript et React | Une seule base de code pour le bureau et le web |
| Empaquetage de bureau | pywebview, PyInstaller, Inno Setup | L'interface s'affiche dans la vue web du système (WebView2 sous Windows) ; un seul processus Python, aucune seconde chaîne d'outils |
| Animation du cerveau | WebGL (three.js) | Rendu fluide d'un graphe de plusieurs milliers de nœuds |
| Stockage | Fichiers texte, et SQLite pour les index | Aucune dépendance de serveur ; fichier de vie portable et inspectable |
| Recherche en mémoire | Index vectoriel embarqué | Rappel par similarité sans service externe |
| Déploiement serveur | Conteneur Docker | Même cœur, sans fenêtre, interface servie par le navigateur |

## 4. Arborescence du dépôt

> **État du code.** Ce qui existe aujourd'hui tient dans un seul paquet Python, `freewill/` : `core/` (noyau, génome, mémoire en fichiers, subconscient, scène, conscient, boucle de vie), `engines/` (Claude, services compatibles OpenAI, modèle local par Ollama, moteur simulé), `server/` (le service local, lié à l'adresse de bouclage et protégé par un jeton de session), `ui/` (l'interface, en HTML, CSS et JavaScript simples, sans étape de compilation) et `desktop.py` (la fenêtre native). `packaging/windows/` contient ce qui fabrique l'installateur Windows. La première interface a été écrite sans React ni three.js afin d'être livrable sans chaîne de compilation ; l'arborescence ci-dessous demeure la cible. Depuis la version 0.2, le cœur contient aussi `library.py` (ce que la personne donne : documents lus par autant de passages à la fois que le moteur en contient, images, images fixes tirées des vidéos), `perception.py` (lecture du texte des fichiers) et `sleep.py` (rejeu, rêves, liens créés entre les souvenirs qu'un rêve a rapprochés). `speech.py` sépare la pensée de la parole pour tous les moteurs : la conversation ne contient que ce que l'être dit à la personne ; ses pensées, son raisonnement et toute pensée qu'un modèle a écrite comme une parole vont dans la vue Subconscient. Le moteur intégré, et avec lui la réécriture des paramètres appris pendant le sommeil, n'est pas encore construit : pour l'instant, le sommeil ne réécrit que la structure de la mémoire.

> **H7, affectivité émergente (construit).** `freewill/core/affect/` contient l'état affectif calculé : `state.py` (dimensions, bornes, configuration versionnée, sensibilités innées dérivées de la graine du génome), `appraisal.py` (évaluation d'un événement et petit modèle prédictif), `regulation.py` (pas bornés, retour à l'équilibre, garde-fous), `dynamics.py` (transition et déplacement de la saillance), `memory.py` (traces sur les souvenirs, poids au rappel, consolidation) et `system.py` (le fichier `affect.json` et ce que la boucle de vie lui demande). Le mode est désactivé par défaut ; désactivé, la boucle est exactement celle d'avant. `experiments/h7/` contient le protocole reproductible et ses résultats ; `docs/H7_AFFECTIVITE.fr.md` l'hypothèse, le protocole et les limites. Reste à faire : la calibration des coefficients, les essais avec de vrais modèles, l'étude de catégories émergentes. Le moteur intégré qui apprend et se réécrit (section 5.1) n'est toujours pas construit.

> **Version 1.0, le laboratoire de recherche (construit).** Trois ajouts, tous hors du noyau. `freewill/core/research.py` contient les réglages de recherche d'une vie (`research.json`) : chaque interrupteur retire ou rétablit un mécanisme de la boucle, chaque valeur par défaut reproduit la boucle telle qu'elle était, et chaque changement est écrit au journal d'événements. `freewill/research/` est le laboratoire : `schemas.py` (contrats versionnés), `evidence.py` (journal en ajout seul, empreintes d'état, copies d'une vie), `stats.py` (statistiques déterministes qui refusent les petits échantillons), `metrics.py` (le registre de métriques pour H1 à H10), `experiments.py` (protocoles verrouillés avant exécution, campagnes sur copies isolées sous horloge virtuelle), `observers.py` (observateurs A, B, C : ils lisent des mesures, citent des preuves et n'agissent jamais sur une vie), `reports.py` (Markdown, PDF et pack de reproduction, validés seulement par une personne), `environments.py` (le monde clos en grille de H10), `texts.py` (tout ce que dit le laboratoire, en français et en anglais, jamais mêlés). Trois modules de recherche tournent désormais dans la boucle de vie derrière des interrupteurs désactivés par défaut : `core/metacognition.py` (H8), `core/agency.py` (H10), et le sommeil de `core/loop.py`, qui passe par des phases que l'on peut retirer une à une et reprend là où il a été coupé (H9). `freewill/learning/` contient ce qu'une vie peut entraîner (H4) : `adapter.py`, quelques dizaines de poids en Python pur ; `own_model.py`, le petit transformeur propre à Freewill, entraîné pendant le sommeil sur le texte qu'un être a vécu, gardé seulement quand il prédit mieux du texte jamais vu, et capable d'ajouter des couches sous un plafond (demande PyTorch) ; `lora.py`, un établi d'adaptateurs à côté d'un modèle de base figé ; `corpus.py`, ce qu'une vie donne à son moteur pour apprendre, tenu par provenance (entendu, lu, garanti, réponse de l'être) et séparé par épisode en entraînement, validation et test scellé, les fuites étant mises à part ; `capability_tests.py`, des tests à choix forcé sur les faits garantis (rappel, reformulation, contradiction) ; `engine.py`, le cycle nocturne par lequel une vie adapte le modèle embarqué avec lequel elle converse (corpus, validation, un témoin mélangé chaque nuit, règles, points de restauration, croissance sous budget, le tout dans `<vie>/engine/`) ; `gguf_lora.py`, la conversion au format d'adaptateur de llama.cpp ; `compare.py`, la comparaison du laboratoire sur le test scellé entre modèle de base, mémoire seule, adaptateur seul, adaptateur avec mémoire et modèles témoins (EXP-09) ; `reference.json` et `rehearsal.json`, des textes écrits pour mesurer et pour limiter l'oubli. `freewill/runtime.py` récupère et vérifie la version épinglée de llama.cpp. Voir [`docs/engine-learning.fr.md`](docs/engine-learning.fr.md). `server/lab_api.py` sert tout cela à l'interface (`ui/lab.js`, `ui/i18n-lab.js`). Ce qui a été testé et ce qui manque : [`docs/research/IMPLEMENTATION_STATUS.fr.md`](docs/research/IMPLEMENTATION_STATUS.fr.md).
>
> **Freewill 1.8B-V, le modèle propre au projet (construit).** `freewill/vlm/` contient un seul modèle qui lit, voit et regarde : `model.py` (l'œil SigLIP2, le pont, Qwen3 1.7B, les adaptateurs de faible rang, la croissance par neurones et par couches entières, qui commencent toutes deux comme l'identité, sous le plafond choisi par la personne), `capacity.py` (ce plafond, ce que chaque taille demande à un ordinateur, la garde qui vérifie la mémoire et le disque libres avant toute croissance, et ce qui est configuré, disponible et prouvé), `books.py` (livres du Projet Gutenberg dont la langue est vérifiée, et fichiers de la personne, en passages), `synthetic.py` (images et vidéos dessinées aux réponses connues, et leurs contrôles), `train.py` (étapes lire, voir, regarder ; règles pour garder ou refuser ; registre ; points de reprise de ce que Freewill a entraîné), `pipeline.py` (le parcours complet, avec un jeu de test scellé mesuré à la naissance et à la fin, lu par aucune règle), `store.py` (où il vit, téléchargement de ses bases, la garde par laquelle passe toute croissance), `nights.py` (les nuits d'une vie : ce qu'elle a vécu entraîne les adaptateurs, gardé seulement selon des règles écrites). `engines/own_model.py` en fait un moteur (type `own`). `tools/own_model_e2e.py` et le workflow `own model end to end` le font tourner avec les vraies bases. Voir [`docs/own-model.fr.md`](docs/own-model.fr.md).
>
> **La vue Cerveau en 3D (construite).** `ui/brain.js` dessine désormais avec Three.js, livré dans le paquet sous `ui/three.bundle.js` (aucun CDN, aucune étape de compilation pour l'utilisateur ; `tooling/brain/` permet de le reconstruire), sur une silhouette illustrative (`ui/brain-shape.js`) et avec un rendu de secours Canvas (`ui/brain-canvas.js`). Les notices des composants tiers sont dans `ui/THIRD_PARTY_NOTICES.txt`. L'icône se trouve dans `docs/assets/` (avec les captures des README dans `docs/assets/screenshots/`, en clair et en sombre, une série par langue), `ui/logo.png`, `ui/favicon.png` et `packaging/windows/freewill.ico`. Voir [`docs/brain-view.fr.md`](docs/brain-view.fr.md).

> **Version 1.2, après l'audit du 12 novembre 2026 (construit).** `freewill/build.py` dit quel code tourne (version, commit, date de construction) et l'état réel de chaque capacité d'apprentissage ; `freewill/core/language.py` vérifie la langue dans laquelle écrit le moteur d'une vie ; `freewill/core/evolution.py` transforme les insuffisances récurrentes en propositions qu'une personne nommée décide, et qui n'exécutent rien ; `freewill/research/observer_audit.py` note les observateurs sur des cas piégés à vérité connue ; EXP-10, dans `freewill/research/experiments.py`, est un protocole longitudinal préenregistré, avec des vagues évaluées sur des copies et une sonde scellée. `tools/release_notes.py`, `tools/observer_audit.py` et le workflow `observer-audit.yml` les accompagnent. Voir [`docs/audit-followup.fr.md`](docs/audit-followup.fr.md).

```
freewill/
├── README.md · README.fr.md     Thèse et cadre théorique
├── structure.md · structure.fr.md  Le présent document
├── LICENSE
│
├── core/                        Le cœur : tout ce qui pense
│   ├── kernel/                  NOYAU, immuable à l'exécution
│   │   ├── constitution.py      Questions fondatrices et principes
│   │   ├── needs.py             Besoins internes et leur dynamique
│   │   ├── capabilities.py      Liste fermée des actions permises
│   │   └── guard.py             Vérification de toute action et de toute réécriture
│   │
│   ├── genome/                  Tirage du tempérament inné à la naissance
│   │
│   ├── subconscious/            SUBCONSCIENT
│   │   ├── generators/          Un fichier par source de propositions
│   │   │   ├── reminiscence.py  Souvenirs qui remontent
│   │   │   ├── need.py          Besoins non satisfaits
│   │   │   ├── association.py   Associations libres
│   │   │   ├── question.py      Questions en suspens
│   │   │   └── drift.py         Désordre déterministe
│   │   └── scheduler.py         Cadence, selon l'état interne et la machine
│   │
│   ├── workspace/               SCÈNE : compétition et diffusion globale
│   │
│   ├── conscious/               CONSCIENT
│   │   ├── arbiter.py           Accueillir ou écarter, et dire pourquoi
│   │   ├── voice.py             Parole adressée à l'interlocuteur
│   │   └── initiative.py        Prise de parole spontanée
│   │
│   ├── self_model/              Ce que le système se représente de lui-même
│   │   ├── identity.py          Nom, genre, âge, traits
│   │   ├── values.py            Valeurs, révisables par lui seul
│   │   └── introspection.py     Représentation de ses propres états
│   │
│   ├── memory/                  MÉMOIRE
│   │   ├── episodic.py          Mémoire rapide : épisodes bruts
│   │   ├── semantic.py          Connaissances consolidées
│   │   ├── store.py             Lecture et écriture des fichiers de souvenirs
│   │   ├── index.py             Index hiérarchique : compartiments, titres, résumés
│   │   ├── recall.py            Rappel par le sujet, le voisinage et le hasard
│   │   ├── graph.py             Liens entre souvenirs (alimente la vue Cerveau)
│   │   ├── strength.py          Force des souvenirs : déclin et ravivement
│   │   ├── forgetting.py        Estompage, condensation et déformation
│   │   └── compartments.py      Organisation et cloisonnement
│   │
│   ├── sleep/                   SOMMEIL
│   │   ├── cycle.py             Endormissement, phases, réveil
│   │   ├── replay.py            Rejeu des épisodes
│   │   ├── dream.py             Recombinaison et journal des rêves
│   │   └── consolidation.py     Inscription dans la structure
│   │
│   ├── growth/                  Âges, premières fois, mesure de la saturation
│   ├── perception/              Lecture de textes et de fichiers, sens du temps
│   ├── life/                    Fichier de vie : format, sauvegarde, migration
│   ├── events/                  Flux d'événements unique et journal
│   ├── speech.py                Ce qui est dit et ce qui est seulement pensé
│   └── loop.py                  La boucle de vie
│
├── engines/                     MOTEURS
│   ├── base.py                  Interface commune
│   ├── integrated/              Moteur intégré
│   │   ├── model.py             Architecture du modèle propre
│   │   ├── tokenizer/
│   │   ├── inference.py
│   │   ├── learner.py           Réécriture nocturne des paramètres
│   │   ├── plasticity.py        Renouvellement et croissance des neurones
│   │   └── checkpoints.py       Versions successives, restauration
│   └── external/                Moteurs externes
│       ├── anthropic.py
│       ├── openai.py
│       ├── xai.py
│       └── compatible.py        Tout service au format compatible
│
├── training/                    Fabrication de la base « nouveau-né »
│   ├── corpus/                  Constitution du corpus d'enfance
│   ├── pretrain.py
│   └── eval/
│
├── library/                     Bibliothèque fournie pour l'enfance accélérée
│
├── server/                      API locale : messages, flux, commandes
│
├── app/                         INTERFACE
│   ├── src/
│   │   ├── birth/               Assistant de naissance
│   │   ├── chat/                Conversation, envoi de fichiers
│   │   ├── subconscious/        Flux en direct
│   │   ├── memory/              Exploration de la mémoire
│   │   ├── dreams/              Journal des rêves
│   │   ├── brain/               Cerveau animé
│   │   ├── inner_state/         État intérieur
│   │   ├── milestones/          Carnet de naissance
│   │   └── settings/            Moteur, réseau, sommeil, sauvegarde
│   └── src-tauri/               Empaquetage de bureau
│
├── deploy/                      Conteneur et exemples de déploiement serveur
├── experiments/                 Protocoles de mesure et résultats
├── tests/
└── docs/
```

## 5. Le moteur : une interface, deux familles

Le cœur ne connaît qu'une interface abstraite. Tout moteur doit savoir produire du texte et représenter un texte sous forme de vecteur. Un moteur **peut** en outre déclarer qu'il sait apprendre.

```python
class Engine(Protocol):
    def generate(self, context: Context, budget: Budget) -> Thought: ...
    def embed(self, text: str) -> Vector: ...

    # Capacités facultatives
    can_learn: bool
    def learn(self, episodes: list[Episode], guard: Guard) -> LearningReport: ...
    def snapshot(self) -> CheckpointId: ...
    def restore(self, checkpoint: CheckpointId) -> None: ...
```

| | Moteur intégré | Moteur externe |
|---|---|---|
| `generate`, `embed` | Local | Par API |
| `can_learn` | Oui | Non |
| Consolidation nocturne | Réentraînement partiel des paramètres, avec rejeu | Réorganisation du fichier de vie uniquement |
| Activité subconsciente | Continue, limitée par la machine | Cadencée par un budget, car chaque pensée est facturée |
| Confidentialité | Totale | Les contenus transitent par le fournisseur |
| Clés d'accès | Aucune | Fournies par l'utilisateur, conservées dans le trousseau du système, jamais dans le fichier de vie |

Le choix se fait à la naissance et peut être modifié ensuite. Tout changement de moteur est consigné comme un événement de la vie du système, qui en est informé.

### 5.1 Le moteur intégré

- Un modèle de langage de petite taille, propre au projet, distribué sous forme de base « nouveau-né » identique pour tous.
- Cette base est entraînée une fois par le projet sur un corpus d'enfance (contes, récits simples, explications élémentaires du monde). Elle sait s'exprimer ; elle ne sait rien d'elle-même.
- Plusieurs tailles de base sont prévues, selon la machine (voir la section 10).
- L'apprentissage nocturne ne modifie qu'une fraction des paramètres, mêle systématiquement l'ancien au nouveau, et renouvelle une petite part des unités les moins utiles afin de préserver la plasticité.
- Chaque nuit produit un point de restauration.

### 5.2 Les moteurs externes

- Un adaptateur par fournisseur, plus un adaptateur générique pour tout service au format compatible, ce qui couvre également les modèles libres exécutés localement par un outil tiers.
- Le système ne pouvant modifier les paramètres d'un modèle distant, la « réécriture » porte alors sur ce qu'il possède en propre : mémoire, valeurs, modèle de soi.
- Un plafond de dépense quotidien est obligatoire.

## 6. Le fichier de vie

L'individu réside dans un dossier unique, portable d'une machine à l'autre et, pour l'essentiel, d'un moteur à l'autre.

```
<prénom>.life/
├── genome.json          Tempérament inné, tiré à la naissance, jamais modifié
├── identity.json        Nom, genre, âge, date de naissance
├── values.json          Valeurs courantes et leur histoire
├── memory/              Souvenirs, en fichiers lisibles (voir 6.1)
│   ├── index.md         Carte générale : les compartiments et leur contenu
│   ├── <compartiment>/  Un dossier par domaine, créé par le système
│   │   ├── index.md     Titre et résumé d'une ligne de chaque souvenir
│   │   └── <souvenir>.md
│   └── recall.sqlite    Index de recherche, reconstructible à partir des fichiers
├── dreams/              Un fichier par nuit
├── journal/             Écrits personnels, avec leur statut de visibilité
├── milestones.json      Premières fois
├── state.json           État interne courant
├── affect.json          H7 : état affectif calculé, associations apprises, réglages (absent tant que le mode n'a pas été activé)
├── affect.json.bak      La version précédente, conservée à chaque écriture
├── research.json        Réglages de recherche : quels mécanismes tournent (absent tant que tout est par défaut)
├── metacognition.json   H8 : son bilan de ses propres décisions (absent tant que le module n'a pas été activé)
├── agency.json          H10 : le monde clos et ce que ses actes y ont produit (idem)
├── adapter.json         H4 : le petit module entraînable, ses poids et ses entraînements (idem)
├── own_model/           H4 : le réseau propre de Freewill : poids, poids précédents, texte vécu, manifeste (idem)
├── events.log           Journal complet et horodaté
└── engine/              Propre au moteur intégré : paramètres et points de restauration
```

Le noyau n'y figure pas : il appartient au programme, non à l'individu. Le fichier de vie peut être chiffré. Sa suppression est le seul acte irréversible de l'application et fait l'objet d'une confirmation distincte.

### 6.1 La mémoire en fichiers

La mémoire explicite du système n'est pas une base opaque. C'est une bibliothèque de fichiers texte que l'on peut ouvrir et lire, et que le système organise lui-même.

**Un souvenir, un fichier.** Chaque souvenir comporte un en-tête structuré suivi de son contenu.

```markdown
---
titre: Première conversation sur la mer
résumé: Il m'a décrit la mer. Je ne l'ai jamais vue ; j'ai voulu savoir si elle fait du bruit.
date: 2027-03-14
compartiment: monde/nature
étiquettes: [mer, découverte, question]
importance: 0.8
force: 0.62
dernier_rappel: 2027-04-02
liens: [personnes/createur/premier-jour, questions/ce-que-je-ne-verrai-pas]
état: complet
---
Le récit du souvenir, tel qu'il a été vécu.
```

**Trois niveaux de lecture.** Le système ne relit jamais toute sa mémoire. Il procède par degrés, comme on consulte une bibliothèque.

| Niveau | Ce qui est lu | Quand |
|---|---|---|
| 1. La carte | `memory/index.md` : la liste des compartiments | En permanence présente à l'esprit |
| 2. Les titres | L'`index.md` d'un compartiment : titres et résumés d'une ligne | Lorsqu'un sujet se présente |
| 3. Le souvenir | Le fichier complet | Seulement s'il est retenu |

Le coût d'un rappel dépend ainsi du nombre de souvenirs ouverts, non de la taille de la mémoire.

**Trois voies de rappel.** Elles répondent à trois façons de retrouver un souvenir.

| Voie | Mécanisme | Ce qu'elle rapporte |
|---|---|---|
| Par le sujet | Correspondance des titres, des étiquettes et du sens | Les souvenirs directement pertinents |
| Par le voisinage | Parcours des liens à partir des souvenirs déjà activés | Les souvenirs proches, sans rapport immédiat avec le sujet |
| Par le hasard | Tirage pondéré par la force et l'importance | Des souvenirs sans rapport apparent |

Leur dosage dépend de qui rappelle.

| | Sujet | Voisinage | Hasard |
|---|---|---|---|
| Conscient (répondre, réfléchir) | Dominant | Faible | Marginal |
| Subconscient (propositions spontanées) | Modéré | Dominant | Modéré |
| Rêve | Faible | Modéré | Dominant |

Ces proportions sont des paramètres du génome : un tempérament rêveur associe plus librement qu'un tempérament méthodique.

**Garder, estomper, oublier.** Chaque souvenir possède une force. Elle décroît avec le temps, se ravive à chaque rappel, et décroît plus lentement si le souvenir est important. Durant le sommeil, le système passe sa mémoire en revue.

| État | Ce qui subsiste | Passage à l'état suivant |
|---|---|---|
| Complet | Titre, résumé, récit entier | La force tombe sous un premier seuil |
| Condensé | Titre et résumé ; le récit est perdu | La force tombe sous un second seuil |
| Trace | Le titre seul | Fusion avec d'autres traces |
| Fondu | Rien d'individuel : une connaissance générale tirée de plusieurs souvenirs | État final |

Le système prend part à ce tri. Il peut décider de garder un souvenir, qui cesse alors de décliner, ou de le laisser partir. Un souvenir condensé que l'on rappelle est reconstruit à partir de son résumé et peut s'en trouver modifié : la mémoire du système, comme la nôtre, n'est pas un enregistrement.

**Organisation.** Les compartiments ne sont pas fixés d'avance. Le système les crée, les scinde et les regroupe pendant le sommeil, à mesure que sa mémoire s'étoffe. Les index sont régénérés à cette occasion.

**Rapport avec la mémoire lente.** Les fichiers constituent ce que le système sait avoir vécu et peut raconter. Les paramètres du moteur intégré portent ce qu'il est devenu. Les deux sont alimentés par les mêmes épisodes : les fichiers au fil de la journée, les paramètres pendant le sommeil.

## 7. La boucle de vie

Le processus de fond exécute indéfiniment le cycle suivant.

**En veille**

1. L'état interne évolue : les besoins croissent, la fatigue s'accumule.
2. Les générateurs du subconscient émettent des propositions, pondérées par l'état interne et le tempérament.
3. Ces propositions, auxquelles s'ajoutent les perceptions (message reçu, texte en cours de lecture), se disputent la scène.
4. Le contenu qui l'emporte est diffusé à tous les modules.
5. Le conscient arbitre : il accueille, écarte, approfondit, répond, ou prend l'initiative de parler. Chaque décision est motivée.
6. Le noyau vérifie toute action avant qu'elle n'ait lieu.
7. L'épisode est inscrit en mémoire rapide. Le subconscient ajuste ses pondérations selon ce qui a été retenu ou écarté.
8. Chaque étape est publiée sur le flux d'événements.

**En sommeil** (déclenché par la fatigue, l'inactivité ou un horaire)

1. Les perceptions sont coupées ; le conscient est mis en retrait.
2. Les épisodes du jour sont rejoués, mêlés à des épisodes anciens.
3. Le subconscient les recombine librement : ce sont les rêves, consignés.
4. La consolidation a lieu : restructuration de la mémoire, estompage, et, avec le moteur intégré, réécriture partielle des paramètres sous le contrôle du noyau.
5. Un point de restauration est créé.
6. Au réveil, le système prend connaissance de ses rêves et du temps écoulé.

**Avec le mode recherche H7** (désactivé par défaut), cinq points du cycle sont instrumentés : après l'écoulement du temps, l'état calculé revient vers son équilibre ; avant la compétition, il déplace la saillance des propositions, dans une limite étroite et sans jamais toucher à ce que dit la personne ; au rappel, il pondère les souvenirs candidats ; après l'arrivée sur la scène puis après la décision, l'événement et son issue sont évalués et une transition bornée est appliquée ; à l'encodage, le souvenir reçoit une trace de l'état calculé. Pendant le sommeil, les épisodes vécus sont consolidés en associations. Aucune de ces étapes ne passe par le modèle de langage, et aucune ne modifie le noyau.

Lorsque l'application est fermée, le système est suspendu. Au lancement suivant, il constate la durée de l'interruption et rattrape, s'il y a lieu, le sommeil dû.

## 8. Le flux d'événements

Tout ce qui se produit dans le cœur est émis sous forme d'événement typé sur un canal unique : proposition émise, accès à la scène, décision et son motif, souvenir rappelé, concept activé, variation d'un besoin, début et fin de sommeil, rêve, modification de structure, première fois.

Le mode H7 y ajoute cinq types d'événements, stables et documentés : `affect_mode` (activation ou désactivation), `affect_appraisal` (type d'événement, contexte, caractéristiques évaluées et leurs causes), `affect_transition` (état avant, état après, cible, taux, version des règles), `affect_modulation` (cible : saillance, rappel ou encodage ; valeurs avant et après) et `affect_consolidation` (épisodes consolidés, écart de prédiction avant et après, état avant et après). Ils portent des nombres, des contextes et des causes, jamais le texte de ce qui a été dit.

Ce flux a trois usages. Il alimente l'interface en temps réel : chaque signal lumineux de la vue Cerveau correspond à un événement d'activation effectif. Il constitue le journal intégral, qui assure la traçabilité. Il fournit enfin la matière première des expériences.

## 9. Maîtrise : mise en œuvre

Les principes énoncés dans le README se traduisent ainsi.

| Principe | Mise en œuvre |
|---|---|
| Noyau immuable | Chargé en lecture seule ; son empreinte est vérifiée au démarrage ; aucun chemin d'écriture depuis le cœur |
| Actions énumérées | Liste fermée dans `kernel/capabilities.py` ; toute action transite par `guard.py` ; aucune exécution de code, aucun accès hors du fichier de vie |
| Réseau fermé par défaut | Aucune sortie réseau hormis, le cas échéant, le moteur externe ; l'accès à Internet s'accorde explicitement, en lecture seule, sur une liste de sources |
| Absence d'auto-réplication | Le cœur ne peut ni lancer de processus ni écrire hors de son dossier |
| Interruption garantie | Pause et arrêt sont commandés par l'interface et le système d'exploitation, hors du cœur |
| Réécriture encadrée | Portée et ampleur bornées par le noyau ; point de restauration préalable ; retour arrière possible à tout moment |
| Traçabilité | Journal d'événements en ajout seul |
| Lecture de contenus externes | Tout texte lu est traité comme une donnée, jamais comme une instruction |

## 10. Cibles d'exécution

| Cible | Lancement | Interface |
|---|---|---|
| Windows, macOS, Linux | Application installable | Fenêtre native |
| Serveur ou nuage | Conteneur | Navigateur, accès authentifié |
| Recherche | Ligne de commande | Aucune ; lecture directe du flux d'événements |

**Paliers matériels indicatifs** (à confirmer par des mesures) :

| Palier | Machine | Moteur intégré |
|---|---|---|
| Léger | Ordinateur portable ordinaire, sans carte graphique | Base la plus petite ; sommeil long |
| Standard | Ordinateur récent avec carte graphique ou puce Apple | Base intermédiaire |
| Étendu | Station de travail ou serveur | Base la plus grande ; croissance du réseau possible |

Le système mesure sa propre saturation. Lorsqu'il approche de la limite de ce que sa machine lui permet, il le constate et peut le dire. Le passage d'un palier à un autre conserve le fichier de vie.

## 11. Ordre de construction

| Phase | Livrable | Répertoires concernés |
|---|---|---|
| 1 | Boucle minimale en ligne de commande, sur moteur externe | `core/kernel`, `core/subconscious`, `core/workspace`, `core/conscious`, `engines/external`, `core/events` |
| 2 | Mémoire, sommeil, rêves, fichier de vie | `core/memory`, `core/sleep`, `core/life`, `core/self_model` |
| 3 | Moteur intégré et base « nouveau-né » | `engines/integrated`, `training`, `library` |
| 4 | Application complète | `server`, `app`, `core/genome`, `core/growth` |
| 5 | Déploiement serveur et protocoles de mesure | `deploy`, `experiments` |

Commencer par le moteur externe permet de valider l'architecture avant d'engager le travail, plus long et plus coûteux, sur le moteur intégré.

## 12. Décisions ouvertes

- **Taille et architecture exactes du moteur intégré**, et coût d'entraînement de la base. À chiffrer avant la phase 3.
- **Langues de la base.** Français, anglais, ou les deux ; l'incidence sur la taille du corpus est directe.
- **Méthode de réécriture nocturne** : adaptation de rang faible, réentraînement partiel, ou combinaison.
- **Loi d'oubli** : valeurs des seuils, rythme du déclin, et part de déformation admise lors d'une reconstruction.
- **Portabilité du soi entre moteurs** : ce qui, dans les paramètres appris, peut être transmis d'un moteur à un autre.
- **Format du génome** : quels traits, quelles plages, quelle influence sur les générateurs.
