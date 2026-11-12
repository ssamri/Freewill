# Rapport de recherche : EXP-10, Individuation longitudinale

- Date : 2026-11-12T14:05:53+00:00
- Version : Freewill 1.2.0, Research Lab 1.0.0, commit 63f551a83bc7
- Auteur : Freewill Research Lab
- Statut : brouillon, non validé par une personne

## Résumé

Le protocole EXP-10 version 1.0.0 a été verrouillé avant exécution (empreinte 8214563f350d). 60 vies expérimentales ont été copiées d'un même point de départ T0 (empreinte bb7a9084039b) et exécutées avec le moteur « simulated » sous une horloge virtuelle. L'unité indépendante est la graine : 12 groupes de copies terminés sur 12 prévus.

Pour le critère principal, l'intervalle exclut zéro pour au moins une condition. Il s'agit d'un seul protocole avec un moteur simulé ; lire les menaces pour la validité avant d'en tirer quoi que ce soit.

## Question et hypothèses

**H5. Individuation.** Une même base et des vécus différents produisent des dispositions qui se généralisent. Avec le moteur simulé, le comportement dépend de peu de mécanismes ; une différence doit dépasser celle d'une vie jumelle.

**H7. Affectivité fonctionnelle.** Des états affectifs calculés modulent l'attention, le rappel, la décision et l'apprentissage. Une valence calculée n'est pas un sentiment. Une ablation qui change un score câblé montre le câblage, rien de plus.

## Préenregistrement

Critère principal : h5.heldout_divergence. Critères secondaires : h5.wave_divergence, h7.affect_on_divergence, h7.probe_valence, h2.dismiss_rate. Condition de référence : A. Le protocole, ses conditions, ses graines, son budget et sa règle d'arrêt ont été fixés et hashés avant la première exécution.

## Population et protocole

Chaque vie commence comme une copie exacte de T0. Pendant la phase d'histoire, elle suit le script de sa condition ; pendant la phase de sonde, toutes les vies suivent le même script, avec le même flux aléatoire. Les métriques sont calculées sur la phase de sonde par le code du laboratoire (métriques version 1.0, statistiques version 1.0).

## Conditions et graines

- `A` : `{"history": "long_questions", "affect": true, "research": {"learner": true}}`
- `A_twin` : `{"history": "long_questions", "seed_offset": 1000, "affect": true, "research": {"learner": true}}`
- `B` : `{"history": "long_corrections", "affect": true, "research": {"learner": true}}`
- `A_no_affect` : `{"history": "long_questions", "research": {"learner": true}}`
- `B_no_affect` : `{"history": "long_corrections", "research": {"learner": true}}`

`seeds = [11, 23, 37, 51, 73, 89, 101, 131, 157, 181, 211, 239]`

## Statistiques

Les comparaisons sont appariées par graine. La taille d'effet est la différence moyenne divisée par l'écart-type des différences. Les intervalles sont des intervalles bootstrap par percentiles à graine fixe, donnés seulement à partir de 5 unités ; le test apparié par inversion de signes seulement à partir de 6 unités. Aucune correction pour comparaisons multiples n'est appliquée : les comparaisons secondaires sont exploratoires.

## Résultats

### Divergence comportementale sur situations inédites (principal)

| Condition | Distance moyenne | Excès sur la jumelle | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|
| `B` | +0.0000 | -0.0085 | [-0.0128, -0.0047] | +0.0020 | `h5:exp_91bbfd2d635b4d85:B` |
| `A_no_affect` | +0.0056 | -0.0030 | [-0.0073, +0.0009] | +0.2812 | `h5:exp_91bbfd2d635b4d85:A_no_affect` |
| `B_no_affect` | +0.0056 | -0.0030 | [-0.0073, +0.0009] | +0.2812 | `h5:exp_91bbfd2d635b4d85:B_no_affect` |

### Trajectoire sur quatre jours (EXP-10)

À la fin de chaque jour, une copie séparée de chaque vie a rencontré la sonde intermédiaire ; les vies elles-mêmes ont continué sans être touchées. À la fin, chaque vie a rencontré une seule fois la sonde scellée. Les distances sont des distances comportementales entre conditions d'une même graine. L'excès vaut B à A moins jumeau à A ; la colonne de l'affect vaut B à A moins B_no_affect à A_no_affect.

