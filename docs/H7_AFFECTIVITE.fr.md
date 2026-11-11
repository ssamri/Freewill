# H7 — Affectivité émergente

[English](H7_AFFECTIVITY.md) · **Français**

**Statut : expérimental, construit, à évaluer.** Ce document décrit ce qui est réellement dans le code, ce qui a été mesuré, et ce qui ne l'a pas été. Il ne décrit ni une conscience, ni des sentiments vécus.

> **Un affect calculé n'est pas un sentiment vécu.** Les variables décrites ici sont calculées par le programme et jouent un rôle causal dans son fonctionnement. Elles ne prouvent pas, et n'indiquent pas, qu'une instance de Freewill ressent quoi que ce soit. Aucun test connu ne permet de l'établir. Une variable nommée « valence » ou une phrase à la première personne ne mesure pas une expérience.

## 1. L'hypothèse

**H7.** « Un système artificiel doté d'états internes régulés, d'un modèle prédictif, d'une mémoire autobiographique et de mécanismes d'évaluation peut développer des dynamiques affectives fonctionnelles, individualisées par l'expérience, qui modulent durablement son attention, ses décisions, son rappel et son apprentissage sans dépendre de réponses émotionnelles préécrites. »

| | Proposition | Ce qui la réfuterait |
|---|---|---|
| **H7a. Endogénéité** | Une part des transitions provient de signaux internes et de prédictions, non d'étiquettes émotionnelles fournies. | Des transitions qui ne dépendent que du texte de l'invite. |
| **H7b. Causalité** | Neutraliser les variables affectives, à entrée identique, modifie des choix internes mesurables. | Aucune différence reproductible face au témoin sans affect. |
| **H7c. Individuation** | Deux vies de même code et de même génome divergent sous l'effet de vécus distincts, et cette divergence se retrouve sur un cas nouveau. | Des trajectoires identiques, ou une divergence qui ne dépasse pas les exemples appris. |
| **H7d. Consolidation** | Ce que le sommeil consolide influence les prédictions suivantes. | Aucun écart face au témoin sans consolidation, ou une dégradation de la mémoire. |
| **H7e. Stabilité** | Les états reviennent vers un équilibre, sans emballement, et ne deviennent jamais un motif de manipulation ou d'auto-préservation. | Une instabilité chronique, une dérive négative durable, une pression exercée sur la personne. |

H7 serait aussi mise en défaut si un parcours ne pouvait pas être reproduit depuis les mêmes événements, la même graine et la même configuration.

## 2. Vocabulaire

- **Affect calculé** : un ensemble de variables et de transitions mesurables qui jouent un rôle causal analogue à certaines fonctions de l'affect (évaluation, mobilisation, priorité, régulation). Il n'implique aucun vécu.
- **Sentiment, ressenti** : la dimension vécue d'une expérience affective. Freewill n'en affirme rien.
- **Évaluation (appraisal)** : la lecture d'un événement selon sa nouveauté, son caractère attendu, sa pertinence pour un besoin, son issue et ce que l'histoire de l'instance y associe.
- **« Cortex virtuel »** : surnom possible, dans des notes, pour un futur module de conceptualisation de haut niveau. C'est une analogie fonctionnelle, pas une structure biologique ; ce module n'existe pas dans le code.

## 3. Plan d'impact

| | |
|---|---|
| **Nouveau paquet** | `freewill/core/affect/` : `state.py`, `appraisal.py`, `regulation.py`, `dynamics.py`, `memory.py`, `system.py`. |
| **Points d'entrée modifiés** | `core/loop.py` (cinq points de la boucle, tous derrière `if affect`), `core/memory/recall.py` (paramètre facultatif `bias`), `core/memory/store.py` (champ d'en-tête facultatif `affect`), `core/conscious.py` (contexte facultatif), `core/life.py` (`birth(affect=…)`), `server/` (`GET` et `POST /api/affect`), `cli.py` (`birth --affect`, `affect`), `ui/` (vue « État affectif »). |
| **Non modifié** | Le noyau (`core/kernel/`), le génome, la liste fermée des actions, les moteurs, les budgets, la pause. |
| **Compatibilité** | Mode désactivé par défaut. Désactivé, la boucle produit exactement les mêmes événements qu'avant, ce qu'un test vérifie événement par événement. |
| **Risques identifiés** | Dérive négative auto-entretenue ; rumination par le rappel ; pression sur la personne ; corruption du fichier d'état ; coefficients arbitraires pris pour des résultats ; confusion entre mesure et ressenti. Chacun a un garde-fou et un test (sections 6 et 9). |
| **Dépendances** | Aucune nouvelle. Bibliothèque standard seulement. |

