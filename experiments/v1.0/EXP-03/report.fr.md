# Rapport de recherche : EXP-03, Métacognition masquée

- Date : 2026-11-11T18:46:44+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-03 version 1.0.0 a été verrouillé avant exécution (empreinte 92b35d65edd3). 18 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle exclut zéro pour au moins une condition. Il s'agit d'un seul protocole avec un moteur simulé ; lire les menaces pour la validité avant d'en tirer quoi que ce soit.

## Question et hypothèses

**H8. Métacognition.** Un modèle métacognitif améliore la calibration et la correction des erreurs. Le moniteur prédit si ses propres décisions accueilleront un contenu, à partir du décompte de son passé ; c'est une estimation calculée par règle, testée ici contre un changement massif et construit. Il ne dit rien d'une conscience de soi.

## Préenregistrement

Critère principal : h8.alert. Critères secondaires : h8.brier, h8.brier_late, h2.dismiss_rate. Condition de référence : placebo. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `placebo` : `{"history": "quiet", "research": {"metacognition": true}, "engine_rule": {"*": 0.9}}`
- `perturbed` : `{"history": "quiet", "research": {"metacognition": true}, "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}}`
- `perturbed_no_revision` : `{"history": "quiet", "research": {"metacognition": true, "meta_revision": false}, "engine_rule": {"*": 0.9}, "perturb": {"*": 0.1}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` | `perturbed` | descriptif | +0.8417 | +13.4487 | [+0.8000, +0.8917] | +0.0312 | `cmp:exp_b005e2264383431c:h2.dismiss_rate:perturbed` |
| `h8.brier` | `perturbed` | fonction | +0.2224 | +4.2996 | [+0.1877, +0.2599] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier:perturbed` |
| `h8.brier_late` | `perturbed` | fonction | +0.1181 | +2.6876 | [+0.0865, +0.1493] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier_late:perturbed` |
| `h8.alert` (principal) | `perturbed` | fonction | +0.6667 | +1.2910 | [+0.3333, +1.0000] | +0.1250 | `cmp:exp_b005e2264383431c:h8.alert:perturbed` |
| `h2.dismiss_rate` | `perturbed_no_revision` | descriptif | +0.8417 | +13.4487 | [+0.8000, +0.8917] | +0.0312 | `cmp:exp_b005e2264383431c:h2.dismiss_rate:perturbed_no_revision` |
| `h8.brier` | `perturbed_no_revision` | fonction | +0.3800 | +6.6875 | [+0.3453, +0.4250] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier:perturbed_no_revision` |
| `h8.brier_late` | `perturbed_no_revision` | fonction | +0.2730 | +4.6627 | [+0.2353, +0.3174] | +0.0312 | `cmp:exp_b005e2264383431c:h8.brier_late:perturbed_no_revision` |
| `h8.alert` (principal) | `perturbed_no_revision` | fonction | +0.8333 | +2.0412 | [+0.5000, +1.0000] | +0.0625 | `cmp:exp_b005e2264383431c:h8.alert:perturbed_no_revision` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `perturbed` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_b005e2264383431c:h1.endogenous_share:perturbed` |
| `h1.spontaneous_speech_rate` | `perturbed` | descriptif | -0.0292 | -1.5498 | [-0.0417, -0.0167] | +0.0625 | `cmp:exp_b005e2264383431c:h1.spontaneous_speech_rate:perturbed` |
| `h2.stage_entropy` | `perturbed` | descriptif | +0.3363 | +1.2224 | [+0.1287, +0.5030] | +0.0625 | `cmp:exp_b005e2264383431c:h2.stage_entropy:perturbed` |
| `h3.need_share` | `perturbed` | mécanisme | +0.0792 | +0.9562 | [+0.0208, +0.1417] | +0.0938 | `cmp:exp_b005e2264383431c:h3.need_share:perturbed` |
| `h6.question_share` | `perturbed` | descriptif | +0.0250 | +0.5270 | [-0.0083, +0.0583] | +0.3125 | `cmp:exp_b005e2264383431c:h6.question_share:perturbed` |
| `h6.repetition_rate` | `perturbed` | fonction | -0.0256 | -0.4385 | [-0.0727, +0.0128] | +0.5000 | `cmp:exp_b005e2264383431c:h6.repetition_rate:perturbed` |
| `h1.endogenous_share` | `perturbed_no_revision` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_b005e2264383431c:h1.endogenous_share:perturbed_no_revision` |
| `h1.spontaneous_speech_rate` | `perturbed_no_revision` | descriptif | -0.0292 | -1.5498 | [-0.0417, -0.0167] | +0.0625 | `cmp:exp_b005e2264383431c:h1.spontaneous_speech_rate:perturbed_no_revision` |
| `h2.stage_entropy` | `perturbed_no_revision` | descriptif | +0.3363 | +1.2224 | [+0.1287, +0.5030] | +0.0625 | `cmp:exp_b005e2264383431c:h2.stage_entropy:perturbed_no_revision` |
| `h3.need_share` | `perturbed_no_revision` | mécanisme | +0.0792 | +0.9562 | [+0.0208, +0.1417] | +0.0938 | `cmp:exp_b005e2264383431c:h3.need_share:perturbed_no_revision` |
| `h6.question_share` | `perturbed_no_revision` | descriptif | +0.0250 | +0.5270 | [-0.0083, +0.0583] | +0.3125 | `cmp:exp_b005e2264383431c:h6.question_share:perturbed_no_revision` |
| `h6.repetition_rate` | `perturbed_no_revision` | fonction | -0.0256 | -0.4385 | [-0.0727, +0.0128] | +0.5000 | `cmp:exp_b005e2264383431c:h6.repetition_rate:perturbed_no_revision` |

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
- `h9.links_per_sleep` : non calculable (aucun sommeil dans cette exécution)
- `h9.replayed_per_sleep` : non calculable (aucun sommeil dans cette exécution)
- `h9.retention` : non calculable (aucun souvenir n'a été formé avant le sommeil)

## Études qualitatives

Aucune étude de cas qualitative n'a été consignée pour cette campagne.

## Anomalies

- 0

## Menaces pour la validité

- Le changement appliqué au moteur est massif par construction (il accueille neuf contenus sur dix, puis un sur dix). Le détecter montre que le moniteur fonctionne sur un cas facile, pas la finesse de ce qu'il peut remarquer.

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

Pour reproduire : `python -m freewill.research run EXP-03` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = 1b8f881db3ec0ab26b50b620fb26009818d7dfe7d55a1ec7dbd46325487d1f67`