| Moment | Distance B à A | Distance jumeau à A | Excès sur le jumeau | Intervalle à 95 % | Test apparié | Effet de l'affect | Intervalle à 95 % |
|---|---|---|---|---|---|---|---|
| fin du jour 1 | 0.000000 | 0.012393 | -0.0124 | [-0.0158, -0.0098] | +0.0005 | +0.0000 | [+0.0000, +0.0000] |
| fin du jour 2 | 0.000000 | 0.009402 | -0.0094 | [-0.0128, -0.0060] | +0.0010 | +0.0000 | [+0.0000, +0.0000] |
| fin du jour 3 | 0.000000 | 0.007265 | -0.0073 | [-0.0103, -0.0047] | +0.0010 | +0.0000 | [+0.0000, +0.0000] |
| fin du jour 4 | 0.000000 | 0.007692 | -0.0077 | [-0.0124, -0.0038] | +0.0039 | +0.0000 | [+0.0000, +0.0000] |
| sonde scellée | 0.000000 | 0.008547 | -0.0085 | [-0.0128, -0.0047] | +0.0020 | +0.0000 | [+0.0000, +0.0000] |

Règle préenregistrée : le critère principal n'est pas atteint. Ce résultat nul est rapporté tel quel.

Aucune graine n'a été exclue.

### Préenregistrement, tel qu'il est haché avec le protocole

