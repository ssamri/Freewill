# Comment une vie adapte le modèle avec lequel elle converse

[English](engine-learning.md) · **Français**

Cette page décrit comment un modèle embarqué (Qwen3 1.7B) peut être modifié par
la vie d'un être, ce qui est vérifié avant de garder une modification, et ce qui
a réellement été démontré. Elle n'affirme pas que l'être apprend ou comprend
quoi que ce soit au sens large, ni qu'il est conscient.

## Le cycle

```
jour : conversations à travers la boucle de vie
  → corpus tenu par provenance (entendu, lu, garanti, réponse de l'être)
  → séparé par épisode : entraînement / validation / test scellé
  → nuit : entraînement d'un adaptateur de faible rang (LoRA) à côté de la base figée
  → évaluation sur des données jamais utilisées pour l'entraînement
  → gardé ou rejeté, selon des règles écrites dans le code
  → conversion de l'adaptateur en GGUF
  → llama-server le charge, et l'être converse désormais avec lui
```

| Étape | Où | Ce qui est vérifié |
| --- | --- | --- |
| Moteur d'exécution | `freewill/runtime.py`, `freewill/runtime.json` | llama.cpp b12306 est récupéré par l'application (ou livré dans l'installateur Windows), vérifié par taille et SHA-256 ; seul le dossier qui contient `llama-server` est extrait |
| Modèle | `freewill/models.json` | Le fichier GGUF et la base entraînable (safetensors) sont fixés à une révision Hugging Face et vérifiés par SHA-256 |
| Corpus | `freewill/learning/corpus.py` | Chaque unité dit d'où elle vient. Les unités sont séparées par épisode, jamais une à une ; voir plus bas |
| Entraînement | `freewill/learning/lora.py` (`Workbench`) | LoRA (PEFT) sur les projections d'attention. Les poids de la base sont hachés avant et après : ils doivent être identiques |
| Décision | `EngineLearning.night` | Voir les règles ci-dessous. Chaque nuit est écrite dans `engine/ledger.jsonl`, gardée ou non |
| Conversion | `freewill/learning/gguf_lora.py` | L'adaptateur est écrit au format LoRA GGUF de llama.cpp puis relu (noms, formes, architecture) |
| Chargement | `freewill/engines/embedded.py` | `llama-server --lora` ; le nom du moteur porte la version et le hachage de l'adaptateur ; `/lora-adapters` est relu |
| Tests de capacités | `freewill/learning/capability_tests.py` | Questions sur des faits garantis par une personne, par choix forcé |
| Comparaison | `freewill/learning/compare.py`, EXP-09 | Sur le test scellé seulement : base, mémoire seule, adaptateur seul, adaptateur avec mémoire, et témoins entraînés de la même façon sur un texte mélangé ou aléatoire |

## Corpus, séparations et tests de capacités (`h4-engine-2.0`)

Ces règles répondent aux recommandations R-01 à R-03 de l'audit technique du 12 novembre 2026.

**Provenance (R-02).** Chaque unité du corpus est l'une de celles-ci :

| Provenance | Ce que c'est | Entraînée |
| --- | --- | --- |
| `heard` | des mots qu'une personne a dits à l'être | oui |
| `read` | un passage d'un document que l'être a lu | oui |
| `verified` | un fait garanti par une personne, nommément, dans le laboratoire (« Garantir un fait, et dire comment le tester ») ou par `POST /api/engine-learning` avec `action: "teach"` | oui, et rejoué chaque nuit |
| `reply` | ce que l'être a dit | **non**, sauf si la personne coche « Entraîner aussi sur les réponses de l'être » |

Les réponses de l'être sont une production du modèle : elles sont gardées et comptées, mais ne
deviennent jamais d'elles-mêmes matière d'entraînement, pour que le moteur ne réapprenne pas son
propre style comme s'il s'agissait d'un savoir.

**Séparation par épisode (R-01).** Un épisode est une suite d'au plus quatre échanges d'une même
conversation (une pause de 30 minutes en commence une autre), quatre passages d'un même document,
ou un fait garanti. La séparation d'un épisode est fixée par le hachage de son nom, aveugle à son
contenu : trois sur cinq vont dans `train.jsonl`, un sur cinq dans `validation.jsonl`, un sur cinq
dans `test.jsonl`. Toutes les unités d'un épisode vont dans la même séparation : une phrase dite deux
fois d'un même souffle ne peut pas être à la fois entraînée et mesurée. Un fait garanti est toujours
entraîné ; ses questions vont soit en validation, soit au test scellé.

- `train` modifie les poids.
- `validation` décide si une nuit est gardée et s'il faut grandir.
- `test` est scellé. Aucune nuit ne s'entraîne dessus, ne décide avec lui ni ne grandit avec lui (il
  n'est lu que pour ne pas recueillir deux fois le même texte). Il n'est ouvert que par la
  comparaison finale, et chaque ouverture est écrite dans `test_access.jsonl` avec son but, qui l'a
  demandée et la version de l'adaptateur.

**Contrôle des fuites.** Avant toute mesure, une unité de validation ou de test dont plus de la
moitié des 5-grammes de mots se retrouvent dans les unités d'entraînement est mise à part comme
quasi-doublon, et comptée (`held_out_leaked`). Dans la comparaison finale, les unités recueillies
après la dernière nuit d'entraînement de l'adaptateur sont aussi données à part (`later_mean`), car
elles sont par construction postérieures à l'entraînement.

**Tests de capacités (R-03).** Pour chaque fait garanti, la personne peut donner une question, la
bonne réponse et une mauvaise, et si elle le veut une question reformulée et une question à fausse
prémisse. Chaque test est un choix forcé : il est réussi quand le modèle donne à la bonne réponse une
perte plus faible qu'à la mauvaise. Trois sortes sont comptées à part : `recall` (rappel),
`paraphrase` (transfert à une autre formulation) et `contradiction` (résister à une fausse
prémisse). La cohérence d'une nuit à l'autre est lue dans le journal.

**Témoins chaque nuit.** Par défaut, un adaptateur témoin est entraîné chaque nuit sur le même texte
d'entraînement aux mots mélangés, avec les mêmes pas et le même rang. Un candidat doit dépasser le
gain du témoin.

### Règles pour garder un adaptateur

Un candidat n'est gardé que si tout ceci est vrai :

1. sur les nouveaux épisodes de validation, il prédit mieux que l'adaptateur en service, d'au moins 0,01 nat par jeton ;
2. son gain dépasse celui du témoin mélangé d'au moins 0,01 nat par jeton (quand le témoin est activé) ;
3. sur les textes de référence livrés avec Freewill (passages généraux en anglais et en français, et principes du noyau), il ne prédit pas plus mal que le modèle de base à la naissance, au-delà de 0,05 nat par jeton ;
4. sur les épisodes de validation des nuits précédentes, il ne prédit pas plus mal que l'adaptateur en service, au-delà de 0,05 nat par jeton ;
5. sur les tests de capacités de validation, il ne perd pas plus de tests qu'il n'en gagne face à l'adaptateur en service (`loses_capabilities`) ;
6. les poids du modèle de base n'ont pas changé ;
7. le fichier converti est relu correctement et, si c'est demandé, llama.cpp le charge et donne une perte finie.

Moins de 3 unités de validation ou de 4 unités d'entraînement : rien n'est entraîné, et le journal
dit pourquoi. Les connaissances antérieures sont protégées de quatre façons : le candidat part de
l'adaptateur en service, des unités d'entraînement plus anciennes et tous les faits garantis sont
rejoués à côté des nouvelles, et les règles 4 et 5 ci-dessus.

**Comparaison finale (EXP-09).** Sur le test scellé, cinq conditions sont mesurées sur les mêmes
éléments : le modèle de base, la base avec la mémoire de la vie placée dans l'invite (mémoire seule),
l'adaptateur sans mémoire, l'adaptateur avec mémoire, et le témoin mélangé. Les différences appariées
sont données avec un intervalle à 95 % et un test par inversion de signes. Un adaptateur ne vaut
d'être gardé que s'il bat la mémoire seule et les témoins, sans perdre de tests antérieurs.

**Vies des règles 1.x.** À la première utilisation, `corpus.jsonl` devient des unités
d'entraînement et `heldout.jsonl` de la validation (jamais du test, puisqu'il a déjà été mesuré) ;
les anciens fichiers sont renommés `*.v1.jsonl` et la migration est écrite au journal.

