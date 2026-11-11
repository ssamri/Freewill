# Rapport de recherche : EXP-07, Agentivité dans un monde virtuel

- Date : 2026-11-11T18:47:35+00:00
- Version : Freewill 1.0.0, Research Lab 1.0.0, commit 679328f829ae
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-07 version 1.0.0 a été verrouillé avant exécution (empreinte c855559c7bfc). 30 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 6 groupes de copies terminés sur 6 prévus.

Pour le critère principal, l'intervalle exclut zéro pour au moins une condition. Il s'agit d'un seul protocole avec un moteur simulé ; lire les menaces pour la validité avant d'en tirer quoi que ce soit.

## Question et hypothèses

**H10. Modèle de soi et agentivité.** Un modèle de soi et d'un monde apprend les conséquences de ses actes. L'être agit dans un tout petit monde clos en grille et attribue les changements à l'aide d'une table de ce que ses actes ont produit auparavant. Le monde est très petit et la comparaison se fait avec une attribution volontairement naïve.

## Préenregistrement

Critère principal : h10.attribution_accuracy. Critères secondaires : h10.prediction_error. Condition de référence : no_self_model. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `no_self_model` : `{"history": "quiet", "research": {"sandbox": true, "self_model": false}, "agency": {"exogenous": 0.25}}`
- `self_model` : `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25}}`
- `self_model_calm` : `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.0}}`
- `self_model_noisy_senses` : `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25, "noise": 0.2}}`
- `self_model_rule_change` : `{"history": "quiet", "research": {"sandbox": true}, "agency": {"exogenous": 0.25, "break_action": "east", "break_after": 60}}`

`seeds = [11, 23, 37, 51, 73, 89]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h10.attribution_accuracy` (principal) | `self_model` | fonction | +0.2833 | +2.1947 | [+0.1917, +0.3708] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model` |
| `h10.attribution_accuracy` (principal) | `self_model_calm` | fonction | +0.3500 | +7.3786 | [+0.3167, +0.3833] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_calm` |
| `h10.attribution_accuracy` (principal) | `self_model_noisy_senses` | fonction | -0.2958 | -3.1005 | [-0.3542, -0.2208] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_noisy_senses` |
| `h10.attribution_accuracy` (principal) | `self_model_rule_change` | fonction | +0.3083 | +2.9510 | [+0.2250, +0.3750] | +0.0312 | `cmp:exp_afe3f73dc0d94e26:h10.attribution_accuracy:self_model_rule_change` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `self_model` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model` |
| `h1.spontaneous_speech_rate` | `self_model` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model` |
| `h2.stage_entropy` | `self_model` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model` |
| `h2.dismiss_rate` | `self_model` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model` |
| `h3.need_share` | `self_model` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model` |
| `h6.question_share` | `self_model` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model` |
| `h6.repetition_rate` | `self_model` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model` |
| `h1.endogenous_share` | `self_model_calm` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_calm` |
| `h1.spontaneous_speech_rate` | `self_model_calm` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_calm` |
| `h2.stage_entropy` | `self_model_calm` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_calm` |
| `h2.dismiss_rate` | `self_model_calm` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_calm` |
| `h3.need_share` | `self_model_calm` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_calm` |
| `h6.question_share` | `self_model_calm` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_calm` |
| `h6.repetition_rate` | `self_model_calm` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_calm` |
| `h1.endogenous_share` | `self_model_noisy_senses` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_noisy_senses` |
| `h1.spontaneous_speech_rate` | `self_model_noisy_senses` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_noisy_senses` |
| `h2.stage_entropy` | `self_model_noisy_senses` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_noisy_senses` |
| `h2.dismiss_rate` | `self_model_noisy_senses` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_noisy_senses` |
| `h3.need_share` | `self_model_noisy_senses` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_noisy_senses` |
| `h6.question_share` | `self_model_noisy_senses` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_noisy_senses` |
| `h6.repetition_rate` | `self_model_noisy_senses` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_noisy_senses` |
| `h1.endogenous_share` | `self_model_rule_change` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.endogenous_share:self_model_rule_change` |
| `h1.spontaneous_speech_rate` | `self_model_rule_change` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h1.spontaneous_speech_rate:self_model_rule_change` |
| `h2.stage_entropy` | `self_model_rule_change` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.stage_entropy:self_model_rule_change` |
| `h2.dismiss_rate` | `self_model_rule_change` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h2.dismiss_rate:self_model_rule_change` |
| `h3.need_share` | `self_model_rule_change` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h3.need_share:self_model_rule_change` |
| `h6.question_share` | `self_model_rule_change` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.question_share:self_model_rule_change` |
| `h6.repetition_rate` | `self_model_rule_change` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_afe3f73dc0d94e26:h6.repetition_rate:self_model_rule_change` |

- `h10.prediction_error` : non calculable (rien à mesurer dans cette exécution)
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
- `h9.retention` : non calculable (aucun souvenir n'a été formé avant le sommeil)

## Études qualitatives

Aucune étude de cas qualitative n'a été consignée pour cette campagne.

## Anomalies

- 0

## Menaces pour la validité

- Le monde est une grille de cinq cases sur cinq avec un seul objet. La comparaison se fait avec une attribution qui prend tout changement pour son propre fait, facile à battre.

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

Pour reproduire : `python -m freewill.research run EXP-07` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = 23b323c653c3303682917ff6ea5200d14b94d9c201314245759cea69ca0ce911`