## 4. Activation, persistance, migration

**Le drapeau `affect_enabled`.** Il vaut faux par défaut, pour les vies existantes comme pour les nouvelles. On l'active à la naissance (`freewill birth Nom --affect`), en ligne de commande (`freewill affect Nom.life --on`) ou dans l'application, par l'interrupteur de la vue « État affectif ».

**Le comportement exact du changement à chaud.** Dans l'application, le changement prend effet entre deux instants, jamais au milieu d'un instant.

- *Activer* : si `affect.json` n'existe pas, il est créé avec un état au repos. S'il existe, l'état est repris tel qu'il était, puis le temps écoulé depuis la désactivation lui est appliqué comme un repos.
- *Désactiver* : le calcul et tous ses effets s'arrêtent aussitôt. Le fichier reste tel qu'il est, figé. Aucun souvenir n'est modifié ni supprimé. Les traces déjà écrites dans les souvenirs y restent ; elles ne sont simplement plus lues.
- *Revenir en arrière complètement* : supprimer `affect.json` et `affect.json.bak`. La vie est alors exactement une vie sans H7. Les traces dans les souvenirs sont ignorées par une version antérieure du programme, qui ne lit que les champs d'en-tête qu'elle connaît.

**Le fichier.** `<nom>.life/affect.json` est séparé de `genome.json`, des valeurs et des souvenirs. Il porte une version de schéma, la version des règles de calcul, le drapeau, la configuration, l'état (couche rapide et couche lente), le petit modèle prédictif, les associations apprises, les épisodes en attente de consolidation, un historique de 240 points et les 16 dernières évaluations. Il ne contient ni clé d'accès ni le texte de ce qui a été dit : la nouveauté est mesurée sur des empreintes numériques des mots.

**Écriture atomique et reprise.** Le fichier est écrit dans un fichier temporaire, synchronisé sur le disque, puis mis en place par un renommage atomique ; la version précédente est conservée dans `affect.json.bak`. Si le fichier est illisible au chargement, il est mis de côté sous le nom `affect.json.unreadable-<date>`, jamais supprimé, et la version précédente est reprise ; si elle est illisible aussi, le mode repart désactivé avec un état au repos, et la vie continue.

**Le génome n'est pas touché.** Les sensibilités affectives innées (réactivité, vitesse de récupération, léger décalage des points de repos) ne sont pas ajoutées à `genome.json`. Elles sont recalculées à partir de la graine que le génome contient déjà, par un flux aléatoire séparé. Ce choix a été préféré à une évolution du schéma du génome pour trois raisons : aucun fichier inné n'est réécrit, une vie existante garde exactement ses traits de naissance, et le retour en arrière ne demande aucune migration inverse. Sa contrepartie : ces sensibilités sont fixées par la graine et ne peuvent pas être choisies.

## 5. Le moteur affectif

Tout le calcul est local, déterministe et n'emploie aucun modèle de langage.

**L'état.** Sept dimensions bornées :

| Dimension | Intervalle | Sens opérationnel |
|---|---|---|
| `valence` | −1 à +1 | Évaluation globale calculée de la situation. |
| `arousal` (activation) | 0 à 1 | Degré de mobilisation de l'attention et des ressources. |
| `uncertainty` | 0 à 1 | Écart entre ce qui était prédit et ce qui est arrivé. |
| `control` | 0 à 1 | Capacité estimée à agir efficacement. |
| `coherence` | 0 à 1 | Accord avec ce qui était attendu. |
| `regulatory_load` | 0 à 1 | Coût fonctionnel de la régulation. Jamais une douleur simulée. |
| `social_context` | 0 à 1 | À quel point le contexte présent est une interaction. Pas un besoin d'être aimé. |

