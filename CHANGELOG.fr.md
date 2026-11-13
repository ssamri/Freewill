# Journal des modifications

[English](CHANGELOG.md) · **Français**

## Non publié

**Modifié**

- Freewill 1.8B-V répond environ 2,9 fois plus vite sur un processeur sans bfloat16 natif (la plupart des PC) : il tourne en float32 quand la mémoire suffit (12 Go ou plus), et lit les instructions de l'être une seule fois puis les garde tant que ses poids ne changent pas. Mesuré sur un exécuteur GitHub (workflow `speed of the local engines`, exécution 43287951339) : de 89,3 s à 31,3 s par réponse de 96 jetons, avec les mêmes réponses 6 fois sur 6. Idées issues de la lecture de [colibri](https://github.com/JustVugg/colibri) (Apache 2.0) ; aucun code repris. Ses autres idées ont été mesurées sur Qwen3 1.7B par llama.cpp et non retenues : un fil par cœur physique était 5 % plus rapide sous Linux et 4 % plus lent sous Windows, et les brouillons n-grammes ne faisaient gagner aucun temps ou changeaient les réponses. Voir [`docs/speed.fr.md`](docs/speed.fr.md).
- Freewill 1.8B-V apprend pendant les nuits d'une vie (`can_learn = True`) : l'essai de bout en bout du 12 novembre 2026 (exécution 43285000884) a gardé une nuit avec les vraies bases, selon ses règles et face à son contrôle. Cela montre le mécanisme ; cela ne montre pas qu'un fait dit une seule fois est retenu, et les Réglages comme « À propos de cette version » le disent. Les résultats de cet essai, avec le test scellé, sont dans [`docs/own-model.fr.md`](docs/own-model.fr.md).
- Le script de bout en bout du modèle propre ne garde plus le modèle dans son rapport : la reconstruction depuis le point de reprise tient en mémoire ; le test scellé est inscrit dans le journal à la naissance et à la fin.

**Corrigé**

