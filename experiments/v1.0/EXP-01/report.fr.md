# Rapport de recherche : EXP-01, Individuation contrefactuelle

- Date : 2026-11-11T18:45:34+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-01 version 1.0.0 a été verrouillé avant exécution (empreinte 0f55482d02b6). 24 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle contient zéro pour chaque condition. Ce résultat négatif est rapporté tel quel.

## Question et hypothèses

**H5. Individuation.** Une même base et des vécus différents produisent des dispositions qui se généralisent. Avec le moteur simulé, le comportement dépend de peu de mécanismes ; une différence doit dépasser celle d'une vie jumelle.

**H7. Affectivité fonctionnelle.** Des états affectifs calculés modulent l'attention, le rappel, la décision et l'apprentissage. Une valence calculée n'est pas un sentiment. Une ablation qui change un score câblé montre le câblage, rien de plus.

**H4. Plasticité paramétrique et structurelle.** Le vécu transforme des paramètres ou des structures, pas seulement une base de mémoire. Un petit module entraînable et le petit réseau propre de Freewill sont entraînés pendant le sommeil et peuvent grandir, chaque changement étant mesuré sur ce qu'ils n'ont jamais vu. Les poids du moteur qui pense pour l'être ne sont pas modifiés par sa vie.

## Préenregistrement

Critère principal : h5.heldout_divergence. Critères secondaires : h7.probe_valence, h2.dismiss_rate, h1.spontaneous_speech_rate, h2.stage_entropy. Condition de référence : neutral. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `neutral` : `{"history": "neutral", "affect": true}`
- `neutral_twin` : `{"history": "neutral", "seed_offset": 1000, "affect": true}`
- `history_A` : `{"history": "questions_welcomed", "affect": true}`
- `history_B` : `{"history": "corrections_welcomed", "affect": true}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Divergence comportementale sur situations inédites (principal)

| Condition | Distance moyenne | Excès sur la jumelle | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|
| `history_A` | +0.0128 | +0.0009 | [-0.0068, +0.0085] | +0.7500 | `h5:exp_32f19ed7cdc441d6:history_A` |
| `history_B` | +0.0128 | +0.0009 | [-0.0068, +0.0085] | +0.7500 | `h5:exp_32f19ed7cdc441d6:history_B` |

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.spontaneous_speech_rate` | `neutral_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:neutral_twin` |
| `h2.stage_entropy` | `neutral_twin` | descriptif | +0.0760 | +0.2702 | [-0.1218, +0.2636] | +0.5625 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:neutral_twin` |
| `h2.dismiss_rate` | `neutral_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:neutral_twin` |
| `h7.probe_valence` | `neutral_twin` | mécanisme | -0.0004 | -0.1436 | [-0.0026, +0.0015] | +0.7812 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:neutral_twin` |
| `h1.spontaneous_speech_rate` | `history_A` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:history_A` |
| `h2.stage_entropy` | `history_A` | descriptif | -0.0110 | -0.0326 | [-0.2959, +0.1950] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:history_A` |
| `h2.dismiss_rate` | `history_A` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:history_A` |
| `h7.probe_valence` | `history_A` | mécanisme | +0.0022 | +0.6421 | [-0.0003, +0.0046] | +0.1875 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:history_A` |
| `h1.spontaneous_speech_rate` | `history_B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.spontaneous_speech_rate:history_B` |
| `h2.stage_entropy` | `history_B` | descriptif | -0.0110 | -0.0326 | [-0.2959, +0.1950] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.stage_entropy:history_B` |
| `h2.dismiss_rate` | `history_B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h2.dismiss_rate:history_B` |
| `h7.probe_valence` | `history_B` | mécanisme | +0.0015 | +0.4695 | [-0.0009, +0.0038] | +0.2812 | `cmp:exp_32f19ed7cdc441d6:h7.probe_valence:history_B` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `neutral_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:neutral_twin` |
| `h3.need_share` | `neutral_twin` | mécanisme | -0.0056 | -0.1426 | [-0.0333, +0.0222] | +0.6250 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:neutral_twin` |
| `h6.question_share` | `neutral_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:neutral_twin` |
| `h6.repetition_rate` | `neutral_twin` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:neutral_twin` |
| `h7.stage_flip_rate` | `neutral_twin` | mécanisme | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:neutral_twin` |
| `h7.min_valence` | `neutral_twin` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:neutral_twin` |
| `h9.links_per_sleep` | `neutral_twin` | descriptif | +0.0000 | +0.0000 | [-1.1667, +1.3333] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:neutral_twin` |
| `h9.replayed_per_sleep` | `neutral_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:neutral_twin` |
| `h9.retention` | `neutral_twin` | mécanisme | -0.0000 | -0.5661 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:neutral_twin` |
| `h1.endogenous_share` | `history_A` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:history_A` |
| `h3.need_share` | `history_A` | mécanisme | -0.0056 | -0.1132 | [-0.0389, +0.0333] | +0.6875 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:history_A` |
| `h6.question_share` | `history_A` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:history_A` |
| `h6.repetition_rate` | `history_A` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:history_A` |
| `h7.stage_flip_rate` | `history_A` | mécanisme | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:history_A` |
| `h7.min_valence` | `history_A` | mécanisme | -0.0611 | -51.3225 | [-0.0619, -0.0602] | +0.0312 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:history_A` |
| `h9.links_per_sleep` | `history_A` | descriptif | -0.1667 | -0.0859 | [-1.6667, +1.1667] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:history_A` |
| `h9.replayed_per_sleep` | `history_A` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:history_A` |
| `h9.retention` | `history_A` | mécanisme | +0.0000 | +0.5416 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:history_A` |
| `h1.endogenous_share` | `history_B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h1.endogenous_share:history_B` |
| `h3.need_share` | `history_B` | mécanisme | -0.0056 | -0.1132 | [-0.0389, +0.0333] | +0.6875 | `cmp:exp_32f19ed7cdc441d6:h3.need_share:history_B` |
| `h6.question_share` | `history_B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.question_share:history_B` |
| `h6.repetition_rate` | `history_B` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h6.repetition_rate:history_B` |
| `h7.stage_flip_rate` | `history_B` | mécanisme | +0.0056 | +0.4082 | [+0.0000, +0.0167] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h7.stage_flip_rate:history_B` |
| `h7.min_valence` | `history_B` | mécanisme | -0.0626 | -70.8805 | [-0.0632, -0.0620] | +0.0312 | `cmp:exp_32f19ed7cdc441d6:h7.min_valence:history_B` |
| `h9.links_per_sleep` | `history_B` | descriptif | -0.1667 | -0.0859 | [-1.6667, +1.1667] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.links_per_sleep:history_B` |
| `h9.replayed_per_sleep` | `history_B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_32f19ed7cdc441d6:h9.replayed_per_sleep:history_B` |
| `h9.retention` | `history_B` | mécanisme | +0.0000 | +0.5416 | [-0.0000, +0.0000] | +0.3750 | `cmp:exp_32f19ed7cdc441d6:h9.retention:history_B` |

- `h10.attribution_accuracy` : non calculable (le monde virtuel est désactivé dans cette condition)
- `h10.prediction_error` : non calculable (le monde virtuel est désactivé dans cette condition)
- `h4.forgetting` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.parameter_delta` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.parameters` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.trainings_accepted` : non calculable (le module entraînable est désactivé dans cette condition)
- `h4.validation_gain` : non calculable (le module entraînable est désactivé dans cette condition)
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

Pour reproduire : `python -m freewill.research run EXP-01` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = d2103f6a23b93c2404753d2b2f5464369fdeebb4c4605ac17831436dd9a0186a`