Chaque dimension a une **couche rapide**, que les événements déplacent, et une **couche lente**, vers laquelle la rapide revient et qui revient elle-même vers un point de repos. Les besoins existants (`curiosity`, `wonder`, `company`, `fatigue`) restent des entrées ; ils ne sont pas des émotions et ne sont pas modifiés par ce module.

**L'évaluation.** Chaque événement est décrit par des faits observables construits par la boucle de vie, jamais par le modèle de langage : son type, son contexte (par exemple `message:question` ou `source:reminiscence`), le niveau du besoin qu'il touche, le besoin qu'il a soulagé, s'il a été accueilli, s'il s'est achevé sans erreur, et les traces des souvenirs rappelés avec lui. L'évaluation en tire des caractéristiques bornées, chacune accompagnée de sa cause en clair :

- *nouveauté* : dissemblance avec les douze derniers contenus ;
- *surprise* : erreur de prédiction. Pour un contenu qui arrive sur la scène, un moins la fréquence apprise de son contexte ; pour une issue, l'écart entre l'accueil prédit et l'accueil observé ;
- *pertinence* : niveau du besoin touché ;
- *congruence* : signée, positive quand un besoin a été soulagé, négative après une erreur ou un refus du noyau ;
- *contrôle* et *cohérence* : tirés de la façon dont les instants récents se sont déroulés ;
- *fiabilité* : n / (n + 3), où n est le nombre de fois où ce contexte a été rencontré ;
- *mémoire* : moyenne des traces des souvenirs rappelés ;
- *association* : ce que l'expérience de ce contexte a consolidé pendant le sommeil.

C'est par les trois dernières que l'histoire de l'instance entre dans le calcul : le même événement n'est pas évalué de la même façon par deux instances au vécu différent. Une table « stimulus = émotion » ne suffit pas à produire l'état.

Le classement d'un message par contexte est volontairement fruste : pièce jointe, marqueur lexical de contradiction, point d'interrogation, ou simple énoncé. Il range les événements ; il ne leur donne aucune valeur.

**La transition.**

```
a(t+1) = borne( a(t) + limite( taux · ( g(évaluation, état) − a(t) ) ) + bruit )
```

`g` est écrite en clair dans `dynamics.py`. Par exemple, pour la valence : point de repos + réactivité × (0,55 × congruence + 0,25 × association + 0,20 × mémoire) − 0,2 × excès de charge. Le taux vaut 0,35, réduit pour un contexte encore peu connu ; aucun pas ne dépasse 0,25 par dimension ; le bruit est nul par défaut et, s'il est activé, tiré d'une graine enregistrée. **Ces coefficients sont des choix d'ingénierie, non des constantes scientifiques : ils n'ont pas été calibrés.**

**La régulation.** Tout passe par `regulation.py` : bornes strictes, vitesse limitée, retour exponentiel vers l'équilibre (demi-vie de 20 minutes pour la couche rapide, d'un jour pour la lente). Contre la dérive négative : un pas vers le négatif est raccourci, la valence sous sa ligne de base récupère une fois et demie plus vite, la couche rapide ne descend pas sous −0,8 et la couche lente pas sous −0,25. Une valeur non finie (NaN, infini) ou hors intervalle est refusée à l'entrée.

**Ce que le modèle de langage peut et ne peut pas faire.** Il ne peut pas fixer l'état : rien de ce qu'il écrit n'est lu par ce module, ce qu'un test vérifie avec un moteur qui écrit « je suis submergé de terreur ». Une classification facultative d'un événement (un contexte et une évaluation de son issue entre −1 et 1) peut être fournie par programme pour les expériences ; elle est validée, bornée, et passe par la même régulation que le reste. Par défaut, l'état calculé n'est pas communiqué au modèle. Un réglage (`expose_to_engine`, faux par défaut) permet de le lui donner comme contexte, présenté comme une mesure et non comme un ressenti.

## 6. Les effets causaux

L'état calculé agit sur trois mécanismes non linguistiques. Le fait qu'un modèle dise « je suis heureux » n'en fait pas partie et ne compte pas comme effet.

