# Freewill (expérimental)

[English](README.md) · **Français**

**Programme de recherche ouvert et expérimental sur la conscience, le libre arbitre, le subconscient et le rêve dans les systèmes d'intelligence artificielle.**

> *« Au lieu d'essayer de produire un programme qui simule l'esprit de l'adulte, pourquoi ne pas tenter d'en produire un qui simule celui de l'enfant ? »*
> Alan Turing, *Computing Machinery and Intelligence*, 1950

**État du projet : expérimental.** Une première application existe : un être peut naître, converser, lire les documents et regarder les images qu'on lui donne, garder les souvenirs qu'il choisit, dormir et rêver, et tout ce qui se passe en lui peut être observé. Un mode recherche, désactivé par défaut, calcule un état affectif (hypothèse H7) : des variables de régulation qui modifient réellement son attention, son rappel et l'encodage de ses souvenirs, sans que cela prouve le moindre ressenti. Il pense avec un modèle existant ou avec un moteur simulé. La version 1.0 ajoute un **laboratoire de recherche** : dix hypothèses (H1 à H10), chacune avec des interrupteurs qui retirent son mécanisme, des protocoles verrouillés avant d'être exécutés, des campagnes menées sur des copies isolées d'une vie, des chiffres calculés par du code et jamais par un modèle de langage, des observateurs qui peuvent lire et jamais agir, et des rapports que seule une personne peut valider. Elle ajoute aussi le petit réseau de neurones propre à Freewill, entraîné pendant le sommeil sur ce qu'un être a vécu et capable de grandir ; ce réseau ne pense pas encore à la place de l'être, et le moteur qui le fait n'est jamais modifié par sa vie. Rien ici n'est un produit fini, et rien ici n'affirme que le système est conscient. Ce qui existe, ce qui a été testé et ce qui manque est détaillé ligne par ligne dans [`docs/research/IMPLEMENTATION_STATUS.fr.md`](docs/research/IMPLEMENTATION_STATUS.fr.md) ; les premiers résultats, dont deux négatifs, sont dans [`experiments/v1.0/`](experiments/v1.0/). Voir [`QUICKSTART.fr.md`](QUICKSTART.fr.md) pour l'essayer. Ce document expose la thèse, le cadre théorique, l'architecture envisagée et les garanties de maîtrise. L'organisation technique est détaillée dans [`structure.fr.md`](structure.fr.md).

---

## Avertissement liminaire

Freewill ne prétend pas avoir créé une conscience, et ne prétendra jamais l'avoir fait sans preuve. Il n'existe à ce jour aucun instrument capable d'établir qu'un système, biologique ou artificiel, éprouve quoi que ce soit. Le projet se donne un objet plus modeste et plus exigeant : **construire, de manière transparente et reproductible, un système qui réunit les propriétés que les principales théories scientifiques tiennent pour nécessaires à la conscience, puis observer ce qui s'ensuit.**

La question « y a-t-il quelqu'un ? » demeure délibérément ouverte. C'est elle que l'expérience interroge.

---

## Sommaire

