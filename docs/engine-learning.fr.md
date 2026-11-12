# Comment une vie adapte le modèle avec lequel elle converse

[English](engine-learning.md) · **Français**

Cette page décrit comment un modèle embarqué (Qwen3 1.7B) peut être modifié par
la vie d'un être, ce qui est vérifié avant de garder une modification, et ce qui
a réellement été démontré. Elle n'affirme pas que l'être apprend ou comprend
quoi que ce soit au sens large, ni qu'il est conscient.

## Le cycle

```
jour : conversations à travers la boucle de vie
  → corpus contrôlé (ce qui a été entendu, et la réponse choisie par l'être)
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
| Corpus | `freewill/learning/engine.py` (`gather`) | Seulement des paires « message entendu → réponse que l'être a choisi de dire ». Un élément sur quatre, choisi par le hachage de son texte, n'est jamais entraîné |
| Entraînement | `freewill/learning/lora.py` (`Workbench`) | LoRA (PEFT) sur les projections d'attention. Les poids de la base sont hachés avant et après : ils doivent être identiques |
| Décision | `EngineLearning.night` | Voir les règles ci-dessous. Chaque nuit est écrite dans `engine/ledger.jsonl`, gardée ou non |
| Conversion | `freewill/learning/gguf_lora.py` | L'adaptateur est écrit au format LoRA GGUF de llama.cpp puis relu (noms, formes, architecture) |
| Chargement | `freewill/engines/embedded.py` | `llama-server --lora` ; le nom du moteur porte la version et le hachage de l'adaptateur ; `/lora-adapters` est relu |
| Comparaison | `freewill/learning/compare.py`, EXP-09 | Base, adapté, et deux témoins entraînés de la même façon sur un texte mélangé ou aléatoire |

## Règles pour garder un adaptateur (`h4-engine-1.2`)

Un candidat n'est gardé que si tout ceci est vrai :

1. sur les nouveaux éléments mis de côté de la vie, il prédit mieux que l'adaptateur en service, d'au moins 0,01 nat par jeton ;
2. sur les textes de référence livrés avec Freewill (passages généraux en anglais et en français, et principes du noyau), il ne prédit pas plus mal que le modèle de base à la naissance, au-delà de 0,05 nat par jeton ;
3. sur les éléments mis de côté les nuits précédentes, il ne prédit pas plus mal que l'adaptateur en service, au-delà de 0,05 nat par jeton ;
4. les poids du modèle de base n'ont pas changé ;
5. le fichier converti est relu correctement et, si c'est demandé, llama.cpp le charge et donne une perte finie.

Moins de 3 éléments mis de côté ou de 4 éléments d'entraînement : rien n'est
entraîné, et le journal dit pourquoi. Les connaissances antérieures sont
protégées de trois façons : le candidat part de l'adaptateur en service, des
éléments d'entraînement plus anciens sont rejoués à côté des nouveaux, et les
règles 2 et 3 ci-dessus.

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
0,01 nat par jeton sur des données mises de côté, et seulement dans le budget
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