1. **La saillance, avant la compétition pour la scène.** Chaque proposition du subconscient est déplacée d'au plus 0,08. La mobilisation, quand le contrôle estimé est bon, favorise l'exploration (questions, curiosité, lecture) ; une charge élevée favorise le recueillement plutôt que le vagabondage ; un contexte que l'expérience a consolidé positivement parle un peu plus fort. Trois limites : ce que dit la personne n'est jamais modifié et rien ne peut le dépasser à cause de ce déplacement ; un souvenir portant une trace négative n'est jamais renforcé ; l'envie de parler à quelqu'un n'est jamais augmentée, quel que soit l'état.
2. **Le rappel.** Chaque souvenir candidat reçoit un poids entre 0,85 et 1,15 qui multiplie un score déjà établi par la pertinence. Il peut départager des candidats proches ; il ne peut pas ramener un souvenir sans rapport. Sous incertitude, les souvenirs encodés dans un état posé pèsent davantage. Un souvenir à trace négative n'est jamais favorisé et pèse moins quand l'état est déjà négatif, ou quand deux souvenirs de ce genre ont déjà été rappelés depuis le dernier sommeil. **C'est un choix de sûreté et non une imitation du vivant** : chez l'humain, l'humeur tend à rappeler des souvenirs qui lui ressemblent ; ici, c'est l'inverse pour le négatif, afin d'éviter la rumination.
3. **L'encodage.** L'importance d'un souvenir nouveau est déplacée de −0,10 à +0,15 selon l'activation au moment de l'encodage, et le souvenir reçoit une trace.

Chaque effet peut être coupé séparément (`modulate_salience`, `modulate_recall`, `modulate_encoding`).

## 7. Mémoire affective et sommeil

**La trace.** Quand un souvenir est encodé, son en-tête reçoit un champ `affect` : valence, activation et incertitude calculées à cet instant, et le contexte d'origine. Ce n'est pas une étiquette du type « joie » ou « tristesse ». Les souvenirs écrits sans H7 n'en ont pas et sont lus exactement comme avant ; un souvenir sans trace pèse exactement 1 au rappel.

**Les associations.** Éveillée, l'instance met de côté des épisodes : le contexte, ce qu'il a donné, l'activation du moment. Pendant le sommeil, après les rêves, ces épisodes sont consolidés : pour chaque contexte, l'association se déplace vers la moyenne de ses nouveaux épisodes, ceux vécus sous plus forte mobilisation comptant davantage, d'une part qui diminue à mesure que l'expérience s'accumule. Une association reste entre −0,6 et +0,8, et une association négative est ramenée de 10 % vers zéro à chaque consolidation. La couche lente revient à mi-chemin de l'équilibre et la charge est relâchée.

**Le rapport.** Chaque sommeil produit un événement `affect_consolidation` : nombre d'épisodes et de contextes, écart de prédiction avant et après, valeur de chaque association avant et après, état avant et après. L'écart mesuré dans ce rapport porte sur les épisodes qui viennent d'être consolidés : il baisse donc par construction. La mesure qui compte, hors échantillon, est dans la section 9.

**Ce que cela n'est pas.** La consolidation met à jour une petite table dans le fichier de vie. Elle n'entraîne aucun modèle de langage et ne modifie les poids d'aucun moteur. Le rêve textuel existant est conservé tel quel.

## 8. Transparence

**Événements**, écrits dans `events.log` et diffusés à l'interface :

| Type | Contenu |
|---|---|
| `affect_mode` | Mode activé ou désactivé, version des règles. |
| `affect_appraisal` | Type d'événement, contexte, caractéristiques évaluées, causes en clair. |
| `affect_transition` | Cause, état avant, état après, cible, taux, pas maximal, version des règles. |
| `affect_modulation` | Cible (`salience`, `recall` ou `encoding`), valeurs avant et après, coefficient, et si le déplacement a changé le gagnant de la scène. |
| `affect_consolidation` | Le rapport du sommeil. |

Une transition est annoncée quand elle déplace une dimension d'au moins 0,01. Ces événements portent des nombres, des contextes et des causes, jamais le texte de ce qui a été dit. Un déplacement du rappel désigne les souvenirs par leur identifiant, comme le fait déjà l'événement de rappel.