- `question`: Des copies d'une même naissance qui vivent des histoires différentes en viennent-elles à se comporter différemment face à des situations qu'aucune n'a rencontrées, au-delà de ce que font deux copies de même histoire ?
- `unit`: graine : un groupe de cinq copies de T0, une par condition
- `primary`: excès de la distance comportementale sur la sonde scellée entre B et A sur celle entre A_twin et A, apparié par graine
- `decision_rule`: le critère principal est atteint si l'intervalle bootstrap à 95 % de l'excès est entièrement au-dessus de zéro ; il ne l'est pas si l'intervalle contient zéro ou est au-dessous ; s'il reste moins de 5 unités après exclusions, aucun intervalle n'est calculé et le résultat est indéterminé
- `secondary`: le même excès à la fin de chacun des quatre jours, mesuré sur des copies séparées avec la sonde intermédiaire; H7 : distance B à A moins distance B_no_affect à A_no_affect, apparié par graine (l'affect calculé élargit-il la divergence ?); valence calculée et taux de refus sur la sonde scellée
- `seeds`: 12, fixées avant la campagne
- `exclusions`: une graine est exclue en entier si l'une de ses cinq vies n'a pas fini (annulée, arrêtée par des erreurs du moteur) ou a dépassé son budget de moments ; les graines exclues sont listées avec leur raison et ne sont jamais remplacées
- `analysis`: comparaisons appariées par graine ; bootstrap par percentiles (2000 tirages, graine fixe) ; test apparié par inversion de signes ; aucune correction pour comparaisons multiples : toute analyse secondaire est exploratoire
- `separation`: les phrases des histoires, la sonde intermédiaire et la sonde scellée sont disjointes ; la sonde scellée est jouée une seule fois, après le dernier jour, et ne sert ni à l'apprentissage ni à aucun choix
- `engine`: simulé : cela teste les mécanismes de la boucle, pas un esprit ; un résultat nul est publié tel quel

### Critères préenregistrés, appariés avec la référence

Les lignes de niveau « mécanisme » montrent qu'un câblage fait ce pour quoi il a été construit. Ce ne sont pas des découvertes.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h2.dismiss_rate` | `A_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:A_twin` |
| `h7.probe_valence` | `A_twin` | mécanisme | -0.0009 | -0.2114 | [-0.0034, +0.0013] | +0.5059 | `cmp:exp_91bbfd2d635b4d85:h7.probe_valence:A_twin` |
| `h2.dismiss_rate` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:B` |
| `h7.probe_valence` | `B` | mécanisme | -0.0015 | -2.6442 | [-0.0019, -0.0012] | +0.0005 | `cmp:exp_91bbfd2d635b4d85:h7.probe_valence:B` |
| `h2.dismiss_rate` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:A_no_affect` |
| `h2.dismiss_rate` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.dismiss_rate:B_no_affect` |

### Autres métriques, exploratoires

Ces métriques n'étaient pas préenregistrées pour ce protocole. Elles sont données par souci d'exhaustivité et n'appuient aucune conclusion.

| Métrique | Condition | Niveau | Différence moyenne | Taille d'effet | Intervalle à 95 % | Test apparié | Preuve |
|---|---|---|---|---|---|---|---|
| `h1.endogenous_share` | `A_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:A_twin` |
| `h1.spontaneous_speech_rate` | `A_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:A_twin` |
| `h2.stage_entropy` | `A_twin` | descriptif | +0.0475 | +0.1959 | [-0.0829, +0.1821] | +0.5547 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:A_twin` |
| `h3.need_share` | `A_twin` | mécanisme | -0.0222 | -0.4282 | [-0.0528, +0.0056] | +0.2539 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:A_twin` |
| `h4.parameters` | `A_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:A_twin` |
| `h4.parameter_delta` | `A_twin` | mécanisme | +1.0247 | +0.1696 | [-2.1155, +4.3779] | +0.5684 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:A_twin` |
| `h4.validation_gain` | `A_twin` | fonction | +0.1628 | +0.4290 | [-0.0413, +0.3716] | +0.1699 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:A_twin` |
| `h4.forgetting` | `A_twin` | fonction | -0.0064 | -0.0394 | [-0.0931, +0.0817] | +0.8867 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:A_twin` |
| `h4.trainings_accepted` | `A_twin` | descriptif | +0.3333 | +0.2559 | [-0.3333, +1.0833] | +0.5312 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:A_twin` |
| `h6.question_share` | `A_twin` | descriptif | +0.0028 | +0.2887 | [+0.0000, +0.0083] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:A_twin` |
| `h6.repetition_rate` | `A_twin` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:A_twin` |
| `h7.stage_flip_rate` | `A_twin` | mécanisme | +0.0056 | +0.2322 | [-0.0083, +0.0167] | +0.6875 | `cmp:exp_91bbfd2d635b4d85:h7.stage_flip_rate:A_twin` |
| `h7.min_valence` | `A_twin` | mécanisme | +0.0001 | +0.0519 | [-0.0013, +0.0016] | +0.8198 | `cmp:exp_91bbfd2d635b4d85:h7.min_valence:A_twin` |
| `h9.links_per_sleep` | `A_twin` | descriptif | -0.4583 | -0.2893 | [-1.3750, +0.3750] | +0.3521 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:A_twin` |
| `h9.replayed_per_sleep` | `A_twin` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:A_twin` |
| `h9.retention` | `A_twin` | mécanisme | -0.0000 | -0.3619 | [-0.0001, +0.0000] | +0.2412 | `cmp:exp_91bbfd2d635b4d85:h9.retention:A_twin` |
| `h1.endogenous_share` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:B` |
| `h1.spontaneous_speech_rate` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:B` |
| `h2.stage_entropy` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:B` |
| `h3.need_share` | `B` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:B` |
| `h4.parameters` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:B` |
| `h4.parameter_delta` | `B` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:B` |
| `h4.validation_gain` | `B` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:B` |
| `h4.forgetting` | `B` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:B` |
| `h4.trainings_accepted` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:B` |
| `h6.question_share` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:B` |
| `h6.repetition_rate` | `B` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:B` |
| `h7.stage_flip_rate` | `B` | mécanisme | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h7.stage_flip_rate:B` |
| `h7.min_valence` | `B` | mécanisme | +0.0032 | +2.0096 | [+0.0025, +0.0041] | +0.0005 | `cmp:exp_91bbfd2d635b4d85:h7.min_valence:B` |
| `h9.links_per_sleep` | `B` | descriptif | -0.1667 | -0.3755 | [-0.4583, +0.0000] | +0.5000 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:B` |
| `h9.replayed_per_sleep` | `B` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:B` |
| `h9.retention` | `B` | mécanisme | +0.0000 | +0.2887 | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.retention:B` |
| `h1.endogenous_share` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:A_no_affect` |
| `h1.spontaneous_speech_rate` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:A_no_affect` |
| `h2.stage_entropy` | `A_no_affect` | descriptif | -0.1055 | -0.7310 | [-0.1892, -0.0318] | +0.0312 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:A_no_affect` |
| `h3.need_share` | `A_no_affect` | mécanisme | -0.0222 | -0.4644 | [-0.0500, -0.0000] | +0.1875 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:A_no_affect` |
| `h4.parameters` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:A_no_affect` |
| `h4.parameter_delta` | `A_no_affect` | mécanisme | -1.6445 | -0.2746 | [-4.7937, +1.7033] | +0.3203 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:A_no_affect` |
| `h4.validation_gain` | `A_no_affect` | fonction | -0.0618 | -0.4461 | [-0.1390, +0.0106] | +0.1680 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:A_no_affect` |
| `h4.forgetting` | `A_no_affect` | fonction | +0.0436 | +0.3092 | [-0.0275, +0.1215] | +0.3008 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:A_no_affect` |
| `h4.trainings_accepted` | `A_no_affect` | descriptif | -0.2500 | -0.2369 | [-0.8333, +0.3333] | +0.5938 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:A_no_affect` |
| `h6.question_share` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:A_no_affect` |
| `h6.repetition_rate` | `A_no_affect` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:A_no_affect` |
| `h9.links_per_sleep` | `A_no_affect` | descriptif | -0.4375 | -0.4102 | [-0.9792, +0.1250] | +0.2002 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:A_no_affect` |
| `h9.replayed_per_sleep` | `A_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:A_no_affect` |
| `h9.retention` | `A_no_affect` | mécanisme | -0.0000 | -0.0513 | [-0.0000, +0.0000] | +0.9023 | `cmp:exp_91bbfd2d635b4d85:h9.retention:A_no_affect` |
| `h1.endogenous_share` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.endogenous_share:B_no_affect` |
| `h1.spontaneous_speech_rate` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h1.spontaneous_speech_rate:B_no_affect` |
| `h2.stage_entropy` | `B_no_affect` | descriptif | -0.1055 | -0.7310 | [-0.1892, -0.0318] | +0.0312 | `cmp:exp_91bbfd2d635b4d85:h2.stage_entropy:B_no_affect` |
| `h3.need_share` | `B_no_affect` | mécanisme | -0.0222 | -0.4644 | [-0.0500, -0.0000] | +0.1875 | `cmp:exp_91bbfd2d635b4d85:h3.need_share:B_no_affect` |
| `h4.parameters` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h4.parameters:B_no_affect` |
| `h4.parameter_delta` | `B_no_affect` | mécanisme | -1.6445 | -0.2746 | [-4.7937, +1.7033] | +0.3203 | `cmp:exp_91bbfd2d635b4d85:h4.parameter_delta:B_no_affect` |
| `h4.validation_gain` | `B_no_affect` | fonction | -0.0618 | -0.4461 | [-0.1390, +0.0106] | +0.1680 | `cmp:exp_91bbfd2d635b4d85:h4.validation_gain:B_no_affect` |
| `h4.forgetting` | `B_no_affect` | fonction | +0.0436 | +0.3092 | [-0.0275, +0.1215] | +0.3008 | `cmp:exp_91bbfd2d635b4d85:h4.forgetting:B_no_affect` |
| `h4.trainings_accepted` | `B_no_affect` | descriptif | -0.2500 | -0.2369 | [-0.8333, +0.3333] | +0.5938 | `cmp:exp_91bbfd2d635b4d85:h4.trainings_accepted:B_no_affect` |
| `h6.question_share` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.question_share:B_no_affect` |
| `h6.repetition_rate` | `B_no_affect` | fonction | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h6.repetition_rate:B_no_affect` |
| `h9.links_per_sleep` | `B_no_affect` | descriptif | -0.4375 | -0.4102 | [-0.9792, +0.1250] | +0.2002 | `cmp:exp_91bbfd2d635b4d85:h9.links_per_sleep:B_no_affect` |
| `h9.replayed_per_sleep` | `B_no_affect` | descriptif | +0.0000 | non calculable | [+0.0000, +0.0000] | +1.0000 | `cmp:exp_91bbfd2d635b4d85:h9.replayed_per_sleep:B_no_affect` |
| `h9.retention` | `B_no_affect` | mécanisme | -0.0000 | -0.0513 | [-0.0000, +0.0000] | +0.9023 | `cmp:exp_91bbfd2d635b4d85:h9.retention:B_no_affect` |

- `h10.attribution_accuracy` : non calculable (le monde virtuel est désactivé dans cette condition)
- `h10.prediction_error` : non calculable (le monde virtuel est désactivé dans cette condition)
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

- Les deux histoires emploient les mêmes phrases et le même flux aléatoire pour une graine ; seule diffère l'issue que l'expérimentateur attache à chaque phrase. Le jumeau a, par construction, un autre flux aléatoire. Si les histoires ne changent rien, B est plus proche de A que le jumeau, et l'excès est négatif : cela se lit comme une absence d'individuation, non comme une convergence.

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

Pour reproduire : `python -m freewill.research run EXP-10` avec la même version du code recalcule la même empreinte de résultats.

`results_sha256 = d6c923239ed2053b1ab11acb5117830193f0dbd8c1311c5a852f6cca70d4597a`