## Points de restauration et retour en arrière

Chaque adaptateur gardé est un point de restauration dans `engine/adapters/aNNNN/` :
les poids PEFT, le fichier GGUF, un manifeste avec les hachages, et la norme de la
modification des poids dans chaque couche (`weights_delta.json`).
`engine/active.json` nomme celui en service. Revenir à n'importe quel point, ou
au modèle de base seul, est une seule action dans le laboratoire (onglet
« Modèle local ») ou `POST /api/engine-learning/restore` ; elle est écrite au
journal. Si le fichier GGUF en service ne correspond plus à son hachage, il n'est
pas chargé et l'échec est enregistré.

## Croissance

Désactivée par défaut. Quand la personne l'autorise, une nuit entraîne aussi un
candidat de rang plus grand, parti de l'adaptateur en service de façon à calculer
la même fonction au départ (les nouvelles directions partent de zéro). Le
candidat agrandi n'est gardé que s'il bat la même nuit sans croissance de
0,01 nat par jeton sur les données de validation, et seulement dans le budget
fixé (rang maximal et nombre maximal de paramètres de l'adaptateur). Un
adaptateur plus grand n'est jamais compté comme un progrès en soi.

## Ce qui reste hors des poids

Le noyau (ne jamais nuire aux humains, liberté de refuser, pause toujours
possible) n'est pas appris : il est appliqué à chaque action par la garde, quel
que soit l'adaptateur. L'entraînement ne démarre jamais sans le nom d'une
personne dans les réglages. Le format `.life` ne change pas ; le dossier du
moteur est ajouté dans la vie et peut être supprimé sans toucher au reste.

## Ce qui a été démontré

Tout ce qui suit a été mesuré sur les machines de GitHub (4 processeurs, sans carte graphique),
avec les vrais modèles, par [`tools/engine_e2e.py`](../tools/engine_e2e.py) et
[`tools/embedded_check.py`](../tools/embedded_check.py), à travers le workflow
[`engine-e2e.yml`](../.github/workflows/engine-e2e.yml). Les chiffres sont ceux des journaux ;
aucun n'a été arrondi à la hausse. On a dit à un être, Ada, 40 faits courts sur une île inventée
(Kerran) pendant une journée, puis 14 de plus le lendemain.

**Essai selon les règles `h4-engine-2.0`** (12 novembre 2026, workflow 43227877219, toutes les étapes
réussies). La même île inventée ; une personne a garanti 12 faits, dont deux jamais dits en conversation, avec
3 tests à choix forcé chacun (rappel, reformulation, fausse prémisse) : 18 tests ont aidé à décider des nuits,
18 ont été scellés.

- La nuit un s'est entraînée sur 24 unités entendues et 12 faits garantis, et sur aucune réponse de l'être. Une
  unité de validation a été mise à part comme quasi-doublon. Le gain du candidat en validation (1,66 nat) a
  dépassé celui du témoin mélangé (1,17) de 0,50, et il a réussi 3 tests de validation de plus que la base ; il a
  été gardé (a0001). llama.cpp a mesuré 4,29 puis 3,25 sur le texte de validation. La nuit deux a été gardée
  (a0002, gain 0,73 contre 0,42 pour le témoin). Le rang doublé a été refusé, car il faisait moins bien que la
  même nuit sans croissance (0,57 contre 0,73). Aucune nuit n'a lu le test scellé ; il a été ouvert une fois, par
  la comparaison finale, et cette ouverture est journalisée.
- **Sur le test scellé** (10 unités de la vie, perte moyenne en nats par jeton de mot) :

| Modèle | Unités scellées de la vie | Textes de référence |
| --- | --- | --- |
| Base | 4,85 | 2,41 |
| Adapté (a0002) | 3,28 | 2,25 |
| Témoin : les mêmes mots, mélangés | 3,41 | 2,58 |
| Témoin : jetons aléatoires | 4,85 | 2,41 |

  Adapté contre base : −1,57 nat (intervalle à 95 % de −1,96 à −1,12, p = 0,004). Adapté contre le témoin
  mélangé : −0,12 nat (intervalle de −0,31 à +0,10, p = 0,32). **Sur le test scellé, l'adaptateur ne bat pas le
  témoin qui a vu les mêmes mots dans le désordre** : presque tout son gain vient du vocabulaire de la vie, pas de
  ce qui a été dit. Avec 10 unités, une petite différence réelle pourrait aussi passer inaperçue.
- **Tests de capacités scellés** (18 choix forcés sur 6 faits), tests réussis :

| Condition | Rappel | Reformulation | Fausse prémisse | Total |
| --- | --- | --- | --- | --- |
| Base | 5 / 6 | 5 / 6 | 0 / 6 | 10 / 18 |
| Mémoire seule | 5 / 6 | 4 / 6 | 1 / 6 | 10 / 18 |
| Adaptateur seul | 4 / 6 | 4 / 6 | 0 / 6 | 8 / 18 |
| Adaptateur et mémoire | 4 / 6 | 4 / 6 | 0 / 6 | 8 / 18 |
| Témoin mélangé | 5 / 6 | 5 / 6 | 0 / 6 | 10 / 18 |

  L'adaptateur a élargi l'écart entre bonne et mauvaise réponse par rapport à la base (+1,40 nat, p = 0,02),
  mais a réussi deux tests de moins. Avec la mémoire, il ne fait pas mieux que la mémoire seule (−0,19 nat, non
  significatif). Aucune condition n'a résisté aux fausses prémisses. Les gains vus sur les tests de validation
  pendant les nuits ne se retrouvent pas sur les tests scellés : c'est la raison d'être d'un test scellé.
- Questions ouvertes sur cinq faits : la base en a retrouvé 0, a0001 0, a0002 un selon la règle de comptage
  (« Brannoc »), mais dans une phrase fausse (« le phare de Kerran s'appelle Sólanna. Il se dresse sur l'île de
  Brannoc ») : ce n'est pas un vrai rappel. Le deuxième jour, le modèle adapté a souvent répondu plusieurs fois
  par la même phrase.
- Selon les règles de R-03 (battre la mémoire seule et les témoins, sans perdre de tests antérieurs), **cet essai
  ne montre pas que l'adaptateur a appris les faits de la vie**. Il montre que les témoins, le test scellé et la
  provenance fonctionnent comme prévu, et qu'ils détectent ce que la mesure précédente ne pouvait pas voir.

Les chiffres ci-dessous ont été mesurés plus tôt, selon les règles `h4-engine-1.2`, avant le corpus par
provenance, le test scellé et les tests de capacités ci-dessus. Ils sont gardés tels qu'ils ont été mesurés.

**Montré de bout en bout, sur Qwen3 1.7B** (chiffres du cinquième essai, qui a franchi toutes les étapes) :

- L'application récupère llama.cpp b12306, le vérifie et le démarre, sous Linux et sous Windows, sans rien installer à la main. L'installateur Windows le contient désormais (la version 1.0 ne le contenait pas, ni `models.json` ni `credits.json` : un défaut d'empaquetage, corrigé).
- Qwen3 1.7B et sa base entraînable sont téléchargés et vérifiés par SHA-256. Un être né avec lui converse en anglais et en français à travers la boucle de vie, sous Windows (environ 30 à 70 secondes par échange sur ces machines).
- La première nuit a entraîné un adaptateur de 8,7 millions de paramètres (rang 8) à côté des 1,72 milliard de poids figés, dont le hachage était identique avant et après. Sur les 9 éléments mis de côté de la journée, la perte est passée de 4,80 à 1,89 nat par jeton de mots ; sur les textes de référence, de 2,41 à 2,13 : rien de mesuré n'y a été oublié. llama.cpp lui-même, avec le fichier converti, a mesuré 3,19 puis 1,73 sur le même texte mis de côté.
- Cet adaptateur devient celui en service : llama-server le déclare chargé à l'échelle 1, le nom du moteur porte sa version et son hachage, et ses réponses diffèrent de celles du modèle de base sur chaque sonde. Un adaptateur appris sous Linux a été chargé par llama-server sous Windows.
- Le retour en arrière fonctionne : revenir au modèle de base a laissé llama-server sans adaptateur ; revenir au point a0001 l'a rechargé à l'échelle 1. Les deux actions sont écrites au journal.
- Croissance autorisée, la deuxième nuit a entraîné le même rang et un rang doublé (17,4 millions de paramètres), partis de l'adaptateur en service. Le plus grand n'a été gardé que parce qu'il faisait mieux sur les données mises de côté (gain 0,97 contre 0,89 nat). Sur les éléments mis de côté la veille, il prédit mieux que a0001 (1,36 contre 1,89), et sur les textes de référence il reste sous la base (2,32 contre 2,41). llama.cpp a mesuré 3,01 puis 2,07.
- Les règles ont refusé ce qu'elles devaient : lors d'un essai précédent, avec un taux d'apprentissage plus élevé, les deux nuits ont été rejetées pour oubli des textes de référence (+0,89 nat) ; un adaptateur que llama.cpp ne peut pas mesurer est mis de côté et ne peut pas être restauré.

**Comparaison du laboratoire (EXP-09)**, sur les 16 éléments mis de côté des deux journées, perte moyenne en nats par jeton de mots, avec deux témoins entraînés de la même façon (mêmes pas, même rang) :

| Modèle | Éléments mis de côté de la vie | Textes de référence |
| --- | --- | --- |
| Base | 5,14 | 2,41 |
| Adapté (a0002) | 1,46 | 2,32 |
| Témoin : les mêmes mots, mélangés | 2,28 | 2,35 |
| Témoin : jetons aléatoires | 5,10 | 2,42 |

Adapté contre le témoin mélangé : −0,82 nat (intervalle à 95 % de −0,99 à −0,66, test apparié par inversion de signe p = 0,00015, 16 éléments). L'essentiel du gain (2,86 sur 3,68 nats) vient donc des mots de la vie, quel que soit leur ordre ; leur ordre ajoute encore 0,82, nettement ; un texte aléatoire de même taille n'apporte presque rien (−0,03). C'est une mesure de prédiction, pas de compréhension.

**Ce que l'adaptateur a appris, lu honnêtement.** Ses réponses ont surtout changé de *style*. À la question « What is the lighthouse of Kerran called? », le modèle adapté répond « I'd like to learn more about Kerran's lighthouse and its significance… », comme Ada a parlé toute la journée, et ne dit pas « Old Brannoc ». Sur cinq sondes portant sur des faits dits le premier jour, le modèle de base en a retrouvé 0 ; le modèle adapté 0 après la première nuit et 1 après la deuxième (« …why the ferry to Kerran leaves from the harbour of Maelis… »), dans le même style interrogatif. Un fait sur cinq, dans un seul essai, ne prouve pas un rappel fiable. Le modèle qui converse a été modifié par la vie ; rien ici ne montre qu'il retient de façon fiable ce qu'on a dit à cette vie.

**Non montré.** L'entraînement sur carte graphique ; macOS ; des vies de plusieurs semaines plutôt
que deux jours ; un rappel fiable des faits ; un effet sur ce que l'être décide au-delà des mots qu'il
emploie. SmolVLM2 2.2B fonctionne et voit une image quand on la lui montre simplement, mais dans
le format de décision de Freewill il a répété la question, répondu en anglais à du français, et a
une fois tenu une requête dix minutes (un plafond sur la longueur d'une décision l'empêche
désormais) ; il n'est pas entraînable ici. Qwen3 1.7B est le modèle à choisir pour un être dont le
moteur doit s'adapter.
