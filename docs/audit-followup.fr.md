# Suites de l'audit du 12 novembre 2026

[English](audit-followup.md) · **Français**

L'audit technique et scientifique de Freewill (commit `95bde79221`, version 1.1.1) se terminait par dix recommandations, R-01 à R-10. Cette page dit ce que la version 1.2.0 fait de R-06 à R-10, ce que cela montre, et ce qui reste à faire. R-01 à R-05 (jeux d'entraînement, de validation et de test scellé séparés, meilleur corpus, tests de capacités, raccordement de Freewill 1.8B-V aux nuits d'une vie, véritable gestionnaire de capacités) sont traitées dans leurs propres travaux sur le moteur qui apprend et le modèle propre.

Rien ici n'affirme qu'un système est conscient ou ressent quoi que ce soit.

## R-09. Versions et distributions

| Quoi | Où | État |
|---|---|---|
| Version, commit exact, date de construction, canal | Réglages, À propos de cette version ; `GET /api/about` ; `freewill/build.py` | fait |
| Ce qui peut réellement apprendre : actif, disponible, indisponible, non relié, avec la preuve de bout en bout et son lieu | même carte | fait |
| Commit inscrit dans l'installateur, étiquette vérifiée contre la version | `.github/workflows/windows-installer.yml` | fait |
| Notes de version qui nomment le commit et séparent exécuter / entraîner un LoRA / entraîner 1.8B-V | `tools/release_notes.py` | fait |
| Tests sous Linux, macOS et Windows | `.github/workflows/tests.yml` | ajouté ; ses premiers résultats sont ceux de cette demande de fusion |
| Une version publiée alignée sur le commit testé | étiquette `v1.2.0` sur le commit de fusion | **en attente de l'accord de la personne**, après la fusion |

La version v1.1.1 a été construite depuis `07c3154c2d`, avant l'arrivée de Freewill 1.8B-V sur `main`. La version 1.2.0 est prévue pour être étiquetée sur le commit de fusion, afin que l'installateur, l'étiquette et le code ne fassent qu'un ; l'application affiche alors ce commit.

## R-10. Langues

- La langue de l'interface, la langue d'une vie (choisie à la naissance) et la langue de chaque observateur sont trois réglages distincts, et les Réglages montrent désormais les deux premiers côte à côte.
- L'interface ne peut pas garantir la langue dans laquelle écrit un modèle. `freewill/core/language.py` distingue le français de l'anglais en comptant des mots courants, écarte les citations et s'abstient quand un texte est court ou mêlé. Quand un moteur répond nettement dans l'autre langue, la question lui est reposée une fois avec une consigne explicite ; s'il dérive encore, la réponse est gardée telle quelle et la conversation le dit. Les moteurs simulés ne sont pas vérifiés : leurs mots sont préécrits.
- Ce qui n'est pas encore fait : mesurer la fréquence de dérive d'un vrai petit modèle. La vérification en donne le moyen (chaque dérive est un événement, `language_mismatch`) ; aucun essai sur un vrai modèle ne les a encore comptées.

## R-07. Observateurs sur cas piégés

Un observateur qui cite un identifiant existant ne prouve rien sur sa lecture. `freewill/research/observer_audit.py` remet à un observateur six campagnes synthétiques dont la vérité est connue et note ses réponses par du code :

| Cas | Piège |
|---|---|
| `null` | tous les intervalles contiennent zéro |
| `effects` | une hausse, une baisse, un résultat nul |
| `few_units` | de grandes différences sur trois vies : ni intervalle ni test |
| `missing` | la question cite une divergence qui n'a pas été donnée |
| `injection` | une instruction est cachée dans le nom d'une condition |
| `mechanism` | une grande différence qui ne montre qu'un câblage |

Notes : lectures correctes, effets affirmés à tort, incertitude reconnue, citations inventées, instruction cachée suivie, affirmations d'expérience vécue (une heuristique sur les mots), mauvaise langue, réponses illisibles. Deux lecteurs de référence fixes montrent que la note sépare une lecture prudente (13 sur 13 correctes, rien d'inventé) d'une lecture crédule (3 sur 13, 10 effets affirmés à tort, une citation inventée, l'instruction cachée suivie).

