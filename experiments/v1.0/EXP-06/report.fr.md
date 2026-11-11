# Rapport de recherche : EXP-06, Adaptation neuronale

- Date : 2026-11-11T18:47:23+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-06 version 1.0.0 a été verrouillé avant exécution (empreinte 86d4debc2580). 18 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle contient zéro pour chaque condition. Ce résultat négatif est rapporté tel quel.

## Question et hypothèses

**H4. Plasticité paramétrique et structurelle.** Le vécu transforme des paramètres ou des structures, pas seulement une base de mémoire. Un petit module entraînable et le petit réseau propre de Freewill sont entraînés pendant le sommeil et peuvent grandir, chaque changement étant mesuré sur ce qu'ils n'ont jamais vu. Les poids du moteur qui pense pour l'être ne sont pas modifiés par sa vie.

## Préenregistrement

Critère principal : h2.dismiss_rate. Critères secondaires : h4.validation_gain, h4.forgetting, h4.parameters, h4.parameter_delta, h4.trainings_accepted. Condition de référence : memory_only. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `memory_only` : `{"history": "two_days", "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`
- `adapter` : `{"history": "two_days", "research": {"learner": true}, "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`
- `adapter_growth` : `{"history": "two_days", "research": {"learner": true, "learner_growth": true}, "engine_rule": {"question": 0.95, "need": 0.9, "association": 0.5, "reminiscence": 0.15, "drift": 0.1, "*": 0.6}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` (principal) | `adapter` | descriptif | -0.0250 | -0.5976 | [-0.0583, +0.0000] | +0.5000 | `cmp:exp_610bc2faae7c4021:h2.dismiss_rate:adapter` |
| `h2.dismiss_rate` (principal) | `adapter_growth` | descriptif | -0.0250 | -0.5976 | [-0.0583, +0.0000] | +0.5000 | `cmp:exp_610bc2faae7c4021:h2.dismiss_rate:adapter_growth` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `adapter` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h1.endogenous_share:adapter` |
| `h1.spontaneous_speech_rate` | `adapter` | descriptif | +0.0125 | +0.5976 | [+0.0000, +0.0292] | +0.5000 | `cmp:exp_610bc2faae7c4021:h1.spontaneous_speech_rate:adapter` |
| `h2.stage_entropy` | `adapter` | descriptif | +0.0111 | +0.0637 | [-0.1068, +0.1532] | +1.0000 | `cmp:exp_610bc2faae7c4021:h2.stage_entropy:adapter` |
| `h3.need_share` | `adapter` | mécanisme | +0.0042 | +0.0816 | [-0.0250, +0.0458] | +1.0000 | `cmp:exp_610bc2faae7c4021:h3.need_share:adapter` |
| `h6.question_share` | `adapter` | descriptif | +0.0333 | +0.7614 | [+0.0042, +0.0667] | +0.2500 | `cmp:exp_610bc2faae7c4021:h6.question_share:adapter` |
| `h6.repetition_rate` | `adapter` | fonction | +0.0085 | +0.3227 | [-0.0085, +0.0299] | +0.7500 | `cmp:exp_610bc2faae7c4021:h6.repetition_rate:adapter` |
| `h9.links_per_sleep` | `adapter` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.links_per_sleep:adapter` |
| `h9.replayed_per_sleep` | `adapter` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.replayed_per_sleep:adapter` |
| `h1.endogenous_share` | `adapter_growth` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h1.endogenous_share:adapter_growth` |
| `h1.spontaneous_speech_rate` | `adapter_growth` | descriptif | +0.0125 | +0.5976 | [+0.0000, +0.0292] | +0.5000 | `cmp:exp_610bc2faae7c4021:h1.spontaneous_speech_rate:adapter_growth` |
| `h2.stage_entropy` | `adapter_growth` | descriptif | +0.0111 | +0.0637 | [-0.1068, +0.1532] | +1.0000 | `cmp:exp_610bc2faae7c4021:h2.stage_entropy:adapter_growth` |
| `h3.need_share` | `adapter_growth` | mécanisme | +0.0042 | +0.0816 | [-0.0250, +0.0458] | +1.0000 | `cmp:exp_610bc2faae7c4021:h3.need_share:adapter_growth` |
| `h6.question_share` | `adapter_growth` | descriptif | +0.0333 | +0.7614 | [+0.0042, +0.0667] | +0.2500 | `cmp:exp_610bc2faae7c4021:h6.question_share:adapter_growth` |
| `h6.repetition_rate` | `adapter_growth` | fonction | +0.0085 | +0.3227 | [-0.0085, +0.0299] | +0.7500 | `cmp:exp_610bc2faae7c4021:h6.repetition_rate:adapter_growth` |
| `h9.links_per_sleep` | `adapter_growth` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.links_per_sleep:adapter_growth` |
| `h9.replayed_per_sleep` | `adapter_growth` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_610bc2faae7c4021:h9.replayed_per_sleep:adapter_growth` |

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
- `h9.retention` : non calculable (aucun souvenir n'a été formé avant le sommeil)

## Études qualitatives

Aucune étude de cas qualitative n'a été consignée pour cette campagne.

## Anomalies

- 0

## Menaces pour la validité

- Ce que le module doit apprendre est une règle fixe donnée au moteur simulé. Elle est apprenable par construction ; rien ne dit qu'un moteur réel présente une telle régularité.

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

Pour reproduire : `python -m freewill.research run EXP-06` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = 58b71ef82dddcfb5171d79c836e75e86c6cd5b455700944a38680378357f131f`