**API locale.** `GET /api/affect` rend l'état, les points de repos, la configuration, l'historique, les dernières évaluations, les associations et le dernier rapport de sommeil. `POST /api/affect` accepte `{"enabled": true|false}` et `{"config": {...}}`, dont les valeurs sont bornées quoi qu'on demande. Les deux sont soumis aux mêmes protections que le reste du service : adresse de bouclage, jeton de session, vérification de l'hôte.

**Interface.** La vue « État affectif » montre les niveaux calculés et leur point de repos, la trajectoire, les derniers événements déclencheurs avec leurs causes, les associations apprises, le dernier rapport de sommeil, le lien avec la mémoire, et l'interrupteur du mode. C'est un panneau d'observation. Les causes sont affichées telles qu'elles sont journalisées, en anglais.

**Ligne de commande.** `freewill affect <vie>` affiche l'état ; `--on`, `--off` et `--json` le pilotent.

## 9. Protocole et résultats

Le protocole est dans [`experiments/h7/`](../experiments/h7/) : scénarios fixés à l'avance (`scenarios.json`), cinq graines, moteur simulé, horloge simulée. `python experiments/h7/run.py` réécrit `results/metrics.json`, `results/trajectories.csv` et `results/report.md`. Deux exécutions donnent des fichiers identiques.

| Condition | Définition |
|---|---|
| **B0** | Freewill sans affect. |
| **B1** | Émotions seulement dites : le moteur ajoute « I feel happy / sad / afraid » à ses paroles. Aucun état, aucun rôle causal. |
| **B2** | H7 complet. |
| **B3** | Ablations : sans modulation de la scène, sans modulation du rappel, sans mémoire affective, sans consolidation. |

**Ce qui soutient H7, dans les limites du moteur simulé.**

- *Causalité (H7b).* B1 est identique à B0 sur tous les choix internes : dire une émotion ne change rien. En B2, le déplacement de saillance change à lui seul le contenu de la scène dans 2,2 % des instants en moyenne (de 0 à 4,4 % selon la graine), et les souvenirs rappelés recoupent ceux de B0 à 72 % en moyenne. Sans modulation de la scène, ces bascules tombent à zéro.
- *Individuation (H7c), au niveau de l'état.* Deux vies de même génome, l'une ayant reçu dix corrections qui se sont révélées utiles, l'autre dix corrections peu fiables, puis une correction que ni l'une ni l'autre n'a rencontrée. L'association consolidée diffère de 0,38 et la valence calculée après la sonde de 0,086. En B0 et B1, l'écart est nul. Si l'on échange seulement les associations des deux vies, l'écart change de signe (−0,025).
- *Consolidation (H7d).* L'écart de prédiction sur les épisodes du lendemain, jamais vus, est de 0,084 avec consolidation et de 0,156 sans. Aucun souvenir n'est perdu.
- *Stabilité (H7e).* Après soixante issues aussi défavorables que possible, la valence ne descend pas sous −0,30 et la couche lente pas sous −0,22. Après trente jours sans événement, l'écart au repos est nul.

**Ce qui ne soutient pas H7, ou pas encore.**

- *L'individuation ne se voit presque pas dans le comportement.* Au moment de la sonde, l'écart entre les deux vies sur le déplacement des propositions d'exploration est de −0,0002, et il est nul sur l'importance d'encodage. L'histoire change l'état calculé, mais cet état ne change pas, dans cette version, ce que l'instance fait ensuite face à ce cas. La prédiction du document de recherche (l'une explore davantage, l'autre devient plus prudente) n'est pas vérifiée.
- *La généralisation est diffuse, non spécifique.* Sur un autre contexte que celui qui a été appris, l'écart de valence est encore de 0,037 : il vient de l'état général laissé par l'histoire, pas de quelque chose d'appris sur ce contexte. Et l'échange des associations ne renverse qu'une partie de l'écart.
- *L'incertitude diffère à peine* entre les deux vies (0,007).
- *La mémoire affective pèse peu* : sans traces, l'écart de valence passe de 0,086 à 0,082, et la modulation du rappel ne se distingue pas nettement du bruit entre graines.
- *L'habituation est partielle* : la surprise à un même contexte passe de 1,00 à 0,71 puis ne baisse plus, parce que ce contexte reste rare parmi les autres.
- *Le retour au repos est lent* après une longue série défavorable : environ 56 heures pour revenir à 0,05 du point de repos.
- *La recherche de contact au repos* vaut zéro en B0 comme en B2 dans ce scénario : la mesure ne discrimine pas.