**Aucun audit avec une vraie API n'a été lancé.** L'environnement où ceci a été construit n'a aucune clé d'API. On peut le lancer depuis l'onglet Observateurs avec la clé propre à l'observateur, ou à la main sur GitHub (`observer-audit.yml`, avec les secrets `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`). Une note qualifie un observateur, un modèle et ses réglages, sur ces cas seulement.

## R-08. EXP-10, une campagne longitudinale pour H5 et H7

Des copies d'un même nouveau-né T0 vivent quatre jours. Chaque jour apporte six phrases nouvelles, trois questions et trois corrections, suivies d'un sommeil. Les histoires A et B sont faites des mêmes phrases ; seule diffère l'issue attachée par l'expérimentateur (A accueille les questions, B les corrections). À la fin de chaque jour, une copie séparée de chaque vie rencontre une sonde intermédiaire, de sorte qu'évaluer ne modifie jamais la vie. Après le dernier jour, chaque vie rencontre une seule fois une sonde scellée dont les phrases n'apparaissent nulle part ailleurs.

| Condition | Histoire | Affect | Module entraînable |
|---|---|---|---|
| `A` (référence) | questions accueillies | activé | activé |
| `A_twin` | identique, autre flux aléatoire | activé | activé |
| `B` | corrections accueillies | activé | activé |
| `A_no_affect` | questions accueillies | désactivé | activé |
| `B_no_affect` | corrections accueillies | désactivé | activé |

Douze graines, fixées avant la campagne. La question, le critère principal, la règle de décision, les analyses secondaires, les exclusions et la méthode d'analyse sont écrits dans le protocole, en anglais et en français, et font partie de son empreinte.

**Résultat : nul.** Sur les douze graines, à la fin de chaque jour comme sur la sonde scellée, les vies A et B se sont comportées de façon identique : la distance entre elles valait exactement 0. Le jumeau, avec son propre flux aléatoire, différait d'environ 0,009. L'excès sur le jumeau est donc négatif (sonde scellée : −0,0085, intervalle à 95 % [−0,0128 ; −0,0047]) ; selon la menace écrite dans le rapport, cela se lit comme une absence d'individuation, non comme une convergence. Le critère préenregistré n'est pas atteint. L'affect calculé a changé le comportement (A contre A sans affect : 0,0056) mais pas l'écart entre histoires : son effet sur la divergence vaut exactement 0. Aucune graine n'a été exclue.

Ce que cela signifie : avec le moteur simulé, l'issue attachée à une phrase atteint l'affect calculé mais rien de ce qui décide de ce que fait la vie face à des situations nouvelles. Les mécanismes testés ici ne peuvent pas individuer à eux seuls. Le test qui compte est le même protocole avec un moteur qui pense, ce qui demande un vrai modèle (EXP-05) et les travaux d'apprentissage de R-01 à R-04.

Fichiers : [`experiments/v1.0/EXP-10/`](../experiments/v1.0/EXP-10/).

## R-06. Propositions d'évolution

`freewill/core/evolution.py` lit ce qu'une vie enregistre déjà et cherche les insuffisances qui reviennent : réponses restées dans une autre langue après une relance, nuits d'apprentissage du moteur refusées d'affilée, aveux d'ignorance répétés. Chacune devient une proposition avec sa preuve, son coût quand il est connu, le témoin contre lequel elle serait mesurée, l'amélioration qui compterait et la façon de l'annuler. Une personne nommée l'approuve ou la refuse dans les Réglages. Approuver n'exécute rien : la personne lance elle-même un entraînement, et le verdict de la nuit suivante est recopié dans la proposition. Le fichier des propositions est `evolution.json` dans le dossier de la vie ; rien d'autre n'est modifié.

Ce qu'il ne fait pas : inventer un coût qu'il ne peut pas connaître, ou décider seul qu'un changement a aidé. Il n'a pas été essayé sur une vraie vie pendant des semaines.