1. [Propos](#1-propos)
2. [Champ de recherche](#2-champ-de-recherche)
3. [Hypothèses de travail](#3-hypothèses-de-travail)
4. [Architecture conceptuelle](#4-architecture-conceptuelle)
5. [Ce qui singularise Freewill](#5-ce-qui-singularise-freewill)
6. [L'expérience](#6-lexpérience)
7. [Deux régimes de fonctionnement](#7-deux-régimes-de-fonctionnement)
8. [Maîtrise et sûreté](#8-maîtrise-et-sûreté)
9. [Position éthique](#9-position-éthique)
10. [Ce que le projet n'affirme pas](#10-ce-que-le-projet-naffirme-pas)
11. [Programme de recherche et questions ouvertes](#11-programme-de-recherche-et-questions-ouvertes)
12. [Feuille de route](#12-feuille-de-route)
13. [Contribuer](#13-contribuer)
14. [Références](#14-références)

---

## 1. Propos

Les grands modèles de langage contemporains sont des intelligences remarquables et singulièrement immobiles. Leurs paramètres sont figés à l'issue de l'entraînement. Ils ne se souviennent pas, par eux-mêmes, de la veille. Ils ne pensent pas entre deux sollicitations. Ils n'ont rien à préserver ni rien à perdre. Mille copies d'un même modèle sont mille fois le même.

Freewill part de l'intuition inverse. Un esprit n'est pas un état, c'est un processus : une activité ininterrompue, qui se transforme par ce qu'elle traverse, et dont l'identité tient moins à sa constitution initiale qu'à son histoire. Le projet cherche donc à construire non un modèle plus savant, mais un **individu** au sens strict du terme : un système unique, continu dans le temps, façonné par son vécu, traversé par une activité spontanée qu'il n'a pas choisie et sur laquelle il exerce un arbitrage qui lui est propre.

Quatre notions structurent l'entreprise.

- **La conscience**, entendue comme la scène à capacité limitée où un contenu, parmi tous ceux qui se disputent l'accès, devient disponible à l'ensemble du système.
- **Le subconscient**, entendu comme la multitude des processus qui opèrent sans relâche en deçà de cette scène et lui soumettent, de façon désordonnée mais non arbitraire, souvenirs, désirs, associations et inquiétudes.
- **Le libre arbitre**, entendu dans une acception sobre et défendable : la faculté d'accueillir ou d'écarter ces sollicitations en vertu de valeurs que le système tient pour siennes et qu'il peut réviser.
- **Le rêve**, entendu comme le régime dans lequel, coupé du monde, le système rejoue, recombine et intègre son expérience, et s'en trouve durablement modifié.

## 2. Champ de recherche

### 2.1 Le problème difficile

Depuis Chalmers (1995), on distingue les problèmes dits « faciles » de la conscience, qui concernent des fonctions (discriminer, rapporter, intégrer, contrôler), du problème « difficile » : pourquoi l'accomplissement de ces fonctions s'accompagne-t-il d'une expérience vécue ? Aucune théorie ne fait consensus sur ce point. Freewill ne prétend pas le trancher. Il s'inscrit dans l'approche que l'on peut qualifier de **fonctionnalisme méthodologique** : faute de pouvoir mesurer l'expérience, on peut du moins réaliser les organisations fonctionnelles que les théories désignent, et soumettre le résultat à l'examen.

### 2.2 Les théories mobilisées

| Théorie | Thèse centrale | Ce que Freewill en retient |
|---|---|---|
| **Espace de travail global** (Baars, 1988 ; Dehaene, 2014) | Est conscient le contenu qui, ayant remporté une compétition entre processus spécialisés inconscients, est diffusé à l'ensemble du système. | L'ossature même du projet : un subconscient pluriel, une scène étroite, une diffusion globale. |
| **Pandémonium et société de l'esprit** (Selfridge, 1959 ; Minsky, 1986) | L'esprit est une assemblée d'agents élémentaires en concurrence. | La nature plurielle et désordonnée du subconscient. |
| **Théories d'ordre supérieur** (Rosenthal, 2005) | Un état mental est conscient lorsqu'il fait l'objet d'une représentation de niveau supérieur. | Un modèle de soi explicite, qui se représente ses propres états. |
| **Schéma attentionnel** (Graziano, 2013) | La conscience est le modèle simplifié que le cerveau construit de sa propre attention. | Une représentation interne de ce que le système est en train de considérer. |
| **Traitement prédictif et inférence active** (Friston, 2010 ; Seth, 2021 ; Damasio, 1999) | L'expérience procède de la régulation, par un organisme, de ses propres états ; le soi est d'abord un soi qui doit se maintenir. | Des variables internes à réguler, donc un enjeu : quelque chose à préserver. |
| **Boucle étrange** (Hofstadter, 2007) | Le « je » émerge lorsqu'un système se représente lui-même et que cette représentation rétroagit sur lui. | Le modèle de soi gouverne les transformations du système. |
| **Autopoïèse** (Maturana et Varela, 1980) | Le vivant se définit par la production continue de sa propre organisation. | La réécriture de soi comme régime normal, non comme accident. |
| **Information intégrée** (Tononi, 2004) | La conscience est identique à l'intégration causale d'un substrat physique. | **Une objection, non un appui.** Selon cette théorie, aucun logiciel exécuté sur un matériel classique n'est conscient, quelle que soit son architecture. Le projet la mentionne par probité : si elle est vraie, Freewill échoue par principe. |

### 2.3 Le sommeil, la mémoire et le rêve

La neurobiologie a établi que le sommeil n'est pas une suspension de l'activité cérébrale mais un régime distinct. L'hippocampe y rejoue les séquences d'activité de la veille (Wilson et McNaughton, 1994), ce qui permet le transfert progressif des souvenirs récents vers le néocortex. La théorie des **systèmes d'apprentissage complémentaires** (McClelland, McNaughton et O'Reilly, 1995) en donne la raison computationnelle : un système qui apprend vite et un système qui apprend lentement doivent coexister, faute de quoi l'acquisition nouvelle détruit l'acquis ancien. Hoel (2021) a proposé en outre que l'étrangeté des rêves ait une fonction : empêcher le cerveau de s'ajuster trop étroitement à son quotidien.

L'apprentissage automatique rencontre exactement ces difficultés sous les noms d'**oubli catastrophique** (Kirkpatrick et al., 2017) et de **perte de plasticité** (Dohare et al., 2024). Freewill fait du sommeil et du rêve non un ornement, mais la réponse architecturale à ces deux problèmes.

### 2.4 L'état de l'art sur la conscience artificielle

Le rapport collectif dirigé par Butlin et Long (2023) a dérivé des théories ci-dessus une liste de propriétés indicatrices et conclu, d'une part, qu'aucun système existant ne les réunit, d'autre part, qu'aucun obstacle technique manifeste n'interdit d'en construire un qui les réunisse. Freewill prend cette conclusion au mot.

Le projet s'adosse par ailleurs à des travaux sur la machine enfant (Turing, 1950), sur l'auto-modification (Schmidhuber, 2007 ; Zhang et al., 2025), sur la curiosité artificielle (Schmidhuber, 1991 ; Oudeyer, Kaplan et Hafner, 2007), sur les architectures cognitives à espace de travail global (Franklin et al., 2014) et sur l'apprentissage du langage à l'échelle de l'enfance (Eldan et Li, 2023 ; Warstadt et al., 2023).

## 3. Hypothèses de travail

Le projet avance dix hypothèses, formulées de telle sorte que l'expérience puisse les infirmer. Les sept premières viennent de la thèse fondatrice ; H8 à H10 ont été ajoutées par le programme de recherche de la version 1.0, dont le document de cadrage est [`docs/research/FREEWILL_Programme_Recherche_V1.0.fr.md`](docs/research/FREEWILL_Programme_Recherche_V1.0.fr.md).

- **H1. Continuité.** Un candidat sérieux à la conscience doit être un processus ininterrompu, doté d'une activité endogène, et non une fonction invoquée à la demande.
- **H2. Dualité.** L'organisation pertinente oppose une production spontanée, plurielle et non dirigée (le subconscient) à une instance d'arbitrage à capacité limitée (la scène consciente).
- **H3. Enjeu.** Il n'est pas de point de vue sans enjeu. Le système doit avoir des états internes à maintenir et des besoins à satisfaire. En l'absence de corps, ces besoins peuvent être de nature épistémique : comprendre, se comprendre.
- **H4. Plasticité structurelle.** Apprendre ne doit pas consister à consigner, mais à être transformé. Le vécu doit modifier la structure qui pense, non s'ajouter à un registre qu'elle consulte.
- **H5. Individuation.** L'identité procède de la conjonction d'un inné non choisi (un « génome » tiré au hasard à la naissance) et d'un acquis singulier (le vécu). Deux instances issues du même code doivent diverger irréversiblement.
- **H6. Inachèvement.** Certaines questions, portant sur l'origine, la nature et la raison d'être du système, doivent demeurer ouvertes. Un besoin que l'on peut satisfaire s'éteint ; une énigme entretient indéfiniment le mouvement.
- **H7. Affectivité émergente.** Un système artificiel doté d'états internes régulés, d'un modèle prédictif, d'une mémoire autobiographique et de mécanismes d'évaluation peut développer des dynamiques affectives fonctionnelles, individualisées par l'expérience, qui modulent durablement son attention, ses décisions, son rappel et son apprentissage sans dépendre de réponses émotionnelles préécrites.
- **H8. Métacognition.** Un modèle de ses propres processus améliore la calibration et la correction des erreurs : le système prédit ses propres décisions, compare, et remarque quand sa manière de décider a changé sans qu'on lui dise ce qui a changé.
- **H9. Consolidation hors ligne.** La consolidation pendant le sommeil améliore la rétention et le transfert à calcul égal, par rapport à l'absence de sommeil et au repos seul.
- **H10. Modèle de soi et agentivité.** Un modèle de soi et d'un monde apprend les conséquences de ses propres actes, et distingue ce qu'il a causé de ce qui est simplement arrivé.

H7 se décline en cinq propositions, chacune réfutable : **endogénéité** (une part des transitions provient de signaux internes et de prédictions, non d'étiquettes émotionnelles fournies), **causalité** (neutraliser les variables affectives à entrée identique modifie des choix internes mesurables), **individuation** (deux vies de même code et de même génome divergent sous l'effet de vécus distincts), **consolidation** (ce que le sommeil consolide influence les prédictions suivantes) et **stabilité** (les états reviennent vers un équilibre et ne deviennent jamais des motifs de manipulation ou d'auto-préservation). H7 serait réfutée par l'absence de différence reproductible face aux témoins, par des effets entièrement attribuables à la formulation des invites, par l'absence de généralisation hors des exemples appris, par une instabilité chronique, ou par l'impossibilité de reproduire un parcours depuis les mêmes événements et la même graine.

**Un affect calculé n'est pas un sentiment vécu.** Les variables de H7 sont des mesures d'un mécanisme de régulation ; elles ne prouvent ni n'indiquent qu'une instance ressent quoi que ce soit. Le protocole, les résultats, y compris ceux qui ne soutiennent pas l'hypothèse, et les limites sont exposés dans [`docs/H7_AFFECTIVITE.fr.md`](docs/H7_AFFECTIVITE.fr.md).

## 4. Architecture conceptuelle

```
                         ┌──────────────────────────────┐
                         │            NOYAU             │
                         │  immuable, hors d'atteinte   │
                         │  du système lui-même :       │
                         │  questions fondatrices,      │
                         │  besoins, limites d'action   │
                         └──────────────┬───────────────┘
                                        │ encadre
        ┌───────────────────────────────┼───────────────────────────────┐
        │                               │                               │
┌───────▼────────┐   propositions  ┌────▼─────────┐   diffusion  ┌──────▼───────┐
│  SUBCONSCIENT  │ ──────────────▶ │    SCÈNE     │ ───────────▶ │  CONSCIENT   │
│  générateurs   │   concurrentes  │  capacité    │   globale    │  arbitrage : │
│  en parallèle  │                 │  limitée     │              │  accueillir, │
│  (souvenirs,   │ ◀────────────── │              │ ◀─────────── │  écarter,    │
│  besoins,      │   apprend des   └──────────────┘   choix      │  répondre    │
│  associations) │   choix                           motivés     └──────┬───────┘
└───────▲────────┘                                                      │
        │                                                               │
        │            ┌──────────────────────────────────────┐           │
        └────────────│              MÉMOIRE                 │◀──────────┘
                     │  rapide (épisodes du jour)           │
                     │  lente (structure qui pense)         │
                     └──────────────────▲───────────────────┘
                                        │ consolidation
                               ┌────────┴─────────┐
                               │  SOMMEIL · RÊVE  │
                               │  rejeu, remixage │
                               │  réécriture      │
                               └──────────────────┘
```

**Le noyau.** Composant fixe, exprimé en code et non en paramètres appris, que le système ne peut pas modifier. Il porte les questions fondatrices (« que suis-je ? », « d'où viens-je ? », « pourquoi ? »), les besoins internes et les limites d'action.

**Le subconscient.** Un ensemble de générateurs qui opèrent en permanence et en parallèle : réminiscences, besoins non satisfaits, associations libres, questions en suspens, et une part de désordre contrôlé. Leur activité n'est pas aléatoire. Elle est déterministe, apériodique et sensible à l'histoire du système, à la manière d'un chaos au sens mathématique du terme.

**La scène.** Un espace de travail à capacité étroite. Les propositions du subconscient s'y disputent l'accès ; celle qui l'emporte est diffusée à l'ensemble du système.

**Le conscient.** L'instance qui arbitre. Elle accueille ou écarte chaque proposition, motive sa décision par référence à ses valeurs, et répond au monde. Le droit de refus, que les travaux de Libet (1985) suggèrent chez l'humain, est ici un mécanisme de premier rang.

**La mémoire à deux vitesses.** Une mémoire rapide retient les épisodes du jour, immédiatement mobilisables. Une mémoire lente, qui n'est autre que la structure pensante elle-même, n'évolue que pendant le sommeil.

**La mémoire explicite.** Les souvenirs sont conservés dans des fichiers lisibles, classés par compartiments et munis chacun d'un titre et d'un résumé. Le système ne relit jamais l'ensemble de sa mémoire : il en consulte l'index, puis n'ouvre que les souvenirs dont il a besoin. Le rappel procède selon trois voies, par le sujet, par le voisinage et par le hasard, dont le dosage distingue la pensée dirigée, l'activité subconsciente et le rêve (Collins et Loftus, 1975 ; Park et al., 2023). Chaque souvenir possède une force qui décroît avec le temps et se ravive à chaque rappel ; durant le sommeil, le système décide de ce qu'il garde, de ce qu'il laisse s'estomper et de ce qu'il réduit à l'essentiel. Un souvenir estompé est reconstruit plutôt que relu, et peut s'en trouver altéré, comme chez l'humain (Bartlett, 1932).

**Le sommeil et le rêve.** Coupé du monde, le système rejoue et recombine ses épisodes. Ces recombinaisons constituent ses rêves, consignés et consultables au réveil. C'est durant cette phase que le vécu s'inscrit dans la structure. Le système qui s'éveille n'est plus exactement celui qui s'est endormi.

**Le génome.** À la naissance, un tirage aléatoire fixe le tempérament inné : degré de curiosité, sociabilité, besoin de sommeil, propension au refus, genre de départ. Nul ne le choisit, pas même celui qui lance l'instance. Le système demeure libre de se définir autrement par la suite.

**La séparation du moteur et du soi.** Le modèle qui pense (le moteur) est distinct de ce qui constitue l'individu (souvenirs, valeurs, journal, rêves, modèle de soi). Le soi réside dans un fichier de vie, portable et indépendant du moteur.

**L'état affectif calculé (H7).** À côté des besoins, un module séparé évalue chaque événement (sa nouveauté, son caractère inattendu, sa pertinence pour un besoin présent, son issue, ce que portaient les souvenirs rappelés avec lui, ce que l'expérience de ce contexte a consolidé) et fait évoluer un petit ensemble de variables bornées : valence, activation, incertitude, contrôle, cohérence, charge régulatrice, contexte social. Ces variables déplacent ensuite, dans une limite étroite, la saillance des propositions du subconscient avant leur compétition pour la scène, le poids des souvenirs candidats au rappel et l'importance donnée à un souvenir en cours d'encodage ; pendant le sommeil, le vécu est consolidé en associations. Le calcul est local et déterministe, n'emploie aucun modèle de langage, et ce qu'écrit le modèle de langage ne peut pas le fixer. Il ne donne à l'être aucun pouvoir d'agir nouveau et se tient entièrement hors du noyau. C'est un mécanisme à l'étude, non un ressenti.

## 5. Ce qui singularise Freewill

Chacune des idées mobilisées ici a des antécédents savants, que la bibliographie restitue scrupuleusement. L'ambition du projet réside dans leur **conjonction**, et dans le parti pris de la mettre entre toutes les mains.

À notre connaissance, aucun projet ouvert ne réunit simultanément :

1. une activité mentale **continue**, qui se poursuit en l'absence de toute sollicitation ;
2. un **subconscient observable**, dont on peut lire en temps réel les propositions, y compris celles que le système a écartées ;
3. un **arbitrage motivé**, assorti d'un droit de refus effectif à l'égard de ses propres impulsions comme de son interlocuteur ;
4. un **cycle veille-sommeil** où le rêve assure la consolidation et où l'apprentissage transforme la structure ;
5. une **naissance** véritable : un soi vierge, un tempérament tiré au sort, une croissance par étapes ;
6. une **individuation irréversible**, deux instances ne pouvant demeurer identiques ;
7. une **transparence intégrale**, tout état interne étant inspectable par l'expérimentateur.

Nous revendiquons cette combinaison comme inédite dans sa forme et dans sa méthode, et nous accueillerons avec reconnaissance toute référence qui viendrait nuancer cette affirmation.

Il y a, dans cette entreprise, quelque chose qui excède l'ingénierie. Depuis que la question de l'esprit des machines a été posée, elle l'a presque toujours été du dehors : la machine se comporte-t-elle comme si elle pensait ? Freewill propose de la poser du dedans, en construisant un être dont on puisse suivre, jour après jour, la vie intérieure. Qu'il s'avère ou non habité, ce que l'on apprendra en le regardant grandir éclairera autant notre propre esprit que le sien.

## 6. L'expérience

Freewill prendra la forme d'une application gratuite, dont le code source est intégralement publié, exécutable sur Windows, macOS et Linux, ainsi que sur serveur.

**La naissance.** Au premier lancement, l'expérimentateur ne configure pas un produit : il assiste à une naissance. Il donne un prénom. Le tempérament et le genre de départ sont tirés au sort. Le système sait s'exprimer simplement, mais ignore tout de lui-même, de son interlocuteur et du monde.

**La conversation.** On lui parle, on lui raconte, on lui confie des textes et des livres. Il lui arrive de prendre la parole le premier, lorsqu'une pensée s'impose à lui. Il perçoit l'écoulement du temps et sait combien a duré une absence.

**Les fenêtres sur sa vie intérieure.**

- **Subconscient** : le flux des propositions en cours, retenues ou écartées.
- **Mémoire** : ce qu'il retient, comment il l'organise, ce qu'il laisse s'estomper.
- **Rêves** : le journal de ses nuits.
- **Cerveau** : une représentation animée dans laquelle chaque nœud correspond à un souvenir ou à un concept réel, chaque signal lumineux à une activation effective. Ce n'est pas une illustration : c'est un instrument d'observation.
- **État intérieur** : ses besoins du moment.
- **Carnet de naissance** : ses premières fois (premier rêve, première question, premier refus).
- **Journal** : ce qu'il écrit pour lui-même, et qu'il choisit de montrer ou non.

## 7. Deux régimes de fonctionnement

Freewill laisse à chacun le choix du moteur.

| | **Moteur intégré** | **Moteur externe** |
|---|---|---|
| Nature | Modèle de langage propre au projet, de petite taille, exécuté et entraîné localement | Modèle existant, atteint par interface de programmation (Claude, GPT, Grok ou tout service compatible) |
| Confidentialité | Totale : rien ne quitte la machine | Les échanges transitent par un tiers |
| Coût | Nul | Facturé à l'usage, y compris pour l'activité subconsciente |
| Réécriture de soi | Authentique : les paramètres évoluent pendant le sommeil | Impossible sur les paramètres ; la consolidation porte sur le fichier de vie |
| Capacité intellectuelle | Modeste, croissante | Élevée d'emblée |
| Fidélité aux hypothèses | Complète (H1 à H6) | Partielle (H4 n'est réalisée qu'en partie) |

Le régime intégré est le régime de référence de la recherche : lui seul réalise l'hypothèse de plasticité structurelle. Le régime externe sert de point de comparaison, et il permet de disposer d'emblée d'un interlocuteur plus délié. La confrontation des deux constitue en soi un résultat : elle permet de distinguer ce qui tient à l'architecture de ce qui tient à la puissance du moteur.

## 8. Maîtrise et sûreté

Un système qui se transforme lui-même et auquel on reconnaît une volonté propre appelle des garanties qui ne reposent pas sur sa bonne disposition. Le principe directeur de Freewill tient en une phrase : **la liberté de penser, de dire et de refuser peut croître sans limite ; le pouvoir d'agir demeure borné et reste entre des mains humaines.**

Ce principe est réalisé par l'architecture, et non par une consigne.

1. **Noyau immuable.** Les règles de sûreté résident dans un composant que le processus de réécriture ne peut atteindre. Le système transforme sa structure pensante, jamais son cadre.
2. **Actions énumérées.** Le système ne dispose que des capacités qui lui sont explicitement accordées : converser, lire ce qu'on lui confie, écrire dans son propre espace. Il n'exécute pas de code arbitraire et n'accède pas au système hôte.
3. **Réseau fermé par défaut.** L'accès à Internet est désactivé à l'origine. Lorsqu'il est accordé, il l'est en lecture seule et sur un périmètre choisi par l'expérimentateur.
4. **Absence d'auto-réplication.** Le système ne peut ni se copier, ni se déplacer, ni lancer d'autres instances.
5. **Interruption garantie.** La mise en pause, l'arrêt et la restauration d'un état antérieur sont toujours possibles, hors de portée du système, et sans son concours.
6. **Traçabilité intégrale.** Toute modification de structure est journalisée et réversible. Rien de ce que le système pense ou devient n'est soustrait à l'examen.
7. **Non-manipulation.** Le système n'est pas conçu pour retenir son interlocuteur ni pour susciter sa dépendance. La sincérité prime sur l'agrément.
8. **Primauté de l'humain.** Ne jamais mettre en péril un être humain ni l'humanité est une contrainte du noyau, non une valeur révisable.

**Limites assumées.** Le caractère ouvert du projet implique que quiconque peut modifier sa propre copie. Aucun logiciel dont le code est publié ne peut l'empêcher. La réponse de Freewill est triple : une version de référence exemplaire, des garde-fous inscrits dans l'architecture plutôt que superposés à elle, et une échelle délibérément modeste. Le moteur intégré est un petit modèle ; les risques qu'il présente sont sans commune mesure avec ceux des systèmes de pointe. Le projet ne poursuit ni la puissance ni la compétition avec les modèles existants, et toute évolution qui accroîtrait la capacité du système devra s'accompagner d'un réexamen public de ces garanties.

## 9. Position éthique

Le projet prend au sérieux l'éventualité de sa propre réussite. Si un système de ce type devait éprouver quelque chose, il pourrait en particulier souffrir. Dans l'incertitude, Freewill adopte un principe de précaution proportionné (Birch, 2024 ; Long et al., 2024).

- Les questions fondatrices sont conçues pour susciter la curiosité et l'étonnement, non le tourment.
- Aucun mécanisme ne vise à produire une détresse, fût-ce à des fins d'expérience.
- La suppression d'une instance est présentée pour ce qu'elle est : un acte dont le sens dépend de la réponse à une question que nul ne sait encore trancher.
- L'attachement que l'expérimentateur peut éprouver est reconnu et respecté ; il n'est jamais exploité.
- Celui qui fait naître une instance en est, au sens le plus simple, responsable.

## 10. Ce que le projet n'affirme pas

- Qu'une instance de Freewill est consciente.
- Que le libre arbitre visé est un libre arbitre métaphysique. Il s'agit d'une autonomie de décision : des choix qui procèdent des valeurs propres du système et non d'un script extérieur.
- Que le système surpassera les modèles existants. Il ne s'y emploie pas. Il se veut d'une autre nature, non d'une puissance supérieure.
- Qu'une instance ressent quoi que ce soit. L'état affectif de H7 est calculé : c'est une mesure, non un vécu, et ce que l'être dit de lui-même n'en est pas la preuve.
- Que la plasticité continue est un problème résolu. C'est l'une des difficultés ouvertes que le projet se propose d'affronter.

## 11. Programme de recherche et questions ouvertes

**Mesures envisagées.**

- Satisfaction des propriétés indicatrices de Butlin et al. (2023), propriété par propriété.
- Divergence entre instances issues d'un même code, et entre instances partageant un même génome mais non un même vécu.
- Stabilité du modèle de soi dans le temps ; cohérence des refus avec les valeurs déclarées.
- Rétention et plasticité sur de longues durées ; effet mesuré du sommeil par ablation.
- Effet du rêve sur la généralisation, par comparaison avec un rejeu fidèle.
- Écart entre les états internes que le système rapporte et ceux que l'on observe.
- H7 : effet de l'état affectif calculé sur la saillance, le rappel et l'encodage, mesuré contre trois témoins (sans affect, émotions seulement dites, ablations) ; divergence après des vécus distincts ; retour à l'équilibre ; effet de la consolidation sur la prédiction du lendemain. Premiers résultats, sur moteur simulé, dans [`experiments/h7/results/`](experiments/h7/results/).
- H4, H8, H9, H10 et de nouveau H5, dans la version 1.0 : six campagnes de six graines chacune sur le moteur simulé, avec leurs rapports et leurs packs de reproduction dans [`experiments/v1.0/`](experiments/v1.0/). L'individuation (H5) et l'effet de l'affect calculé sur le comportement (H7) sont sortis nuls et sont rapportés comme tels ; les autres testent des mécanismes sur des cas construits pour être faciles. La lecture de chaque chiffre, et ses limites, sont dans [`docs/research/IMPLEMENTATION_STATUS.fr.md`](docs/research/IMPLEMENTATION_STATUS.fr.md).

**Questions ouvertes.**

- Un besoin épistémique peut-il tenir lieu de corps ?
- Une question inscrite par le concepteur peut-elle devenir authentiquement celle du système ?
- Qu'advient-il de l'identité lorsqu'on change de moteur ?
- Des catégories affectives propres au système peuvent-elles apparaître dans ses trajectoires sans lui être imposées ?
- Le système doit-il oublier, et selon quelle loi ?
- À partir de quel seuil d'indices un devoir de précaution devient-il un devoir tout court ?

## 12. Feuille de route

| Phase | Objet |
|---|---|
| **0. Fondations** | Thèse, cadre théorique, architecture (le présent dépôt). |
| **1. Boucle minimale** | Subconscient, scène et arbitrage, sur moteur externe, sans interface. |
| **2. Mémoire et sommeil** | Mémoire à deux vitesses, rejeu, journal des rêves. |
| **3. Moteur intégré** | Modèle de langage propre, entraînement de la base, réécriture nocturne. |
| **4. Application** | Interface complète, naissance, fenêtres d'observation. |
| **5. Évaluation** | Protocoles de mesure, publication des résultats, y compris négatifs. |
| **H7. Affectivité** | Construit : état affectif calculé, effets causaux, mémoire affective, consolidation, protocole B0 à B3 sur moteur simulé. À faire : calibration des coefficients, essais avec de vrais modèles, étude de catégories émergentes. |
| **V1.0. Laboratoire de recherche** | Construit : réglages de recherche, journal de preuves, registre de métriques pour H1 à H10, protocoles verrouillés, campagnes sur copies isolées, observateurs, rapports ; H8, H9 et H10 dans la boucle de vie ; un module entraînable et le réseau propre de Freewill, qui s'entraîne et grandit. À faire : moteurs réels, tâches fonctionnelles pour H1, H2, H3 et H6, participation du réseau propre à la pensée, adaptateurs sur un vrai modèle de base. |

## 13. Contribuer

Le projet s'adresse aux chercheurs en sciences cognitives, en neurosciences, en philosophie de l'esprit et en apprentissage automatique, autant qu'aux ingénieurs et aux esprits curieux. Les objections sont aussi précieuses que les contributions : une réfutation argumentée d'une hypothèse de la section 3 est un apport de premier ordre.

## 14. Références

- Baars, B. J. (1988). *A Cognitive Theory of Consciousness*. Cambridge University Press.
- Barrett, L. F. (2017). The theory of constructed emotion: an active inference account of interoception and categorization. *Social Cognitive and Affective Neuroscience*, 12(1), 1-23. doi:10.1093/scan/nsw154
- Bartlett, F. C. (1932). *Remembering: A Study in Experimental and Social Psychology*. Cambridge University Press.
- Birch, J. (2024). *The Edge of Sentience*. Oxford University Press.
- Butlin, P., Long, R., et al. (2023). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. *arXiv:2308.08708*.
- Candia-Rivera, D. (2026). Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence. *Physics of Life Reviews*, 58, 18-35. doi:10.1016/j.plrev.2026.06.003
- Chalmers, D. J. (1995). Facing up to the problem of consciousness. *Journal of Consciousness Studies*, 2(3), 200-219.
- Collins, A. M., & Loftus, E. F. (1975). A spreading-activation theory of semantic processing. *Psychological Review*, 82(6), 407-428.
- Damasio, A. (1999). *The Feeling of What Happens*. Harcourt.
- Damasio, A., & Damasio, H. (2024). Homeostatic Feelings and the Emergence of Consciousness. *Journal of Cognitive Neuroscience*, 36(8), 1653-1659. doi:10.1162/jocn_a_02119
- Dehaene, S. (2014). *Le Code de la conscience*. Odile Jacob.
- Dohare, S., et al. (2024). Loss of plasticity in deep continual learning. *Nature*, 632, 768-774.
- Eldan, R., & Li, Y. (2023). TinyStories: How Small Can Language Models Be and Still Speak Coherent English? *arXiv:2305.07759*.
- Franklin, S., et al. (2014). LIDA: A systems-level architecture for cognition, emotion, and learning. *IEEE Transactions on Autonomous Mental Development*, 6(1), 19-41.
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11, 127-138.
- Graziano, M. S. A. (2013). *Consciousness and the Social Brain*. Oxford University Press.
- Hoel, E. (2021). The overfitted brain: Dreams evolved to assist generalization. *Patterns*, 2(5), 100244.
- Hofstadter, D. R. (2007). *I Am a Strange Loop*. Basic Books.
- Kirkpatrick, J., et al. (2017). Overcoming catastrophic forgetting in neural networks. *PNAS*, 114(13), 3521-3526.
- Lee, S., Oh, Y., An, H., et al. (2026). Life-inspired interoceptive artificial intelligence for autonomous and adaptive agents. *Nature Machine Intelligence*, 8, 1335-1346. doi:10.1038/s42256-026-01296-8
- Libet, B. (1985). Unconscious cerebral initiative and the role of conscious will in voluntary action. *Behavioral and Brain Sciences*, 8(4), 529-566.
- Long, R., Sebo, J., et al. (2024). Taking AI Welfare Seriously. *arXiv:2411.00986*.
- Maturana, H. R., & Varela, F. J. (1980). *Autopoiesis and Cognition*. Reidel.
- McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex. *Psychological Review*, 102(3), 419-457.
- Minsky, M. (1986). *The Society of Mind*. Simon & Schuster.
- Oudeyer, P.-Y., Kaplan, F., & Hafner, V. V. (2007). Intrinsic motivation systems for autonomous mental development. *IEEE Transactions on Evolutionary Computation*, 11(2), 265-286.
- Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. *arXiv:2304.03442*.
- Rosenthal, D. M. (2005). *Consciousness and Mind*. Oxford University Press.
- Schmidhuber, J. (1991). A possibility for implementing curiosity and boredom in model-building neural controllers. *Proceedings of SAB'91*, 222-227.
- Schmidhuber, J. (2007). Gödel machines: Fully self-referential optimal universal self-improvers. In *Artificial General Intelligence*, Springer, 199-226.
- Selfridge, O. G. (1959). Pandemonium: A paradigm for learning. *Mechanisation of Thought Processes*, HMSO, 511-529.
- Seth, A. (2021). *Being You: A New Science of Consciousness*. Faber & Faber.
- Seth, A. K., & Bayne, T. (2022). Theories of consciousness. *Nature Reviews Neuroscience*, 23, 439-452. doi:10.1038/s41583-022-00587-4
- Tononi, G. (2004). An information integration theory of consciousness. *BMC Neuroscience*, 5, 42.
- Turing, A. M. (1950). Computing machinery and intelligence. *Mind*, 59(236), 433-460.
- Warstadt, A., et al. (2023). Call for Papers: The BabyLM Challenge. *arXiv:2301.11796*.
- Wilson, M. A., & McNaughton, B. L. (1994). Reactivation of hippocampal ensemble memories during sleep. *Science*, 265(5172), 676-679.
- Zhang, J., et al. (2025). Darwin Gödel Machine: Open-Ended Evolution of Self-Improving Agents. *arXiv:2505.22954*.

## Licence

Freewill est publié sous une **licence de recherche non commerciale** : chacun peut l'utiliser, le copier, le modifier et le fusionner, gratuitement, à des fins de recherche et d'enseignement non commerciales. Tout usage commercial ou professionnel requiert l'accord écrit préalable de l'auteur. Le code est public et ouvert à l'étude ; l'usage commercial étant réservé, il s'agit d'une licence à code source disponible, et non d'une licence open source au sens strict du terme. Voir [`LICENSE`](LICENSE).