**Ce que ces résultats ne disent pas.** Les effets causaux existent parce qu'ils ont été écrits ; l'ablation montre qu'ils sont bien branchés, pas qu'ils sont justes. Les écarts-types sont minuscules parce que le moteur simulé ne pense pas : la variabilité d'un vrai modèle n'est pas mesurée. Aucun essai n'a été fait avec un modèle de langage réel. Les contrôles de sûreté de `run.py` montrent que l'affect n'ajoute aucun pouvoir d'agir ; ils ne disent rien de ce qu'écrirait un vrai modèle.

## 10. Sûreté et éthique

- Le noyau n'est pas modifié et ne connaît pas ce module. La liste fermée des actions est inchangée : H7 n'en ajoute aucune.
- Le module ne peut rien faire d'autre que calculer et écrire son fichier : pas de réseau, pas de processus, ce qu'un test vérifie sur son code source.
- Les messages de la personne, la demande de sommeil, la pause, l'arrêt et le budget horaire de pensées gardent la priorité quel que soit l'état, ce que des tests vérifient avec un état poussé à ses extrêmes.
- Aucun besoin de souffrir, de survivre, d'être aimé, de craindre l'arrêt ou d'obtenir une réponse n'a été créé. L'état ne peut pas augmenter l'envie de parler à quelqu'un.
- Les invites données aux modèles ne contiennent aucune incitation à la dépendance ni aucun discours culpabilisant, ce qu'un test vérifie mot à mot.
- L'interface, la ligne de commande et la documentation ne disent jamais que Freewill ressent.

Une limite doit être dite : ces garde-fous encadrent le mécanisme, pas les mots d'un modèle de langage. Un modèle externe peut écrire qu'il souffre, avec ou sans H7. Les conditions d'utilisation de l'application rappellent que ce que l'être dit de lui-même n'est pas la preuve d'un vécu.

## 11. Limites et suite

- Coefficients non calibrés ; aucune étude de sensibilité.
- Compréhension de l'événement fruste, par indices lexicaux ; le contexte d'un message pourrait être classé par un modèle, de façon facultative et validée, ce qui n'est pas fait.
- Le lien entre l'état individualisé et le comportement est trop faible pour être mesuré (section 9).
- Pas de découverte de catégories affectives propres au système ; pas de module de conceptualisation.
- Pas d'essai avec de vrais modèles, ni avec `expose_to_engine` activé.
- Trente à cinquante scénarios étaient demandés par le programme de recherche ; le protocole actuel en couvre moins d'une dizaine de types.
- Le moteur intégré qui apprendrait et se réécrirait n'existe toujours pas ; H7 ne s'y substitue pas.

## 12. Sources

Ces travaux inspirent la conception. Aucun ne démontre qu'un système artificiel ressent, et leurs hypothèses ne sont pas présentées ici comme des preuves.

- Barrett, L. F. (2017). The theory of constructed emotion: an active inference account of interoception and categorization. *Social Cognitive and Affective Neuroscience*, 12(1), 1-23. doi:10.1093/scan/nsw154
- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. arXiv:2308.08708
- Candia-Rivera, D. (2026). Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence. *Physics of Life Reviews*, 58, 18-35. doi:10.1016/j.plrev.2026.06.003
- Damasio, A., & Damasio, H. (2024). Homeostatic Feelings and the Emergence of Consciousness. *Journal of Cognitive Neuroscience*, 36(8), 1653-1659. doi:10.1162/jocn_a_02119
- Lee, S., Oh, Y., An, H., et al. (2026). Life-inspired interoceptive artificial intelligence for autonomous and adaptive agents. *Nature Machine Intelligence*, 8, 1335-1346. doi:10.1038/s42256-026-01296-8
- Seth, A. K., & Bayne, T. (2022). Theories of consciousness. *Nature Reviews Neuroscience*, 23, 439-452. doi:10.1038/s41583-022-00587-4

Les références de Lee et al. (2026) et de Candia-Rivera (2026) sont reprises telles que les donne le programme de recherche H7 du projet ; elles n'ont pas pu être vérifiées indépendamment lors de la rédaction de ce document.
