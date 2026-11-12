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
| Chargement | `freewill/engines/embedded.py` | `llama-server --lora-scaled` ; le nom du moteur porte la version et le hachage de l'adaptateur ; `/lora-adapters` est relu |
| Comparaison | `freewill/learning/compare.py`, EXP-09 | Base, adapté, et deux témoins entraînés de la même façon sur un texte mélangé ou aléatoire |

## Règles pour garder un adaptateur (`h4-engine-1.1`)

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
au modèle de base seul, est une seule action dans le Research Lab (onglet
Apprentissage) ou `POST /api/engine-learning/restore` ; elle est écrite au
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

RESULTS
