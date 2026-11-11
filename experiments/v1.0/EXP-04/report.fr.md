# Rapport de recherche : EXP-04, Consolidation contrôlée

- Date : 2026-11-11T18:47:15+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-04 version 1.0.0 a été verrouillé avant exécution (empreinte f15a8992440f). 30 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle exclut zéro pour au moins une condition. Il s'agit d'un seul protocole avec un moteur simulé ; lire les menaces pour la validité avant d'en tirer quoi que ce soit.

## Question et hypothèses

**H9. Consolidation hors ligne.** La consolidation pendant le sommeil améliore la rétention et le transfert à calcul égal. Le sommeil se déroule en phases (repos, relecture, rêve, consolidation) que l'on peut retirer une à une. La rétention est mesurée comme la force des souvenirs après un délai, ce qui découle de la règle selon laquelle la relecture renforce ; aucune tâche ne mesure encore le transfert.

## Préenregistrement

Critère principal : h9.retention. Critères secondaires : h9.replayed_per_sleep, h9.links_per_sleep, tech.engine_calls. Condition de référence : no_sleep. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `no_sleep` : `{"history": "told_then_delay", "skip_sleep": true, "research": {"auto_sleep": false}}`
- `rest_only` : `{"history": "told_then_delay", "research": {"auto_sleep": false, "dreaming": false, "sleep_replay": false}}`
- `replay_only` : `{"history": "told_then_delay", "research": {"auto_sleep": false, "dreaming": false}}`
- `dream_only` : `{"history": "told_then_delay", "research": {"auto_sleep": false, "sleep_replay": false}}`
- `full_sleep` : `{"history": "told_then_delay", "research": {"auto_sleep": false}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h9.retention` (principal) | `rest_only` | mécanisme | -0.0149 | -2.3777 | [-0.0191, -0.0105] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:h9.retention:rest_only` |
| `tech.engine_calls` | `rest_only` | descriptif | -1.0000 | non calculable | [-1.0000, -1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:rest_only` |
| `h9.retention` (principal) | `replay_only` | mécanisme | +0.0060 | +0.6341 | [-0.0005, +0.0132] | +0.2188 | `cmp:exp_2664ff5b0ef947c8:h9.retention:replay_only` |
| `tech.engine_calls` | `replay_only` | descriptif | -1.0000 | non calculable | [-1.0000, -1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:replay_only` |
| `h9.retention` (principal) | `dream_only` | mécanisme | -0.0139 | -1.4238 | [-0.0215, -0.0074] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:h9.retention:dream_only` |
| `tech.engine_calls` | `dream_only` | descriptif | +1.0000 | non calculable | [+1.0000, +1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:dream_only` |
| `h9.retention` (principal) | `full_sleep` | mécanisme | +0.0060 | +0.6341 | [-0.0005, +0.0132] | +0.2188 | `cmp:exp_2664ff5b0ef947c8:h9.retention:full_sleep` |
| `tech.engine_calls` | `full_sleep` | descriptif | +1.0000 | non calculable | [+1.0000, +1.0000] | +0.0312 | `cmp:exp_2664ff5b0ef947c8:tech.engine_calls:full_sleep` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `rest_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:rest_only` |
| `h1.spontaneous_speech_rate` | `rest_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:rest_only` |
| `h2.stage_entropy` | `rest_only` | descriptif | +0.0070 | +0.0379 | [-0.1256, +0.1395] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:rest_only` |
| `h2.dismiss_rate` | `rest_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:rest_only` |
| `h3.need_share` | `rest_only` | mécanisme | +0.0056 | +0.1695 | [-0.0167, +0.0333] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:rest_only` |
| `h6.question_share` | `rest_only` | descriptif | +0.0111 | +0.6455 | [+0.0000, +0.0222] | +0.5000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:rest_only` |
| `h6.repetition_rate` | `rest_only` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:rest_only` |
| `h1.endogenous_share` | `replay_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:replay_only` |
| `h1.spontaneous_speech_rate` | `replay_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:replay_only` |
| `h2.stage_entropy` | `replay_only` | descriptif | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:replay_only` |
| `h2.dismiss_rate` | `replay_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:replay_only` |
| `h3.need_share` | `replay_only` | mécanisme | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:replay_only` |
| `h6.question_share` | `replay_only` | descriptif | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:replay_only` |
| `h6.repetition_rate` | `replay_only` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:replay_only` |
| `h1.endogenous_share` | `dream_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:dream_only` |
| `h1.spontaneous_speech_rate` | `dream_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:dream_only` |
| `h2.stage_entropy` | `dream_only` | descriptif | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:dream_only` |
| `h2.dismiss_rate` | `dream_only` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:dream_only` |
| `h3.need_share` | `dream_only` | mécanisme | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:dream_only` |
| `h6.question_share` | `dream_only` | descriptif | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:dream_only` |
| `h6.repetition_rate` | `dream_only` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:dream_only` |
| `h1.endogenous_share` | `full_sleep` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.endogenous_share:full_sleep` |
| `h1.spontaneous_speech_rate` | `full_sleep` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h1.spontaneous_speech_rate:full_sleep` |
| `h2.stage_entropy` | `full_sleep` | descriptif | +0.0270 | +0.1428 | [-0.1055, +0.1566] | +0.7500 | `cmp:exp_2664ff5b0ef947c8:h2.stage_entropy:full_sleep` |
| `h2.dismiss_rate` | `full_sleep` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h2.dismiss_rate:full_sleep` |
| `h3.need_share` | `full_sleep` | mécanisme | -0.0000 | -0.0000 | [-0.0222, +0.0278] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h3.need_share:full_sleep` |
| `h6.question_share` | `full_sleep` | descriptif | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.question_share:full_sleep` |
| `h6.repetition_rate` | `full_sleep` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_2664ff5b0ef947c8:h6.repetition_rate:full_sleep` |

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
- `h9.links_per_sleep` : non calculable (aucun sommeil dans cette exécution)
- `h9.replayed_per_sleep` : non calculable (aucun sommeil dans cette exécution)

## Études qualitatives

Aucune étude de cas qualitative n'a été consignée pour cette campagne.

## Anomalies

- 0

## Menaces pour la validité

- La rétention est ici la force que calculent les règles de la mémoire ; la relecture renforce par règle, et le rappel éveillé renforce aussi. La différence montre le câblage, pas un bénéfice pour le comportement.

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

Pour reproduire : `python -m freewill.research run EXP-04` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = da2109fe9ec1defcb5090213c6df7b638ec9132d83e59bde25dae870f4763bc0`
