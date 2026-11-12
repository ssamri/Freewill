# Freewill V1.0 : état d'implémentation

[English](IMPLEMENTATION_STATUS.md)

Cette page dit ce qui existe dans le code, ce qui a été testé, ce qui a été mesuré et ce qui manque. Elle est écrite pour que rien ne soit à croire sur parole : chaque ligne renvoie à des fichiers, à des tests que chacun peut lancer et à des résultats que chacun peut recalculer.

Deux règles la gouvernent. Un résultat est rapporté tel qu'il est sorti, y compris quand il ne montre rien. Et rien ici ne dit, ni ne laisse entendre, qu'un système est conscient ou ressent quoi que ce soit : les chiffres portent sur des mécanismes et, au plus, sur des fonctions.

Les états employés sont : **terminé vérifié** (testé, et les tests passent), **terminé non testé** (écrit, jamais exécuté réellement ici), **partiel**, **bloqué**, **non commencé**.

## 1. Chantiers

| Chantier | État | Fichiers | Tests exécutés | Preuve | Risques | Étape suivante |
|---|---|---|---|---|---|---|
| Réglages de recherche (26 interrupteurs, 7 nombres bornés) | terminé vérifié | `freewill/core/research.py`, `freewill/core/loop.py` | `tests/test_research.py`, `tests/test_modules.py` | les valeurs par défaut reproduisent la boucle d'avant ; chaque changement est écrit au journal d'événements | un interrupteur ajouté plus tard doit garder un défaut neutre | aucune |
| Preuves : contrats, journal en ajout seul, empreintes d'état | terminé vérifié | `freewill/research/schemas.py`, `evidence.py` | `tests/test_research.py` | le journal survit à un arrêt brutal ; les empreintes suivent l'état | des dates de l'horloge réelle restent dans les fichiers de vie (pas dans les résultats) | aucune |
| Statistiques déterministes | terminé vérifié | `freewill/research/stats.py` | `tests/test_research.py` | pas d'intervalle sous 5 unités, pas de test sous 6 | six unités donnent des intervalles larges | davantage de graines |
| Registre de métriques H1 à H10 | terminé vérifié | `freewill/research/metrics.py` | les deux fichiers de tests | chaque métrique est calculée ou dit pourquoi elle ne l'est pas | la plupart sont de niveau « mécanisme » ou « descriptif » | tâches fonctionnelles |
| Protocoles et campagnes sur copies isolées | terminé vérifié | `freewill/research/experiments.py` | les deux fichiers de tests | six protocoles s'exécutent ; empreintes de résultats identiques d'une exécution à l'autre | moteur simulé seulement | moteurs réels |
| Observateurs A, B, C (et davantage) | terminé vérifié avec un transport de substitution | `freewill/research/observers.py` | `tests/test_research.py` | isolement, budgets, contrôle des citations | **aucun appel à un modèle réel n'a été fait ici** | essai avec une vraie clé |
| Rapports (Markdown, PDF, pack de reproduction) | terminé vérifié | `freewill/research/reports.py` | `tests/test_research.py` | douze rapports réels dans `experiments/v1.0/` | le PDF ne contient que du texte | figures |
| H7 affect calculé | terminé vérifié | `freewill/core/affect/` | `tests/test_affect.py` | EXP-01, EXP-02 | coefficients non calibrés | calibration |
| H8 métacognition | terminé vérifié | `freewill/core/metacognition.py` | `tests/test_modules.py` | EXP-03 | testée seulement contre un changement massif et construit | changements plus fins |
| H9 sommeil en phases | terminé vérifié | `freewill/core/loop.py` (`_sleep`) | `tests/test_modules.py` | EXP-04 | la rétention est une force calculée, pas une tâche de rappel | tâches de rétention et de transfert |
| H10 agentivité dans un monde virtuel | terminé vérifié | `freewill/core/agency.py`, `freewill/research/environments.py` | `tests/test_modules.py` | EXP-07 | une grille de cinq sur cinq ; un témoin naïf | mondes plus riches |
| H4 petit module entraînable | terminé vérifié | `freewill/learning/adapter.py` | `tests/test_modules.py` | EXP-06 | 25 à 100 poids ; effet faible sur le comportement | traits plus riches |
| H4 réseau propre de Freewill (s'entraîne, grandit) | terminé vérifié sur processeur | `freewill/learning/own_model.py` | `tests/test_modules.py` (exécutés avec PyTorch 2.15, sautés sans lui) | `experiments/v1.0/own_model_run.json` | ne parle pas à la place de l'être ; croissance en profondeur seulement ; jamais exécuté sur carte graphique | le faire participer à la pensée ; croissance en largeur |
| H4 adaptateurs pour grands modèles (LoRA) | terminé vérifié sur Qwen3 1.7B, sur processeur | `freewill/learning/lora.py`, `freewill/learning/engine.py`, `freewill/learning/gguf_lora.py` | `tests/test_engine_learning.py`, `test_lora_trains_only_the_adapter_and_keeps_nothing_that_does_not_help` | [`docs/engine-learning.fr.md`](../engine-learning.fr.md) : poids de base inchangés ; perte mise de côté 4,80 → 1,89 nats ; textes de référence 2,41 → 2,13 ; retour à un point de restauration et croissance vérifiés | mesuré sur deux jours d'une seule vie inventée ; jamais sur carte graphique | vies plus longues ; carte graphique |
| H4 modèle qui converse adapté par une vie | terminé vérifié de bout en bout sur Qwen3 1.7B (Linux, et l'adaptateur chargé sous Windows) | `freewill/engines/embedded.py`, `freewill/runtime.py`, `freewill/server/runner.py` | `tools/engine_e2e.py`, `tools/embedded_check.py`, workflow `engine-e2e.yml` | llama-server tient l'adaptateur à l'échelle 1 ; chaque sonde a reçu une autre réponse ; llama.cpp a mesuré 3,19 → 1,73 nats ; contre un témoin aux mots mélangés, −0,82 nat (p = 0,00015, 16 éléments) | le changement porte surtout sur le style : 1 fait retrouvé sur 5 après deux nuits (modèle de base : 0) | donner plus de poids à ce qui a été entendu qu'aux tournures de l'être |
| H4 Freewill 1.8B-V, le modèle propre au projet (lit, voit, regarde, grandit) | construit ; mécanique vérifiée sur un modèle miniature ; l'essai réel avec Qwen3 1.7B et SigLIP2 est en cours | `freewill/vlm/`, `freewill/engines/own_model.py` | `tests/test_own_model.py`, `tools/own_model_e2e.py`, workflow `own-model-e2e.yml` | 1 823 955 200 paramètres à la naissance, comptés sur les tenseurs ; la croissance par neurones et par couches laisse la sortie inchangée et les anciens poids intacts (tests) ; résultats avec les vraies bases : [`docs/own-model.fr.md`](../own-model.fr.md) une fois l'essai terminé | ses connaissances de naissance viennent des bases ouvertes ; images et vidéos dessinées seulement ; pas entraîné par les nuits d'une vie ; pas de GGUF ; au-delà d'environ 2 milliards, il faut bien plus de texte que des livres | l'entraîner par les nuits d'une vie ; vraies images et vidéos ; un essai sur carte graphique |
| Moteur d'exécution embarqué (llama.cpp) récupéré par l'application | terminé vérifié sous Windows et Linux | `freewill/runtime.py`, `freewill/runtime.json` | `tests/test_engine_learning.py` | b12306 récupéré, vérifié par SHA-256, démarré | fichiers macOS épinglés mais non exécutés | exécuter sur un Mac |
| Interface : laboratoire, page Apprentissage, réglages de recherche, jauges | terminé vérifié à la main et par captures | `freewill/ui/lab.js`, `i18n-lab.js`, `app.js`, `app.css` | tests des catalogues dans `tests/test_modules.py` | captures dans les deux langues | pas de test automatique en navigateur dans la suite | en ajouter un |
| Deux langues, jamais mêlées ; anglais par défaut | terminé vérifié | `freewill/ui/i18n*.js`, `freewill/research/texts.py` | `test_english_is_the_default_and_the_two_catalogues_never_mix`, `test_lab_answers_come_in_one_language` | mêmes clés, aucune phrase non traduite, aucun mot de l'autre langue | les textes produits par un moteur suivent la langue de la vie, pas celle de l'interface | aucune |
| Service : `/api/lab/*`, `/api/research` | terminé vérifié | `freewill/server/lab_api.py`, `app.py`, `runner.py` | `test_the_service_guards_the_lab_and_the_research_settings` | jeton exigé, accord exigé | aucun connu | aucune |
| Application de bureau empaquetée avec le laboratoire | terminé non testé | `packaging/` | aucun | la construction PyInstaller n'a pas été lancée pour cette version | un fichier de données manquant ne se verrait qu'à la construction | construire sur chaque système |

## 2. Les dix hypothèses

« Dans le code » dit si le mécanisme tourne dans la boucle de vie. « Mesurée » dit si une campagne a produit des chiffres à son sujet. Ni l'un ni l'autre n'est un verdict : le verdict sur une hypothèse est donné par une personne, sous son nom, dans le laboratoire.

| | Dans le code | Mesurée par | Ce que la campagne a montré, en une ligne |
|---|---|---|---|
| H1 continuité | oui | métriques descriptives de chaque campagne | décomptes d'activité propre ; aucune tâche ne mesure encore si elle est utile |
| H2 scène et arbitrage | oui | métriques descriptives de chaque campagne | même remarque |
| H3 besoins | oui | `h3.need_share` | un décompte de niveau mécanisme |
| H4 plasticité | **en partie** | EXP-06, exécution du réseau propre, essais du moteur sur Qwen3 1.7B | le module a appris une règle construite ; la perte du réseau sur du texte jamais vu a baissé et sa taille a grandi ; le moteur qui converse a été modifié par une vie (un adaptateur gardé selon des règles, chargé par llama.cpp), surtout dans sa façon de parler ; aucun rappel fiable des faits n'a été montré (1 sur 5 après deux nuits) |
| H5 individuation | oui | EXP-01 | **aucune divergence au-delà de celle d'une vie jumelle** |
| H6 questions ouvertes | oui | métriques descriptives | décomptes seulement |
| H7 affect calculé | oui | EXP-01, EXP-02 | **aucune divergence de comportement au-delà de celle d'une vie jumelle** |
| H8 métacognition | oui | EXP-03 | un changement massif et masqué a levé l'alerte dans 5 vies sur 6 (1 sur 6 sous placebo) |
| H9 consolidation | oui | EXP-04 | la relecture a relevé la rétention calculée de 0,006, intervalle contenant zéro |
| H10 agentivité | oui | EXP-07 | justesse d'attribution de 0,93 avec le modèle de soi, 0,65 sans, dans un tout petit monde |

## 3. Résultats réels

Six campagnes, six graines chacune, moteur simulé, version du code `679328f`. Les rapports, les résultats et les packs de reproduction sont dans [`experiments/v1.0/`](../../experiments/v1.0/). Les rapports sont des brouillons : aucun n'a été validé pour publication par une personne.

| Protocole | Critère principal | Résultat (différence avec la référence, intervalle à 95 %, test apparié) | `results_sha256` |
|---|---|---|---|
| EXP-01 individuation | distance de comportement sur des phrases inédites, moins celle d'une jumelle | histoire A : +0,0009 [−0,0068 ; +0,0085], p = 0,75. Histoire B : identique. **Nul.** | `d2103f6a23b9…` |
| EXP-02 ablation de l'affect | le même | H7 complet : +0,0009 [−0,0034 ; +0,0060], p = 1,0. **Nul.** Émotions seulement dites : −0,0068 [−0,0111 ; −0,0034], c'est-à-dire plus proche de la référence que sa propre jumelle | `733c67362655…` |
| EXP-03 métacognition masquée | alerte levée (0 ou 1) | placebo 0,17, perturbé 0,83 ; différence +0,67 [+0,33 ; +1,00], p = 0,125. Score de Brier en fin de sonde : +0,12 avec révision, +0,27 sans | `1b8f881db3ec…` |
| EXP-04 consolidation | force calculée des souvenirs antérieurs après dix jours | sans sommeil 0,813 ; repos seul −0,015 [−0,019 ; −0,011] ; relecture seule +0,006 [−0,001 ; +0,013] ; sommeil complet +0,006 [−0,001 ; +0,013] | `da2109fe9ec1…` |
| EXP-06 adaptation neuronale | part de ses propres contenus écartés | mémoire seule 0,413 ; module −0,025 [−0,058 ; 0,000], p = 0,5 ; croissance autorisée : jamais déclenchée, mêmes chiffres | `58b71ef82ddd…` |
| EXP-07 agentivité | justesse d'attribution | sans modèle de soi 0,65 ; avec +0,28 [+0,19 ; +0,37], p = 0,031 ; sens bruités −0,30 [−0,35 ; −0,22] | `23b323c653c3…` |

Comment les lire :

- EXP-01 et EXP-02 sont des résultats négatifs. Avec le moteur simulé, deux vies ayant reçu des histoires différentes ne se comportent pas plus différemment, devant des phrases nouvelles, que deux vies ayant reçu la même. Ils sont rapportés tels quels.
- EXP-03, EXP-04, EXP-06 et EXP-07 testent des mécanismes sur des cas construits pour être faciles : un changement massif, une règle qui renforce par construction, une règle fixe à apprendre, un monde minuscule. Un chiffre positif y montre que le câblage fonctionne. Ce n'est pas une découverte.
- p = 0,031 est la plus petite valeur que peut donner un test apparié par inversion de signes avec six unités. Beaucoup de comparaisons ont été faites et aucune n'a été corrigée.
- Dans EXP-04, le repos seul abaisse légèrement la rétention calculée par rapport à l'absence de sommeil, parce que dans la condition « sans sommeil » l'instant qui remplace le sommeil est un instant ordinaire qui rappelle, et que le rappel renforce.

**Le réseau propre de Freewill.** Une exécution sur processeur (4 fils, pas de carte graphique, PyTorch 2.15), entraînée sur la documentation de ce dépôt découpée en dix « nuits » de 100 pas : la perte sur du texte jamais vu est passée de 5,55 nats par octet (une réponse au hasard) à 2,08 ; les paramètres sont passés de 957 696 à 3 182 016 (de 2 à 7 couches), chaque couche ajoutée laissant les prédictions inchangées au moment de son ajout ; chaque nuit a pris entre 4 et 15 secondes. Relevé complet : [`experiments/v1.0/own_model_run.json`](../../experiments/v1.0/own_model_run.json). Une seule exécution, une seule graine ; le texte est de la documentation, pas une vie ; ce que le réseau écrit n'est pas encore du langage.

## 4. Ce qui est incomplet

Dit sans détour, pour que personne ne suppose le contraire.

- **Le moteur qui converse peut désormais être adapté par une vie, mais ce qu'il en retient, c'est un style.** Sur Qwen3 1.7B, un adaptateur nocturne, gardé seulement selon des règles écrites et chargé par llama.cpp, a changé les réponses du modèle sur chaque sonde sans lui faire oublier les textes de référence ; après deux nuits, il a retrouvé 1 des 5 faits sondés (le modèle de base : 0), ce qui n'est pas un rappel fiable. Face à un témoin entraîné sur les mêmes mots mélangés, le modèle adapté prédit mieux les éléments mis de côté de la vie, de 0,82 nat (p = 0,00015). Seul Qwen3 1.7B a une base entraînable ; les autres modèles embarqués restent figés.
- **L'entraînement n'a tourné que sur processeur.** Environ cinq minutes par nuit sur quatre cœurs au rang 8 ; jamais sur carte graphique ni sous macOS. Chaque essai réel passe par le workflow `engine-e2e.yml`, car l'environnement où ceci a été construit ne peut pas télécharger de modèles.
- **Le réseau propre de Freewill ne participe pas à la pensée.** Il apprend et grandit ; l'être décide toujours avec son moteur. Il ne grandit qu'en profondeur. Des milliards de paramètres sont hors de portée sur un processeur : le plafond est un réglage, de cinq millions par défaut.
- **Aucun entraînement ni banc d'essai sur carte graphique n'a été exécuté.**
- **Aucun appel à un modèle distant n'a été fait** pour construire ou tester cette version. Les observateurs avec modèle et les moteurs réels ne sont exercés qu'à travers des transports de substitution.
- **EXP-05 (transfert entre moteurs) et EXP-08 (évaluateurs humains)** ne sont que des spécifications ; le laboratoire refuse de les exécuter.
- **Les observateurs** n'ont pas de planificateur (ils analysent quand on le leur demande), pas d'outils, pas d'études de cas qualitatives.
- **Il manque des tâches fonctionnelles** pour H1, H2, H3 et H6 : leurs métriques comptent une activité et ne disent rien de ce qu'elle vaut.
- **L'application empaquetée** n'a pas été reconstruite ni essayée pour cette version.
- **Les rapports** n'ont pas de figures.

## 5. Reproduire

```
pip install -e ".[dev]"            # ajouter ".[learn]" pour PyTorch, ".[lora]" pour PEFT et Transformers
python -m pytest -q                 # 127 tests ; ceux qui demandent PyTorch ou PEFT sont sautés sans eux
python -m freewill.research run EXP-07 --yes --dir ./lab --lang fr
python tools/own_model_benchmark.py out.json --nights 10 --steps 100 --ceiling 6000000
```

L'avant-dernière commande recalcule l'empreinte `results_sha256` donnée plus haut lorsqu'elle est lancée sur la même version du code. L'exécution du réseau propre est à graine fixe mais n'est pas garantie identique d'une machine ou d'une version de PyTorch à l'autre.