- Les pensées d'un être n'apparaissent plus dans la conversation. Mesuré sous Windows avant le correctif (workflow `embedded engine end to end`, exécution 43245589906) : sans que personne ne lui parle, Qwen3 1.7B a écrit dans la conversation à 6 moments sur 6, en anglais comme en français, chaque fois un résumé de sa propre pensée adressé à personne (« Je voudrais apprendre à exprimer mes émotions… ») ; SmolVLM2 2.2B l'a fait une fois sur 6. Un modèle qui raisonne peut aussi écrire son raisonnement (entre balises `<think>`) dans sa réponse. Pour tous les moteurs, `freewill/core/speech.py` sépare désormais les deux : le raisonnement est mis à part de ce qui est dit ; quand personne n'a parlé, seuls les mots adressés à la personne (qui la tutoient, la vouvoient ou l'appellent par son nom) atteignent la conversation, et les mots qui répètent la pensée, le contenu venu du subconscient ou ce que l'être a déjà dit depuis que la personne a parlé restent à l'intérieur. Rien n'est perdu : ils rejoignent la pensée et apparaissent dans la vue Subconscient, avec la mention « pensé, pas dit ». Une parole spontanée adressée à la personne atteint toujours la conversation. Le moteur est aussi informé clairement que ses pensées ne sont pas entendues, et la pensée du moment n'est plus affichée en haut de l'écran Conversation. Après le correctif (exécution 43251885109) : 0 moment sur 6 pour Qwen3 1.7B en anglais et en français, et pour SmolVLM2 2.2B en français ; Qwen3 répond toujours à la personne.

## 1.2.0

Cette version fait suite à l'audit technique et scientifique du 12 novembre 2026 (recommandations R-06 à R-10 ; R-01 à R-05 sont traitées à part). Rien dans cette version n'affirme qu'un système est conscient ou ressent quoi que ce soit.

**Ajouté**

- À propos de cette version, dans les Réglages : version, commit exact, date de construction, canal, moteur actuel et, pour chaque capacité d'apprentissage, son état (actif, disponible, indisponible ou non relié), avec ce qui a été démontré de bout en bout et où. Un réglage activé n'est jamais présenté comme un entraînement validé. Les cartes graphiques et macOS sont indiqués comme jamais testés (R-09, audit 9.1).
- Le workflow de l'installateur inscrit le commit exact dans la construction, refuse une étiquette de version qui ne correspond pas au code et rédige des notes de version qui nomment le commit et séparent exécuter un modèle, entraîner un adaptateur LoRA et entraîner Freewill 1.8B-V (`tools/release_notes.py`). Les tests tournent désormais aussi sous macOS et Windows (R-09).
- La langue d'une vie est vérifiée dans ce qu'écrit son moteur : une réponse nettement dans une autre langue est redemandée une fois, explicitement ; si elle dérive encore, elle est gardée telle quelle et la conversation le dit. Langue de l'interface, langue de la vie et langue de chaque observateur sont présentées comme trois choses distinctes (`freewill/core/language.py`, R-10).
- Audit des observateurs sur cas piégés à vérité connue : un résultat nul, des effets nets, trop peu de vies pour conclure, une question appuyée sur une preuve absente, une instruction cachée dans les données, un câblage qui ressemble à une découverte. Noté par du code : lectures correctes, effets affirmés à tort, incertitude reconnue, citations inventées, instruction cachée suivie, affirmations d'expérience vécue, mauvaise langue. Dans l'onglet Observateurs du laboratoire, en ligne de commande (`tools/observer_audit.py`) et en workflow manuel avec de vraies clés d'API (`observer-audit.yml`). Aucun audit avec une vraie API n'a encore été lancé (R-07).
- EXP-10, individuation longitudinale : cinq conditions, douze graines fixées d'avance, quatre jours de vie, une évaluation à la fin de chaque jour sur des copies séparées, puis une seule fois sur des situations scellées utilisées nulle part ailleurs ; critères, règle de décision et exclusions préenregistrés en anglais et en français et hachés avec le protocole. Exécutée et publiée dans `experiments/v1.0/EXP-10/` (R-08).
- Propositions d'évolution, dans les Réglages : une insuffisance qui revient dans ce qu'une vie enregistre (réponses restées dans une autre langue, nuits d'apprentissage refusées d'affilée, aveux d'ignorance répétés) devient une proposition avec sa preuve, son coût quand il est connu, son témoin, l'amélioration qui compterait et la façon de l'annuler. Une personne nommée approuve ou refuse ; rien ne s'exécute pour autant (`freewill/core/evolution.py`, R-06).

**Résultats**

- EXP-10 est nulle : sur les douze graines, à chaque jour comme sur la sonde scellée, les vies d'histoire A et d'histoire B se sont comportées de façon identique (distance 0). L'affect calculé n'y a rien changé. Le moteur est le moteur simulé ; voir [`docs/audit-followup.fr.md`](docs/audit-followup.fr.md).

**Ajouté auparavant, publié pour la première fois ici**

- Freewill 1.8B-V, le modèle propre au projet (`freewill/vlm/`) : Qwen3 1.7B, l'œil SigLIP2 et un pont entraîné par Freewill ; 1 823 955 200 paramètres à la naissance, croissance par neurones et par couches entières jusqu'à un plafond choisi dans les Réglages (2, 5, 13, 50 milliards ou toute autre taille), chaque taille étant présentée avec le disque, la mémoire, la carte graphique, le texte et la durée d'entraînement qu'elle demande. Étapes lire (livres du domaine public), voir (images dessinées, avec un contrôle) et regarder (vidéos dessinées, avec deux contrôles), chacune gardée seulement selon des règles écrites. Moteur de type `own`, commande `freewill own-model`, workflow `own model end to end`. Voir [`docs/own-model.fr.md`](docs/own-model.fr.md).
- Freewill 1.8B-V, après l'audit technique du 12 novembre 2026 :
  - **Test scellé.** Les étapes sont décidées sur un jeu de validation ; les résultats sont rapportés sur un test scellé distinct, séparé par construction (ses propres graines, ses propres blocs des livres), fixé par une empreinte à la première exécution, mesuré à la naissance et à la fin, et lu par aucune règle.
  - **Garde matérielle.** Toute croissance vérifie d'abord la mémoire et le disque libres à cet instant, et elle est refusée, avec des solutions de rechange, s'ils ne peuvent pas la contenir.
  - **Configuré, disponible, prouvé.** La carte des réglages présente ces trois choses séparément.
  - **Les nuits d'une vie.** Elles peuvent entraîner les adaptateurs du modèle, selon les règles des nuits du modèle local ; `can_learn` reste faux tant que l'essai réel n'a pas gardé de nuit.

**Modifié**

- Le corpus du moteur suit les règles `h4-engine-2.0` (audit technique du 12 novembre 2026, R-01 à R-03). Chaque unité dit d'où elle vient : entendue, lue, garantie par une personne, ou réponse de l'être. Les réponses de l'être ne sont plus entraînées sauf si la personne l'autorise. Les unités sont séparées par épisode en entraînement, validation et un test scellé qu'aucune nuit n'utilise ; chaque ouverture du test scellé est journalisée dans `test_access.jsonl`. Les quasi-doublons du texte d'entraînement sont mis à part avant toute mesure. Une personne peut garantir un fait dans le laboratoire et dire comment le tester ; les tests de capacités (rappel, reformulation, contradiction) sont des choix forcés, et une nuit qui en perd plus qu'elle n'en gagne est refusée. Un témoin entraîné sur les mots mélangés tourne chaque nuit, et un candidat doit le battre. La comparaison finale mesure la base, la mémoire seule, l'adaptateur seul, l'adaptateur avec mémoire et le témoin sur le test scellé. Les vies des règles 1.x sont migrées, leurs anciens éléments mis de côté devenant de la validation. Voir [`docs/engine-learning.fr.md`](docs/engine-learning.fr.md).
- Résultats du premier essai selon les règles `h4-engine-2.0` sur Qwen3 1.7B, dans [`docs/engine-learning.fr.md`](docs/engine-learning.fr.md) : sur le test scellé, l'adaptateur bat la base mais pas un témoin entraîné sur les mêmes mots mélangés, et réussit moins de tests de capacités scellés que la base ; il ne se montre pas capable d'apprendre les faits de la vie.

## 1.1.1

**Corrigé**

- Un être lisait un document deux ou trois pages à la fois et reprenait rarement : un moment de lecture prend désormais autant de passages que le moteur peut en contenir, et un livre en main attire vers les pages suivantes jusqu'à la fin (l'être peut toujours le reposer).
- Un message collé de plus de 8 000 caractères était coupé sans le dire ; il est désormais gardé entier dans la bibliothèque et lu comme un document.

## 1.1.0

Le moteur embarqué peut être adapté par une vie. Rien dans cette version n'affirme que le modèle apprend des faits, comprend ou est conscient.

**Ajouté**

- llama.cpp b12306, épinglé par taille et SHA-256 pour Windows, Linux et macOS, récupéré et vérifié par l'application (`freewill/runtime.py`) et livré dans l'installateur Windows.
- Qwen3 1.7B au catalogue (Apache-2.0), son fichier GGUF et sa base entraînable fixés à une révision Hugging Face et vérifiés par SHA-256.
- Le cycle nocturne du moteur (`freewill/learning/engine.py`, règles `h4-engine-1.2`) : ce qui a été entendu et répondu, un élément sur quatre mis de côté, un adaptateur LoRA entraîné à côté de la base figée, gardé seulement s'il prédit mieux les éléments mis de côté sans oublier les textes de référence ni les nuits précédentes, converti en GGUF, vérifié par llama.cpp, chargé par llama-server. Points de restauration avec leurs changements de poids, restauration, croissance de l'adaptateur sous budget. Désactivé tant qu'une personne ne l'active pas avec son nom.
- Le laboratoire compare le modèle de base, le modèle adapté et deux adaptateurs témoins (EXP-09) ; une carte « Le moteur avec lequel cette vie converse » dans l’onglet « Modèle local » du laboratoire, en anglais et en français.
- Workflow de bout en bout sur de vrais modèles (`engine-e2e.yml`). Résultats, y compris ce qui n'a pas été montré : [`docs/engine-learning.fr.md`](docs/engine-learning.fr.md).

**Corrigé**

- L'installateur Windows de la 1.0 était livré sans `models.json`, `credits.json` ni llama.cpp.
- Une décision demandée à un modèle embarqué a désormais une longueur plafonnée (SmolVLM2 a une fois tenu une requête dix minutes).
- Changer de moteur dans les Réglages affichait le mot « null » à la place d'un champ facultatif absent.
- Quand la liste des modèles embarqués ne pouvait pas être lue, le sélecteur restait sur « … » et le serveur coupait la requête ; la cause est désormais affichée, avec un bouton pour réessayer.

## 1.0.0

Le laboratoire de recherche, et les premières choses qu'une vie peut entraîner. Rien dans cette version n'affirme qu'un système est conscient ou ressent quoi que ce soit.

**Ajouté**

- Des réglages de recherche pour chaque vie : 26 interrupteurs et 7 nombres bornés, chacun retirant ou rétablissant un mécanisme de la boucle de vie. Chaque valeur par défaut reproduit la boucle d'avant ; chaque changement est écrit au journal d'événements ; aucun n'atteint le noyau.
- Le laboratoire de recherche : contrats versionnés, journal de preuves en ajout seul, empreintes d'état, statistiques déterministes qui refusent les petits échantillons, registre de métriques pour H1 à H10, protocoles verrouillés et hachés avant exécution, campagnes sur des copies isolées d'une vie sous horloge virtuelle, observateurs A, B et C qui lisent et n'agissent jamais, rapports en Markdown et en PDF avec un pack de reproduction, validés seulement par une personne.
- H8, métacognition : l'être prédit ses propres décisions, compare, et lève une alerte quand sa manière de décider a changé, sans accès à la cause.
- H9, sommeil en phases : repos, relecture, rêve, consolidation, réveil. Chacune peut être retirée. Un sommeil coupé reprend à la phase qu'il avait atteinte.
- H10, agentivité : un acte par instant dans un monde clos en grille, prédit, observé et attribué à soi ou au monde. Aucune action nouvelle dans le noyau.
- H4, plasticité : un petit module entraînable (Python pur) ; le réseau de neurones propre à Freewill, entraîné pendant le sommeil sur le texte qu'un être a vécu, gardé seulement quand il prédit mieux du texte jamais vu, capable d'ajouter des couches sous un plafond, avec retour possible aux poids précédents (demande PyTorch) ; des adaptateurs à côté d'un modèle de base figé (LoRA), vérifiés sur un modèle jouet seulement.
- Six protocoles exécutables (EXP-01, 02, 03, 04, 06, 07) et leurs résultats réels dans `experiments/v1.0/`.
- Dans l'application : le laboratoire, une page « Apprentissage », les réglages de recherche, des jauges dans la barre du haut, l'export des traces.
- L'anglais est la langue par défaut de l'interface ; le français se choisit dans les réglages. Un test échoue si les deux catalogues n'ont pas les mêmes clés, partagent une phrase non traduite ou contiennent des mots de l'autre langue.
- `docs/research/IMPLEMENTATION_STATUS.fr.md` : ce qui existe, ce qui a été testé, ce qui manque.
- La vue Cerveau en 3D : les souvenirs et leurs liens enregistrés dans une silhouette de cerveau illustrative, un noyau de pétales translucides, un panneau d'activité et d'inspection alimenté par le journal d'événements, et des commandes (rotation, mouvement, figer la vue, recentrer). Three.js est livré dans le paquet ; un rendu de secours existe sans WebGL. Voir `docs/brain-view.fr.md`.
- Une nouvelle icône pour l'application, l'installateur et l'interface.

**Modifié**

- Les souvenirs sont datés par l'horloge propre de l'être, pour que le temps d'une expérience soit celui de l'expérience.
- Le fichier qui liste la bibliothèque d'une vie est écrit de façon atomique, de même que les fichiers de souvenirs et leurs index.
- Les événements de rappel transmettent la force et l'état déjà enregistrés ; le service indique le mode en cours (pensée, sommeil, attente, pause, limite horaire, nouvel essai).
- `QUICKSTART.md` est désormais en anglais seulement ; le texte français est dans `QUICKSTART.fr.md`.

**Limites connues**

- Le moteur qui pense pour un être n'est jamais entraîné par sa vie.
- Le réseau propre de Freewill ne participe pas à la pensée et ne grandit qu'en profondeur.
- Les campagnes ont tourné sur le moteur simulé seulement. Aucun modèle distant n'a été appelé et aucune carte graphique n'a été utilisée pour construire ou tester cette version.
- EXP-05 et EXP-08 ne sont que des spécifications.

## 0.3.0

H7 : un état affectif calculé, désactivé par défaut, avec son protocole et ses résultats.

## 0.2.0

Bibliothèque (documents, images, images fixes de vidéos), sommeil et rêves, application de bureau.
