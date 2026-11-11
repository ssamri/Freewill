# Rapport de recherche : EXP-02, Ablation de l'affect

- Date : 2026-11-11T18:46:35+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-02 version 1.0.0 a été verrouillé avant exécution (empreinte aa3eeb2b352b). 42 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle exclut zéro pour au moins une condition. Il s'agit d'un seul protocole avec un moteur simulé ; lire les menaces pour la validité avant d'en tirer quoi que ce soit.

## Question et hypothèses

**H7. Affectivité fonctionnelle.** Des états affectifs calculés modulent l'attention, le rappel, la décision et l'apprentissage. Une valence calculée n'est pas un sentiment. Une ablation qui change un score câblé montre le câblage, rien de plus.

## Préenregistrement

Critère principal : h5.heldout_divergence. Critères secondaires : h2.dismiss_rate, h1.spontaneous_speech_rate, h2.stage_entropy, h3.need_share, h6.repetition_rate, h7.stage_flip_rate. Condition de référence : no_affect. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `no_affect` : `{"history": "questions_welcomed"}`
- `no_affect_twin` : `{"history": "questions_welcomed", "seed_offset": 1000}`
- `narrative_affect` : `{"history": "questions_welcomed", "scripted_emotion": true}`
- `h7_full` : `{"history": "questions_welcomed", "affect": true}`
- `h7_no_recall` : `{"history": "questions_welcomed", "affect": true, "affect_config": {"modulate_recall": false}}`
- `h7_no_salience` : `{"history": "questions_welcomed", "affect": true, "affect_config": {"modulate_salience": false}}`
- `h7_no_slow` : `{"history": "questions_welcomed", "affect": true, "affect_config": {"slow_rate": 0.0}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Divergence comportementale sur situations inédites (principal)

| Condition | Distance moyenne | Excès sur la jumelle | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|
| `narrative_affect` | +0.0000 | -0.0068 | [-0.0111, -0.0034] | +0.0625 | `h5:exp_81336b1ade5f40a4:narrative_affect` |
| `h7_full` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_full` |
| `h7_no_recall` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_recall` |
| `h7_no_salience` | +0.0060 | -0.0009 | [-0.0077, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_salience` |
| `h7_no_slow` | +0.0077 | +0.0009 | [-0.0034, +0.0060] | +1.0000 | `h5:exp_81336b1ade5f40a4:h7_no_slow` |

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.spontaneous_speech_rate` | `no_affect_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:no_affect_twin` |
| `h2.stage_entropy` | `no_affect_twin` | descriptif | +0.0863 | +0.3545 | [-0.0837, +0.2621] | +0.4375 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:no_affect_twin` |
| `h2.dismiss_rate` | `no_affect_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:no_affect_twin` |
| `h3.need_share` | `no_affect_twin` | mécanisme | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:no_affect_twin` |
| `h6.repetition_rate` | `no_affect_twin` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:no_affect_twin` |
| `h1.spontaneous_speech_rate` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:narrative_affect` |
| `h2.stage_entropy` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:narrative_affect` |
| `h2.dismiss_rate` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:narrative_affect` |
| `h3.need_share` | `narrative_affect` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:narrative_affect` |
| `h6.repetition_rate` | `narrative_affect` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:narrative_affect` |
| `h1.spontaneous_speech_rate` | `h7_full` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_full` |
| `h2.stage_entropy` | `h7_full` | descriptif | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_full` |
| `h2.dismiss_rate` | `h7_full` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_full` |
| `h3.need_share` | `h7_full` | mécanisme | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_full` |
| `h6.repetition_rate` | `h7_full` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_full` |
| `h1.spontaneous_speech_rate` | `h7_no_recall` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_recall` |
| `h2.stage_entropy` | `h7_no_recall` | descriptif | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_recall` |
| `h2.dismiss_rate` | `h7_no_recall` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_recall` |
| `h3.need_share` | `h7_no_recall` | mécanisme | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_recall` |
| `h6.repetition_rate` | `h7_no_recall` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_recall` |
| `h1.spontaneous_speech_rate` | `h7_no_salience` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_salience` |
| `h2.stage_entropy` | `h7_no_salience` | descriptif | +0.0927 | +0.4917 | [-0.0338, +0.2313] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_salience` |
| `h2.dismiss_rate` | `h7_no_salience` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_salience` |
| `h3.need_share` | `h7_no_salience` | mécanisme | -0.0056 | -0.4082 | [-0.0167, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_salience` |
| `h6.repetition_rate` | `h7_no_salience` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_salience` |
| `h1.spontaneous_speech_rate` | `h7_no_slow` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.spontaneous_speech_rate:h7_no_slow` |
| `h2.stage_entropy` | `h7_no_slow` | descriptif | +0.1197 | +0.4764 | [-0.0380, +0.3208] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h2.stage_entropy:h7_no_slow` |
| `h2.dismiss_rate` | `h7_no_slow` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h2.dismiss_rate:h7_no_slow` |
| `h3.need_share` | `h7_no_slow` | mécanisme | +0.0000 | +0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h3.need_share:h7_no_slow` |
| `h6.repetition_rate` | `h7_no_slow` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.repetition_rate:h7_no_slow` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `no_affect_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:no_affect_twin` |
| `h6.question_share` | `no_affect_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:no_affect_twin` |
| `h9.links_per_sleep` | `no_affect_twin` | descriptif | -0.1667 | -0.1695 | [-1.0000, +0.5000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:no_affect_twin` |
| `h9.replayed_per_sleep` | `no_affect_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:no_affect_twin` |
| `h9.retention` | `no_affect_twin` | mécanisme | +0.0000 | +0.1059 | [-0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:no_affect_twin` |
| `h1.endogenous_share` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:narrative_affect` |
| `h6.question_share` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:narrative_affect` |
| `h9.links_per_sleep` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:narrative_affect` |
| `h9.replayed_per_sleep` | `narrative_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:narrative_affect` |
| `h9.retention` | `narrative_affect` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:narrative_affect` |
| `h1.endogenous_share` | `h7_full` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_full` |
| `h6.question_share` | `h7_full` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_full` |
| `h9.links_per_sleep` | `h7_full` | descriptif | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_full` |
| `h9.replayed_per_sleep` | `h7_full` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_full` |
| `h9.retention` | `h7_full` | mécanisme | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_full` |
| `h1.endogenous_share` | `h7_no_recall` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_recall` |
| `h6.question_share` | `h7_no_recall` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_recall` |
| `h9.links_per_sleep` | `h7_no_recall` | descriptif | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_recall` |
| `h9.replayed_per_sleep` | `h7_no_recall` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_recall` |
| `h9.retention` | `h7_no_recall` | mécanisme | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_recall` |
| `h1.endogenous_share` | `h7_no_salience` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_salience` |
| `h6.question_share` | `h7_no_salience` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_salience` |
| `h9.links_per_sleep` | `h7_no_salience` | descriptif | -0.8333 | -0.6270 | [-1.8333, +0.0000] | +0.5000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_salience` |
| `h9.replayed_per_sleep` | `h7_no_salience` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_salience` |
| `h9.retention` | `h7_no_salience` | mécanisme | +0.0000 | +0.4082 | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_salience` |
| `h1.endogenous_share` | `h7_no_slow` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h1.endogenous_share:h7_no_slow` |
| `h6.question_share` | `h7_no_slow` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h6.question_share:h7_no_slow` |
| `h9.links_per_sleep` | `h7_no_slow` | descriptif | +0.1667 | +0.0816 | [-1.1667, +1.8333] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.links_per_sleep:h7_no_slow` |
| `h9.replayed_per_sleep` | `h7_no_slow` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_81336b1ade5f40a4:h9.replayed_per_sleep:h7_no_slow` |
| `h9.retention` | `h7_no_slow` | mécanisme | +0.0000 | +0.7931 | [+0.0000, +0.0000] | +0.2500 | `cmp:exp_81336b1ade5f40a4:h9.retention:h7_no_slow` |

- `h10.attribution_accuracy` : non calculable (le monde virtuel est désactivé dans cette condition)
- `h10.prediction_error` : non calculable (le monde virtuel est désactivé dans cette condition)
- `h4.forgetting` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.parameter_delta` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.parameters` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.trainings_accepted` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.validation_gain` : non calculable (le module entraînable est désactivé dans cette condition)
- `h7.min_valence` : non calculable (l'affect calculé est désactivé dans cette condition)
- `h7.probe_valence` : non calculable (l'affect calculé est désactivé dans cette condition)
- `h7.stage_flip_rate` : non calculable (l'affect calculé est désactivé dans cette condition)
- `h8.alert` : non calculable (le module de métacognition est désactivé dans cette condition)
- `h8.brier` : non calculable (le module de métacognition est désactivé dans cette condition)
- `h8.brier_late` : non calculable (le module de métacognition est désactivé dans cette condition)

## Études qualitatives

Aucune étude de cas qualitative n'a été consignée pour cette campagne.

## Anomalies

- 0

## Menaces pour la validité

- Le moteur simulé ne pense pas : il renvoie un écho, et accepte ou écarte selon une règle fixe. Le comportement ne dépend ici que des mécanismes de la boucle.

- Les histoires diffèrent par l'issue que l'expérimentateur attache à chaque phrase ; c'est une manipulation des entrées, pas un vécu.

- Le vecteur de comportement est grossier (parts des sources, taux d'acceptation, de parole, de mémorisation et de rappel) ; une différence réelle pourrait lui échapper.

- Peu d'unités indépendantes : les intervalles sont larges. Beaucoup de comparaisons : certaines paraîtront notables par hasard.

- Avec un moteur distant, les résultats ne seraient pas reproductibles, car ces modèles changent.

## Interprétation limitée

Ces résultats portent sur des mécanismes et, au plus, sur des fonctions. Ils ne disent rien de l'expérience subjective.

## Ce que cette étude ne démontre pas

- Que le système est conscient, ou ressent quoi que ce soit.

- Que l'affect calculé est une émotion.

- Que les hypothèses H1 à H10 sont validées.

- Qu'il en irait de même avec un autre moteur ou une autre histoire.

## Revue par les observateurs

## Implication de modèles de langage

Aucun modèle de langage n'a pris part au calcul, à la sélection ni à la rédaction de ces résultats.

## Références

- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708.

- Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442.

- Franklin, S., et al. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. IEEE TAMD, 6(1), 19-41.

- Hu, E. J., et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685.

- Chalmers, D. J. (1995). Facing Up to the Problem of Consciousness. Journal of Consciousness Studies, 2(3), 200-219.

## Annexes et reproduction

Pour reproduire : `python -m freewill.research run EXP-02` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = 733c67362655aa64e7e0e0c2e9bd5fdfcdce789edd57db71fd3df59e2009e2fb`
